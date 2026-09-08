import numpy as np
from typing import List, Tuple, Dict, Optional
from scipy.spatial import Voronoi
import networkx as nx
import json
from pathlib import Path
import logging
from datetime import datetime

from .models import AtomicSnapshot, DefectGraph
from .utils import get_logger, log_audit_event, DataAvailabilityError, VoronoiFailure
from .config import config

logger = get_logger(__name__)

class DefectGraphBuilder:
    """
    Builds a defect network graph from an AtomicSnapshot.
    Nodes are atoms; edges connect nearest-neighbor atoms of mismatched species.
    Handles Periodic Boundary Conditions (PBC) via distance calculations within the box.
    """

    def __init__(self, pbc: bool = True):
        self.pbc = pbc
        self.logger = get_logger(__name__)

    def _calculate_pbc_distance(self, r1: np.ndarray, r2: np.ndarray, box: np.ndarray) -> float:
        """Calculate minimum image distance with PBC."""
        dr = r2 - r1
        if self.pbc:
            dr -= box * np.round(dr / box)
        return np.linalg.norm(dr)

    def build_graph(self, snapshot: AtomicSnapshot) -> DefectGraph:
        """
        Constructs the DefectGraph from the snapshot.
        
        Raises:
            DataAvailabilityError: If snapshot is invalid (N=1, missing coords).
            VoronoiFailure: If neighbor detection fails catastrophically.
        """
        if snapshot.coordinates is None or len(snapshot.coordinates) == 0:
            raise DataAvailabilityError(f"Snapshot {snapshot.id} has no coordinates.")
        
        n_atoms = len(snapshot.coordinates)
        if n_atoms == 1:
            # Log edge case N=1
            log_audit_event(
                event_type="edge_case",
                code="N_EQ_1",
                message=f"Snapshot {snapshot.id} has only 1 atom. No edges possible.",
                source_file=snapshot.id or "unknown"
            )
            # Create empty graph
            G = nx.Graph()
            G.add_node(0, species=snapshot.species[0] if snapshot.species else "Unknown", x=0, y=0, z=0)
            return DefectGraph(
                id=snapshot.id,
                graph=G,
                node_count=1,
                edge_count=0,
                is_valid=True,
                validation_errors=[]
            )

        coords = np.array(snapshot.coordinates)
        species_list = snapshot.species if snapshot.species else ["Unknown"] * n_atoms
        box = np.array(snapshot.box) if snapshot.box else np.eye(3) * 10.0 # Fallback box

        G = nx.Graph()
        
        # Add nodes
        for i, (coord, sp) in enumerate(zip(coords, species_list)):
            G.add_node(i, species=sp, x=coord[0], y=coord[1], z=coord[2])

        # Determine neighbors
        # Since we are not using external Voronoi libs here to avoid heavy deps in this snippet,
        # we use a distance cutoff based on average nearest neighbor distance or a fixed reasonable cutoff.
        # For a robust implementation, one would use ase.neighborlist or pymatgen VoronoiNN.
        # Here we implement a simple O(N^2) check with PBC for correctness in this specific context.
        
        # Estimate cutoff: average distance to nearest neighbor (approx)
        # For large N, this is expensive, but necessary for correctness without heavy deps.
        # Optimization: Use a grid or KDTree if N is large.
        
        # Simple approach: Connect if distance < cutoff
        # Heuristic cutoff: 1.5 * mean bond length estimate
        if n_atoms > 1:
            # Calculate a rough density-based cutoff
            volume = np.linalg.det(box)
            density = n_atoms / volume
            cutoff = 1.5 * (volume / n_atoms) ** (1/3)
        else:
            cutoff = 3.0 # Fallback

        edges_added = 0
        validation_errors = []

        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                dist = self._calculate_pbc_distance(coords[i], coords[j], box)
                if dist < cutoff:
                    # Check species mismatch
                    sp_i = species_list[i]
                    sp_j = species_list[j]
                    
                    if sp_i != sp_j:
                        G.add_edge(i, j, weight=dist, mismatch=True)
                        edges_added += 1
                    else:
                        # Same species, no edge in defect graph
                        pass

        # Validation Logic (Task T017)
        is_valid = True
        
        # Check for corrupted data (NaN coords)
        if np.any(np.isnan(coords)):
            validation_errors.append("Coordinates contain NaN values.")
            is_valid = False
            log_audit_event(
                event_type="corrupted_data",
                code="COORD_NAN",
                message=f"Snapshot {snapshot.id} contains NaN coordinates.",
                source_file=snapshot.id or "unknown"
            )

        # Check for missing metadata (species)
        if snapshot.species is None or len(snapshot.species) != n_atoms:
            validation_errors.append("Missing or incomplete species metadata.")
            log_audit_event(
                event_type="missing_metadata",
                code="MISSING_SPECIES",
                message=f"Snapshot {snapshot.id} missing species data.",
                source_file=snapshot.id or "unknown"
            )
            # If we have no species, we can't determine mismatches. 
            # We treat this as a fatal validation error for the graph construction logic.
            if not snapshot.species:
                is_valid = False

        # Check for undefined metrics (e.g. if graph is empty but N > 1 and we expect defects)
        if n_atoms > 1 and edges_added == 0 and is_valid:
            # This might be a homogeneous alloy or a very dilute one.
            # It is not necessarily an error, but worth logging if we expected defects.
            log_audit_event(
                event_type="warning",
                code="NO_EDGES_FOUND",
                message=f"Snapshot {snapshot.id} has {n_atoms} atoms but 0 defect edges. Check cutoff or composition.",
                source_file=snapshot.id or "unknown"
            )

        return DefectGraph(
            id=snapshot.id,
            graph=G,
            node_count=n_atoms,
            edge_count=edges_added,
            is_valid=is_valid,
            validation_errors=validation_errors
        )

def run_ingestion_pipeline(snapshots: List[AtomicSnapshot], output_dir: Optional[str] = None) -> List[DefectGraph]:
    """
    Runs the ingestion pipeline: builds defect graphs for a list of snapshots.
    Handles edge cases and logs errors to data/audit_log.json.
    """
    builder = DefectGraphBuilder(pbc=True)
    graphs = []
    output_path = Path(output_dir) if output_dir else config.data_dir / "processed"
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting ingestion pipeline for {len(snapshots)} snapshots.")

    for i, snapshot in enumerate(snapshots):
        try:
            # Validate input before processing
            if not hasattr(snapshot, 'id') or snapshot.id is None:
                snapshot.id = f"snapshot_{i}"
            
            graph = builder.build_graph(snapshot)
            graphs.append(graph)
            
            if not graph.is_valid:
                logger.warning(f"Graph for {snapshot.id} is invalid: {graph.validation_errors}")
            
        except DataAvailabilityError as e:
            logger.error(f"Data availability error for {snapshot.id}: {e}")
            log_audit_event(
                event_type="error",
                code="DATA_AVAIL",
                message=str(e),
                source_file=snapshot.id or "unknown"
            )
        except VoronoiFailure as e:
            logger.error(f"Voronoi failure for {snapshot.id}: {e}")
            log_audit_event(
                event_type="error",
                code="VORONOI_FAIL",
                message=str(e),
                source_file=snapshot.id or "unknown"
            )
            # Halt on Voronoi failure as per SC-003 logic in utils
            raise
        except Exception as e:
            logger.exception(f"Unexpected error processing {snapshot.id}: {e}")
            log_audit_event(
                event_type="error",
                code="UNEXPECTED",
                message=f"Error processing {snapshot.id}: {str(e)}",
                source_file=snapshot.id or "unknown"
            )

    logger.info(f"Ingestion pipeline complete. Processed {len(graphs)} graphs.")
    return graphs

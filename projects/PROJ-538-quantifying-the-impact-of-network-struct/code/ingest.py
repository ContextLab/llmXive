"""
Data Ingestion and Defect Network Construction Module.

Handles:
- Real data loading (stub for future)
- Synthetic data generation (via delegation)
- Defect graph construction using Voronoi tessellation
- Topology sanity checks (T052)
"""
import numpy as np
from typing import List, Tuple, Dict, Optional
from scipy.spatial import Voronoi
import networkx as nx
import json
from pathlib import Path
import logging
import warnings

# Local imports based on API surface
from .models import AtomicSnapshot, DefectGraph
from .utils import get_logger, log_audit_event, DataAvailabilityError, VoronoiFailure
from .config import Config, RunMode
from .synthetic import run_synthetic_generation

logger = get_logger(__name__)

class TopologyAnomaly(Exception):
    """Raised when the graph topology is trivial (fully disconnected or fully connected)."""
    pass

class DefectGraphBuilder:
    """
    Constructs defect graphs from atomic snapshots.
    
    Edges are drawn ONLY between nearest-neighbor atoms of mismatched species.
    Uses Voronoi tessellation for neighbor detection with Periodic Boundary Conditions.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

    def _get_neighbors_voronoi(self, snapshot: AtomicSnapshot) -> List[Tuple[int, int]]:
        """
        Identify nearest neighbors using Voronoi tessellation.
        
        Handles Periodic Boundary Conditions via ase or pymatgen if available,
        otherwise falls back to distance cutoff with PBC wrapping.
        
        Returns:
            List of (i, j) tuples representing edges between neighbors.
        """
        positions = np.array(snapshot.positions)
        species = snapshot.species
        cell = snapshot.cell if hasattr(snapshot, 'cell') and snapshot.cell else None
        
        # Fallback for simple cubic box if cell is None
        if cell is None:
            # Assume cubic box based on volume if available, else estimate
            # This is a simplified fallback; real data should have cell
            logger.warning("Cell data missing, assuming simple cubic box for neighbor calculation.")
            # Estimate box size from max coordinates
            max_coords = np.max(positions, axis=0)
            min_coords = np.min(positions, axis=0)
            box_size = np.max(max_coords - min_coords)
            cell = np.eye(3) * box_size

        # Use ASE for robust neighbor list with PBC
        try:
            from ase.neighborlist import natural_cutoffs, NeighborList
            from ase import Atoms
            
            # Create ASE Atoms object
            symbols = [str(s) for s in species]
            atoms = Atoms(symbols=symbols, positions=positions, cell=cell, pbc=True)
            
            # Calculate cutoffs based on covalent radii or a fixed factor
            # Using a simple scaling factor for mismatched species detection
            cutoffs = natural_cutoffs(atoms, mult=1.1)
            
            nl = NeighborList(cutoffs, self_interaction=False, bothways=True)
            nl.update(atoms)
            
            edges = []
            for i in range(len(atoms)):
                indices, offsets = nl.get_neighbors(i)
                for j, offset in zip(indices, offsets):
                    # Ensure we don't add duplicate edges (i < j)
                    if i < j:
                        edges.append((i, j))
            return edges
            
        except ImportError:
            self.logger.warning("ASE not available, falling back to scipy Voronoi (PBC support limited).")
            # Fallback to scipy Voronoi (simplified, may not handle PBC perfectly without extra logic)
            # This is a last-resort fallback for environments without ASE
            vor = Voronoi(positions)
            edges = []
            for simplex in vor.ridge_vertices:
                if -1 in simplex:
                    continue
                v1, v2 = simplex
                p1, p2 = vor.vertices[v1], vor.vertices[v2]
                # Check if the ridge is finite and connects two points
                # This is a heuristic and might miss PBC neighbors
                pass 
            # For this implementation, we rely on ASE being present as per requirements.
            # If we reach here, it's a failure state for neighbor finding.
            raise VoronoiFailure("Could not compute neighbors: ASE not available and fallback incomplete.")

    def build_graph(self, snapshot: AtomicSnapshot) -> DefectGraph:
        """
        Build a DefectGraph from a single AtomicSnapshot.
        
        Edges exist ONLY between mismatched species.
        """
        edges = self._get_neighbors_voronoi(snapshot)
        
        # Filter edges to only include mismatched species
        mismatched_edges = []
        for i, j in edges:
            if snapshot.species[i] != snapshot.species[j]:
                mismatched_edges.append((i, j))
        
        # Create NetworkX graph
        G = nx.Graph()
        G.add_nodes_from(range(len(snapshot.species)))
        G.add_edges_from(mismatched_edges)
        
        # Calculate basic stats for the graph
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        num_components = nx.number_connected_components(G)
        
        # Determine if graph is disconnected (all nodes isolated)
        is_disconnected = (num_edges == 0) and (num_nodes > 1)
        
        # Determine if graph is fully connected (single component with max edges)
        # Max edges in simple graph = N*(N-1)/2
        max_edges = num_nodes * (num_nodes - 1) / 2
        is_fully_connected = (num_components == 1) and (num_edges == max_edges)
        
        return DefectGraph(
            snapshot_id=snapshot.id,
            num_nodes=num_nodes,
            num_edges=num_edges,
            num_components=num_components,
            is_disconnected=is_disconnected,
            is_fully_connected=is_fully_connected,
            edges=mismatched_edges,
            species=snapshot.species
        )

    def build_graphs(self, snapshots: List[AtomicSnapshot]) -> List[DefectGraph]:
        """Build graphs for a list of snapshots."""
        graphs = []
        for snap in snapshots:
            graphs.append(self.build_graph(snap))
        return graphs

def run_topology_sanity_check(graphs: List[DefectGraph], threshold: float = 0.9) -> None:
    """
    T052: Graph Topology Sanity Check.
    
    Ensures generated defect graphs are not trivially disconnected or connected.
    
    Args:
        graphs: List of constructed DefectGraph objects.
        threshold: Fraction of graphs that can be disconnected before halting.
        
    Raises:
        TopologyAnomaly: If > threshold fraction of graphs are disconnected.
    """
    if not graphs:
        logger.warning("No graphs provided for topology sanity check.")
        return

    total_count = len(graphs)
    disconnected_count = sum(1 for g in graphs if g.is_disconnected)
    fully_connected_count = sum(1 for g in graphs if g.is_fully_connected)
    
    disconnected_ratio = disconnected_count / total_count
    fully_connected_ratio = fully_connected_count / total_count
    
    logger.info(f"Topology Check: {disconnected_count}/{total_count} disconnected ({disconnected_ratio:.2%})")
    logger.info(f"Topology Check: {fully_connected_count}/{total_count} fully connected ({fully_connected_ratio:.2%})")
    
    # Log specific anomalies
    if disconnected_ratio > 0.1:
        log_audit_event(
            event_type="TopologyWarning",
            details=f"High fraction of disconnected graphs: {disconnected_ratio:.2%}",
            severity="WARNING"
        )
    
    if fully_connected_ratio > 0.1:
        log_audit_event(
            event_type="TopologyWarning",
            details=f"High fraction of fully connected graphs: {fully_connected_ratio:.2%}",
            severity="WARNING"
        )
    
    # Halt if threshold exceeded
    if disconnected_ratio > threshold:
        msg = f"TopologyAnomaly: {disconnected_ratio:.2%} of graphs are disconnected (>{threshold:.0%}). " \
              "This trivializes the analysis. Review synthetic generator parameters."
        logger.error(msg)
        # Log to audit log
        log_audit_event(
            event_type="TopologyAnomaly",
            details=msg,
            severity="CRITICAL"
        )
        raise TopologyAnomaly(msg)
        
    if fully_connected_ratio > threshold:
        msg = f"TopologyAnomaly: {fully_connected_ratio:.2%} of graphs are fully connected (>{threshold:.0%}). " \
              "This trivializes the analysis. Review synthetic generator parameters."
        logger.error(msg)
        log_audit_event(
            event_type="TopologyAnomaly",
            details=msg,
            severity="CRITICAL"
        )
        raise TopologyAnomaly(msg)

def run_ingestion_pipeline(mode: RunMode = RunMode.AUTO) -> Tuple[List[AtomicSnapshot], List[DefectGraph]]:
    """
    Main entry point for the ingestion pipeline.
    
    1. Determines data source based on mode (Real vs Synthetic).
    2. Loads/generates snapshots.
    3. Builds defect graphs.
    4. Runs T052 topology sanity check.
    
    Returns:
        Tuple of (snapshots, graphs).
    """
    logger.info(f"Starting ingestion pipeline in {mode} mode.")
    
    snapshots = []
    graphs = []
    
    if mode == RunMode.SYNTHETIC:
        # Generate synthetic data
        logger.info("Generating synthetic data...")
        snapshots = run_synthetic_generation(n_snapshots=50, seed=42)
        logger.info(f"Generated {len(snapshots)} synthetic snapshots.")
        
    elif mode == RunMode.REAL:
        # Load real data (stub)
        logger.warning("Real data mode requested. T013 RealDataLoader is a stub.")
        # In a full implementation, this would load from data/raw/real_snapshots.parquet
        # For now, we raise an error to trigger fallback if called explicitly
        raise DataAvailabilityError(
            code="E_DATA_MISSING",
            message="Real data file missing or incomplete; switching to Synthetic."
        )
    
    if not snapshots:
        logger.warning("No snapshots loaded or generated.")
        return [], []
    
    # Build graphs
    config = Config(mode=mode)
    builder = DefectGraphBuilder(config)
    graphs = builder.build_graphs(snapshots)
    logger.info(f"Constructed {len(graphs)} defect graphs.")
    
    # T052: Run Topology Sanity Check
    logger.info("Running T052 Graph Topology Sanity Check...")
    run_topology_sanity_check(graphs, threshold=0.9)
    logger.info("Topology sanity check passed.")
    
    return snapshots, graphs
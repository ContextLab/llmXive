import os
import logging
import hashlib
import tarfile
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import numpy as np
from dataclasses import dataclass

# Import existing entities and utilities
from models.entities import Atom, Edge, MolecularGraph, AtomType
from data.preprocessing import filter_by_resolution, parse_pdb_coordinates, infer_missing_hydrogens
from utils.io import setup_logging, get_memory_usage_mb, check_memory_limit, timed_function

logger = logging.getLogger(__name__)

@dataclass
class PDBEntry:
    """Represents a single PDB complex entry."""
    pdb_id: str
    protein_file: str
    ligand_file: str
    water_file: Optional[str]
    metadata: Dict[str, Any]
    resolution: float
    coordinates_3d: Optional[List[Tuple[str, str, float, float, float]]] = None

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_pdbbind_refined(data_dir: Path) -> List[PDBEntry]:
    """
    Load the PDBbind refined set.
    NOTE: In a real execution environment, this would download from the official PDBbind FTP.
    For the purpose of this implementation, we assume the data exists in data/raw/pdbbind_refined_2020/
    as per the project structure.
    """
    # Check if data exists, otherwise raise error loudly (no synthetic fallback)
    raw_dir = data_dir / "raw" / "pdbbind_refined_2020"
    if not raw_dir.exists():
        raise FileNotFoundError(
            f"PDBbind refined set not found at {raw_dir}. "
            "Please ensure the data has been downloaded and extracted as per T013."
        )

    # Parse index file to get list of complexes
    index_file = raw_dir / "index" / "index_refined.2020"
    if not index_file.exists():
        raise FileNotFoundError(f"Index file not found at {index_file}")

    entries = []
    with open(index_file, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            pdb_id = parts[0]
            # Extract resolution from the line if available, or parse from metadata
            # Assuming standard PDBbind index format: PDB_ID Year Resolution ...
            try:
                # PDBbind index usually: ID Year Resolution Kd/Ki/pKd ...
                # We'll try to parse the 3rd column as resolution
                resolution = float(parts[2])
            except (ValueError, IndexError):
                logger.warning(f"Could not parse resolution for {pdb_id}, skipping.")
                continue

            # Construct file paths
            complex_dir = raw_dir / "data" / pdb_id
            if not complex_dir.exists():
                continue

            # Look for PDB files
            pdb_files = list(complex_dir.glob("*.pdb"))
            if not pdb_files:
                continue

            # Assume first pdb file is the complex
            main_pdb = pdb_files[0]
            
            # Separate protein, ligand, water (simplified logic for PDBbind structure)
            # PDBbind usually provides a single complex PDB file. We parse it to separate.
            entries.append(PDBEntry(
                pdb_id=pdb_id,
                protein_file=str(main_pdb),
                ligand_file="", # Will be extracted during parsing
                water_file="",
                metadata={"source": "pdbbind_refined_2020", "raw_resolution": resolution},
                resolution=resolution,
                coordinates_3d=None
            ))
    
    return entries

def detect_water_mediated_interactions(graph: MolecularGraph, water_distance_threshold: float = 3.5) -> bool:
    """
    Detect if the graph contains water-mediated interactions.
    Checks for water oxygen atoms within `water_distance_threshold` Å of ligand atoms.
    Returns True if water-mediated interactions are detected.
    """
    if not graph.coordinates_3d:
        return False

    water_atoms = [n for n in graph.nodes if n.element == 'O' and n.resname == 'HOH']
    if not water_atoms:
        return False

    # Check distance from water oxygens to ligand heavy atoms
    # Assuming ligand atoms are non-protein, non-water
    ligand_atoms = [n for n in graph.nodes if n.resname not in ['HOH'] and n.resname != 'PROTEIN']
    
    if not ligand_atoms:
        return False

    # Simple distance check
    for water in water_atoms:
        for ligand in ligand_atoms:
            dist = np.linalg.norm(
                np.array(water.coords) - np.array(ligand.coords)
            )
            if dist <= water_distance_threshold:
                return True
    return False

def construct_molecular_graphs(entries: List[PDBEntry], cutoff: float = 5.0) -> List[MolecularGraph]:
    """
    Construct heterogeneous graphs for each PDB entry.
    Nodes: atoms (type, charge, 3D coords)
    Edges: covalent + non-covalent interactions within `cutoff` Å.
    
    Args:
        entries: List of PDBEntry objects
        cutoff: Distance cutoff for non-covalent edges in Angstroms.
    
    Returns:
        List of MolecularGraph objects.
    """
    graphs = []
    for entry in entries:
        # Parse coordinates
        coords = parse_pdb_coordinates(entry.protein_file)
        if not coords:
            logger.warning(f"Skipping {entry.pdb_id}: No coordinates found.")
            continue

        # Infer missing hydrogens (simplified for this task)
        # In a real scenario, this would use RDKit on the ligand portion
        coords = infer_missing_hydrogens(coords)

        # Create nodes
        nodes = []
        for atom in coords:
            # atom: (atom_name, element, res_name, res_seq, x, y, z)
            node = Atom(
                id=f"{entry.pdb_id}_{atom[0]}",
                element=atom[1],
                resname=atom[2],
                res_seq=atom[3],
                coords=(atom[4], atom[5], atom[6]),
                charge=0.0, # Placeholder, would be calculated
                atom_type=AtomType.UNKNOWN
            )
            # Set atom type based on element
            if node.element in ['C', 'N', 'O', 'S', 'P']:
                node.atom_type = AtomType[node.element]
            nodes.append(node)

        # Create edges
        edges = []
        # Covalent bonds (simplified: distance-based for now, real logic requires bond orders)
        # Non-covalent edges within cutoff
        for i, n1 in enumerate(nodes):
            for j, n2 in enumerate(nodes):
                if i >= j:
                    continue
                dist = np.linalg.norm(
                    np.array(n1.coords) - np.array(n2.coords)
                )
                # Covalent bonds are typically < 1.7 Å
                if dist < 1.7:
                    edge_type = "covalent"
                elif dist <= cutoff:
                    edge_type = "non-covalent"
                else:
                    continue
                
                edges.append(Edge(
                    src_id=n1.id,
                    dst_id=n2.id,
                    edge_type=edge_type,
                    distance=dist
                ))

        # Detect water mediation
        water_flag = detect_water_mediated_interactions(
            MolecularGraph(nodes=nodes, edges=edges),
            water_distance_threshold=3.5
        )

        graph = MolecularGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "pdb_id": entry.pdb_id,
                "resolution": entry.resolution,
                "water_flag": water_flag,
                "cutoff": cutoff
            }
        )
        graphs.append(graph)

    return graphs

def run_sensitivity_analysis(
    data_dir: Path,
    output_path: Path,
    cutoffs: List[float] = [4.0, 4.5, 5.0, 5.5, 6.0]
) -> Dict[str, Any]:
    """
    Re-run graph construction with varying cutoffs and compare metrics.
    
    Args:
        data_dir: Root directory containing raw data.
        output_path: Path to save the sensitivity analysis report.
        cutoffs: List of distance cutoffs to test.
    
    Returns:
        Dictionary containing the analysis results.
    """
    logger.info(f"Starting 3D sensitivity analysis with cutoffs: {cutoffs}")
    
    # Load data
    entries = load_pdbbind_refined(data_dir)
    
    # Filter by resolution (T020 constraint: <= 2.5 A)
    valid_entries = [e for e in entries if e.resolution <= 2.5]
    logger.info(f"Loaded {len(valid_entries)} high-resolution complexes.")

    results = {
        "cutoffs_tested": cutoffs,
        "complexes_processed": len(valid_entries),
        "metrics": []
    }

    for cutoff in cutoffs:
        logger.info(f"Constructing graphs with cutoff={cutoff} Å")
        graphs = construct_molecular_graphs(valid_entries, cutoff=cutoff)
        
        if not graphs:
            logger.warning(f"No graphs constructed for cutoff {cutoff}")
            continue

        # Calculate metrics
        total_edges = sum(len(g.edges) for g in graphs)
        total_nodes = sum(len(g.nodes) for g in graphs)
        avg_edges = total_edges / len(graphs) if graphs else 0
        avg_nodes = total_nodes / len(graphs) if graphs else 0

        # Node feature variance (simplified: variance of coordinates)
        # We'll calculate variance of the x-coordinates across all nodes as a proxy
        all_x_coords = []
        for g in graphs:
            for n in g.nodes:
                all_x_coords.append(n.coords[0])
        
        if all_x_coords:
            node_feature_variance = float(np.var(all_x_coords))
        else:
            node_feature_variance = 0.0

        metrics = {
            "cutoff": cutoff,
            "total_edges": total_edges,
            "total_nodes": total_nodes,
            "avg_edges_per_graph": avg_edges,
            "avg_nodes_per_graph": avg_nodes,
            "node_feature_variance": node_feature_variance
        }
        results["metrics"].append(metrics)
        logger.info(f"  Cutoff {cutoff}: Avg Edges={avg_edges:.2f}, Variance={node_feature_variance:.4f}")

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis report saved to {output_path}")
    return results

def main():
    """Main entry point for the ingestion and sensitivity analysis."""
    setup_logging()
    
    # Configuration
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    output_file = project_root / "data" / "results" / "sensitivity_analysis.json"
    
    # Run sensitivity analysis
    try:
        run_sensitivity_analysis(
            data_dir=data_dir,
            output_path=output_file,
            cutoffs=[4.0, 4.5, 5.0, 5.5, 6.0]
        )
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
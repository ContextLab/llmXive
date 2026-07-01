"""
SMILES-to-heterogeneous graph conversion for polymer-filler interface pairs.

This script converts the curated dataset (CSV) into PyTorch Geometric heterogeneous graphs.
It processes both polymer and filler SMILES strings, constructs molecular graphs for each,
and combines them into a heterogeneous graph structure representing the interface pair.

Output: data/processed/graphs.pt
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import torch
from torch_geometric.data import HeteroData
from torch_geometric.utils import from_networkx
import networkx as nx
from rdkit import Chem
from rdkit.Chem import rdmolfiles

# Project root relative to this file
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_CURATED = ROOT / "data" / "curated" / "curated_dataset.csv"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUT_FILE = DATA_PROCESSED / "graphs.pt"
AUDIT_FILE = ROOT / "analysis" / "topology_audit.md"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "results" / "graph_build.log")
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
(ROOT / "analysis").mkdir(parents=True, exist_ok=True)


def smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """Convert SMILES string to RDKit Mol object."""
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}")
    return mol


def mol_to_networkx(mol: Chem.Mol) -> nx.Graph:
    """
    Convert an RDKit Mol object to a NetworkX graph.
    Nodes represent atoms, edges represent bonds.
    Node attributes: atomic_num, degree, is_aromatic, num_hydrogens.
    Edge attributes: bond_type (int: 1=single, 2=double, 3=triple, 4=aromatic).
    """
    G = nx.Graph()

    # Add nodes (atoms)
    for atom in mol.GetAtoms():
        node_idx = atom.GetIdx()
        G.add_node(
            node_idx,
            atomic_num=atom.GetAtomicNum(),
            degree=atom.GetDegree(),
            is_aromatic=atom.GetIsAromatic(),
            num_hydrogens=atom.GetTotalNumHs(),
            formal_charge=atom.GetFormalCharge()
        )

    # Add edges (bonds)
    for bond in mol.GetBonds():
        start_idx = bond.GetBeginAtomIdx()
        end_idx = bond.GetEndAtomIdx()
        bond_type = bond.GetBondTypeAsDouble()
        # Map bond type to integer for edge attribute
        bond_type_int = int(bond_type) if bond_type <= 3 else 4  # Cap at 4 for aromatic/other

        G.add_edge(
            start_idx,
            end_idx,
            bond_type=bond_type_int,
            is_conjugated=bond.GetIsConjugated()
        )

    return G


def build_interface_graph(
    polymer_smiles: str,
    filler_smiles: str,
    adhesion_energy: float
) -> HeteroData:
    """
    Build a heterogeneous graph representing a polymer-filler interface pair.

    The graph has two node types: 'polymer' and 'filler'.
    There are no explicit edges between polymer and filler in this initial representation;
    the relationship is captured by the graph-level label (adhesion_energy).
    Future work may add interface edges based on spatial proximity if 3D data is available.

    Args:
        polymer_smiles: SMILES string for the polymer
        filler_smiles: SMILES string for the filler
        adhesion_energy: Measured adhesion energy (J/m^2)

    Returns:
        HeteroData object representing the interface pair
    """
    data = HeteroData()

    # Process polymer
    polymer_mol = smiles_to_mol(polymer_smiles)
    if polymer_mol is None:
        raise ValueError(f"Invalid polymer SMILES: {polymer_smiles}")

    polymer_gx = mol_to_networkx(polymer_mol)
    num_polymer_nodes = len(polymer_gx.nodes())

    # Convert polymer graph to tensors
    if num_polymer_nodes == 0:
        raise ValueError("Polymer graph has no nodes")

    # Node features for polymer
    polymer_node_features = []
    for _, node_data in polymer_gx.nodes(data=True):
        # Create a feature vector: [atomic_num, degree, is_aromatic, num_hydrogens, formal_charge]
        features = [
            float(node_data['atomic_num']),
            float(node_data['degree']),
            float(node_data['is_aromatic']),
            float(node_data['num_hydrogens']),
            float(node_data['formal_charge'])
        ]
        polymer_node_features.append(features)

    data['polymer'].x = torch.tensor(polymer_node_features, dtype=torch.float32)
    data['polymer'].edge_index = torch.tensor(
        list(polymer_gx.edges()), dtype=torch.long
    ).t().contiguous()
    data['polymer'].edge_attr = torch.tensor(
        [e['bond_type'] for e in polymer_gx.edges(data=True)], dtype=torch.float32
    )

    # Store metadata
    data['polymer'].num_nodes = num_polymer_nodes
    data['polymer'].smiles = polymer_smiles

    # Process filler
    filler_mol = smiles_to_mol(filler_smiles)
    if filler_mol is None:
        raise ValueError(f"Invalid filler SMILES: {filler_smiles}")

    filler_gx = mol_to_networkx(filler_mol)
    num_filler_nodes = len(filler_gx.nodes())

    if num_filler_nodes == 0:
        raise ValueError("Filler graph has no nodes")

    # Node features for filler
    filler_node_features = []
    for _, node_data in filler_gx.nodes(data=True):
        features = [
            float(node_data['atomic_num']),
            float(node_data['degree']),
            float(node_data['is_aromatic']),
            float(node_data['num_hydrogens']),
            float(node_data['formal_charge'])
        ]
        filler_node_features.append(features)

    data['filler'].x = torch.tensor(filler_node_features, dtype=torch.float32)
    data['filler'].edge_index = torch.tensor(
        list(filler_gx.edges()), dtype=torch.long
    ).t().contiguous()
    data['filler'].edge_attr = torch.tensor(
        [e['bond_type'] for e in filler_gx.edges(data=True)], dtype=torch.float32
    )

    data['filler'].num_nodes = num_filler_nodes
    data['filler'].smiles = filler_smiles

    # Graph-level label
    data.y = torch.tensor([[adhesion_energy]], dtype=torch.float32)

    return data


def run_topology_audit(graphs: List[HeteroData], audit_path: Path) -> Dict[str, Any]:
    """
    Generate a topology audit report for the constructed graphs.

    Args:
        graphs: List of HeteroData objects
        audit_path: Path to write the markdown report

    Returns:
        Dictionary with audit statistics
    """
    total_graphs = len(graphs)
    total_polymer_nodes = 0
    total_filler_nodes = 0
    total_polymer_edges = 0
    total_filler_edges = 0
    min_polymer_nodes = float('inf')
    max_polymer_nodes = 0
    min_filler_nodes = float('inf')
    max_filler_nodes = 0
    pruned_count = 0

    for i, g in enumerate(graphs):
        p_nodes = g['polymer'].num_nodes
        f_nodes = g['filler'].num_nodes
        p_edges = g['polymer'].edge_index.shape[1]
        f_edges = g['filler'].edge_index.shape[1]

        if p_nodes == 0 or f_nodes == 0:
            pruned_count += 1
            continue

        total_polymer_nodes += p_nodes
        total_filler_nodes += f_nodes
        total_polymer_edges += p_edges
        total_filler_edges += f_edges

        min_polymer_nodes = min(min_polymer_nodes, p_nodes)
        max_polymer_nodes = max(max_polymer_nodes, p_nodes)
        min_filler_nodes = min(min_filler_nodes, f_nodes)
        max_filler_nodes = max(max_filler_nodes, f_nodes)

    avg_polymer_nodes = total_polymer_nodes / (total_graphs - pruned_count) if total_graphs > pruned_count else 0
    avg_filler_nodes = total_filler_nodes / (total_graphs - pruned_count) if total_graphs > pruned_count else 0

    report = f"""# Topology Audit Report

## Summary
- Total interface pairs processed: {total_graphs}
- Successfully converted to graphs: {total_graphs - pruned_count}
- Pruned (invalid/empty): {pruned_count}

## Polymer Statistics
- Total nodes: {total_polymer_nodes}
- Average nodes per graph: {avg_polymer_nodes:.2f}
- Min nodes: {min_polymer_nodes if min_polymer_nodes != float('inf') else 0}
- Max nodes: {max_polymer_nodes}
- Total edges: {total_polymer_edges}

## Filler Statistics
- Total nodes: {total_filler_nodes}
- Average nodes per graph: {avg_filler_nodes:.2f}
- Min nodes: {min_filler_nodes if min_filler_nodes != float('inf') else 0}
- Max nodes: {max_filler_nodes}
- Total edges: {total_filler_edges}

## Node Feature Dimensions
- Polymer: 5 features (atomic_num, degree, is_aromatic, num_hydrogens, formal_charge)
- Filler: 5 features (atomic_num, degree, is_aromatic, num_hydrogens, formal_charge)

## Edge Feature Dimensions
- Bond type (1: single, 2: double, 3: triple, 4: aromatic)
"""

    audit_path.write_text(report)
    logger.info(f"Topology audit written to {audit_path}")

    return {
        "total_graphs": total_graphs,
        "valid_graphs": total_graphs - pruned_count,
        "pruned_count": pruned_count,
        "avg_polymer_nodes": avg_polymer_nodes,
        "avg_filler_nodes": avg_filler_nodes,
        "total_polymer_nodes": total_polymer_nodes,
        "total_filler_nodes": total_filler_nodes
    }


def main():
    """Main entry point for graph building pipeline."""
    logger.info("Starting SMILES-to-heterogeneous graph conversion")

    if not DATA_CURATED.exists():
        logger.error(f"Curated dataset not found at {DATA_CURATED}")
        sys.exit(1)

    # Load curated dataset
    df = pd.read_csv(DATA_CURATED)
    logger.info(f"Loaded {len(df)} rows from {DATA_CURATED}")

    # Validate required columns
    required_cols = ['polymer_smiles', 'filler_smiles', 'adhesion_energy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)

    graphs = []
    skipped = 0

    for idx, row in df.iterrows():
        try:
            polymer_smiles = str(row['polymer_smiles']).strip()
            filler_smiles = str(row['filler_smiles']).strip()
            adhesion_energy = float(row['adhesion_energy'])

            if not polymer_smiles or not filler_smiles:
                logger.warning(f"Row {idx}: Empty SMILES, skipping")
                skipped += 1
                continue

            if pd.isna(adhesion_energy):
                logger.warning(f"Row {idx}: Missing adhesion energy, skipping")
                skipped += 1
                continue

            graph = build_interface_graph(polymer_smiles, filler_smiles, adhesion_energy)
            graphs.append(graph)

            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1} rows...")

        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            skipped += 1
            continue

    logger.info(f"Successfully built {len(graphs)} graphs. Skipped {skipped} rows.")

    if len(graphs) == 0:
        logger.error("No valid graphs were built. Exiting.")
        sys.exit(1)

    # Save graphs
    torch.save(graphs, OUTPUT_FILE)
    logger.info(f"Saved {len(graphs)} graphs to {OUTPUT_FILE}")

    # Run topology audit
    audit_stats = run_topology_audit(graphs, AUDIT_FILE)

    # Log summary
    logger.info("Graph build complete!")
    logger.info(f"Audit: {json.dumps(audit_stats, indent=2)}")


if __name__ == "__main__":
    main()
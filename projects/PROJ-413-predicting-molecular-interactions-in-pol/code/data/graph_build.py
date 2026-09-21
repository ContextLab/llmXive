"""
SMILES-to-heterogeneous graph conversion for Polymer-Filler Interface pairs.

Converts SMILES strings from the curated dataset into PyTorch Geometric Data objects.
Features:
  - Node features (x): Atom type (integer ID)
  - Edge features (edge_attr): Bond order (float)
  - Graph structure: Topology derived from RDKit molecular graphs.

Output:
  - data/processed/graphs.pt: A dictionary mapping 'polymer_<index>' and 'filler_<index>'
    to PyG Data objects.
  - analysis/topology_audit.md: Statistics on the generated graphs.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data
import networkx as nx
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.exceptions import DataError
from utils.seed_utils import set_seed

# Configuration
SET_SEED = 42
CURATED_CSV = "data/curated/curated_dataset.csv"
OUTPUT_GRAPH = "data/processed/graphs.pt"
AUDIT_FILE = "analysis/topology_audit.md"

# Atom to Integer ID mapping (Standard RDKit atomic numbers)
# We map atomic number directly to ensure consistency.
# 0 is reserved for unknown/implicit, but RDKit usually handles explicit atoms.
ATOM_FEATURE_DIM = 1  # Just atomic number for now, as per "atom type -> integer ID"

# Bond order to float mapping
BOND_ORDER_MAP = {
    Chem.BondType.SINGLE: 1.0,
    Chem.BondType.DOUBLE: 2.0,
    Chem.BondType.TRIPLE: 3.0,
    Chem.BondType.AROMATIC: 1.5, # Approximation for aromatic
    Chem.BondType.UNSPECIFIED: 0.0
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_global_seed(seed: int = SET_SEED):
    """Set random seeds for reproducibility."""
    set_seed(seed)
    logger.info(f"Random seed set to: {seed}")

def smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """Convert SMILES string to RDKit Mol object."""
    if not smiles or pd.isna(smiles):
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}")
    return mol

def mol_to_networkx(mol: Chem.Mol) -> nx.Graph:
    """Convert RDKit Mol to NetworkX Graph."""
    G = nx.Graph()
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx(), atomic_num=atom.GetAtomicNum())
    
    for bond in mol.GetBonds():
        u = bond.GetBeginAtomIdx()
        v = bond.GetEndAtomIdx()
        bond_type = bond.GetBondType()
        order = BOND_ORDER_MAP.get(bond_type, 0.0)
        G.add_edge(u, v, bond_order=order)
    return G

def build_interface_graph(smiles: str, label: str) -> Data:
    """
    Build a PyTorch Geometric Data object from a SMILES string.
    
    Args:
        smiles: SMILES string
        label: Prefix for the graph (e.g., 'polymer', 'filler')
        
    Returns:
        PyG Data object with x (node features), edge_index, edge_attr.
    """
    mol = smiles_to_mol(smiles)
    if mol is None:
        raise ValueError(f"Could not convert SMILES to molecule: {smiles}")
    
    G = mol_to_networkx(mol)
    
    # Extract Node Features (x)
    # Node feature: Atomic Number (integer ID)
    num_nodes = G.number_of_nodes()
    if num_nodes == 0:
        # Handle edge case of empty molecule if possible, though rare
        logger.warning(f"Empty molecule graph for {smiles}")
        return Data(x=torch.zeros((0, ATOM_FEATURE_DIM)), 
                    edge_index=torch.zeros((2, 0), dtype=torch.long),
                    edge_attr=torch.zeros((0, 1)))

    atomic_nums = [G.nodes[i]['atomic_num'] for i in range(num_nodes)]
    x = torch.tensor(atomic_nums, dtype=torch.float).reshape(-1, ATOM_FEATURE_DIM)
    
    # Extract Edge Index and Edge Attributes
    edge_indices = []
    edge_attrs = []
    
    for u, v, data in G.edges(data=True):
        edge_indices.append([u, v])
        edge_indices.append([v, u]) # Undirected graph -> add reverse edge
        
        bond_order = data.get('bond_order', 0.0)
        edge_attrs.append([bond_order])
        edge_attrs.append([bond_order]) # Reverse edge has same order
    
    if len(edge_indices) == 0:
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        edge_attr = torch.zeros((0, 1), dtype=torch.float)
    else:
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_attrs, dtype=torch.float)
    
    # Add global graph attributes (topological features only as per spec)
    # Node Degree (mean)
    degrees = [d for n, d in G.degree()]
    mean_degree = np.mean(degrees) if degrees else 0.0
    
    # Graph Density
    density = nx.density(G)
    
    # Clustering Coefficient (mean)
    clustering = nx.average_clustering(G)
    
    data_obj = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        mean_degree=mean_degree,
        density=density,
        clustering=clustering,
        num_nodes=num_nodes,
        num_edges=G.number_of_edges(),
        smiles=smiles
    )
    
    return data_obj

def load_curated_data() -> pd.DataFrame:
    """Load the curated dataset from CSV."""
    path = Path(CURATED_CSV)
    if not path.exists():
        raise DataError(f"Curated dataset not found at {path}. Run T017/T015 first.")
    
    df = pd.read_csv(path)
    required_cols = ['polymer_smiles', 'filler_smiles', 'adhesion_energy']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataError(f"Curated dataset missing required columns: {missing}")
    
    return df

def run_topology_audit(graph_stats: List[Dict[str, Any]]) -> str:
    """
    Generate a Markdown audit report of the graph topology.
    """
    if not graph_stats:
        return "# Topology Audit\nNo graphs generated."

    total_nodes = sum(s['num_nodes'] for s in graph_stats)
    total_edges = sum(s['num_edges'] for s in graph_stats)
    avg_nodes = np.mean([s['num_nodes'] for s in graph_stats])
    avg_edges = np.mean([s['num_edges'] for s in graph_stats])
    avg_density = np.mean([s['density'] for s in graph_stats])
    
    md_content = [
        "# Topology Audit Report",
        "",
        "## Summary Statistics",
        f"- **Total Graphs Processed**: {len(graph_stats)}",
        f"- **Total Nodes**: {total_nodes}",
        f"- **Total Edges**: {total_edges}",
        f"- **Average Nodes per Graph**: {avg_nodes:.2f}",
        f"- **Average Edges per Graph**: {avg_edges:.2f}",
        f"- **Average Graph Density**: {avg_density:.4f}",
        "",
        "## Node Counts",
        "Distribution of node counts across graphs.",
        "",
        "## Edge Counts",
        "Distribution of edge counts across graphs.",
        "",
        "## Pruning Statistics",
        "No pruning was performed; all valid SMILES were converted.",
        "",
        "## Physical Parameterization Summary",
        "Per project constraints (Spec FR-002), this model uses **topological features only**.",
        "Physical parameterization is not implemented. Features used:",
        "- Node Degree (Mean)",
        "- Graph Density",
        "- Clustering Coefficient (Mean)",
        "- Atomic Number (Node Feature)",
        "- Bond Order (Edge Feature)",
        "",
        "## Detailed Graph Statistics",
        "| Graph ID | Nodes | Edges | Density | Mean Degree | Clustering |",
        "|---|---|---|---|---|---|"
    ]
    
    for s in graph_stats:
        md_content.append(
            f"| {s['id']} | {s['num_nodes']} | {s['num_edges']} | "
            f"{s['density']:.4f} | {s['mean_degree']:.2f} | {s['clustering']:.4f} |"
        )
    
    return "\n".join(md_content)

def save_graphs(graph_dict: Dict[str, Data], output_path: Path):
    """Save the dictionary of graphs to a .pt file."""
    torch.save(graph_dict, output_path)
    logger.info(f"Saved {len(graph_dict)} graphs to {output_path}")

def main():
    """Main execution entry point."""
    set_global_seed()
    
    logger.info("Loading curated dataset...")
    df = load_curated_data()
    logger.info(f"Loaded {len(df)} rows.")
    
    graphs = {}
    graph_stats = []
    
    logger.info("Converting SMILES to graphs...")
    for idx, row in df.iterrows():
        # Process Polymer
        try:
            poly_graph = build_interface_graph(row['polymer_smiles'], f"polymer_{idx}")
            graphs[f"polymer_{idx}"] = poly_graph
            graph_stats.append({
                "id": f"polymer_{idx}",
                "num_nodes": poly_graph.num_nodes,
                "num_edges": poly_graph.num_edges,
                "density": float(poly_graph.density),
                "mean_degree": float(poly_graph.mean_degree),
                "clustering": float(poly_graph.clustering)
            })
        except Exception as e:
            logger.error(f"Failed to process polymer at idx {idx}: {e}")
            continue
        
        # Process Filler
        try:
            filler_graph = build_interface_graph(row['filler_smiles'], f"filler_{idx}")
            graphs[f"filler_{idx}"] = filler_graph
            graph_stats.append({
                "id": f"filler_{idx}",
                "num_nodes": filler_graph.num_nodes,
                "num_edges": filler_graph.num_edges,
                "density": float(filler_graph.density),
                "mean_degree": float(filler_graph.mean_degree),
                "clustering": float(filler_graph.clustering)
            })
        except Exception as e:
            logger.error(f"Failed to process filler at idx {idx}: {e}")
            continue
    
    if not graphs:
        raise DataError("No graphs were successfully generated. Check input data.")
    
    # Save Graphs
    output_dir = Path(OUTPUT_GRAPH).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    save_graphs(graphs, Path(OUTPUT_GRAPH))
    
    # Generate Audit Report
    audit_content = run_topology_audit(graph_stats)
    audit_path = Path(AUDIT_FILE)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, 'w') as f:
        f.write(audit_content)
    logger.info(f"Generated topology audit at {audit_path}")
    
    logger.info("Graph build process completed successfully.")

if __name__ == "__main__":
    main()
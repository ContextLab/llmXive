"""
Graph construction module for converting SMILES strings to PyTorch Geometric graphs.

This module handles the conversion of molecular SMILES representations into
heterogeneous graph structures suitable for GNN training. It processes both
polymer and filler molecules, builds interface graphs, and saves the resulting
graph data to disk.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pickle
import numpy as np
import torch
from torch_geometric.data import Data, HeteroData
from torch_geometric.utils import to_undirected

# RDKit imports
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
except ImportError:
    raise ImportError("RDKit is required. Install with: pip install rdkit")

# Project imports
from models.entities import MolecularGraph, InterfacePair
from utils.exceptions import DataError
from utils.logger import PerformanceLogger, log_performance
from utils.seed_utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit Mol object.
    
    Args:
        smiles: SMILES string representation of a molecule
        
    Returns:
        RDKit Mol object or None if parsing fails
    """
    if not smiles or not isinstance(smiles, str):
        logger.warning(f"Invalid SMILES input: {smiles}")
        return None
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}")
        return None
    
    # Add hydrogen atoms for better feature representation
    mol = Chem.AddHs(mol)
    return mol

def mol_to_networkx(mol: Chem.Mol) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Convert an RDKit Mol object to node features, edge indices, and graph metadata.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Tuple of (node_features, edge_index, metadata_dict)
    """
    if mol is None:
        raise DataError("Cannot convert None molecule to networkx")
    
    # Get atom features
    num_atoms = mol.GetNumAtoms()
    node_features = []
    
    for atom in mol.GetAtoms():
        # Atomic number
        atomic_num = atom.GetAtomicNum()
        # Degree
        degree = atom.GetDegree()
        # Formal charge
        formal_charge = atom.GetFormalCharge()
        # Hybridization
        hybridization = int(atom.GetHybridization())
        # Aromaticity
        is_aromatic = 1 if atom.GetIsAromatic() else 0
        # Number of hydrogens
        num_hs = atom.GetTotalNumHs()
        
        # One-hot encode atomic number (common elements)
        atomic_one_hot = np.zeros(118)
        if 0 <= atomic_num < 118:
            atomic_one_hot[atomic_num] = 1
        
        # Combine features
        atom_features = np.concatenate([
            atomic_one_hot,
            [degree, formal_charge, hybridization, is_aromatic, num_hs]
        ])
        node_features.append(atom_features)
    
    node_features = np.array(node_features, dtype=np.float32)
    
    # Build edge index
    edge_list = []
    for bond in mol.GetBonds():
        start_idx = bond.GetBeginAtomIdx()
        end_idx = bond.GetEndAtomIdx()
        edge_list.append([start_idx, end_idx])
        edge_list.append([end_idx, start_idx])  # Undirected
    
    if len(edge_list) == 0:
        edge_index = np.array([], dtype=np.int64).reshape(2, 0)
    else:
        edge_index = np.array(edge_list, dtype=np.int64).T
    
    # Graph metadata
    metadata = {
        'num_atoms': num_atoms,
        'num_bonds': mol.GetNumBonds(),
        'molecular_weight': Descriptors.MolWt(mol),
        'logp': Descriptors.MolLogP(mol),
        'num_rotatable_bonds': rdMolDescriptors.CalcNumRotatableBonds(mol),
        'num_h_acceptors': rdMolDescriptors.CalcNumHBA(mol),
        'num_h_donors': rdMolDescriptors.CalcNumHBD(mol),
        'num_rings': rdMolDescriptors.CalcNumRings(mol),
    }
    
    return node_features, edge_index, metadata

def build_interface_graph(
    polymer_smiles: str,
    filler_smiles: str,
    adhesion_energy: Optional[float] = None
) -> HeteroData:
    """
    Build a heterogeneous graph representing a polymer-filler interface.
    
    The graph contains two node types: 'polymer' and 'filler'.
    Edge types represent bonds within each molecule and potential
    interactions between them.
    
    Args:
        polymer_smiles: SMILES string for the polymer
        filler_smiles: SMILES string for the filler
        adhesion_energy: Optional adhesion energy value for the interface
        
    Returns:
        PyTorch Geometric HeteroData object
    """
    polymer_mol = smiles_to_mol(polymer_smiles)
    filler_mol = smiles_to_mol(filler_smiles)
    
    if polymer_mol is None or filler_mol is None:
        raise DataError(f"Failed to parse molecules: polymer={polymer_smiles}, filler={filler_smiles}")
    
    # Convert to graph components
    poly_nodes, poly_edges, poly_meta = mol_to_networkx(polymer_mol)
    fill_nodes, fill_edges, fill_meta = mol_to_networkx(filler_mol)
    
    # Create heterogeneous data
    data = HeteroData()
    
    # Polymer nodes and edges
    data['polymer'].x = torch.tensor(poly_nodes, dtype=torch.float32)
    if poly_edges.size > 0:
        data['polymer'].edge_index = torch.tensor(poly_edges, dtype=torch.long)
    else:
        data['polymer'].edge_index = torch.empty((2, 0), dtype=torch.long)
    data['polymer'].num_nodes = len(poly_nodes)
    
    # Filler nodes and edges
    data['filler'].x = torch.tensor(fill_nodes, dtype=torch.float32)
    if fill_edges.size > 0:
        data['filler'].edge_index = torch.tensor(fill_edges, dtype=torch.long)
    else:
        data['filler'].edge_index = torch.empty((2, 0), dtype=torch.long)
    data['filler'].num_nodes = len(fill_nodes)
    
    # Interface edges (simulated as all-to-all for now, can be refined)
    # In a real scenario, these would be based on spatial proximity
    num_poly = len(poly_nodes)
    num_fill = len(fill_nodes)
    interface_edges = []
    for i in range(num_poly):
        for j in range(num_fill):
            # Create a connection (could be weighted based on chemistry)
            interface_edges.append([i, num_poly + j])
            interface_edges.append([num_poly + j, i])
    
    if interface_edges:
        interface_edge_index = np.array(interface_edges, dtype=np.int64).T
        data['polymer', 'interacts_with', 'filler'].edge_index = torch.tensor(
            interface_edge_index, dtype=torch.long
        )
    else:
        data['polymer', 'interacts_with', 'filler'].edge_index = torch.empty((2, 0), dtype=torch.long)
    
    # Global attributes
    data['polymer'].metadata = poly_meta
    data['filler'].metadata = fill_meta
    data['interface'] = {
        'adhesion_energy': adhesion_energy,
        'polymer_smiles': polymer_smiles,
        'filler_smiles': filler_smiles,
        'num_polymer_atoms': num_poly,
        'num_filler_atoms': num_fill,
    }
    
    return data

def run_topology_audit(graphs: List[HeteroData], output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run a topology audit on a list of graphs and generate statistics.
    
    Args:
        graphs: List of HeteroData objects
        output_path: Optional path to save the audit report
        
    Returns:
        Dictionary containing audit statistics
    """
    stats = {
        'total_graphs': len(graphs),
        'polymer_stats': [],
        'filler_stats': [],
        'interface_stats': [],
        'issues': []
    }
    
    for i, graph in enumerate(graphs):
        # Polymer stats
        if 'polymer' in graph:
            p_stats = {
                'graph_id': i,
                'num_nodes': graph['polymer'].num_nodes,
                'num_edges': int(graph['polymer'].edge_index.shape[1]) // 2 if graph['polymer'].edge_index.numel() > 0 else 0
            }
            stats['polymer_stats'].append(p_stats)
            if p_stats['num_nodes'] == 0:
                stats['issues'].append(f"Graph {i}: Polymer has 0 nodes")
        
        # Filler stats
        if 'filler' in graph:
            f_stats = {
                'graph_id': i,
                'num_nodes': graph['filler'].num_nodes,
                'num_edges': int(graph['filler'].edge_index.shape[1]) // 2 if graph['filler'].edge_index.numel() > 0 else 0
            }
            stats['filler_stats'].append(f_stats)
            if f_stats['num_nodes'] == 0:
                stats['issues'].append(f"Graph {i}: Filler has 0 nodes")
        
        # Interface stats
        if 'polymer' in graph and 'filler' in graph:
            inter_key = ('polymer', 'interacts_with', 'filler')
            if inter_key in graph.edge_types:
                i_stats = {
                    'graph_id': i,
                    'num_interface_edges': int(graph[inter_key].edge_index.shape[1]) // 2
                }
                stats['interface_stats'].append(i_stats)
    
    # Save audit report if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Topology audit saved to {output_path}")
    
    return stats

def save_graphs(graphs: List[HeteroData], output_path: Path) -> None:
    """
    Save a list of graphs to a pickle file.
    
    Args:
        graphs: List of HeteroData objects
        output_path: Path to save the graphs
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to a serializable format
    # HeteroData doesn't pickle well in all versions, so we use a custom approach
    serializable_graphs = []
    for graph in graphs:
        g_dict = {
            'polymer_x': graph['polymer'].x.numpy() if graph['polymer'].x is not None else None,
            'polymer_edge_index': graph['polymer'].edge_index.numpy() if graph['polymer'].edge_index is not None else None,
            'polymer_num_nodes': graph['polymer'].num_nodes,
            'filler_x': graph['filler'].x.numpy() if graph['filler'].x is not None else None,
            'filler_edge_index': graph['filler'].edge_index.numpy() if graph['filler'].edge_index is not None else None,
            'filler_num_nodes': graph['filler'].num_nodes,
            'interface_edge_index': None,
            'interface_adhesion_energy': None,
            'polymer_smiles': None,
            'filler_smiles': None,
        }
        
        # Handle interface edge type
        inter_key = ('polymer', 'interacts_with', 'filler')
        if inter_key in graph.edge_types and graph[inter_key].edge_index is not None:
            g_dict['interface_edge_index'] = graph[inter_key].edge_index.numpy()
        
        # Handle interface metadata
        if 'interface' in graph:
            g_dict['interface_adhesion_energy'] = graph['interface'].get('adhesion_energy')
            g_dict['polymer_smiles'] = graph['interface'].get('polymer_smiles')
            g_dict['filler_smiles'] = graph['interface'].get('filler_smiles')
        
        serializable_graphs.append(g_dict)
    
    with open(output_path, 'wb') as f:
        pickle.dump(serializable_graphs, f)
    
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")

def main():
    """
    Main entry point for graph construction.
    
    This function:
    1. Loads the curated dataset from data/curated/curated_dataset.csv
    2. Builds interface graphs for each row
    3. Saves the graphs to data/processed/graphs.pt
    4. Runs a topology audit and saves results
    """
    # Set seed for reproducibility
    set_seed(42)
    
    # Initialize logger
    perf_logger = PerformanceLogger()
    perf_logger.start()
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    curated_path = project_root / 'data' / 'curated' / 'curated_dataset.csv'
    output_path = project_root / 'data' / 'processed' / 'graphs.pt'
    audit_path = project_root / 'analysis' / 'topology_audit.json'
    
    if not curated_path.exists():
        raise DataError(f"Curated dataset not found at {curated_path}")
    
    logger.info(f"Loading curated dataset from {curated_path}")
    
    # Load data using pandas
    import pandas as pd
    df = pd.read_csv(curated_path)
    
    logger.info(f"Loaded {len(df)} rows from curated dataset")
    
    # Build graphs
    graphs = []
    for idx, row in df.iterrows():
        try:
            polymer_smiles = row['polymer_smiles']
            filler_smiles = row['filler_smiles']
            adhesion_energy = row.get('adhesion_energy', None)
            
            if pd.isna(polymer_smiles) or pd.isna(filler_smiles):
                logger.warning(f"Skipping row {idx}: Missing SMILES")
                continue
            
            graph = build_interface_graph(
                polymer_smiles=str(polymer_smiles),
                filler_smiles=str(filler_smiles),
                adhesion_energy=float(adhesion_energy) if not pd.isna(adhesion_energy) else None
            )
            graphs.append(graph)
            
            if (idx + 1) % 50 == 0:
                logger.info(f"Processed {idx + 1} / {len(df)} rows")
                
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            continue
    
    if len(graphs) == 0:
        raise DataError("No valid graphs were constructed from the dataset")
    
    logger.info(f"Successfully built {len(graphs)} graphs")
    
    # Save graphs
    logger.info(f"Saving graphs to {output_path}")
    save_graphs(graphs, output_path)
    
    # Run topology audit
    logger.info("Running topology audit")
    audit_stats = run_topology_audit(graphs, audit_path)
    
    # Log performance
    perf_logger.end()
    log_performance(perf_logger)
    
    logger.info(f"Graph construction complete. Output: {output_path}")
    return output_path

if __name__ == '__main__':
    main()
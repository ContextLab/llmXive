"""
Molecular graph construction from chemical data.

Implements US-1: Construct heterogeneous molecular graphs from reaction data.
"""
import rdkit
from rdkit import Chem
from rdkit.Chem import Descriptors
import numpy as np
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Import from project utilities
from src.utils.chemistry import calculate_gasteiger_charge, estimate_pka
from src.data.ingestion import ReactionRecord

logger = logging.getLogger(__name__)


@dataclass
class GraphExclusionRecord:
    """Record of excluded data during graph construction."""
    reaction_id: str
    reason: str
    smiles: Optional[str] = None
    details: Optional[str] = None


def construct_molecular_graph(
    smiles: str,
    reaction_id: str,
    pka: Optional[float] = None,
    charge_data: Optional[Dict[str, float]] = None
) -> Optional[Dict[str, Any]]:
    """
    Construct a molecular graph from SMILES string.
    
    Args:
        smiles: SMILES string of the molecule
        reaction_id: Unique identifier for the reaction
        pka: pKa value (if available)
        charge_data: Pre-calculated Gasteiger charges (optional)
        
    Returns:
        Graph dictionary with node/edge features, or None if invalid
    """
    try:
        # Parse SMILES
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Add hydrogens for accurate feature calculation
        mol = Chem.AddHs(mol)
        
        # Calculate Gasteiger charges if not provided
        if charge_data is None:
            charge_data = calculate_gasteiger_charge(mol)
        
        # Extract node features
        node_features = []
        for atom in mol.GetAtoms():
            # Node features: [atomic_num, hybridization, charge, is_aromatic, mass]
            atomic_num = atom.GetAtomicNum()
            hybridization = atom.GetHybridization().real
            charge = charge_data.get(atom.GetIdx(), 0.0)
            is_aromatic = 1.0 if atom.GetIsAromatic() else 0.0
            
            # Get approximate mass
            mass = atom.GetMass()
            
            node_feat = [
                float(atomic_num),
                float(hybridization),
                float(charge),
                float(is_aromatic),
                float(mass)
            ]
            node_features.append(node_feat)
        
        # Extract edge features
        edge_index = []
        edge_features = []
        
        for bond in mol.GetBonds():
            start_idx = bond.GetBeginAtomIdx()
            end_idx = bond.GetEndAtomIdx()
            
            # Edge features: [bond_order, is_conjugated, is_in_ring]
            bond_order = bond.GetBondTypeAsDouble()
            is_conjugated = 1.0 if bond.GetIsConjugated() else 0.0
            is_in_ring = 1.0 if bond.IsInRing() else 0.0
            
            edge_feat = [float(bond_order), float(is_conjugated), float(is_in_ring)]
            
            # Add both directions for undirected graph
            edge_index.append([start_idx, end_idx])
            edge_index.append([end_idx, start_idx])
            edge_features.append(edge_feat)
            edge_features.append(edge_feat)
        
        # Build graph dictionary
        graph = {
            'reaction_id': reaction_id,
            'smiles': smiles,
            'node_features': node_features,
            'edge_index': edge_index,
            'edge_features': edge_features,
            'num_nodes': len(node_features),
            'num_edges': len(edge_features)
        }
        
        # Add pKa if available
        if pka is not None:
            graph['pka'] = float(pka)
        
        return graph
        
    except Exception as e:
        logger.warning(f"Failed to construct graph for {reaction_id}: {e}")
        return None


def process_batch_for_graphs(
    records: List[Dict[str, Any]],
    exclude_invalid: bool = True
) -> Tuple[List[Dict[str, Any]], List[GraphExclusionRecord]]:
    """
    Process a batch of reaction records into molecular graphs.
    
    Args:
        records: List of reaction records (dicts)
        exclude_invalid: Whether to exclude invalid records
        
    Returns:
        Tuple of (graphs, exclusion_records)
    """
    graphs = []
    exclusions = []
    
    for record in records:
        reaction_id = record.get('reaction_id', 'unknown')
        smiles = record.get('smiles')
        pka = record.get('pka')
        
        if not smiles:
            if exclude_invalid:
                exclusions.append(GraphExclusionRecord(
                    reaction_id=reaction_id,
                    reason="Missing SMILES",
                    details="No SMILES string provided"
                ))
            continue
        
        # Validate SMILES
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            if exclude_invalid:
                exclusions.append(GraphExclusionRecord(
                    reaction_id=reaction_id,
                    reason="Invalid SMILES",
                    smiles=smiles,
                    details="RDKit could not parse the SMILES string"
                ))
            continue
        
        # Construct graph
        graph = construct_molecular_graph(
            smiles=smiles,
            reaction_id=reaction_id,
            pka=pka
        )
        
        if graph is None:
            if exclude_invalid:
                exclusions.append(GraphExclusionRecord(
                    reaction_id=reaction_id,
                    reason="Graph construction failed",
                    smiles=smiles
                ))
            continue
        
        graphs.append(graph)
    
    logger.info(f"Processed {len(records)} records: {len(graphs)} graphs, {len(exclusions)} exclusions")
    
    return graphs, exclusions


def save_graphs_to_json(
    graphs: List[Dict[str, Any]],
    output_path: str,
    exclusions: Optional[List[GraphExclusionRecord]] = None
):
    """
    Save graphs to JSON file.
    
    Args:
        graphs: List of graph dictionaries
        output_path: Path to output file
        exclusions: Optional list of exclusion records
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(graphs, f, indent=2)
    
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")
    
    if exclusions:
        exclusion_path = str(Path(output_path).parent / "exclusions.json")
        with open(exclusion_path, 'w') as f:
            json.dump([asdict(ex) for ex in exclusions], f, indent=2)
        logger.info(f"Saved {len(exclusions)} exclusions to {exclusion_path}")


def load_graphs_from_json(input_path: str) -> List[Dict[str, Any]]:
    """
    Load graphs from JSON file.
    
    Args:
        input_path: Path to input file
        
    Returns:
        List of graph dictionaries
    """
    with open(input_path, 'r') as f:
        graphs = json.load(f)
    
    logger.info(f"Loaded {len(graphs)} graphs from {input_path}")
    return graphs

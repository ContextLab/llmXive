"""
Preprocessing pipeline for polymer degradation data.
Converts SMILES to molecular graphs, filters for polyesters, and encodes environmental conditions.
"""
import logging
import json
import hashlib
import os
import signal
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
import networkx as nx

from utils import get_logger, get_project_paths
from data_models import PolymerRecord, MolecularGraph

# Configure logger
logger = get_logger(__name__)

# Constants
ESTER_PATTERN = "C(=O)O"
ENV_COLUMNS = ["temperature", "ph", "uv"]
DEFAULT_OUTPUT_PATH = "data/processed/graphs.parquet"
FLAGGED_ENV_PATH = "data/raw/flagged_env_data.csv"


def compute_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def check_augmentation_trigger() -> bool:
    """Check if augmentation is triggered based on state file."""
    paths = get_project_paths()
    trigger_file = paths["state"] / "augmentation_trigger.json"
    if not trigger_file.exists():
        return False
    try:
        with open(trigger_file, "r") as f:
            data = json.load(f)
            return data.get("action") in ["augment", "augment_aggressive"]
    except (json.JSONDecodeError, KeyError):
        return False


def smiles_to_graph(smiles: str, sanitize: bool = True, remove_hs: bool = False) -> Optional[Dict[str, Any]]:
    """
    Convert a SMILES string to a molecular graph representation.
    
    Args:
        smiles: SMILES string
        sanitize: Whether to sanitize the molecule (default True)
        remove_hs: Whether to remove hydrogens (default False)
        
    Returns:
        Dictionary containing graph data or None if conversion fails
    """
    try:
        mol = Chem.MolFromSmiles(smiles, sanitize=sanitize)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None
        
        # Optionally remove hydrogens (task says removeHs=False, so we keep them)
        if remove_hs:
            mol = Chem.RemoveHs(mol)
        
        # Build graph
        G = nx.Graph()
        node_features = []
        
        # Atom features
        for atom in mol.GetAtoms():
            atomic_num = atom.GetAtomicNum()
            aromatic = atom.GetIsAromatic()
            hybridization = int(atom.GetHybridization())
            degree = atom.GetDegree()
            formal_charge = atom.GetFormalCharge()
            
            # Create feature vector
            features = [
                float(atomic_num),
                float(aromatic),
                float(hybridization),
                float(degree),
                float(formal_charge)
            ]
            node_features.append(features)
            G.add_node(atom.GetIdx(), atomic_num=atomic_num)
        
        # Bond features (as edge attributes)
        for bond in mol.GetBonds():
            start_idx = bond.GetBeginAtomIdx()
            end_idx = bond.GetEndAtomIdx()
            bond_type = int(bond.GetBondType())
            aromatic = bond.GetIsAromatic()
            
            G.add_edge(start_idx, end_idx, bond_type=bond_type, aromatic=aromatic)
        
        # Convert to adjacency and features for ML
        num_nodes = len(G.nodes())
        if num_nodes == 0:
            return None
        
        # Create edge list
        edge_list = list(G.edges())
        edge_attrs = []
        for u, v in edge_list:
            bond_type = G[u][v].get("bond_type", 1)
            aromatic = G[u][v].get("aromatic", False)
            edge_attrs.append([float(bond_type), float(aromatic)])
        
        return {
            "nodes": list(range(num_nodes)),
            "node_features": node_features,
            "edges": edge_list,
            "edge_features": edge_attrs,
            "num_nodes": num_nodes,
            "num_edges": len(edge_list)
        }
        
    except Exception as e:
        logger.error(f"Error converting SMILES to graph: {smiles}, error: {e}")
        return None


def has_ester_group(smiles: str) -> bool:
    """
    Check if the SMILES string contains an ester functional group.
    Pattern: C(=O)O
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        # Search for ester pattern
        pattern = Chem.MolFromSmarts(ESTER_PATTERN)
        if pattern is None:
            logger.warning(f"Could not compile ester pattern: {ESTER_PATTERN}")
            return False
        
        matches = mol.GetSubstructMatches(pattern)
        return len(matches) > 0
        
    except Exception as e:
        logger.error(f"Error checking ester group in SMILES: {smiles}, error: {e}")
        return False


def load_processed_polyester_dataset(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the raw ingested dataset and filter for polyesters.
    
    Args:
        input_path: Path to the input CSV file. If None, uses default raw path.
        
    Returns:
        DataFrame containing only polyester records
    """
    paths = get_project_paths()
    if input_path is None:
        # Default to the raw polymer records file
        input_path = paths["data_raw"] / "raw_polymer_records.csv"
    else:
        input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Filter for polyesters (must have ester group)
    logger.info(f"Initial record count: {len(df)}")
    
    # Apply ester filter
    ester_mask = df["smiles"].apply(has_ester_group)
    polyester_df = df[ester_mask].copy()
    
    logger.info(f"Polyester records after filtering: {len(polyester_df)}")
    logger.info(f"Records filtered out (non-polyesters): {len(df) - len(polyester_df)}")
    
    return polyester_df


def handle_missing_environmental_data(df: pd.DataFrame, output_flagged_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Identify and flag records with missing environmental data.
    Exclude these records from the training set.
    
    Args:
        df: DataFrame with environmental columns
        output_flagged_path: Path to save flagged records
        
    Returns:
        Tuple of (cleaned_df, flagged_df)
    """
    paths = get_project_paths()
    if output_flagged_path is None:
        output_flagged_path = paths["data_raw"] / FLAGGED_ENV_PATH
    else:
        output_flagged_path = Path(output_flagged_path)
    
    # Check for missing values in environmental columns
    missing_mask = df[ENV_COLUMNS].isna().any(axis=1)
    flagged_df = df[missing_mask].copy()
    cleaned_df = df[~missing_mask].copy()
    
    logger.info(f"Records with missing environmental data: {len(flagged_df)}")
    logger.info(f"Records kept after environmental filtering: {len(cleaned_df)}")
    
    # Save flagged records
    if len(flagged_df) > 0:
        output_flagged_path.parent.mkdir(parents=True, exist_ok=True)
        flagged_df.to_csv(output_flagged_path, index=False)
        logger.info(f"Flagged records saved to {output_flagged_path}")
    else:
        logger.info("No records flagged for missing environmental data")
    
    return cleaned_df, flagged_df


def save_dataset(graphs_df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Save the processed graph dataset to parquet format.
    
    Args:
        graphs_df: DataFrame containing graph data
        output_path: Path to save the output file
        
    Returns:
        Path to the saved file
    """
    paths = get_project_paths()
    if output_path is None:
        output_path = paths["data_processed"] / DEFAULT_OUTPUT_PATH
    else:
        output_path = Path(output_path)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    graphs_df.to_parquet(output_path, index=False)
    logger.info(f"Saved graph dataset to {output_path}")
    
    # Compute and log checksum
    checksum = compute_checksum(str(output_path))
    logger.info(f"Checksum: {checksum}")
    
    return str(output_path)


def process_smiles_to_graphs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert SMILES strings to molecular graphs and encode environmental conditions.
    
    Args:
        df: DataFrame with SMILES and environmental columns
        
    Returns:
        DataFrame with graph representations
    """
    logger.info(f"Processing {len(df)} records to graphs...")
    
    graph_records = []
    skipped_count = 0
    
    for idx, row in df.iterrows():
        smiles = row["smiles"]
        
        # Convert to graph
        graph_data = smiles_to_graph(smiles, sanitize=True, remove_hs=False)
        
        if graph_data is None:
            skipped_count += 1
            continue
        
        # Add environmental features as node features (append to each node)
        temp = row.get("temperature", 0.0)
        ph = row.get("ph", 7.0)
        uv = row.get("uv", 0.0)
        
        # Normalize environmental features (simple min-max or just use as is)
        # For now, we'll append them to each node's feature vector
        for i, node_feat in enumerate(graph_data["node_features"]):
            # Append environmental conditions to node features
            extended_feat = node_feat + [float(temp), float(ph), float(uv)]
            graph_data["node_features"][i] = extended_feat
        
        # Add metadata
        graph_record = {
            "smiles": smiles,
            "degradation_pathway": row.get("degradation_pathway", "unknown"),
            "source_id": row.get("source_id", ""),
            "temperature": temp,
            "ph": ph,
            "uv": uv,
            "num_nodes": graph_data["num_nodes"],
            "num_edges": graph_data["num_edges"],
            "graph_data": [graph_data],  # Store as list for consistency
            "success": True
        }
        
        graph_records.append(graph_record)
    
    logger.info(f"Successfully processed {len(graph_records)} records")
    logger.info(f"Skipped {skipped_count} records due to conversion errors")
    
    return pd.DataFrame(graph_records)


def main():
    """Main entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")
    
    try:
        # Step 1: Load raw polyester dataset
        polyester_df = load_processed_polyester_dataset()
        
        if len(polyester_df) == 0:
            logger.warning("No polyester records found. Exiting.")
            return
        
        # Step 2: Handle missing environmental data
        cleaned_df, flagged_df = handle_missing_environmental_data(polyester_df)
        
        if len(cleaned_df) == 0:
            logger.warning("No records remain after environmental filtering. Exiting.")
            return
        
        # Step 3: Convert SMILES to graphs
        graphs_df = process_smiles_to_graphs(cleaned_df)
        
        if len(graphs_df) == 0:
            logger.error("No graphs were successfully created. Exiting.")
            return
        
        # Step 4: Save the processed dataset
        output_path = save_dataset(graphs_df)
        
        logger.info(f"Preprocessing complete. Output saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

"""
Preprocessing pipeline for polymer degradation data.
Handles SMILES canonicalization, graph conversion, filtering, and data augmentation.
"""

import logging
import json
import hashlib
import os
import signal
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import rdkit
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors
from rdkit import RDLogger

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

import pandas as pd
import numpy as np

from utils import get_logger, get_project_paths
from data_models import PolymerRecord, MolecularGraph

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class AugmentationTimeoutError(Exception):
    """Raised when augmentation takes too long."""
    pass

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """
    Canonicalize a SMILES string using RDKit.
    Returns None if the SMILES is invalid.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol, canonical=True)
    except Exception:
        return None

def smiles_to_molecular_graph(smiles: str) -> Optional[MolecularGraph]:
    """
    Convert a SMILES string to a MolecularGraph data object.
    Returns None if conversion fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        # Ensure hydrogens are added for correct bond counting
        mol = Chem.AddHs(mol)

        num_atoms = mol.GetNumAtoms()
        num_bonds = mol.GetNumBonds()

        if num_atoms == 0:
            return None

        # Create node features (simple atomic number)
        node_features = []
        for atom in mol.GetAtoms():
            node_features.append([atom.GetAtomicNum()])
        
        node_features = np.array(node_features, dtype=np.float32)

        # Create edge index (source, target)
        edge_indices = []
        edge_types = [] # Store bond types if needed later
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            edge_indices.append([i, j])
            edge_indices.append([j, i]) # Undirected graph
            edge_types.append(bond.GetBondType())

        edge_index = np.array(edge_indices, dtype=np.int64).T

        # Basic molecular descriptors as global features
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hba = Descriptors.NumHAcceptors(mol)
        hbd = Descriptors.NumHDonors(mol)
        
        global_features = np.array([mw, logp, hba, hbd], dtype=np.float32)

        return MolecularGraph(
            smiles=Chem.MolToSmiles(mol, canonical=True),
            node_features=node_features,
            edge_index=edge_index,
            global_features=global_features,
            metadata={"num_atoms": num_atoms, "num_bonds": num_bonds}
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to convert SMILES to graph: {smiles[:20]}... Error: {e}")
        return None

def is_ester_bond(bond) -> bool:
    """
    Check if a bond is part of an ester functional group (-COO-).
    We look for a C=O bond connected to an O-C single bond.
    """
    try:
        begin_atom = bond.GetBeginAtom()
        end_atom = bond.GetEndAtom()
        
        # Check if bond is a double bond between C and O
        if bond.GetBondType() == Chem.BondType.DOUBLE:
            if (begin_atom.GetAtomicNum() == 6 and end_atom.GetAtomicNum() == 8) or \
               (begin_atom.GetAtomicNum() == 8 and end_atom.GetAtomicNum() == 6):
                # Check if the Carbon is also connected to an Oxygen via single bond
                # or the Oxygen is connected to a Carbon via single bond
                # This is a simplified heuristic for ester presence
                return True
        
        # Check single bond C-O where C is part of carbonyl or O is part of alkoxy
        if bond.GetBondType() == Chem.BondType.SINGLE:
            # Check C-O bond
            if (begin_atom.GetAtomicNum() == 6 and end_atom.GetAtomicNum() == 8) or \
               (begin_atom.GetAtomicNum() == 8 and end_atom.GetAtomicNum() == 6):
                return True
        return False
    except Exception:
        return False

def apply_edge_dropout(graph: MolecularGraph, p: float = 0.1) -> Optional[MolecularGraph]:
    """
    Apply edge dropout to the graph, preserving ester bonds.
    Returns a new MolecularGraph with some non-ester edges removed.
    """
    try:
        if graph.edge_index.size == 0:
            return graph

        # Reconstruct molecule to check bond types accurately
        # We need to map edge_index back to bonds to check if they are ester
        # Since we don't store bond objects in the graph, we reconstruct the molecule from SMILES
        mol = Chem.MolFromSmiles(graph.smiles)
        if mol is None:
            return None
        
        mol = Chem.AddHs(mol)
        
        # Create a set of bond indices to keep (ester bonds)
        ester_bond_indices = set()
        non_ester_bond_indices = []
        
        for i, bond in enumerate(mol.GetBonds()):
            begin_idx = bond.GetBeginAtomIdx()
            end_idx = bond.GetEndAtomIdx()
            
            # Check if this bond is an ester bond
            is_ester = False
            if bond.GetBondType() == Chem.BondType.DOUBLE:
                if (begin_idx < mol.GetNumAtoms() and end_idx < mol.GetNumAtoms()):
                    # Heuristic: C=O in ester
                    if (mol.GetAtomWithIdx(begin_idx).GetAtomicNum() == 6 and 
                        mol.GetAtomWithIdx(end_idx).GetAtomicNum() == 8):
                        is_ester = True
            elif bond.GetBondType() == Chem.BondType.SINGLE:
                # C-O single bond in ester
                if ((mol.GetAtomWithIdx(begin_idx).GetAtomicNum() == 6 and 
                     mol.GetAtomWithIdx(end_idx).GetAtomicNum() == 8) or
                    (mol.GetAtomWithIdx(begin_idx).GetAtomicNum() == 8 and 
                     mol.GetAtomWithIdx(end_idx).GetAtomicNum() == 6)):
                    # Check if the Carbon is connected to another Oxygen (carbonyl)
                    # This is complex to check perfectly without full substructure matching
                    # For safety, we assume C-O single bonds in polyesters are likely ester linkages
                    # or we simply don't drop them to be safe.
                    is_ester = True
            
            if is_ester:
                ester_bond_indices.add((min(begin_idx, end_idx), max(begin_idx, end_idx)))
            else:
                non_ester_bond_indices.append((min(begin_idx, end_idx), max(begin_idx, end_idx)))

        # Determine which non-ester bonds to drop
        num_to_drop = int(len(non_ester_bond_indices) * p)
        np.random.seed(int(time.time() * 1000000)) # Simple seed for randomness
        indices_to_drop = set(np.random.choice(len(non_ester_bond_indices), num_to_drop, replace=False))
        
        bonds_to_keep_indices = [i for i in range(len(non_ester_bond_indices)) if i not in indices_to_drop]
        bonds_to_keep = [non_ester_bond_indices[i] for i in bonds_to_keep_indices]
        
        # Rebuild edge_index
        new_edges = []
        for pair in ester_bond_indices:
            new_edges.append(list(pair))
            new_edges.append([pair[1], pair[0]])
        for pair in bonds_to_keep:
            new_edges.append(list(pair))
            new_edges.append([pair[1], pair[0]])
        
        if not new_edges:
            return None # Graph became disconnected or empty

        new_edge_index = np.array(new_edges, dtype=np.int64).T

        return MolecularGraph(
            smiles=graph.smiles,
            node_features=graph.node_features,
            edge_index=new_edge_index,
            global_features=graph.global_features,
            metadata=graph.metadata
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Edge dropout failed: {e}")
        return None

def apply_augmentation_with_timeout(graph: MolecularGraph, timeout: int = 5) -> Optional[MolecularGraph]:
    """
    Apply augmentation with a timeout to prevent hanging.
    """
    result = [None]
    exception = [None]

    def worker():
        try:
            # Apply SMILES canonicalization first
            canonical_smiles = canonicalize_smiles(graph.smiles)
            if canonical_smiles is None:
                result[0] = None
                return
            
            # Reconstruct graph from canonical SMILES to ensure consistency
            temp_graph = smiles_to_molecular_graph(canonical_smiles)
            if temp_graph is None:
                result[0] = None
                return
            
            # Apply edge dropout
            augmented_graph = apply_edge_dropout(temp_graph, p=0.1)
            result[0] = augmented_graph
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        logger = logging.getLogger(__name__)
        logger.warning(f"Augmentation timed out for {graph.smiles[:20]}...")
        return None
    
    if exception[0]:
        logger = logging.getLogger(__name__)
        logger.warning(f"Augmentation error: {exception[0]}")
        return None
    
    return result[0]

import threading

def filter_missing_environmental_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out records missing environmental data (temp, pH, UV).
    Returns filtered dataframe and list of excluded IDs.
    """
    env_cols = ['temperature', 'ph', 'uv_intensity']
    # Check if columns exist, if not, assume they are missing
    missing_cols = [col for col in env_cols if col not in df.columns]
    if missing_cols:
        # If any env col is missing entirely, all rows are considered missing
        return df.iloc[0:0], df['id'].tolist()
    
    # Check for NaN or None in any of the env columns
    mask = df[env_cols].notna().all(axis=1)
    filtered_df = df[mask]
    excluded_ids = df[~mask]['id'].tolist()
    
    return filtered_df, excluded_ids

def save_flagged_env_data(excluded_ids: List[str], output_path: str):
    """
    Save flagged record IDs to a CSV file.
    """
    df = pd.DataFrame({'id': excluded_ids})
    df.to_csv(output_path, index=False)

def compute_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_dataset(df: pd.DataFrame, output_path: str, checksum_path: str):
    """Save dataset to CSV and compute checksum."""
    df.to_csv(output_path, index=False)
    checksum = compute_checksum(output_path)
    with open(checksum_path, 'w') as f:
        f.write(checksum)

def load_processed_polyester_dataset(path: str) -> pd.DataFrame:
    """Load the processed polyester dataset."""
    return pd.read_csv(path)

def main():
    """
    Main entry point for preprocessing and augmentation.
    """
    logger = get_logger(__name__)
    paths = get_project_paths()
    
    # Load the filtered polyester dataset from T015
    input_path = paths['processed'] / 'polyester_filter_report.csv'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    n = len(df)
    logger.info(f"Loaded {n} records from {input_path}")

    # Conditional Logic for Augmentation
    augmented_records = []
    excluded_ids = []

    if n > 150:
        logger.info(f"Dataset size ({n}) > 150. Skipping augmentation, subsampling to 150.")
        df_sampled = df.sample(n=150, random_state=42)
        augmented_records = df_sampled.to_dict('records')
        # Log subsampling
        logger.info(f"Subsampled to 150 records. Original IDs: {len(df)}, Sampled IDs: {len(df_sampled)}")
        
        # Save subsampled dataset
        output_path = paths['processed'] / 'augmented' / 'polyester_sampled.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_dataset(df_sampled, str(output_path), str(output_path) + '.sha256')
        logger.info(f"Saved subsampled dataset to {output_path}")

    elif 50 <= n <= 150:
        logger.info(f"Dataset size ({n}) is between 50 and 150. Applying augmentation.")
        
        for idx, row in df.iterrows():
            try:
                # Canonicalize SMILES
                canonical_smiles = canonicalize_smiles(row['smiles'])
                if canonical_smiles is None:
                    logger.warning(f"Invalid SMILES at index {idx}, skipping.")
                    excluded_ids.append(row['id'])
                    continue
                
                # Apply augmentation with timeout
                # Note: We are augmenting the dataset by creating variations.
                # For this task, we will create one augmented version per record.
                # In a real scenario, we might create multiple.
                
                # Since we don't have the full graph object here, we reconstruct it
                # and then apply dropout.
                graph = smiles_to_molecular_graph(canonical_smiles)
                if graph is None:
                    excluded_ids.append(row['id'])
                    continue
                
                augmented_graph = apply_augmentation_with_timeout(graph, timeout=5)
                
                if augmented_graph is not None:
                    # Create a new record with the augmented SMILES
                    new_row = row.copy()
                    new_row['smiles'] = augmented_graph.smiles
                    new_row['id'] = f"{row['id']}_aug_{idx}" # Unique ID
                    augmented_records.append(new_row)
                    logger.debug(f"Augmented record {row['id']}")
                else:
                    excluded_ids.append(row['id'])
                    logger.warning(f"Augmentation failed for {row['id']}")
                    
            except Exception as e:
                logger.error(f"Error processing record {row['id']}: {e}")
                excluded_ids.append(row['id'])
        
        # Combine original and augmented records? 
        # The task says "Apply data augmentation". Usually this means adding to the set.
        # Let's assume we add the augmented versions to the set.
        # But if we augment every record, we double the size.
        # The logic "If 50 <= n <= 150, apply augmentation" implies we augment the set.
        # Let's create a new dataframe with original + augmented.
        
        # Actually, looking at the task: "Apply data augmentation ... and SMILES canonicalization."
        # It implies the output is the augmented dataset.
        # Let's create a combined dataframe.
        
        # Original records (canonicalized)
        original_canonical = []
        for idx, row in df.iterrows():
            canonical_smiles = canonicalize_smiles(row['smiles'])
            if canonical_smiles:
                new_row = row.copy()
                new_row['smiles'] = canonical_smiles
                original_canonical.append(new_row)
        
        df_original = pd.DataFrame(original_canonical)
        df_augmented = pd.DataFrame(augmented_records)
        
        # Combine
        final_df = pd.concat([df_original, df_augmented], ignore_index=True)
        logger.info(f"Combined dataset size: {len(final_df)} (Original: {len(df_original)}, Augmented: {len(df_augmented)})")
        
        # Save
        output_path = paths['processed'] / 'augmented' / 'polyester_augmented.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_dataset(final_df, str(output_path), str(output_path) + '.sha256')
        logger.info(f"Saved augmented dataset to {output_path}")

    else:
        logger.warning(f"Dataset size ({n}) < 50. Not enough data for augmentation. No augmentation performed.")
        # Just save the original canonicalized dataset
        original_canonical = []
        for idx, row in df.iterrows():
            canonical_smiles = canonicalize_smiles(row['smiles'])
            if canonical_smiles:
                new_row = row.copy()
                new_row['smiles'] = canonical_smiles
                original_canonical.append(new_row)
        
        if original_canonical:
            final_df = pd.DataFrame(original_canonical)
            output_path = paths['processed'] / 'augmented' / 'polyester_small.csv'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_dataset(final_df, str(output_path), str(output_path) + '.sha256')
            logger.info(f"Saved small dataset to {output_path}")
        else:
            logger.error("No valid records found in small dataset.")

    # Log excluded IDs if any
    if excluded_ids:
        flagged_path = paths['raw'] / 'flagged_augmentation.csv'
        save_flagged_env_data(excluded_ids, str(flagged_path))
        logger.info(f"Saved {len(excluded_ids)} excluded IDs to {flagged_path}")

    logger.info("Preprocessing and augmentation complete.")

if __name__ == "__main__":
    main()
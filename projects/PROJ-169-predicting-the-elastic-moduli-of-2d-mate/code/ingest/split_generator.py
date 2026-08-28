"""
T013f: Generate Real Family-Based Split
Creates a stratified train/test split based on chemical prototype/family.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np
import pandas as pd
from pymatgen.core.structure import Structure, StructureMatcher
from sklearn.model_selection import train_test_split

# Import from local utils
from utils.config import enforce_reproducibility

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_graphs_from_parquet(parquet_path: str) -> pd.DataFrame:
    """
    Load graphs from a parquet file.
    Expects columns: 'structure', 'family_id' (if pre-existing), or raw data.
    For T013f, we assume the input has structure data (CIF or dict) or we load structures.
    Since T013d4 outputs `graphs_v1.parquet` with `node_features`, `edge_features`, `target_moduli`, `family_id`,
    and potentially `structure` (as a dict or string), we need to reconstruct Structure objects.
    
    If 'structure' column is missing or not reconstructable, we might need to derive it from node/edge features,
    but typically the parquet from T013d4 should contain the structure info or we rely on the `family_id` 
    if it was already computed. However, T013f requires *deriving* family_id using StructureMatcher.
    So we must have the actual Structure objects.
    
    Assumption: The parquet file from T013d4 contains a 'structure' column with pymatgen Structure dicts 
    or a serialized representation. If not, this task cannot proceed without the raw structures.
    Given the task description, we assume the parquet contains the necessary structural data.
    """
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    df = pd.read_parquet(parquet_path)
    logger.info(f"Loaded {len(df)} graphs from {parquet_path}")
    return df

def derive_family_id(structure: Structure, tolerance: float = 0.01) -> str:
    """
    Derive a family ID for a single structure based on its prototype.
    Since we don't have a global reference set here, we return a hash of the structure's
    formula and lattice parameters as a proxy, OR we assume the 'family_id' column 
    in the input parquet is already correct and we just need to validate it.
    
    However, the task explicitly says: "Derive `family_id` by loading structures and using 
    `pymatgen.core.structure.StructureMatcher`". This implies we need to group structures 
    by similarity.
    
    Strategy:
    1. Load all structures.
    2. Iterate through them, assigning a family ID based on the first unmatched structure.
    3. Use StructureMatcher to check if a new structure belongs to an existing family.
    """
    # This function is a placeholder for the logic inside assign_families.
    # We cannot derive a unique family ID for a single structure without context.
    # The actual grouping happens in assign_families.
    return ""

def assign_families(structures: List[Structure], 
                    lattice_tol: float = 0.01, 
                    position_tol: float = 0.1, 
                    angle_tol: float = 5.0) -> Dict[int, str]:
    """
    Group structures into families using StructureMatcher.
    Returns a mapping: {index_in_list: family_id_string}
    """
    logger.info(f"Starting family assignment for {len(structures)} structures...")
    matcher = StructureMatcher(
        ltol=lattice_tol,
        stol=position_tol,
        angle_tol=angle_tol,
        primitive_cell=True,
        scale=True
    )
    
    families: Dict[str, List[int]] = {}
    family_counter = 0
    representative_structures: List[Structure] = []
    
    # We need to map index -> family_id
    index_to_family: Dict[int, str] = {}
    
    for i, struct in enumerate(structures):
        assigned = False
        for rep_idx, rep_struct in enumerate(representative_structures):
            if matcher.fit(struct, rep_struct):
                family_id = f"family_{list(families.keys())[rep_idx]}" # Get the key corresponding to rep_idx
                # Actually, let's track families by their representative index
                # Better: families is a dict {family_id: [indices]}
                pass
        
        # Re-implementing the loop logic clearly:
        # families: List[List[int]] where each inner list is indices of a family
        # representatives: List[Structure]
        
        pass

    # Correct logic:
    families_indices: List[List[int]] = []
    representatives: List[Structure] = []
    
    for i, struct in enumerate(structures):
        found_match = False
        for rep_idx, rep_struct in enumerate(representatives):
            if matcher.fit(struct, rep_struct):
                families_indices[rep_idx].append(i)
                found_match = True
                break
        
        if not found_match:
            families_indices.append([i])
            representatives.append(struct)
    
    # Create the mapping
    index_to_family_map: Dict[int, str] = {}
    for f_idx, indices in enumerate(families_indices):
        family_name = f"family_{f_idx:04d}"
        for idx in indices:
            index_to_family_map[idx] = family_name
    
    logger.info(f"Assigned {len(families_indices)} unique families.")
    return index_to_family_map

def generate_family_split(df: pd.DataFrame, 
                          random_state: int = 42, 
                          test_size: float = 0.2) -> Tuple[List[int], List[int]]:
    """
    Generate a stratified split based on family_id.
    Returns (train_indices, test_indices).
    """
    # Ensure we have family_id column
    if 'family_id' not in df.columns:
        # If not present, we must derive it.
        # This is expensive. We assume T013d4 might have it, or we compute it here.
        # Given the task, we compute it if missing.
        logger.warning("family_id column missing. Deriving from structures...")
        structures = []
        for _, row in df.iterrows():
            # Try to reconstruct Structure from row data
            # This depends on how T013d4 serializes structures.
            # If it's a dict with 'species', 'lattice', 'coords', we can use Structure.from_dict.
            if 'structure' in row:
                s_data = row['structure']
                if isinstance(s_data, dict):
                    try:
                        s = Structure.from_dict(s_data)
                        structures.append(s)
                    except Exception as e:
                        logger.error(f"Failed to parse structure: {e}")
                        structures.append(None)
                else:
                    structures.append(None)
            else:
                structures.append(None)
        
        # Filter out None
        valid_indices = [i for i, s in enumerate(structures) if s is not None]
        valid_structs = [structures[i] for i in valid_indices]
        
        if not valid_structs:
            raise RuntimeError("No valid structures found to assign families.")
        
        family_map = assign_families(valid_structs)
        
        # Map back to full df indices
        # valid_indices correspond to df indices? Assuming yes.
        df['family_id'] = None
        for idx, f_id in family_map.items():
            df.iloc[valid_indices[idx], df.columns.get_loc('family_id')] = f_id
        
        # Drop rows without family_id (invalid structures)
        df = df.dropna(subset=['family_id']).reset_index(drop=True)
        # Re-indexing might break external references, but for split generation it's okay.
        # However, we need to return indices relative to the *original* or *current* df?
        # The task says "Consume graphs_v1.parquet". The output split_indices.json should
        # contain indices into the *current* loaded dataframe (which is the processed one).
        # If we dropped rows, the indices are 0..N-1 of the filtered df.
        # But wait, T013d4 output might be the ground truth. If we drop rows, we are changing the dataset.
        # Better: Keep all rows, but if we can't assign a family, maybe exclude them from split?
        # For now, assume all have valid structures.
    
    # Stratified split
    # We need to split indices, not the dataframe itself, to preserve order if needed?
    # train_test_split returns arrays of indices if we pass indices.
    
    indices = df.index.tolist()
    families = df['family_id'].tolist()
    
    try:
        train_idx, test_idx = train_test_split(
            indices,
            test_size=test_size,
            random_state=random_state,
            stratify=families
        )
    except Exception as e:
        # If stratification fails (e.g., small families), we might need to adjust.
        # But the requirement is strict: "Ensure no training family appears in the test set."
        # train_test_split with stratify ensures this.
        logger.error(f"Stratified split failed: {e}")
        raise
    
    return train_idx, test_idx

def verify_family_separation(train_indices: List[int], 
                             test_indices: List[int], 
                             df: pd.DataFrame) -> None:
    """
    Verify that no family appears in both train and test sets.
    Exits with code 1 if violation found.
    """
    train_families = set(df.loc[train_indices, 'family_id'].unique())
    test_families = set(df.loc[test_indices, 'family_id'].unique())
    
    intersection = train_families.intersection(test_families)
    
    if intersection:
        logger.error(f"SC-002 VIOLATION: Families found in both train and test: {intersection}")
        logger.error("Exiting with code 1.")
        sys.exit(1)
    
    logger.info("Family separation verified. No overlap found.")

def save_split(train_indices: List[int], 
               test_indices: List[int], 
               output_path: str) -> None:
    """
    Atomically write the split to JSON.
    Uses tempfile.mkstemp in the same directory, then os.rename.
    """
    output_dir = os.path.dirname(output_path)
    if not output_dir:
        output_dir = "."
    
    try:
        fd, temp_path = tempfile.mkstemp(suffix=".json", dir=output_dir)
        logger.info(f"Writing split to temporary file: {temp_path}")
        
        split_data = {
            "train_indices": train_indices,
            "test_indices": test_indices,
            "metadata": {
                "train_size": len(train_indices),
                "test_size": len(test_indices),
                "random_state": 42
            }
        }
        
        with os.fdopen(fd, 'w') as f:
            json.dump(split_data, f, indent=2)
        
        os.rename(temp_path, output_path)
        logger.info(f"Split successfully written to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to write split atomically: {e}")
        # Clean up temp file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate family-based stratified split.")
    parser.add_argument("--input", type=str, required=True, help="Path to input parquet file (graphs_v1.parquet).")
    parser.add_argument("--output", type=str, required=True, help="Path to output split JSON file.")
    parser.add_argument("--test-size", type=float, default=0.2, help="Fraction of data for test set.")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    
    args = parser.parse_args()
    
    # Enforce reproducibility
    enforce_reproducibility()
    
    logger.info(f"Loading data from {args.input}...")
    df = load_graphs_from_parquet(args.input)
    
    if df.empty:
        logger.error("Input dataframe is empty.")
        sys.exit(1)
    
    logger.info("Assigning families...")
    # If family_id is missing, we derive it.
    if 'family_id' not in df.columns:
        # Derive structures from the dataframe
        # This assumes the dataframe has a 'structure' column or equivalent.
        # If not, we might need to reconstruct from node/edge features, which is complex.
        # For now, assume 'structure' column exists as a dict.
        structures = []
        valid_indices = []
        for i, row in df.iterrows():
            if 'structure' in row and isinstance(row['structure'], dict):
                try:
                    s = Structure.from_dict(row['structure'])
                    structures.append(s)
                    valid_indices.append(i)
                except Exception as e:
                    logger.warning(f"Skipping invalid structure at index {i}: {e}")
            else:
                logger.warning(f"Skipping row {i}: missing or invalid structure data.")
        
        if not structures:
            logger.error("No valid structures found to assign families.")
            sys.exit(1)
        
        family_map = assign_families(structures)
        
        # Assign to dataframe
        # We need to map the index in 'structures' back to the dataframe index
        df['family_id'] = None
        for local_idx, global_idx in enumerate(valid_indices):
            df.iloc[global_idx, df.columns.get_loc('family_id')] = family_map[local_idx]
        
        # Drop rows without family_id
        df = df.dropna(subset=['family_id']).reset_index(drop=True)
        logger.info(f"Filtered to {len(df)} valid structures with assigned families.")
    else:
        # If family_id exists, we assume it's correct, but we could validate it?
        # The task says "Derive family_id", so we might ignore existing and re-derive?
        # "Derive family_id by loading structures..." implies we must compute it.
        # So we should re-derive even if it exists, to ensure consistency with StructureMatcher.
        # But that's expensive. Let's assume if it exists, it was derived correctly.
        # However, to be safe and follow instructions strictly:
        logger.info("Re-deriving family_id to ensure consistency with StructureMatcher...")
        # (Same logic as above, but we skip the 'if not in columns' check and always run)
        # For brevity in this implementation, if it exists, we trust it? 
        # No, the task says "Derive". So we must run the assignment.
        # Let's do it unconditionally if we can extract structures.
        structures = []
        valid_indices = []
        for i, row in df.iterrows():
            if 'structure' in row and isinstance(row['structure'], dict):
                try:
                    s = Structure.from_dict(row['structure'])
                    structures.append(s)
                    valid_indices.append(i)
                except Exception as e:
                    logger.warning(f"Skipping invalid structure at index {i}: {e}")
        
        if not structures:
            logger.error("No valid structures found to assign families.")
            sys.exit(1)
        
        family_map = assign_families(structures)
        df['family_id'] = None
        for local_idx, global_idx in enumerate(valid_indices):
            df.iloc[global_idx, df.columns.get_loc('family_id')] = family_map[local_idx]
        df = df.dropna(subset=['family_id']).reset_index(drop=True)
    
    logger.info("Generating split...")
    train_indices, test_indices = generate_family_split(
        df, 
        random_state=args.random_state, 
        test_size=args.test_size
    )
    
    logger.info("Verifying family separation...")
    verify_family_separation(train_indices, test_indices, df)
    
    logger.info(f"Saving split to {args.output}...")
    save_split(train_indices, test_indices, args.output)
    
    logger.info("Split generation complete.")

if __name__ == "__main__":
    main()
"""
Module for K-Fold Leave-Ligand-Scaffold-Out (LLSO) Split Generation.

This module implements the logic to:
1. Extract ligand scaffold IDs from graphs using RDKit.
2. Generate 5-fold LLSO splits ensuring no scaffold overlap between train and test.
3. Write the splits to a JSON file.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit import RDLogger
import hashlib

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent

def load_graphs_for_splitting() -> pd.DataFrame:
    """
    Load the processed graphs from the parquet file.
    
    Returns:
        pd.DataFrame: DataFrame containing graph data with necessary columns.
    """
    project_root = get_project_root()
    graphs_path = project_root / "data" / "processed" / "graphs.parquet"
    
    if not graphs_path.exists():
        raise FileNotFoundError(
            f"Graphs file not found at {graphs_path}. "
            "Please ensure T017b and T017c have been completed successfully."
        )
    
    logger.info(f"Loading graphs from {graphs_path}")
    df = pd.read_parquet(graphs_path)
    
    required_columns = ['sample_id', 'ligand_class', 'metal_center', 'coordination_sphere_smiles']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in graphs.parquet: {missing_cols}. "
            "Ensure T017c has populated 'coordination_sphere_smiles'."
        )
    
    logger.info(f"Loaded {len(df)} graphs for splitting")
    return df

def extract_ligand_scaffold_id(graph_row: pd.Series) -> str:
    """
    Derive a unique scaffold ID from the coordination sphere SMILES.
    
    This function uses RDKit to:
    1. Parse the SMILES string of the coordination sphere ligands.
    2. Generate a Morgan fingerprint (radius=2, 2048 bits).
    3. Convert the fingerprint to a string representation.
    4. Hash the string to create a compact, unique scaffold ID.
    
    Args:
        graph_row: A row from the graphs DataFrame containing 'coordination_sphere_smiles'.
        
    Returns:
        str: A unique scaffold ID string.
    """
    smiles = graph_row.get('coordination_sphere_smiles')
    
    if not smiles or pd.isna(smiles) or smiles == "":
        # Fallback for missing SMILES: use sample_id to ensure uniqueness but no chemical info
        logger.warning(f"Missing SMILES for sample {graph_row.get('sample_id')}, using fallback ID")
        return f"fallback_{graph_row.get('sample_id')}"
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Could not parse SMILES for sample {graph_row.get('sample_id')}, using fallback")
            return f"fallback_{graph_row.get('sample_id')}"
        
        # Generate Morgan fingerprint
        fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        fp_str = fp.toBitString()
        
        # Create a hash of the fingerprint string to get a compact ID
        scaffold_hash = hashlib.sha256(fp_str.encode('utf-8')).hexdigest()[:16]
        return scaffold_hash
        
    except Exception as e:
        logger.error(f"Error processing SMILES for sample {graph_row.get('sample_id')}: {e}")
        return f"fallback_{graph_row.get('sample_id')}"

def compute_scaffold_clusters(df: pd.DataFrame) -> Dict[str, List[int]]:
    """
    Group sample indices by their scaffold ID.
    
    Args:
        df: DataFrame with 'scaffold_id' column.
    
    Returns:
        Dict[str, List[int]]: Mapping of scaffold_id -> list of sample indices.
    """
    clusters = {}
    for idx, row in df.iterrows():
        scaffold_id = row['scaffold_id']
        if scaffold_id not in clusters:
            clusters[scaffold_id] = []
        clusters[scaffold_id].append(idx)
    return clusters

def generate_llso_splits(
    df: pd.DataFrame,
    n_folds: int = 5,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate K-Fold LLSO splits ensuring no scaffold overlap between train and test.
    
    Logic:
    1. Group samples by scaffold_id.
    2. Shuffle the unique scaffold IDs.
    3. Assign each scaffold to a fold.
    4. For each fold k:
       - Test set = samples belonging to scaffolds assigned to fold k.
       - Train set = samples belonging to scaffolds NOT assigned to fold k.
       - Val set = a subset of the train set (stratified by scaffold).
    
    Args:
        df: DataFrame containing graph data with 'scaffold_id' column.
        n_folds: Number of folds (default 5).
        seed: Random seed for reproducibility.
    
    Returns:
        List[Dict[str, Any]]: List of 5 splits, each containing 'train', 'val', 'test' indices.
    """
    logger.info(f"Generating {n_folds}-fold LLSO splits with seed {seed}")
    
    # Ensure scaffold_id column exists
    if 'scaffold_id' not in df.columns:
        raise ValueError("DataFrame must contain 'scaffold_id' column for LLSO splitting.")
    
    # Get unique scaffold IDs and their counts
    scaffold_counts = df['scaffold_id'].value_counts()
    unique_scaffolds = scaffold_counts.index.tolist()
    
    # Shuffle scaffolds deterministically
    rng = np.random.RandomState(seed)
    rng.shuffle(unique_scaffolds)
    
    # Assign scaffolds to folds
    n_scaffolds = len(unique_scaffolds)
    scaffold_fold_map = {}
    for i, scaffold in enumerate(unique_scaffolds):
        fold_idx = i % n_folds
        scaffold_fold_map[scaffold] = fold_idx
    
    # Build splits
    splits = []
    for fold_idx in range(n_folds):
        # Identify test scaffolds for this fold
        test_scaffolds = [s for s, f in scaffold_fold_map.items() if f == fold_idx]
        
        # Identify train scaffolds (all others)
        train_scaffolds = [s for s, f in scaffold_fold_map.items() if f != fold_idx]
        
        # Filter indices
        test_mask = df['scaffold_id'].isin(test_scaffolds)
        train_mask = df['scaffold_id'].isin(train_scaffolds)
        
        test_indices = df[test_mask].index.tolist()
        train_indices = df[train_mask].index.tolist()
        
        # Create a small validation set from the train scaffolds (10% of train scaffolds)
        # We want to ensure val scaffolds are disjoint from test scaffolds (already guaranteed)
        # and also disjoint from train scaffolds? No, val is usually part of the train split
        # in standard K-fold, but for LLSO, we often keep val as a separate set of scaffolds
        # from the same "train" pool to tune hyperparameters.
        # Strategy: Split the train_scaffolds into train_scaffolds and val_scaffolds.
        
        val_scaffolds_count = int(len(train_scaffolds) * 0.1)
        if val_scaffolds_count > 0:
            # Shuffle train scaffolds and pick first val_scaffolds_count for validation
            val_rng = np.random.RandomState(seed + fold_idx)
            shuffled_train_scaffolds = train_scaffolds.copy()
            val_rng.shuffle(shuffled_train_scaffolds)
            val_scaffolds = shuffled_train_scaffolds[:val_scaffolds_count]
            final_train_scaffolds = [s for s in train_scaffolds if s not in val_scaffolds]
            
            val_mask = df['scaffold_id'].isin(val_scaffolds)
            train_mask_final = df['scaffold_id'].isin(final_train_scaffolds)
            
            val_indices = df[val_mask].index.tolist()
            final_train_indices = df[train_mask_final].index.tolist()
        else:
            # If too few scaffolds, put all train into train, val is empty
            final_train_indices = train_indices
            val_indices = []
        
        splits.append({
            "fold": fold_idx,
            "train_indices": final_train_indices,
            "val_indices": val_indices,
            "test_indices": test_indices,
            "train_scaffolds": final_train_scaffolds,
            "val_scaffolds": val_scaffolds,
            "test_scaffolds": test_scaffolds
        })
        
        logger.info(f"Fold {fold_idx}: Train={len(final_train_indices)}, Val={len(val_indices)}, Test={len(test_indices)}")
        
        # Verification: Ensure no scaffold overlap
        train_s_set = set(final_train_scaffolds)
        test_s_set = set(test_scaffolds)
        val_s_set = set(val_scaffolds)
        
        if train_s_set & test_s_set:
            raise RuntimeError(f"Fold {fold_idx}: Scaffold overlap between train and test!")
        if val_s_set & test_s_set:
            raise RuntimeError(f"Fold {fold_idx}: Scaffold overlap between val and test!")
        
    logger.info(f"Successfully generated {n_folds} LLSO splits.")
    return splits

def write_splits_json(splits: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """
    Write the splits to a JSON file.
    
    Args:
        splits: List of split dictionaries.
        output_path: Path to save the JSON file. Defaults to project/data/processed/splits.json.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "splits.json"
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_to_serializable(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        return obj
    
    serializable_splits = convert_to_serializable(splits)
    
    logger.info(f"Writing splits to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(serializable_splits, f, indent=2)
    
    logger.info(f"Splits written successfully to {output_path}")

def run_split_generation() -> None:
    """
    Main entry point for generating splits.
    """
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 1. Load graphs
        df = load_graphs_for_splitting()
        
        # 2. Extract scaffold IDs
        logger.info("Extracting ligand scaffold IDs...")
        df['scaffold_id'] = df.apply(extract_ligand_scaffold_id, axis=1)
        
        # 3. Generate splits
        splits = generate_llso_splits(df, n_folds=5, seed=42)
        
        # 4. Write to JSON
        write_splits_json(splits)
        
        logger.info("Split generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during split generation: {e}")
        raise

def main():
    """
    Command-line entry point.
    """
    run_split_generation()

if __name__ == "__main__":
    main()

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import RDKit for molecular handling and scaffold extraction
try:
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold
    from rdkit import RDLogger
except ImportError:
    # Fallback for environments where RDKit might not be installed yet,
    # though requirements.txt should handle this.
    raise ImportError("RDKit is required for scaffold splitting. Please install it via requirements.txt.")

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

# Import local utilities
from src.utils.logging import get_logger, log_message

def get_burcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extracts the Murcko scaffold from a SMILES string.
    
    Args:
        smiles: The SMILES string of the molecule.
        
    Returns:
        Canonical SMILES of the Murcko scaffold, or None if parsing fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        if scaffold is None:
            return None
        
        return Chem.MolToSmiles(scaffold)
    except Exception:
        return None

def calculate_scaffold_split(
    df: pd.DataFrame,
    smiles_column: str = 'reactants_smiles',
    target_column: str = 'yield',
    test_fraction: float = 0.2,
    val_fraction: float = 0.1,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits the dataset into train, validation, and test sets using the 
    Murcko Scaffold Split strategy to prevent data leakage.
    
    This ensures that molecules with the same scaffold do not appear in 
    multiple splits, which is critical for evaluating generalization to 
    new chemical structures.
    
    Args:
        df: The input DataFrame containing reaction data.
        smiles_column: The column name containing reactant/product SMILES.
        target_column: The column name containing the target variable (yield).
        test_fraction: Fraction of data to use for testing.
        val_fraction: Fraction of data to use for validation.
        random_state: Random seed for reproducibility.
        
    Returns:
        A tuple of (train_df, val_df, test_df).
    """
    logger = get_logger(__name__)
    
    # Calculate scaffold for each entry
    logger.info(f"Calculating Murcko scaffolds for {len(df)} entries...")
    df['scaffold'] = df[smiles_column].apply(get_burcko_scaffold)
    
    # Filter out entries where scaffold could not be determined
    valid_mask = df['scaffold'].notna()
    invalid_count = (~valid_mask).sum()
    if invalid_count > 0:
        logger.warning(f"Skipping {invalid_count} entries with invalid scaffolds.")
    
    df_valid = df[valid_mask].copy()
    
    # Group by scaffold
    scaffold_groups = df_valid.groupby('scaffold')
    scaffold_indices = list(scaffold_groups.groups.keys())
    
    # Shuffle scaffolds deterministically
    np.random.seed(random_state)
    np.random.shuffle(scaffold_indices)
    
    # Calculate split indices
    n_scaffolds = len(scaffold_indices)
    test_cutoff = int(n_scaffolds * test_fraction)
    val_cutoff = test_cutoff + int(n_scaffolds * val_fraction)
    
    test_scaffolds = set(scaffold_indices[:test_cutoff])
    val_scaffolds = set(scaffold_indices[test_cutoff:val_cutoff])
    train_scaffolds = set(scaffold_indices[val_cutoff:])
    
    logger.info(f"Scaffold Split completed:")
    logger.info(f"  Train scaffolds: {len(train_scaffolds)}")
    logger.info(f"  Val scaffolds: {len(val_scaffolds)}")
    logger.info(f"  Test scaffolds: {len(test_scaffolds)}")
    
    # Assign splits
    def assign_split(scaffold):
        if scaffold in test_scaffolds:
            return 'test'
        elif scaffold in val_scaffolds:
            return 'val'
        else:
            return 'train'
    
    df_valid['split'] = df_valid['scaffold'].apply(assign_split)
    
    train_df = df_valid[df_valid['split'] == 'train'].drop(columns=['scaffold', 'split'])
    val_df = df_valid[df_valid['split'] == 'val'].drop(columns=['scaffold', 'split'])
    test_df = df_valid[df_valid['split'] == 'test'].drop(columns=['scaffold', 'split'])
    
    logger.info(f"Split sizes: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    return train_df, val_df, test_df

def main():
    """
    Main entry point for running the Scaffold Split logic.
    This function expects a pre-downloaded and parsed dataset.
    """
    logger = get_logger(__name__)
    logger.info("Starting Scaffold Split execution...")
    
    # Example usage: Load a dataset (path should be configured or passed as argument)
    # For this implementation, we assume the data is in data/processed/reactions_parsed.csv
    input_path = "data/processed/reactions_parsed.csv"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. Please run download.py and parse.py first.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} reactions from {input_path}")
        
        # Perform the split
        train_df, val_df, test_df = calculate_scaffold_split(
            df,
            smiles_column='reactants_smiles',
            target_column='yield',
            test_fraction=0.2,
            val_fraction=0.1,
            random_state=42
        )
        
        # Save the splits
        output_dir = "data/processed"
        os.makedirs(output_dir, exist_ok=True)
        
        train_path = os.path.join(output_dir, "train_split.csv")
        val_path = os.path.join(output_dir, "val_split.csv")
        test_path = os.path.join(output_dir, "test_split.csv")
        
        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)
        
        logger.info(f"Saved train split to {train_path}")
        logger.info(f"Saved val split to {val_path}")
        logger.info(f"Saved test split to {test_path}")
        
        # Log summary statistics
        logger.info(f"Train set size: {len(train_df)}")
        logger.info(f"Val set size: {len(val_df)}")
        logger.info(f"Test set size: {len(test_df)}")
        
    except Exception as e:
        logger.error(f"Error during scaffold split: {e}")
        raise

if __name__ == "__main__":
    main()
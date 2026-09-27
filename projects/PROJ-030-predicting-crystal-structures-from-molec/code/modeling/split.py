import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import train_test_split
from collections import defaultdict

from config import get_path_data, get_path_processed_data, get_path_validation
from ingestion.models import MoleculeRecord

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def group_rare_space_groups(data: pd.DataFrame, threshold: int = 20) -> pd.DataFrame:
    """
    Groups space groups with fewer than 'threshold' samples into an 'Other' category.
    This must be done PRIOR to splitting to ensure the 'Other' category is treated
    as a single class during the scaffold split.
    """
    if 'space_group' not in data.columns:
        raise ValueError("Dataset must contain a 'space_group' column.")

    space_group_counts = data['space_group'].value_counts()
    rare_space_groups = space_group_counts[space_group_counts < threshold].index
    
    # Log the number of groups being collapsed
    logger.info(f"Found {len(rare_space_groups)} rare space groups (count < {threshold}). Collapsing to 'Other'.")
    
    data = data.copy()
    data['space_group'] = data['space_group'].replace(rare_space_groups, 'Other')
    return data

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extracts the Bemis-Murcko scaffold from a SMILES string.
    Returns None if the molecule cannot be parsed.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.warning(f"Failed to generate scaffold for SMILES '{smiles}': {e}")
        return None

def scaffold_split(data: pd.DataFrame, random_state: int = 42, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs a scaffold-based split using the Bemis-Murcko algorithm.
    
    Strategy:
    1. Generate a scaffold for each molecule.
    2. Group molecules by their scaffold.
    3. Split the unique scaffolds into train/test sets.
    4. Assign all molecules belonging to a scaffold to the same set.
    
    This guarantees zero scaffold overlap between train and test sets.
    """
    if 'smiles' not in data.columns:
        raise ValueError("Dataset must contain a 'smiles' column to generate scaffolds.")

    logger.info("Generating Bemis-Murcko scaffolds for all molecules...")
    scaffolds = data['smiles'].apply(get_murcko_scaffold)
    
    # Handle None scaffolds (failed parsing) by assigning a unique placeholder
    # to ensure they don't get grouped with valid scaffolds, but still split.
    # We give them a unique ID so they are treated as individual scaffolds.
    unique_counter = 0
    scaffold_ids = []
    for s in scaffolds:
        if s is None:
            scaffold_ids.append(f"__FAILED_PARSE_{unique_counter}__")
            unique_counter += 1
        else:
            scaffold_ids.append(s)
    
    data = data.copy()
    data['_scaffold_id'] = scaffold_ids

    # Group by scaffold
    scaffold_groups = data.groupby('_scaffold_id')
    unique_scaffolds = list(scaffold_groups.groups.keys())
    
    logger.info(f"Found {len(unique_scaffolds)} unique scaffolds.")

    # Split the unique scaffolds
    train_scaffolds, test_scaffolds = train_test_split(
        unique_scaffolds, 
        test_size=test_size, 
        random_state=random_state
    )
    
    # Create sets for fast lookup
    train_scaffold_set = set(train_scaffolds)
    test_scaffold_set = set(test_scaffolds)

    # Assign indices
    train_indices = []
    test_indices = []

    for idx, scaffold_id in zip(data.index, data['_scaffold_id']):
        if scaffold_id in train_scaffold_set:
            train_indices.append(idx)
        elif scaffold_id in test_scaffold_set:
            test_indices.append(idx)
        else:
            # This should theoretically not happen if split covers all
            logger.warning(f"Scaffold {scaffold_id} not found in split sets.")

    # Drop the temporary scaffold column
    data = data.drop(columns=['_scaffold_id'])

    train_df = data.loc[train_indices].reset_index(drop=True)
    test_df = data.loc[test_indices].reset_index(drop=True)

    logger.info(f"Scaffold split completed. Train: {len(train_df)}, Test: {len(test_df)}")
    
    return train_df, test_df

def verify_zero_overlap(train_data: pd.DataFrame, test_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Verifies that there is no overlap in scaffolds between train and test sets.
    Returns a report dictionary with the verification status and details.
    """
    logger.info("Verifying zero scaffold overlap...")
    
    if 'smiles' not in train_data.columns or 'smiles' not in test_data.columns:
        raise ValueError("Both train and test data must contain 'smiles' columns.")

    train_scaffolds = set(train_data['smiles'].apply(get_murcko_scaffold).dropna())
    test_scaffolds = set(test_data['smiles'].apply(get_murcko_scaffold).dropna())
    
    overlap = train_scaffolds.intersection(test_scaffolds)
    
    is_valid = len(overlap) == 0
    
    report = {
        "overlap_verified": is_valid,
        "train_scaffold_count": len(train_scaffolds),
        "test_scaffold_count": len(test_scaffolds),
        "overlap_count": len(overlap),
        "overlap_scaffolds": list(overlap) if not is_valid else []
    }
    
    if is_valid:
        logger.info("Zero scaffold overlap verified successfully.")
    else:
        logger.error(f"Scaffold overlap detected! {len(overlap)} scaffolds found in both sets.")
        
    return report

def main():
    """Main function to perform the split and save the indices."""
    try:
        # Load the dataset
        input_path = get_path_data('crystal_dataset.csv')
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Dataset not found at {input_path}. Run the ingestion pipeline first.")
        
        logger.info(f"Loading dataset from {input_path}...")
        df = pd.read_csv(input_path)
        
        # Group rare space groups
        logger.info("Grouping rare space groups...")
        df = group_rare_space_groups(df, threshold=20)
        
        # Perform scaffold split
        logger.info("Performing scaffold split...")
        train_df, test_df = scaffold_split(df, random_state=42, test_size=0.2)
        
        # Verify zero overlap
        overlap_report = verify_zero_overlap(train_df, test_df)
        
        if not overlap_report['overlap_verified']:
            raise ValueError("Scaffold overlap detected! Split failed verification.")
        
        # Save split indices
        train_indices = train_df.index.tolist()
        test_indices = test_df.index.tolist()
        
        split_indices = {
            'train': train_indices,
            'test': test_indices,
            'train_count': len(train_indices),
            'test_count': len(test_indices)
        }
        
        output_split_path = get_path_processed_data('split_indices.json')
        with open(output_split_path, 'w') as f:
            json.dump(split_indices, f, indent=2)
        logger.info(f"Saved split indices to {output_split_path}")
        
        # Save validation report
        validation_report = {
            'overlap_verified': overlap_report['overlap_verified'],
            'train_scaffold_count': overlap_report['train_scaffold_count'],
            'test_scaffold_count': overlap_report['test_scaffold_count'],
            'overlap_count': overlap_report['overlap_count'],
            'method': 'Bemis-Murcko Scaffold Split',
            'rare_space_group_threshold': 20
        }
        
        output_report_path = get_path_validation('scaffold_overlap_report.json')
        with open(output_report_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        logger.info(f"Saved validation report to {output_report_path}")
        
        logger.info("Split task completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during split process: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
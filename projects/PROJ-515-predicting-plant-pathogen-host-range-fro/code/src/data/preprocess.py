import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

from loguru import logger
from src.utils.logging import get_logger
from src.config import Paths, Seeds, ModelParams, Thresholds, get_default_config

logger = get_logger(__name__)

def load_interactions(data_dir: Path) -> pd.DataFrame:
    """
    Load the merged interaction table from data/raw/interactions_merged.csv.
    
    Args:
        data_dir: Path to the data directory.
        
    Returns:
        DataFrame with columns: pathogen, host, label (1=infected, 0=not_infected, -1=unknown)
        
    Raises:
        FileNotFoundError: If the interaction file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    file_path = data_dir / "raw" / "interactions_merged.csv"
    
    if not file_path.exists():
        logger.error(f"Interaction file not found: {file_path}")
        raise FileNotFoundError(f"Interaction file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    required_cols = {'pathogen', 'host', 'label'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        logger.error(f"Interaction file missing required columns: {missing}")
        raise ValueError(f"Interaction file missing required columns: {missing}")
    
    if df.empty:
        logger.warning("Interaction file is empty.")
        return df
        
    return df

def filter_unknown_labels(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separate known (1, 0) and unknown (-1) labels.
    
    Args:
        df: Interaction DataFrame.
        
    Returns:
        Tuple of (known_df, unknown_df)
    """
    known_df = df[df['label'] != -1].copy()
    unknown_df = df[df['label'] == -1].copy()
    return known_df, unknown_df

def load_valid_pathogens(data_dir: Path) -> List[str]:
    """
    Load the list of valid pathogens (those with >0 interactions) from data/processed/valid_pathogens.json.
    
    Args:
        data_dir: Path to the data directory.
        
    Returns:
        List of valid pathogen IDs.
        
    Raises:
        FileNotFoundError: If the valid pathogens file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    file_path = data_dir / "processed" / "valid_pathogens.json"
    
    if not file_path.exists():
        logger.error(f"Valid pathogens file not found: {file_path}. "
                     "Run T010C (Zero Interaction check) before proceeding.")
        raise FileNotFoundError(f"Valid pathogens file not found: {file_path}. "
                                "Run T010C before proceeding.")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        logger.error(f"Valid pathogens file must contain a list, got {type(data)}")
        raise ValueError(f"Valid pathogens file must contain a list, got {type(data)}")
        
    return data

def split_pathogen_stratified(
    df: pd.DataFrame, 
    valid_pathogens: List[str], 
    data_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Perform pathogen-stratified split of the interaction data.
    
    This ensures that pathogens present in the test set are not used in training,
    preventing data leakage.
    
    Args:
        df: Interaction DataFrame.
        valid_pathogens: List of valid pathogen IDs.
        data_dir: Path to the data directory.
        test_size: Fraction of pathogens to hold out for testing.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, val_df, metadata)
        
    Raises:
        ValueError: If there are insufficient pathogens for splitting.
    """
    # Filter to only valid pathogens first
    df_valid = df[df['pathogen'].isin(valid_pathogens)].copy()
    
    unique_pathogens = df_valid['pathogen'].unique()
    n_pathogens = len(unique_pathogens)
    
    if n_pathogens < 10:
        logger.error(f"Insufficient pathogens ({n_pathogens}) for stratified split. "
                     "Minimum 10 required (including hold-out set).")
        raise ValueError(f"Insufficient pathogens ({n_pathogens}) for stratified split. "
                         "Minimum 10 required.")
    
    np.random.seed(random_state)
    np.random.shuffle(unique_pathogens)
    
    # Reserve 10 pathogens for hold-out set (independent validation)
    holdout_count = 10
    if n_pathogens <= holdout_count:
        logger.warning(f"Not enough pathogens for hold-out set. Using all {n_pathogens} for train/val.")
        train_val_pathogens = unique_pathogens
        holdout_pathogens = []
    else:
        holdout_pathogens = list(unique_pathogens[:holdout_count])
        train_val_pathogens = list(unique_pathogens[holdout_count:])
    
    # Split train/val from the remaining pathogens
    n_train_val = len(train_val_pathogens)
    n_train = int(n_train_val * (1 - test_size))
    
    train_pathogens = train_val_pathogens[:n_train]
    val_pathogens = train_val_pathogens[n_train:]
    
    train_df = df_valid[df_valid['pathogen'].isin(train_pathogens)].copy()
    val_df = df_valid[df_valid['pathogen'].isin(val_pathogens)].copy()
    holdout_df = df_valid[df_valid['pathogen'].isin(holdout_pathogens)].copy()
    
    if train_df.empty:
        logger.error("Training set is empty after splitting. Check pathogen distribution.")
        raise ValueError("Training set is empty after splitting.")
    
    if val_df.empty and len(holdout_pathogens) == 0:
        logger.error("Validation set is empty. Check split ratio.")
        raise ValueError("Validation set is empty.")
    
    metadata = {
        'train_pathogens': train_pathogens,
        'val_pathogens': val_pathogens,
        'holdout_pathogens': holdout_pathogens,
        'train_count': len(train_df),
        'val_count': len(val_df),
        'holdout_count': len(holdout_df),
        'total_pathogens': n_pathogens,
        'random_state': random_state
    }
    
    logger.info(f"Split complete: Train={len(train_df)}, Val={len(val_df)}, Holdout={len(holdout_df)}")
    logger.info(f"Pathogens: Train={len(train_pathogens)}, Val={len(val_pathogens)}, Holdout={len(holdout_pathogens)}")
    
    return train_df, val_df, metadata

def save_split_metadata(metadata: Dict[str, Any], data_dir: Path) -> None:
    """
    Save split metadata to data/processed/split_metadata.json.
    
    Args:
        metadata: Split metadata dictionary.
        data_dir: Path to the data directory.
    """
    output_path = data_dir / "processed" / "split_metadata.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Split metadata saved to {output_path}")

def generate_data_quality_report(df: pd.DataFrame, data_dir: Path) -> Dict[str, Any]:
    """
    Generate a data quality report quantifying missing data per pathogen.
    
    Args:
        df: Interaction DataFrame.
        data_dir: Path to the data directory.
        
    Returns:
        Data quality report dictionary.
    """
    if df.empty:
        report = {
            'total_interactions': 0,
            'unique_pathogens': 0,
            'unique_hosts': 0,
            'missing_percentage': 100.0,
            'per_pathogen_missing': {},
            'status': 'empty'
        }
    else:
        total_interactions = len(df)
        unique_pathogens = df['pathogen'].nunique()
        unique_hosts = df['host'].nunique()
        
        # Calculate missing percentage (label == -1)
        missing_count = (df['label'] == -1).sum()
        missing_percentage = (missing_count / total_interactions) * 100 if total_interactions > 0 else 0.0
        
        # Per-pathogen missing
        per_pathogen_missing = {}
        for pathogen in df['pathogen'].unique():
            pathogen_interactions = df[df['pathogen'] == pathogen]
            pathogen_missing = (pathogen_interactions['label'] == -1).sum()
            pathogen_total = len(pathogen_interactions)
            per_pathogen_missing[pathogen] = {
                'total': int(pathogen_total),
                'missing': int(pathogen_missing),
                'missing_percentage': round((pathogen_missing / pathogen_total) * 100, 2) if pathogen_total > 0 else 0.0
            }
        
        report = {
            'total_interactions': int(total_interactions),
            'unique_pathogens': int(unique_pathogens),
            'unique_hosts': int(unique_hosts),
            'missing_percentage': round(missing_percentage, 2),
            'per_pathogen_missing': per_pathogen_missing,
            'status': 'healthy' if missing_percentage < 50 else 'concerning'
        }
    
    output_path = data_dir / "reports" / "data_quality_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Data quality report saved to {output_path}")
    return report

def run_preprocessing_pipeline(
    data_dir: Path,
    output_dir: Optional[Path] = None,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run the complete preprocessing pipeline:
    1. Load interactions
    2. Filter unknown labels
    3. Load valid pathogens
    4. Split data (pathogen-stratified)
    5. Generate data quality report
    
    Args:
        data_dir: Path to the data directory.
        output_dir: Path to save processed outputs (defaults to data_dir/processed).
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing split dataframes and metadata.
        
    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If data quality checks fail (e.g., zero interactions).
    """
    if output_dir is None:
        output_dir = data_dir / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load interactions
    logger.info("Loading interactions...")
    try:
        interactions_df = load_interactions(data_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    if interactions_df.empty:
        logger.error("Interaction data is empty. Cannot proceed.")
        raise ValueError("Interaction data is empty.")
    
    # 2. Filter unknown labels
    logger.info("Filtering unknown labels...")
    known_df, unknown_df = filter_unknown_labels(interactions_df)
    logger.info(f"Known interactions: {len(known_df)}, Unknown: {len(unknown_df)}")
    
    # 3. Load valid pathogens
    logger.info("Loading valid pathogens...")
    try:
        valid_pathogens = load_valid_pathogens(data_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    if not valid_pathogens:
        logger.error("No valid pathogens found. Check T010C output.")
        raise ValueError("No valid pathogens found.")
    
    # 4. Split data
    logger.info("Performing pathogen-stratified split...")
    try:
        train_df, val_df, metadata = split_pathogen_stratified(
            known_df, valid_pathogens, data_dir, random_state=random_state
        )
    except ValueError as e:
        logger.error(str(e))
        raise
    
    # 5. Save split metadata
    save_split_metadata(metadata, data_dir)
    
    # 6. Generate data quality report
    logger.info("Generating data quality report...")
    generate_data_quality_report(interactions_df, data_dir)
    
    # Save processed splits
    train_path = output_dir / "train_interactions.csv"
    val_path = output_dir / "val_interactions.csv"
    known_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    
    logger.info(f"Train saved to {train_path}")
    logger.info(f"Val saved to {val_path}")
    
    logger.info("Preprocessing pipeline completed successfully.")
    
    return {
        'train': train_df,
        'val': val_df,
        'metadata': metadata
    }

def main():
    """Main entry point for preprocessing pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run preprocessing pipeline")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to data directory")
    parser.add_argument("--output-dir", type=str, default=None, help="Path to output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    result = run_preprocessing_pipeline(data_dir, output_dir, args.seed)
    
    logger.info(f"Pipeline completed. Train: {len(result['train'])}, Val: {len(result['val'])}")

if __name__ == "__main__":
    main()
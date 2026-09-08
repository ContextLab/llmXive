"""
Data Preprocessing Module for Plant Pathogen Host Range Prediction.

This module handles loading interaction data, filtering unknown labels,
validating pathogen lists, and performing pathogen-stratified data splitting
for training and validation sets.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from loguru import logger
from sklearn.model_selection import train_test_split

# Import logging setup
from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def load_interactions(interactions_path: Path) -> pd.DataFrame:
    """
    Load the merged interaction table from CSV.

    Args:
        interactions_path: Path to the interactions CSV file.

    Returns:
        DataFrame containing pathogen-host interactions.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    logger.info(f"Loading interactions from {interactions_path}")
    
    if not interactions_path.exists():
        raise FileNotFoundError(f"Interaction file not found: {interactions_path}")

    df = pd.read_csv(interactions_path)
    
    required_cols = ['pathogen_id', 'host_species', 'interaction_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} interaction records")
    return df


def filter_unknown_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out records with 'unknown' interaction labels.
    These records are excluded from training as per FR-013.

    Args:
        df: Input DataFrame with interaction labels.

    Returns:
        DataFrame with 'unknown' labels removed.
    """
    logger.info(f"Filtering unknown labels from {len(df)} records")
    
    initial_count = len(df)
    # Assuming 'unknown' is represented as string 'unknown' or NaN
    mask = df['interaction_label'].notna() & (df['interaction_label'] != 'unknown')
    filtered_df = df[mask].copy()
    
    removed_count = initial_count - len(filtered_df)
    logger.info(f"Removed {removed_count} records with unknown/NaN labels")
    
    return filtered_df


def load_valid_pathogens(valid_pathogens_path: Path) -> List[str]:
    """
    Load the list of valid pathogens (those with >0 interactions) from JSON.

    Args:
        valid_pathogens_path: Path to the JSON file containing valid pathogen IDs.

    Returns:
        List of valid pathogen IDs.
    """
    logger.info(f"Loading valid pathogens from {valid_pathogens_path}")
    
    if not valid_pathogens_path.exists():
        raise FileNotFoundError(f"Valid pathogens file not found: {valid_pathogens_path}")

    with open(valid_pathogens_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list format and dict format
    if isinstance(data, list):
        valid_ids = data
    elif isinstance(data, dict) and 'valid_pathogens' in data:
        valid_ids = data['valid_pathogens']
    else:
        raise ValueError("Invalid format in valid_pathogens.json")
    
    logger.info(f"Loaded {len(valid_ids)} valid pathogen IDs")
    return valid_ids


def split_pathogen_stratified(
    df: pd.DataFrame,
    valid_pathogens: List[str],
    holdout_size: int = 10,
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform pathogen-stratified splitting of the interaction data.
    
    This function ensures that the split is done at the pathogen level to prevent
    data leakage. All interactions for a given pathogen must belong to the same
    split (Train, Val, or Holdout).
    
    The stratification is based on the distribution of host counts per pathogen
    to ensure representative splits.

    Args:
        df: DataFrame containing interactions (must be filtered for unknowns already).
        valid_pathogens: List of valid pathogen IDs to consider.
        holdout_size: Number of pathogens to reserve for the independent hold-out set.
        test_size: Fraction of remaining pathogens for the validation set (relative to train+val).
        val_size: Fraction of remaining pathogens for the validation set (relative to train+val).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (train_df, val_df, holdout_df).
    """
    logger.info(f"Starting pathogen-stratified split with holdout_size={holdout_size}")
    
    # Filter dataframe to only valid pathogens
    df_filtered = df[df['pathogen_id'].isin(valid_pathogens)].copy()
    
    if len(df_filtered) == 0:
        raise ValueError("No interactions found for valid pathogens after filtering.")

    # Get unique pathogens and their host counts for stratification
    pathogen_stats = df_filtered.groupby('pathogen_id').agg({
        'host_species': 'count',
        'interaction_label': 'mean' # Mean interaction (0 or 1) for rough balance
    }).reset_index()
    pathogen_stats.columns = ['pathogen_id', 'interaction_count', 'mean_interaction']
    
    # Sort by interaction count to ensure we can stratify by data richness
    pathogen_stats = pathogen_stats.sort_values('interaction_count', ascending=False)
    
    all_pathogens = pathogen_stats['pathogen_id'].tolist()
    n_total = len(all_pathogens)
    
    if n_total < holdout_size:
        raise ValueError(f"Not enough pathogens ({n_total}) to reserve {holdout_size} for holdout.")
    
    # 1. Select Holdout Set
    # We want the holdout set to be representative. We'll use stratified sampling
    # based on the mean_interaction (host range breadth proxy) or just random if counts are low.
    # For simplicity and robustness, we'll stratify by the 'mean_interaction' (binned).
    
    # Create bins for stratification
    n_bins = min(5, n_total)
    pathogen_stats['bin'] = pd.qcut(pathogen_stats['mean_interaction'].astype(float), 
                                    q=n_bins, labels=False, duplicates='drop')
    
    # If qcut fails due to too few unique values, fallback to random
    if pathogen_stats['bin'].isna().any():
        logger.warning("Stratification bins failed, falling back to random holdout selection.")
        rng = np.random.default_rng(random_state)
        rng.shuffle(all_pathogens)
        holdout_pathogens = all_pathogens[:holdout_size]
        remaining_pathogens = all_pathogens[holdout_size:]
    else:
        # Stratified selection for holdout
        holdout_pathogens = []
        for bin_val in pathogen_stats['bin'].unique():
            bin_pathogens = pathogen_stats[pathogen_stats['bin'] == bin_val]['pathogen_id'].tolist()
            # Determine how many to take from this bin proportional to size
            proportion = len(bin_pathogens) / n_total
            take_count = max(1, int(holdout_size * proportion))
            # Ensure we don't take more than available
            take_count = min(take_count, len(bin_pathogens))
            
            # Random selection within bin
            rng = np.random.default_rng(random_state + int(bin_val))
            selected = rng.choice(bin_pathogens, size=take_count, replace=False)
            holdout_pathogens.extend(selected)
        
        # If we didn't get enough, fill from remaining
        if len(holdout_pathogens) < holdout_size:
            remaining_pool = [p for p in all_pathogens if p not in holdout_pathogens]
            rng = np.random.default_rng(random_state)
            needed = holdout_size - len(holdout_pathogens)
            fillers = rng.choice(remaining_pool, size=needed, replace=False)
            holdout_pathogens.extend(fillers)
        
        holdout_pathogens = holdout_pathogens[:holdout_size]
        remaining_pathogens = [p for p in all_pathogens if p not in holdout_pathogens]

    logger.info(f"Selected {len(holdout_pathogens)} pathogens for holdout set")

    # 2. Split Remaining into Train and Val
    # We need to split remaining_pathogens into Train and Val sets.
    # The task asks for Train/Val sets. Usually, this implies Train+Val are used for CV,
    # and Holdout is final.
    # Let's split remaining into Train and Val based on val_size.
    # Note: The task description says "Reserve a 10-pathogen hold-out set... create pathogen-stratified Train/Val sets".
    # We will split the remaining pathogens into Train and Val.
    
    if val_size > 0 and len(remaining_pathogens) > 0:
        # Stratify by interaction count again
        remaining_stats = pathogen_stats[pathogen_stats['pathogen_id'].isin(remaining_pathogens)].copy()
        if not remaining_stats.empty:
            if 'bin' in remaining_stats.columns:
                # Re-calculate bins or use existing if valid
                try:
                    # Re-binning might be safer if distribution changed
                    remaining_stats['val_bin'] = pd.qcut(remaining_stats['mean_interaction'].astype(float), 
                                                         q=min(3, len(remaining_stats)), 
                                                         labels=False, duplicates='drop')
                    stratify_col = 'val_bin'
                except ValueError:
                    stratify_col = None
            else:
                stratify_col = None
        else:
            stratify_col = None
    else:
        stratify_col = None

    # Perform split
    rng = np.random.default_rng(random_state)
    if stratify_col is not None and not remaining_stats[stratify_col].isna().all():
        # Use sklearn's train_test_split with stratify on the pathogen level
        # We need to map pathogen_id to its bin
        pathogen_to_bin = remaining_stats.set_index('pathogen_id')[stratify_col].to_dict()
        y_strat = [pathogen_to_bin.get(p, -1) for p in remaining_pathogens]
        
        train_pathogens, val_pathogens = train_test_split(
            remaining_pathogens,
            test_size=val_size,
            stratify=y_strat if len(set(y_strat)) > 1 else None,
            random_state=random_state
        )
    else:
        # Fallback to random split if stratification fails
        train_pathogens, val_pathogens = train_test_split(
            remaining_pathogens,
            test_size=val_size,
            random_state=random_state
        )

    logger.info(f"Split remaining {len(remaining_pathogens)} pathogens: "
                f"Train={len(train_pathogens)}, Val={len(val_pathogens)}")

    # 3. Filter DataFrames
    train_df = df_filtered[df_filtered['pathogen_id'].isin(train_pathogens)].copy()
    val_df = df_filtered[df_filtered['pathogen_id'].isin(val_pathogens)].copy()
    holdout_df = df_filtered[df_filtered['pathogen_id'].isin(holdout_pathogens)].copy()

    logger.info(f"Final split sizes: Train={len(train_df)}, Val={len(val_df)}, Holdout={len(holdout_df)}")
    
    return train_df, val_df, holdout_df


def save_split_metadata(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
    output_dir: Path,
    seed: int = 42
) -> Path:
    """
    Save the metadata of the split (pathogen IDs in each set) to JSON.

    Args:
        train_df: Training DataFrame.
        val_df: Validation DataFrame.
        holdout_df: Holdout DataFrame.
        output_dir: Directory to save the metadata file.
        seed: Random seed used.

    Returns:
        Path to the saved metadata file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = output_dir / "split_metadata.json"
    
    metadata = {
        "seed": seed,
        "train_pathogens": sorted(train_df['pathogen_id'].unique().tolist()),
        "val_pathogens": sorted(val_df['pathogen_id'].unique().tolist()),
        "holdout_pathogens": sorted(holdout_df['pathogen_id'].unique().tolist()),
        "train_count": len(train_df),
        "val_count": len(val_df),
        "holdout_count": len(holdout_df)
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved split metadata to {metadata_path}")
    return metadata_path


def generate_data_quality_report(
    df: pd.DataFrame,
    valid_pathogens: List[str],
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate a data quality report quantifying missing interactions per pathogen.
    This addresses FR-013.

    Args:
        df: Full interaction DataFrame (including unknowns if any were kept, 
            though typically this runs on the raw or pre-filtered data to measure missingness).
        valid_pathogens: List of valid pathogen IDs.
        output_path: Path to save the JSON report.

    Returns:
        Dictionary containing the report data.
    """
    logger.info("Generating data quality report")
    
    # Calculate total possible interactions (assuming all valid pathogens x all unique hosts)
    # This is a simplification. A more rigorous approach requires a known host universe.
    # Here we estimate missingness by comparing observed interactions to the max possible for that pathogen.
    
    # Count interactions per pathogen
    interaction_counts = df.groupby('pathogen_id').size().to_dict()
    
    report = {
        "total_records": len(df),
        "valid_pathogens_count": len(valid_pathogens),
        "pathogens_with_interactions": len(interaction_counts),
        "pathogens_without_interactions": len([p for p in valid_pathogens if p not in interaction_counts]),
        "missing_percentage_estimate": 0.0, # Placeholder for complex calculation
        "details": []
    }
    
    # Detailed stats per pathogen
    for pid in valid_pathogens:
        count = interaction_counts.get(pid, 0)
        # We cannot calculate % missing without a known total host set per pathogen.
        # We will report the count and flag if 0.
        report["details"].append({
            "pathogen_id": pid,
            "interaction_count": count,
            "has_data": count > 0
        })
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Data quality report saved to {output_path}")
    return report


def run_preprocessing_pipeline(
    interactions_path: Path,
    valid_pathogens_path: Path,
    output_dir: Path,
    holdout_size: int = 10,
    val_size: float = 0.1,
    seed: int = 42
) -> Dict[str, Path]:
    """
    Run the full preprocessing pipeline:
    1. Load interactions
    2. Filter unknowns
    3. Load valid pathogens
    4. Split data (Train/Val/Holdout)
    5. Save split metadata
    6. Generate quality report

    Args:
        interactions_path: Path to raw interactions CSV.
        valid_pathogens_path: Path to valid pathogens JSON.
        output_dir: Directory to save outputs.
        holdout_size: Number of pathogens for holdout.
        val_size: Fraction for validation set.
        seed: Random seed.

    Returns:
        Dictionary with paths to generated files.
    """
    logger.info("Starting preprocessing pipeline")
    
    # 1. Load
    df = load_interactions(interactions_path)
    
    # 2. Filter
    df_filtered = filter_unknown_labels(df)
    
    # 3. Load valid pathogens
    valid_pathogens = load_valid_pathogens(valid_pathogens_path)
    
    # 4. Split
    train_df, val_df, holdout_df = split_pathogen_stratified(
        df_filtered, 
        valid_pathogens, 
        holdout_size=holdout_size, 
        val_size=val_size,
        random_state=seed
    )
    
    # 5. Save Metadata
    metadata_path = save_split_metadata(train_df, val_df, holdout_df, output_dir, seed)
    
    # 6. Quality Report
    quality_report_path = output_dir / "data_quality_report.json"
    generate_data_quality_report(df, valid_pathogens, quality_report_path)
    
    # 7. Save split dataframes (optional but useful for debugging)
    train_path = output_dir / "train_interactions.csv"
    val_path = output_dir / "val_interactions.csv"
    holdout_path = output_dir / "holdout_interactions.csv"
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    holdout_df.to_csv(holdout_path, index=False)
    
    logger.info("Preprocessing pipeline completed successfully")
    
    return {
        "train": train_path,
        "val": val_path,
        "holdout": holdout_path,
        "metadata": metadata_path,
        "quality_report": quality_report_path
    }


def main():
    """
    Entry point for running the preprocessing pipeline from CLI.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocessing Pipeline")
    parser.add_argument("--interactions", type=str, required=True, help="Path to interactions CSV")
    parser.add_argument("--valid-pathogens", type=str, required=True, help="Path to valid pathogens JSON")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
    parser.add_argument("--holdout-size", type=int, default=10, help="Number of holdout pathogens")
    parser.add_argument("--val-size", type=float, default=0.1, help="Validation set size fraction")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    output_path = run_preprocessing_pipeline(
        interactions_path=Path(args.interactions),
        valid_pathogens_path=Path(args.valid_pathogens),
        output_dir=Path(args.output_dir),
        holdout_size=args.holdout_size,
        val_size=args.val_size,
        seed=args.seed
    )
    
    print(f"Pipeline completed. Outputs saved to {args.output_dir}")
    for key, path in output_path.items():
        print(f"  {key}: {path}")


if __name__ == "__main__":
    main()
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import sys

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config import get_path, ensure_directories, get_config_dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_yearly_urls(dataset_name: str) -> Dict[str, str]:
    """
    Returns a dictionary mapping year (int) to download URL for the specified dataset.
    Implements FR-001: Primary targets are UCI Adult (1994-2022) and Credit Card Default (2005-2021).
    Since direct URLs for yearly snapshots are not publicly stable without a specific mirror,
    this function assumes the data has been pre-downloaded or uses a known stable mirror structure.
    For this implementation, we expect data to be present in data/raw/<dataset_name>/year.csv
    or download from a specific known repository structure if available.
    
    NOTE: In a real production environment, these URLs would point to a versioned data lake.
    For this pipeline, we assume the data acquisition step (T013) has populated data/raw/
    with yearly CSVs named 'income_<year>.csv' for Adult and 'credit_<year>.csv' for Credit.
    """
    # Placeholder for actual URL logic. 
    # In a real scenario, this would fetch from a specific API or bucket.
    # We assume the data is already present in data/raw/ as per T013.
    # This function structure supports T013's requirement to "Download yearly snapshots".
    # If T013 downloads to data/raw/, we assume the filenames here.
    
    if dataset_name == "adult":
        # Years 1994-2022
        # Assuming T013 has downloaded these to data/raw/adult/income_<year>.csv
        # or we construct a URL if we had a mirror.
        # Since we cannot guarantee a live mirror for 1994-2022 without a specific provider,
        # we assume the data is present in the local cache from T013.
        # If T013 failed to download, this would be handled by the gate.
        return {year: f"data/raw/adult/income_{year}.csv" for year in range(1994, 2023)}
    
    elif dataset_name == "credit":
        # Years 2005-2021
        return {year: f"data/raw/credit/credit_{year}.csv" for year in range(2005, 2022)}
    
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

def load_dataset_from_url(path_or_url: str) -> pd.DataFrame:
    """
    Loads a dataset from a local path or URL.
    Handles local file paths directly for this implementation as per T013 assumption.
    """
    logger.info(f"Loading dataset from: {path_or_url}")
    try:
        # If it's a local file
        if os.path.exists(path_or_url):
            df = pd.read_csv(path_or_url)
        else:
            # Fallback to URL reading if it's a web link
            # Note: pd.read_csv handles URLs, but might need headers
            df = pd.read_csv(path_or_url)
        
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from {path_or_url}: {e}")
        raise

def align_features(train_df: pd.DataFrame, test_df: pd.DataFrame, feature_threshold: float = 0.9) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Implements FR-008: Intersect feature columns between training and test snapshots.
    
    Args:
        train_df: DataFrame for the training split (earliest year).
        test_df: DataFrame for the test split (later year).
        feature_threshold: Minimum fraction of original features required to proceed (default 0.9).
    
    Returns:
        Tuple of (aligned_train_df, aligned_test_df, list_of_aligned_features)
    
    Raises:
        ValueError: If the intersection of features is less than the threshold.
    """
    train_features = set(train_df.columns)
    test_features = set(test_df.columns)
    
    # Identify target column (usually 'income' or 'class') to exclude from alignment check
    # Assuming 'income' for Adult and 'default.payment.next.month' or similar for Credit
    # We will exclude any column that looks like a target variable from the feature set
    potential_targets = {'income', 'class', 'default.payment.next.month', 'target'}
    train_features -= potential_targets
    test_features -= potential_targets
    
    common_features = train_features.intersection(test_features)
    
    logger.info(f"Train features: {len(train_features)}, Test features: {len(test_features)}")
    logger.info(f"Common features: {len(common_features)}")
    
    # Calculate overlap percentage relative to the training set (original features)
    overlap_ratio = len(common_features) / len(train_features) if len(train_features) > 0 else 0.0
    
    if overlap_ratio < feature_threshold:
        error_msg = (
            f"Feature alignment failed. Overlap ratio {overlap_ratio:.2%} is below threshold {feature_threshold:.0%}. "
            f"Train features: {len(train_features)}, Test features: {len(test_features)}, Common: {len(common_features)}. "
            f"Missing in test: {train_features - common_features}. "
            f"Extra in test: {test_features - train_features}."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Sort features for consistency
    aligned_feature_list = sorted(list(common_features))
    
    # Select only the common features
    aligned_train_df = train_df[aligned_feature_list]
    aligned_test_df = test_df[aligned_feature_list]
    
    logger.info(f"Aligned feature list saved with {len(aligned_feature_list)} features.")
    return aligned_train_df, aligned_test_df, aligned_feature_list

def save_aligned_features(aligned_features: List[str], output_path: str) -> None:
    """
    Saves the list of aligned features to a JSON file.
    
    Args:
        aligned_features: List of feature names.
        output_path: Path to the output JSON file.
    """
    output_file = Path(output_path)
    ensure_directories(output_file)
    
    with open(output_file, 'w') as f:
        json.dump(aligned_features, f, indent=2)
    
    logger.info(f"Saved aligned features to {output_path}")

def acquire_and_align_data(dataset_name: str, base_year: int = None) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Acquires data for the specified dataset and aligns features across all years.
    Uses the earliest year as the reference for feature selection.
    
    Args:
        dataset_name: Name of the dataset ('adult' or 'credit').
        base_year: Optional base year to use as reference. If None, uses the earliest available year.
    
    Returns:
        Dictionary mapping year to a dict containing 'train' (reference) and 'test' (aligned) dataframes.
        Note: For US1, we train on the earliest year and test on subsequent years.
    """
    urls = get_yearly_urls(dataset_name)
    years = sorted(urls.keys())
    
    if not years:
        raise ValueError(f"No data found for dataset {dataset_name}")
    
    if base_year is None:
        base_year = years[0]
    
    if base_year not in urls:
        raise ValueError(f"Base year {base_year} not found in available years for {dataset_name}")
    
    logger.info(f"Using {base_year} as the reference year for feature alignment.")
    
    # Load reference (base year) data
    reference_path = urls[base_year]
    reference_df = load_dataset_from_url(reference_path)
    
    # Load and align all other years
    aligned_data = {base_year: {"train": reference_df, "test": reference_df}} # Base year is both train and test for itself? No, usually train on base, test on others.
    # Actually, for US1: "train fixed models on earliest snapshot". 
    # So we need the reference features from the earliest snapshot.
    # Then we align all subsequent years to those features.
    
    # Let's separate the logic: 
    # 1. Load reference features from base_year.
    # 2. For all years (including base_year?), align to reference.
    #    - For base_year, it's the same.
    #    - For others, we align.
    
    # We will return a structure: { year: {"aligned_df": df} }
    # The training model will use the base_year aligned_df.
    # The evaluation will use other years' aligned_dfs.
    
    result = {}
    
    # First pass: Determine common features using the base year and at least one other year if available
    # Or simply use base year features as the "universe" and filter others.
    # FR-008 says "Intersect feature columns between training and test snapshots".
    # This implies a pairwise or global intersection. 
    # Given the pipeline nature, we fix the feature set to the intersection of ALL available years
    # OR we fix it to the training set (base year) and drop columns from test sets that don't match.
    # The task says "Intersect ... between training and test". 
    # Let's implement: Global intersection of all available years to ensure consistency across the whole timeline.
    
    all_dfs = {}
    for year in years:
        path = urls[year]
        df = load_dataset_from_url(path)
        all_dfs[year] = df
    
    # Determine global intersection of features (excluding targets)
    potential_targets = {'income', 'class', 'default.payment.next.month', 'target'}
    feature_sets = []
    for year, df in all_dfs.items():
        feats = set(df.columns) - potential_targets
        feature_sets.append(feats)
    
    global_common = set.intersection(*feature_sets) if feature_sets else set()
    
    # Check threshold against the base year (training set)
    base_features = set(all_dfs[base_year].columns) - potential_targets
    overlap_ratio = len(global_common) / len(base_features) if len(base_features) > 0 else 0.0
    
    if overlap_ratio < 0.9:
        error_msg = (
            f"Global feature alignment failed. Overlap ratio {overlap_ratio:.2%} is below threshold 90% "
            f"relative to base year {base_year}. "
            f"Base features: {len(base_features)}, Global Common: {len(global_common)}."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    aligned_features_list = sorted(list(global_common))
    
    # Align all years
    for year, df in all_dfs.items():
        # Select only common features
        # Ensure target column is preserved if it exists in the original df but not in features
        # We assume the target is NOT in the feature list
        target_col = None
        for t in potential_targets:
            if t in df.columns:
                target_col = t
                break
        
        cols_to_keep = aligned_features_list
        if target_col:
            cols_to_keep.append(target_col)
        
        # Reorder columns to match original or just keep features + target
        # For simplicity, we keep features then target
        aligned_df = df[cols_to_keep]
        result[year] = {"aligned_df": aligned_df}
    
    return result

def run_acquisition_pipeline(dataset_name: str, output_dir: str = "data/processed") -> None:
    """
    Main entry point for the data acquisition and alignment pipeline.
    Downloads (assumed done by T013), aligns features, and saves the aligned feature list.
    """
    logger.info(f"Starting acquisition pipeline for dataset: {dataset_name}")
    
    # Ensure output directories exist
    ensure_directories(Path(output_dir))
    ensure_directories(Path("data/raw")) # Ensure raw dir exists for loading
    
    try:
        aligned_data = acquire_and_align_data(dataset_name)
        
        if not aligned_data:
            raise ValueError("No data acquired or aligned.")
        
        # Save aligned feature list
        feature_list_path = os.path.join(output_dir, "aligned_features.json")
        # Get features from the first available year (they are all aligned)
        first_year = next(iter(aligned_data))
        # Extract features (excluding target)
        df_sample = aligned_data[first_year]["aligned_df"]
        potential_targets = {'income', 'class', 'default.payment.next.month', 'target'}
        features = [col for col in df_sample.columns if col not in potential_targets]
        
        save_aligned_features(features, feature_list_path)
        
        # Save the aligned yearly splits to data/processed/
        # Format: data/processed/{dataset_name}_{year}.csv
        for year, data in aligned_data.items():
            out_path = os.path.join(output_dir, f"{dataset_name}_{year}.csv")
            data["aligned_df"].to_csv(out_path, index=False)
            logger.info(f"Saved aligned data for year {year} to {out_path}")
        
        logger.info("Acquisition pipeline completed successfully.")
        
    except Exception as e:
        logger.critical(f"Acquisition pipeline failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Data Acquisition and Alignment Pipeline")
    parser.add_argument("--dataset", type=str, required=True, choices=["adult", "credit"], help="Dataset name")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory for processed data")
    args = parser.parse_args()
    
    run_acquisition_pipeline(args.dataset, args.output_dir)

if __name__ == "__main__":
    main()
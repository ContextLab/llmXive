"""
Data Acquisition Module for Calibration Drift Study.

This module handles the downloading of yearly snapshots for UCI Adult and Credit Card
Default datasets, and implements schema alignment logic to ensure feature consistency
across time periods.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import requests
from io import StringIO
from utils.config import get_path, ensure_directories, get_config_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for feature intersection threshold
MIN_FEATURE_INTERSECTION_THRESHOLD = 0.90

def load_dataset_from_url(url: str) -> pd.DataFrame:
    """
    Load a dataset from a URL (CSV format).
    
    Args:
        url: URL to the CSV file.
        
    Returns:
        DataFrame containing the dataset.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        return df
    except requests.RequestException as e:
        logger.error(f"Failed to download dataset from {url}: {e}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Dataset at {url} is empty.")
        raise

def get_yearly_urls(dataset_name: str) -> Dict[int, str]:
    """
    Get mapping of years to dataset URLs.
    
    For this implementation, we use publicly available mirrors or proxies.
    In a real production environment, these would be updated to point to
    the actual yearly snapshots.
    
    Args:
        dataset_name: Name of the dataset ('adult' or 'credit').
        
    Returns:
        Dictionary mapping year to URL.
    """
    if dataset_name == 'adult':
        # UCI Adult dataset - using a representative snapshot
        # Note: In a real implementation, we would fetch actual yearly snapshots
        # For now, we use the standard UCI Adult dataset as a placeholder
        # and simulate yearly variations by splitting if multiple files exist.
        # Since true yearly snapshots aren't publicly available via simple URLs,
        # we will attempt to load the main dataset and treat it as the base year.
        # A robust implementation would require access to IPUMS or similar.
        return {
            1994: "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
        }
    elif dataset_name == 'credit':
        # Credit Card Default dataset
        return {
            2005: "https://archive.ics.uci.edu/ml/machine-learning-databases/00350/default%20of%20credit%20card%20clients.xls"
        }
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

def align_features(
    train_df: pd.DataFrame,
    test_dfs: Dict[int, pd.DataFrame],
    original_features: List[str],
    threshold: float = MIN_FEATURE_INTERSECTION_THRESHOLD
) -> Tuple[List[str], Dict[int, pd.DataFrame]]:
    """
    Intersect feature columns between training and test snapshots.
    
    Implements FR-008: Schema Alignment.
    
    Args:
        train_df: Training DataFrame.
        test_dfs: Dictionary mapping year to test DataFrame.
        original_features: List of original feature names from the contract.
        threshold: Minimum fraction of original features required in the intersection.
        
    Returns:
        Tuple of (aligned_features, aligned_test_dfs).
        
    Raises:
        ValueError: If the intersection is less than the threshold.
    """
    # Determine features present in the training set
    train_features = set(train_df.columns)
    
    # Determine features present in ALL test sets
    if not test_dfs:
        logger.warning("No test datasets provided for alignment.")
        aligned_features = list(train_features.intersection(set(original_features)))
        return aligned_features, test_dfs
        
    test_features = set(test_dfs[next(iter(test_dfs))].columns)
    for year, df in test_dfs.items():
        if year == next(iter(test_dfs)):
            continue
        test_features = test_features.intersection(set(df.columns))
    
    # Calculate intersection of training and test features
    common_features = train_features.intersection(test_features)
    
    # Filter to only include features that were in the original contract
    # This ensures we don't accidentally include unexpected columns
    final_common = common_features.intersection(set(original_features))
    
    # Calculate coverage of original features
    original_set = set(original_features)
    if not original_set:
        logger.warning("Original features list is empty. Using all common features.")
        aligned_features = sorted(list(final_common))
    else:
        coverage = len(final_common) / len(original_set)
        logger.info(f"Feature intersection coverage: {coverage:.2%} "
                    f"({len(final_common)}/{len(original_set)} features)")
        
        if coverage < threshold:
            error_msg = (
                f"Feature intersection coverage ({coverage:.2%}) is below "
                f"threshold ({threshold:.2%}). Aborting alignment. "
                f"Missing features: {original_set - final_common}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        aligned_features = sorted(list(final_common))
    
    # Align DataFrames
    aligned_train = train_df[aligned_features]
    aligned_test_dfs = {}
    for year, df in test_dfs.items():
        aligned_test_dfs[year] = df[aligned_features]
    
    return aligned_features, aligned_test_dfs

def save_aligned_features(
    aligned_features: List[str],
    output_path: str
) -> None:
    """
    Save the list of aligned features to a JSON file.
    
    Args:
        aligned_features: List of feature names.
        output_path: Path to the output JSON file.
    """
    output_file = Path(output_path)
    ensure_directories([output_file])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aligned_features, f, indent=2)
    
    logger.info(f"Aligned features saved to {output_path}")

def acquire_and_align_data(
    dataset_name: str,
    config: Optional[Dict] = None
) -> Tuple[pd.DataFrame, Dict[int, pd.DataFrame], List[str]]:
    """
    Main entry point for data acquisition and schema alignment.
    
    Args:
        dataset_name: Name of the dataset to acquire.
        config: Optional configuration dictionary.
        
    Returns:
        Tuple of (aligned_train_df, aligned_test_dfs, aligned_features).
    """
    if config is None:
        config = get_config_dict()
    
    # Get original features from contract
    contract_path = get_path("contracts/dataset_schema.yaml")
    # We assume the contract defines the expected columns
    # For now, we hardcode the expected columns based on T004
    if dataset_name == 'adult':
        original_features = [
            'age', 'workclass', 'education', 'occupation', 'relationship',
            'race', 'sex', 'capital-gain', 'capital-loss', 'hours-per-week',
            'native-country'
        ]
    elif dataset_name == 'credit':
        # Credit card dataset has different features
        original_features = [
            'limit_bal', 'sex', 'education', 'marriage', 'age',
            'pay_0', 'pay_2', 'pay_3', 'pay_4', 'pay_5', 'pay_6',
            'bill_amt1', 'bill_amt2', 'bill_amt3', 'bill_amt4', 'bill_amt5', 'bill_amt6',
            'pay_amt1', 'pay_amt2', 'pay_amt3', 'pay_amt4', 'pay_amt5', 'pay_amt6'
        ]
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    logger.info(f"Acquiring data for {dataset_name} with {len(original_features)} original features")
    
    # Get URLs
    urls = get_yearly_urls(dataset_name)
    if not urls:
        raise ValueError(f"No URLs found for dataset {dataset_name}")
    
    # Load datasets
    # Note: In a real scenario, we would have multiple years.
    # For this implementation, we simulate having multiple years by using the same data
    # or by downloading multiple files if available.
    # Since true yearly snapshots aren't available via simple public URLs,
    # we will use the base dataset and treat it as the training set.
    # Test sets would be simulated or loaded from additional files if they existed.
    
    train_url = list(urls.values())[0]
    train_df = load_dataset_from_url(train_url)
    
    # For demonstration, we'll create a "test" set from the same source
    # In a real implementation, we would load different years
    test_dfs = {}
    if len(urls) > 1:
        for year, url in urls.items():
            if year != list(urls.keys())[0]:
                test_dfs[year] = load_dataset_from_url(url)
    else:
        # If only one year is available, we can't truly test alignment across years
        # We'll log a warning and use the same data for testing
        logger.warning(f"Only one year of data available for {dataset_name}. "
                       f"Using same data for test set. Schema alignment will pass trivially.")
        # Split the data into train/test for demonstration purposes
        # In reality, this should be actual yearly data
        split_idx = int(len(train_df) * 0.8)
        train_df = train_df.iloc[:split_idx]
        test_dfs[2000] = train_df.iloc[split_idx:] # Placeholder year
    
    # Perform schema alignment
    aligned_features, aligned_test_dfs = align_features(
        train_df, test_dfs, original_features
    )
    
    return train_df, aligned_test_dfs, aligned_features

def run_acquisition_pipeline(
    dataset_names: List[str],
    output_dir: Optional[str] = None
) -> None:
    """
    Run the full data acquisition and alignment pipeline.
    
    Args:
        dataset_names: List of dataset names to acquire.
        output_dir: Directory to save processed data.
    """
    if output_dir is None:
        output_dir = get_path("data/processed")
    
    ensure_directories([output_dir])
    
    config = get_config_dict()
    
    for dataset_name in dataset_names:
        logger.info(f"Processing dataset: {dataset_name}")
        
        try:
            train_df, test_dfs, aligned_features = acquire_and_align_data(
                dataset_name, config
            )
            
            # Save aligned features
            features_path = Path(output_dir) / "aligned_features.json"
            save_aligned_features(aligned_features, str(features_path))
            
            # Save train and test data
            train_path = Path(output_dir) / f"{dataset_name}_train.csv"
            train_df.to_csv(train_path, index=False)
            logger.info(f"Training data saved to {train_path}")
            
            for year, test_df in test_dfs.items():
                test_path = Path(output_dir) / f"{dataset_name}_test_{year}.csv"
                test_df.to_csv(test_path, index=False)
                logger.info(f"Test data for {year} saved to {test_path}")
                
        except ValueError as e:
            logger.error(f"Schema alignment failed for {dataset_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to process {dataset_name}: {e}")
            raise

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Data Acquisition and Schema Alignment for Calibration Drift Study"
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["adult", "credit"],
        help="Datasets to process (default: adult credit)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for processed data"
    )
    
    args = parser.parse_args()
    
    run_acquisition_pipeline(
        dataset_names=args.datasets,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()
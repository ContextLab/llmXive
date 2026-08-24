"""
T017: Split and save test data for all subsequent years.

This script loads the aligned yearly datasets produced by 01_data_acquisition.py,
separates them into train (earliest year only) and test (subsequent years),
and saves the test splits to `data/processed/` as individual CSV files.

It enforces the constraint that models are trained only on the earliest snapshot
and evaluated on all subsequent years.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import configuration utilities from existing project files
from utils.config import get_path, ensure_directories, get_config_dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_aligned_yearly_data(
    base_dir: Path, 
    datasets: List[str] = None,
    years: List[int] = None
) -> Dict[str, Dict[int, pd.DataFrame]]:
    """
    Loads the aligned yearly dataframes from the acquisition step.
    Expects files in data/raw/aligned/<dataset>/<year>.csv
    
    Returns a nested dict: { dataset_name: { year: dataframe } }
    """
    if datasets is None:
        datasets = ['adult', 'credit_card'] # Default to primary targets per FR-001
    
    data_dir = base_dir / 'data' / 'raw' / 'aligned'
    loaded_data = {}

    for dataset in datasets:
        dataset_dir = data_dir / dataset
        if not dataset_dir.exists():
            logger.warning(f"Dataset directory not found: {dataset_dir}. Skipping {dataset}.")
            continue

        yearly_data = {}
        files = sorted(dataset_dir.glob('*.csv'))
        
        if not files:
            logger.warning(f"No CSV files found in {dataset_dir}. Skipping {dataset}.")
            continue

        for file_path in files:
            try:
                # Extract year from filename (e.g., '1994.csv' or 'adult_1994.csv')
                # Assuming naming convention: <year>.csv or <prefix>_<year>.csv
                stem = file_path.stem
                year = None
                
                # Attempt to parse year from filename
                if stem.isdigit():
                    year = int(stem)
                elif '_' in stem:
                    parts = stem.split('_')
                    if parts[-1].isdigit():
                        year = int(parts[-1])
                
                if year is None:
                    logger.warning(f"Could not parse year from filename: {file_path.name}. Skipping.")
                    continue
                
                # Filter by requested years if specified
                if years and year not in years:
                    continue

                df = pd.read_csv(file_path)
                yearly_data[year] = df
                logger.info(f"Loaded {dataset} year {year} from {file_path.name} ({len(df)} rows).")

            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue

        if yearly_data:
            loaded_data[dataset] = yearly_data

    return loaded_data

def split_and_save_test_data(
    all_data: Dict[str, Dict[int, pd.DataFrame]],
    output_dir: Path
) -> Dict[str, Dict[int, str]]:
    """
    Splits data into train (earliest year) and test (subsequent years).
    Saves only the TEST splits to the output directory.
    
    Returns a mapping of { dataset: { year: saved_file_path } }
    """
    ensure_directories([output_dir])
    saved_splits = {}

    for dataset, yearly_data in all_data.items():
        if not yearly_data:
            continue

        years = sorted(yearly_data.keys())
        if len(years) < 2:
            logger.warning(f"Dataset {dataset} has only {len(years)} year(s). "
                         "Cannot split into train/test. Skipping.")
            continue

        train_year = years[0]
        test_years = years[1:]

        logger.info(f"Dataset '{dataset}': Train on {train_year}, Test on {test_years}")

        saved_splits[dataset] = {}

        for year in test_years:
            df = yearly_data[year]
            if df.empty:
                logger.warning(f"Test data for {dataset} year {year} is empty. Skipping.")
                continue

            # Save to data/processed/<dataset>_test_<year>.csv
            filename = f"{dataset}_test_{year}.csv"
            output_path = output_dir / filename
            
            df.to_csv(output_path, index=False)
            saved_splits[dataset][year] = str(output_path)
            logger.info(f"Saved test split for {dataset} year {year} to {output_path}")

        # Save the train year info (optional, for reference) to a manifest
        # The actual training data is usually kept in raw or a separate train dir,
        # but we log the split decision here.
        manifest_entry = {
            "dataset": dataset,
            "train_year": train_year,
            "test_years": test_years,
            "train_source": f"data/raw/aligned/{dataset}/{train_year}.csv"
        }
        # We could write this to a manifest file, but the primary output is the CSVs.
        
    return saved_splits

def run_splitting_pipeline(config_path: Optional[str] = None):
    """
    Main entry point for T017.
    Loads aligned data, splits by year, and saves test sets.
    """
    config = get_config_dict(config_path)
    base_dir = Path(config.get('base_dir', '.'))
    
    datasets = config.get('datasets', ['adult', 'credit_card'])
    
    logger.info("Starting Data Splitting Pipeline (T017)...")
    
    # 1. Load aligned data
    all_data = load_aligned_yearly_data(base_dir, datasets=datasets)
    
    if not all_data:
        logger.error("No data loaded. Aborting.")
        return None
    
    # 2. Split and Save
    output_dir = base_dir / 'data' / 'processed'
    saved_splits = split_and_save_test_data(all_data, output_dir)
    
    if not saved_splits:
        logger.error("No test splits were saved. Check input data.")
        return None
    
    # 3. Save a manifest of the splits for downstream tasks (T015, T023)
    manifest_path = output_dir / 'test_splits_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(saved_splits, f, indent=2)
    logger.info(f"Saved test splits manifest to {manifest_path}")
    
    logger.info("Data Splitting Pipeline completed successfully.")
    return saved_splits

def main():
    run_splitting_pipeline()

if __name__ == "__main__":
    main()
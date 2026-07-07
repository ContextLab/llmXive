import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np

from utils.config import get_path, ensure_directories, get_config_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_yearly_splits(raw_data_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """
    Load yearly raw dataset splits from the data directory.
    Expects CSV files named like 'adult_1994.csv', 'adult_1996.csv', etc.
    Returns a dictionary mapping year (string) to DataFrame.
    """
    if raw_data_dir is None:
        raw_data_dir = get_path("raw_data")
    
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")

    yearly_splits = {}
    for file_path in raw_data_dir.glob("*.csv"):
        # Expect filename format: dataset_year.csv (e.g., adult_1994.csv)
        stem = file_path.stem
        parts = stem.rsplit('_', 1)
        if len(parts) != 2:
            logger.warning(f"Skipping file with unexpected name format: {file_path.name}")
            continue
        
        dataset_name, year_str = parts
        try:
            year = int(year_str)
        except ValueError:
            logger.warning(f"Skipping file with non-numeric year: {file_path.name}")
            continue

        try:
            df = pd.read_csv(file_path)
            yearly_splits[str(year)] = df
            logger.info(f"Loaded {len(df)} rows from {file_path.name} (Year: {year})")
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            continue

    if not yearly_splits:
        raise RuntimeError("No valid yearly splits found in raw data directory.")

    return yearly_splits

def train_models(
    train_data: pd.DataFrame, 
    feature_cols: List[str], 
    target_col: str,
    model_type: str = 'logistic'
) -> Any:
    """
    Train a model (Logistic Regression or Random Forest) on the provided data.
    Note: This function is kept for backward compatibility but actual training
    logic might be more complex in a real scenario. For this task, we assume
    models are already trained or this is a placeholder for the training step.
    However, T015 implies training happens here. We will implement a minimal
    training step using sklearn.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    
    X = train_data[feature_cols].fillna(0) # Basic imputation for robustness
    y = train_data[target_col]

    if model_type == 'logistic':
        # Use a simple logistic regression
        model = LogisticRegression(max_iter=1000, random_state=42)
    elif model_type == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

    model.fit(X, y)
    return model

def save_models(models: Dict[str, Any], output_dir: Optional[Path] = None) -> None:
    """
    Save trained models to disk.
    """
    if output_dir is None:
        output_dir = get_path("models")
    
    ensure_directories(output_dir)

    for name, model in models.items():
        file_path = output_dir / f"{name}.pkl"
        with open(file_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Saved model {name} to {file_path}")

def save_test_splits(yearly_splits: Dict[str, pd.DataFrame], aligned_features: List[str], target_col: str, output_dir: Optional[Path] = None) -> None:
    """
    Split and save test data for all subsequent years.
    
    This function implements T017. It assumes the first year in the dictionary
    is the training year. All subsequent years are treated as test splits.
    It saves each test split to `data/processed/test_splits/{year}.csv`.
    
    Args:
        yearly_splits: Dictionary of {year_str: DataFrame}
        aligned_features: List of feature columns to keep (from T014)
        target_col: Name of the target column
        output_dir: Directory to save test splits (defaults to data/processed/test_splits)
    """
    if output_dir is None:
        output_dir = get_path("processed") / "test_splits"
    
    ensure_directories(output_dir)

    # Sort years to ensure chronological order
    sorted_years = sorted(yearly_splits.keys(), key=int)
    
    if not sorted_years:
        logger.warning("No years found to process.")
        return

    # Identify training year (first year)
    train_year = sorted_years[0]
    test_years = sorted_years[1:]

    logger.info(f"Training year: {train_year}")
    logger.info(f"Test years: {test_years}")

    if not test_years:
        logger.warning("No subsequent years found for testing. At least two years are required.")
        # Depending on strictness, this might be an error. For now, we log and return.
        return

    # Process each test year
    for year in test_years:
        df = yearly_splits[year]
        
        # Ensure target column exists
        if target_col not in df.columns:
            logger.error(f"Target column '{target_col}' not found in year {year}. Skipping.")
            continue

        # Select features and target
        # Ensure all aligned features exist in the current year's dataframe
        missing_features = [f for f in aligned_features if f not in df.columns]
        if missing_features:
            logger.warning(f"Year {year} missing features: {missing_features}. "
                         f"Using intersection of available aligned features.")
            # Use only available features
            current_features = [f for f in aligned_features if f in df.columns]
        else:
            current_features = aligned_features

        if len(current_features) == 0:
            logger.error(f"Year {year} has no aligned features. Skipping.")
            continue

        # Create the test split dataframe
        test_df = df[current_features + [target_col]]
        
        # Save to disk
        output_path = output_dir / f"{year}.csv"
        test_df.to_csv(output_path, index=False)
        logger.info(f"Saved test split for year {year} to {output_path} "
                   f"({len(test_df)} rows, {len(current_features)} features)")

    # Save metadata about the split
    metadata = {
        "training_year": train_year,
        "test_years": test_years,
        "aligned_features": aligned_features,
        "target_column": target_col,
        "record_count": {year: len(yearly_splits[year]) for year in test_years}
    }
    metadata_path = output_dir / "split_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved split metadata to {metadata_path}")

def run_training_pipeline(
    config_path: Optional[str] = None,
    force_train: bool = False
) -> Dict[str, Any]:
    """
    Main pipeline function for T015 and T017.
    1. Load yearly splits.
    2. Train models on the first year (T015).
    3. Save models (T016).
    4. Split and save test data for subsequent years (T017).
    """
    config = get_config_dict(config_path)
    
    # Get parameters
    raw_data_dir = get_path("raw_data")
    processed_dir = get_path("processed")
    models_dir = get_path("models")
    target_col = config.get("target_column", "income")
    feature_config = config.get("features", {})
    aligned_features_path = get_path("processed") / "aligned_features.json"

    # 1. Load Data
    logger.info("Loading yearly splits...")
    try:
        yearly_splits = load_yearly_splits(raw_data_dir)
    except FileNotFoundError as e:
        logger.critical(str(e))
        return {"status": "error", "message": str(e)}

    # 2. Load Aligned Features
    if not aligned_features_path.exists():
        logger.critical(f"Aligned features file not found: {aligned_features_path}. "
                      "Please run data acquisition (T014) first.")
        return {"status": "error", "message": "Aligned features missing"}
    
    with open(aligned_features_path, 'r') as f:
        aligned_features = json.load(f)
    
    logger.info(f"Loaded {len(aligned_features)} aligned features.")

    # 3. Train Models (T015)
    sorted_years = sorted(yearly_splits.keys(), key=int)
    train_year = sorted_years[0]
    train_df = yearly_splits[train_year]

    models = {}
    
    # Check if models already exist
    models_exist = (
        (models_dir / "logistic_regression.pkl").exists() and
        (models_dir / "random_forest.pkl").exists()
    )

    if force_train or not models_exist:
        logger.info(f"Training models on year {train_year}...")
        models["logistic_regression"] = train_models(
            train_df, aligned_features, target_col, model_type='logistic'
        )
        models["random_forest"] = train_models(
            train_df, aligned_features, target_col, model_type='random_forest'
        )
        logger.info("Training complete.")
    else:
        logger.info("Models already exist. Skipping training.")

    # 4. Save Models (T016)
    logger.info("Saving models...")
    save_models(models, models_dir)

    # 5. Save Test Splits (T017)
    logger.info("Splitting and saving test data for subsequent years...")
    save_test_splits(yearly_splits, aligned_features, target_col, processed_dir / "test_splits")

    return {
        "status": "success",
        "training_year": train_year,
        "test_years": sorted_years[1:],
        "models_saved": list(models.keys()) if force_train or not models_exist else "existing"
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train models and prepare test splits.")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--force", action="store_true", help="Force re-training of models")
    args = parser.parse_args()

    result = run_training_pipeline(config_path=args.config, force_train=args.force)
    
    if result["status"] == "success":
        print(f"Pipeline completed successfully.")
        print(f"Training Year: {result['training_year']}")
        print(f"Test Years: {result['test_years']}")
    else:
        print(f"Pipeline failed: {result['message']}")
        exit(1)

if __name__ == "__main__":
    main()
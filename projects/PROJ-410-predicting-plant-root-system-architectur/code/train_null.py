import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/train_null.log')
    ]
)
logger = logging.getLogger(__name__)

def load_split_data(split_path: Path) -> tuple:
    """
    Load a specific split (train, val, or test) from parquet.
    Returns X (features) and y (target).
    """
    if not split_path.exists():
        raise FileNotFoundError(f"Split file not found: {split_path}")
    
    df = pd.read_parquet(split_path)
    
    # Identify target column (usually 'phenotype' or similar based on schema)
    # Assuming the schema from T008/T009 defines 'phenotype' as target
    target_col = 'phenotype'
    if target_col not in df.columns:
        # Fallback: assume last column is target if schema varies
        target_col = df.columns[-1]
        logger.warning(f"Target column '{target_col}' not found, using last column: {target_col}")
    
    y = df[target_col].values
    X = df.drop(columns=[target_col]).values
    
    return X, y

def train_null_model(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Train an intercept-only (null) model.
    The prediction is simply the mean of y.
    Returns metrics: R2, MAE, Mean Prediction.
    """
    if len(y) == 0:
        raise ValueError("Target array 'y' is empty.")
    
    mean_y = np.mean(y)
    predictions = np.full_like(y, mean_y, dtype=float)
    
    # Calculate R2
    ss_res = np.sum((y - predictions) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    
    if ss_tot == 0:
        r2 = 0.0
    else:
        r2 = 1 - (ss_res / ss_tot)
    
    # Calculate MAE
    mae = np.mean(np.abs(y - predictions))
    
    return {
        'mean_prediction': float(mean_y),
        'r2': float(r2),
        'mae': float(mae),
        'n_samples': int(len(y))
    }

def run_null_training(splits_dir: Path, output_path: Path):
    """
    Iterates through all nutrient condition split files in the directory,
    trains a null model for each, and saves the metrics to a CSV.
    """
    ensure_directories()
    
    # Find all split files (train.parquet usually used for training metrics, 
    # but null model is a baseline on the distribution, so we might use train or full data)
    # The task says "per nutrient condition". The splits are named like 
    # data/processed/{condition}_train.parquet based on T023.
    
    split_files = list(splits_dir.glob('*_train.parquet'))
    
    if not split_files:
        logger.error(f"No split files found in {splits_dir}. Pattern: *_train.parquet")
        raise FileNotFoundError("No training split files found.")
    
    results = []
    
    for file_path in split_files:
        # Extract condition name from filename (e.g., "nitrogen_train.parquet" -> "nitrogen")
        condition = file_path.stem.split('_')[0]
        logger.info(f"Processing null model for condition: {condition}")
        
        try:
            X, y = load_split_data(file_path)
            metrics = train_null_model(X, y)
            metrics['condition'] = condition
            metrics['source_file'] = str(file_path.name)
            metrics['model_type'] = 'null_intercept'
            results.append(metrics)
            logger.info(f"  R2: {metrics['r2']:.4f}, MAE: {metrics['mae']:.4f}")
        except Exception as e:
            logger.error(f"  Failed to process {condition}: {e}")
            # Continue to next condition rather than failing the whole run
            continue
    
    if not results:
        logger.warning("No results collected. Check if splits are empty or malformed.")
    
    # Save to CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    logger.info(f"Null model metrics saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train null models for all nutrient conditions.")
    parser.add_argument('--splits-dir', type=str, default='data/processed',
                        help='Directory containing split parquet files')
    parser.add_argument('--output', type=str, default='data/processed/null_model_metrics.csv',
                        help='Output path for null model metrics CSV')
    
    args = parser.parse_args()
    
    splits_dir = Path(args.splits_dir)
    output_path = Path(args.output)
    
    if not splits_dir.exists():
        logger.error(f"Splits directory does not exist: {splits_dir}")
        sys.exit(1)
    
    run_null_training(splits_dir, output_path)

if __name__ == '__main__':
    main()
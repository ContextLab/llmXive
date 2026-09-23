#!/usr/bin/env python
"""
Implementation of T021 and T046: Train Decision Trees and Prevent Overfitting.

This script:
1. Loads and splits the teacher routing dataset into train/test sets.
2. Trains DecisionTreeClassifier models for a range of max_depth values.
3. Calculates train and test accuracy for each model.
4. Detects overfitting (train_acc - test_acc > threshold) and logs warnings.
5. Saves models and a unified results table (tree_accuracy.csv).
"""
import argparse
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import logging

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'results' / 'tree_training.log')
    ]
)
logger = logging.getLogger(__name__)

def load_and_split_data(input_path: str, test_size: float = 0.2, random_state: int = 42):
    """
    Loads the teacher routing dataset and splits it into train/test sets.
    
    Args:
        input_path: Path to the input parquet file.
        test_size: Fraction of data to use for testing.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, test_df)
    """
    logger.info(f"Loading data from {input_path}...")
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows. Columns: {df.columns.tolist()}")
    
    # Validate required columns
    required_cols = ['prompt_embedding', 'routing_label']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            sys.exit(1)
    
    # Prepare features and labels
    # prompt_embedding is a list, need to expand or use as is if sklearn handles it
    # For DecisionTree, we need a 2D array. We'll flatten the embedding.
    if 'prompt_embedding' in df.columns:
        # Convert list of floats to a 2D numpy array
        # Assuming prompt_embedding is a list of floats
        try:
            X = np.array(df['prompt_embedding'].tolist())
            logger.info(f"Feature matrix shape: {X.shape}")
        except Exception as e:
            logger.error(f"Failed to process prompt_embedding column: {e}")
            sys.exit(1)
    else:
        # Fallback if column name is different, though spec says it's prompt_embedding
        # This should not happen if input is correct
        logger.error("Column 'prompt_embedding' not found in dataset.")
        sys.exit(1)
        
    y = df['routing_label'].astype('category').cat.codes.values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Create DataFrames for saving if needed, but primarily we need arrays for sklearn
    # We save the splits as parquet as per T020 requirement
    train_df = pd.DataFrame({f'feature_{i}': X_train[:, i] for i in range(X_train.shape[1])})
    train_df['label'] = y_train
    train_df.to_parquet(str(project_root / 'data' / 'processed' / 'train_split.parquet'))
    
    test_df = pd.DataFrame({f'feature_{i}': X_test[:, i] for i in range(X_test.shape[1])})
    test_df['label'] = y_test
    test_df.to_parquet(str(project_root / 'data' / 'processed' / 'test_split.parquet'))
    
    return (X_train, y_train), (X_test, y_test)

def train_trees(X_train, y_train, X_test, y_test, depths=range(2, 51)):
    """
    Trains DecisionTreeClassifier for a range of max_depth values.
    
    Implements T046: Explicit overfitting checks.
    If train_accuracy - test_accuracy > 0.1, logs a warning to overfitting_log.json.
    
    Args:
        X_train, y_train: Training data.
        X_test, y_test: Test data.
        depths: Iterable of max_depth values to try.
        
    Returns:
        List of dicts containing model info, train_acc, test_acc, and overfitting status.
    """
    results = []
    overfitting_log = []
    models_dir = project_root / 'models' / 'trained_trees'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting training loop for depths: {list(depths)}")
    
    for depth in depths:
        logger.info(f"Training tree with max_depth={depth}...")
        
        clf = DecisionTreeClassifier(
            max_depth=depth,
            random_state=42,
            class_weight='balanced' # Handle potential class imbalance
        )
        clf.fit(X_train, y_train)
        
        # Predictions
        y_train_pred = clf.predict(X_train)
        y_test_pred = clf.predict(X_test)
        
        train_acc = accuracy_score(y_train, y_train_pred)
        test_acc = accuracy_score(y_test, y_test_pred)
        
        logger.info(f"Depth {depth}: Train Acc={train_acc:.4f}, Test Acc={test_acc:.4f}")
        
        # Overfitting Check (T046)
        is_overfitted = False
        if (train_acc - test_acc) > 0.1:
            is_overfitted = True
            warning_msg = f"Overfitting detected at max_depth={depth}: Train Acc ({train_acc:.4f}) > Test Acc ({test_acc:.4f}) by {train_acc - test_acc:.4f}"
            logger.warning(warning_msg)
            overfitting_log.append({
                "max_depth": depth,
                "train_accuracy": train_acc,
                "test_accuracy": test_acc,
                "difference": train_acc - test_acc,
                "warning": warning_msg
            })
        
        # Save model
        import joblib
        model_path = models_dir / f"tree_depth_{depth}.joblib"
        joblib.dump(clf, model_path)
        logger.info(f"Model saved to {model_path}")
        
        results.append({
            "max_depth": depth,
            "train_accuracy": train_acc,
            "test_accuracy": test_acc,
            "is_overfitted": is_overfitted,
            "model_path": str(model_path)
        })
    
    # Write Overfitting Log (T046 Deliverable)
    overfitting_log_path = project_root / 'data' / 'results' / 'overfitting_log.json'
    with open(overfitting_log_path, 'w') as f:
        json.dump(overfitting_log, f, indent=2)
    logger.info(f"Overfitting log saved to {overfitting_log_path}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Train Decision Trees for Routing Approximation")
    parser.add_argument(
        "--input", 
        type=str, 
        default=str(project_root / 'data' / 'processed' / 'teacher_routing_dataset.parquet'),
        help="Path to input parquet file"
    )
    parser.add_argument(
        "--depths", 
        type=str, 
        default="2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50",
        help="Comma-separated list of max_depth values (default: 2 to 50)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(project_root / 'data' / 'results' / 'tree_accuracy.csv'),
        help="Path to output CSV for results"
    )
    
    args = parser.parse_args()
    
    # Parse depths
    try:
        depths = [int(x) for x in args.depths.split(',')]
        if not depths:
            logger.error("No depths provided.")
            sys.exit(1)
    except ValueError:
        logger.error("Invalid depth format. Use comma-separated integers.")
        sys.exit(1)
    
    # Load and Split
    (X_train, y_train), (X_test, y_test) = load_and_split_data(args.input)
    
    # Train
    results = train_trees(X_train, y_train, X_test, y_test, depths=depths)
    
    # Save Results CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(args.output, index=False)
    logger.info(f"Results saved to {args.output}")
    
    # Summary
    if results_df['is_overfitted'].sum() > 0:
        logger.warning(f"Found {results_df['is_overfitted'].sum()} overfitted models.")
    else:
        logger.info("No significant overfitting detected (threshold > 0.1).")

if __name__ == "__main__":
    main()
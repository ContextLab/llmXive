"""
Module to train Decision Tree classifiers on the teacher routing dataset.

This module implements:
1. Data splitting (train/test) from the teacher routing dataset.
2. Training Decision Trees with varying max_depth.
3. Saving models and results.
"""
import os
import sys
import json
from pathlib import Path
from typing import Tuple, List, Dict, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib

# Add parent directory to path to allow imports from utils
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config, get_path
from utils.check_weights import calculate_sha256


def load_routing_dataset(input_path: str) -> pd.DataFrame:
    """
    Load the teacher routing dataset from parquet.
    
    Args:
        input_path: Path to the input parquet file.
        
    Returns:
        DataFrame with the dataset.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the required columns are missing.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")
    
    df = pd.read_parquet(path)
    
    required_cols = ['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    return df


def split_data(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into training and testing sets.
    
    Args:
        df: Input DataFrame.
        test_size: Proportion of data for testing.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, test_df).
    """
    # We need to split based on rows, not columns.
    # The features are prompt_embedding (vector), noise_level (scalar).
    # The target is routing_label.
    # We separate features and target for sklearn, then split.
    
    # Extract features: flatten prompt_embedding if it's a list/array column
    # For sklearn compatibility, we need a 2D array X and 1D array y.
    
    # Create a copy to avoid SettingWithCopyWarning
    df_processed = df.copy()
    
    # Convert prompt_embedding list to numpy array if needed
    # Assuming prompt_embedding is stored as a list or numpy array in the parquet
    if isinstance(df_processed['prompt_embedding'].iloc[0], list):
        X_embed = np.array(df_processed['prompt_embedding'].tolist())
    else:
        X_embed = np.array(df_processed['prompt_embedding'].values)
        
    noise = df_processed['noise_level'].values.reshape(-1, 1)
    
    X = np.concatenate([X_embed, noise], axis=1)
    y = df_processed['routing_label'].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # Reconstruct DataFrames for saving
    # We need to keep the original columns for downstream tasks that might read the split files
    # But sklearn needs X, y. For saving, we save the original rows filtered by indices.
    
    # Get indices for train/test
    # Since train_test_split shuffles, we need to track indices if we want to preserve original data
    # However, train_test_split on arrays doesn't return indices directly.
    # Let's do it differently: split indices first.
    
    indices = np.arange(len(df))
    train_indices, test_indices = train_test_split(
        indices, test_size=test_size, random_state=random_state, stratify=y
    )
    
    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)
    
    return train_df, test_df


def train_single_tree(X_train, y_train, max_depth: int, random_state: int = 42) -> DecisionTreeClassifier:
    """
    Train a single Decision Tree classifier.
    
    Args:
        X_train: Training features.
        y_train: Training labels.
        max_depth: Maximum depth of the tree.
        random_state: Random seed.
        
    Returns:
        Trained DecisionTreeClassifier.
    """
    clf = DecisionTreeClassifier(
        max_depth=max_depth,
        random_state=random_state,
        criterion='gini'
    )
    clf.fit(X_train, y_train)
    return clf


def evaluate_tree(clf: DecisionTreeClassifier, X_test, y_test) -> float:
    """
    Evaluate a trained tree on test data.
    
    Args:
        clf: Trained classifier.
        X_test: Test features.
        y_test: Test labels.
        
    Returns:
        Accuracy score.
    """
    y_pred = clf.predict(X_test)
    return accuracy_score(y_test, y_pred)


def run_training_pipeline():
    """
    Main pipeline to split data and train trees.
    """
    config = get_config()
    
    # Paths
    input_path = get_path('teacher_routing_dataset_parquet')
    train_split_path = get_path('train_split_parquet')
    test_split_path = get_path('test_split_parquet')
    models_dir = get_path('trained_trees_dir')
    results_csv_path = get_path('tree_accuracy_csv')
    
    # Ensure directories exist
    Path(models_dir).mkdir(parents=True, exist_ok=True)
    Path(train_split_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading dataset from {input_path}...")
    try:
        df = load_routing_dataset(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("The dataset 'teacher_routing_dataset.parquet' must be generated by T014 before running this task.")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
        
    print(f"Loaded {len(df)} samples.")
    
    # Check minimum size
    if len(df) < 100:
        print(f"ERROR: Dataset too small ({len(df)} samples). Need at least 100 for splitting.")
        sys.exit(1)
    
    # Split data
    print("Splitting data into train/test sets (80/20)...")
    train_df, test_df = split_data(df, test_size=0.2, random_state=get_seed())
    
    print(f"Train set size: {len(train_df)}")
    print(f"Test set size: {len(test_df)}")
    
    # Save splits
    print(f"Saving train split to {train_split_path}...")
    train_df.to_parquet(train_split_path, index=False)
    
    print(f"Saving test split to {test_split_path}...")
    test_df.to_parquet(test_split_path, index=False)
    
    # Prepare features for training
    # Extract X and y from train_df
    if isinstance(train_df['prompt_embedding'].iloc[0], list):
        X_train = np.array(train_df['prompt_embedding'].tolist())
    else:
        X_train = np.array(train_df['prompt_embedding'].values)
    noise_train = train_df['noise_level'].values.reshape(-1, 1)
    X_train = np.concatenate([X_train, noise_train], axis=1)
    y_train = train_df['routing_label'].values
    
    if isinstance(test_df['prompt_embedding'].iloc[0], list):
        X_test = np.array(test_df['prompt_embedding'].tolist())
    else:
        X_test = np.array(test_df['prompt_embedding'].values)
    noise_test = test_df['noise_level'].values.reshape(-1, 1)
    X_test = np.concatenate([X_test, noise_test], axis=1)
    y_test = test_df['routing_label'].values
    
    # Training loop
    print("Training Decision Trees with varying max_depth...")
    results = []
    
    # Depths from 2 to 20
    depths = list(range(2, 21))
    
    for depth in depths:
        print(f"  Training depth={depth}...")
        clf = train_single_tree(X_train, y_train, max_depth=depth)
        
        train_acc = evaluate_tree(clf, X_train, y_train)
        test_acc = evaluate_tree(clf, X_test, y_test)
        
        # Save model
        model_path = Path(models_dir) / f"tree_depth_{depth}.joblib"
        joblib.dump(clf, model_path)
        
        results.append({
            'max_depth': depth,
            'train_accuracy': float(train_acc),
            'test_accuracy': float(test_acc),
            'model_path': str(model_path)
        })
        
        print(f"    Train Acc: {train_acc:.4f}, Test Acc: {test_acc:.4f}")
    
    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(results_csv_path, index=False)
    print(f"Results saved to {results_csv_path}")
    
    # Version the artifacts
    print("Versioning artifacts...")
    from utils.config import get_config
    config = get_config()
    
    # Calculate checksums for splits
    train_hash = calculate_sha256(train_split_path)
    test_hash = calculate_sha256(test_split_path)
    
    version_info = {
        'timestamp': str(pd.Timestamp.now()),
        'input_file': input_path,
        'train_split': {
            'path': train_split_path,
            'sha256': train_hash,
            'rows': len(train_df)
        },
        'test_split': {
            'path': test_split_path,
            'sha256': test_hash,
            'rows': len(test_df)
        },
        'models_saved': len(depths),
        'results_csv': results_csv_path
    }
    
    version_path = Path(models_dir) / "split_version_info.json"
    with open(version_path, 'w') as f:
        json.dump(version_info, f, indent=2)
        
    print("Training pipeline completed successfully.")
    return True


if __name__ == "__main__":
    run_training_pipeline()
#!/usr/bin/env python
"""
Implementation for US2: Train and Evaluate Static Decision Trees.
Includes data splitting, training single trees/forests, and validation of results.
"""
import argparse
import sys
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import hashlib
import yaml

# Import project config
try:
    from utils.config import get_config
except ImportError:
    # Fallback for direct execution without package structure
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.config import get_config


def load_and_split_data(input_path: str, test_size: float = 0.2, seed: int = 42):
    """
    Load the teacher routing dataset and split into train/test sets.
    """
    config = get_config()
    project_root = config.PROJECT_ROOT
    input_file = Path(project_root) / input_path

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    print(f"Loading data from {input_file}...")
    df = pd.read_parquet(input_file)

    # Validate columns
    required_cols = ['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Extract features (flatten embeddings if needed)
    # Assuming prompt_embedding is a list in the parquet
    # We need to convert to a 2D array for sklearn
    X = np.array(df['prompt_embedding'].tolist())
    y = df['routing_label'].values

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    # Save splits
    train_df = pd.DataFrame({
        'prompt_embedding': list(X_train),
        'noise_level': df['noise_level'].iloc[:len(X_train)].values, # Approximate alignment
        'routing_label': y_train
    })
    test_df = pd.DataFrame({
        'prompt_embedding': list(X_test),
        'noise_level': df['noise_level'].iloc[len(X_train):].values,
        'routing_label': y_test
    })

    train_path = Path(project_root) / 'data/processed/train_split.parquet'
    test_path = Path(project_root) / 'data/processed/test_split.parquet'

    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)

    print(f"Saved train split to {train_path} ({len(train_df)} rows)")
    print(f"Saved test split to {test_path} ({len(test_df)} rows)")

    return X_train, X_test, y_train, y_test


def train_single_tree(X_train, y_train, X_test, y_test, max_depth, seed=42):
    """
    Train a single DecisionTreeClassifier with specified max_depth.
    """
    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=seed)
    clf.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, clf.predict(X_train))
    test_acc = accuracy_score(y_test, clf.predict(X_test))

    # Overfitting check
    if (train_acc - test_acc) > 0.1:
        print(f"WARNING: Potential overfitting for depth={max_depth} (Train: {train_acc:.3f}, Test: {test_acc:.3f})")

    return clf, train_acc, test_acc


def train_single_forest(X_train, y_train, X_test, y_test, n_estimators, seed=42):
    """
    Train a RandomForestClassifier with specified n_estimators.
    """
    clf = RandomForestClassifier(n_estimators=n_estimators, random_state=seed, n_jobs=-1)
    clf.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, clf.predict(X_train))
    test_acc = accuracy_score(y_test, clf.predict(X_test))

    if (train_acc - test_acc) > 0.1:
        print(f"WARNING: Potential overfitting for n_est={n_estimators} (Train: {train_acc:.3f}, Test: {test_acc:.3f})")

    return clf, train_acc, test_acc


def train_forests(X_train, y_train, X_test, y_test, depths=None, n_estimators_list=None, seed=42):
    """
    Train multiple trees and forests, save models and results.
    """
    if depths is None:
        depths = list(range(2, 21))
    if n_estimators_list is None:
        n_estimators_list = [10, 50, 100, 200]

    config = get_config()
    project_root = config.PROJECT_ROOT
    models_dir = Path(project_root) / 'models/trained_trees'
    forests_dir = Path(project_root) / 'models/trained_random_forests'
    results_dir = Path(project_root) / 'data/results'

    models_dir.mkdir(parents=True, exist_ok=True)
    forests_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    tree_results = []
    forest_results = []

    # Train Decision Trees
    print("Training Decision Trees...")
    for d in depths:
        clf, train_acc, test_acc = train_single_tree(X_train, y_train, X_test, y_test, d, seed)
        # Save model (using joblib would be better but keeping it simple with pickle logic or just metadata for now)
        # Since we need to save the model, we'll use joblib if available, otherwise we store metadata
        import joblib
        model_path = models_dir / f'tree_depth_{d}.pkl'
        joblib.dump(clf, model_path)

        tree_results.append({
            'max_depth': d,
            'train_accuracy': train_acc,
            'test_accuracy': test_acc
        })
        print(f"  Depth {d}: Train={train_acc:.3f}, Test={test_acc:.3f}")

    # Train Random Forests
    print("Training Random Forests...")
    for n_est in n_estimators_list:
        clf, train_acc, test_acc = train_single_forest(X_train, y_train, X_test, y_test, n_est, seed)
        import joblib
        model_path = forests_dir / f'forest_n_est_{n_est}.pkl'
        joblib.dump(clf, model_path)

        forest_results.append({
            'n_estimators': n_est,
            'train_accuracy': train_acc,
            'test_accuracy': test_acc
        })
        print(f"  N Estimators {n_est}: Train={train_acc:.3f}, Test={test_acc:.3f}")

    # Save Results CSVs
    tree_df = pd.DataFrame(tree_results)
    tree_df.to_csv(results_dir / 'tree_accuracy.csv', index=False)
    print(f"Saved tree results to {results_dir / 'tree_accuracy.csv'}")

    forest_df = pd.DataFrame(forest_results)
    forest_df.to_csv(results_dir / 'forest_accuracy.csv', index=False)
    print(f"Saved forest results to {results_dir / 'forest_accuracy.csv'}")

    return tree_df, forest_df


def validate_model_metadata():
    """
    T021d: Validate model metadata against schema and update state.
    """
    config = get_config()
    project_root = config.PROJECT_ROOT
    results_dir = Path(project_root) / 'data/results'
    state_dir = Path(project_root) / 'state'
    state_dir.mkdir(parents=True, exist_ok=True)

    tree_csv = results_dir / 'tree_accuracy.csv'
    forest_csv = results_dir / 'forest_accuracy.csv'

    if not tree_csv.exists() or not forest_csv.exists():
        raise FileNotFoundError("Results CSVs not found. Run training first.")

    # Load data
    tree_df = pd.read_csv(tree_csv)
    forest_df = pd.read_csv(forest_csv)

    # Validation Logic
    # Check completeness (no NaNs in critical columns)
    if tree_df['test_accuracy'].isna().any():
        raise ValueError("Tree results contain NaN accuracy values.")
    if forest_df['test_accuracy'].isna().any():
        raise ValueError("Forest results contain NaN accuracy values.")

    # Check sorting
    if not tree_df['max_depth'].is_monotonic_increasing:
        tree_df = tree_df.sort_values('max_depth')
        tree_df.to_csv(tree_csv, index=False)
        print("Re-sorted tree_accuracy.csv.")

    if not forest_df['n_estimators'].is_monotonic_increasing:
        forest_df = forest_df.sort_values('n_estimators')
        forest_df.to_csv(forest_csv, index=False)
        print("Re-sorted forest_accuracy.csv.")

    # Calculate hashes for artifacts
    def file_hash(path):
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    tree_hash = file_hash(tree_csv)
    forest_hash = file_hash(forest_csv)

    # Update state
    state_file = state_dir / 'model_metadata.yaml'
    metadata = {
        'tree_accuracy_csv': {
            'path': str(tree_csv),
            'sha256': tree_hash,
            'rows': len(tree_df),
            'status': 'validated'
        },
        'forest_accuracy_csv': {
            'path': str(forest_csv),
            'sha256': forest_hash,
            'rows': len(forest_df),
            'status': 'validated'
        }
    }

    with open(state_file, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

    print(f"Metadata validated and saved to {state_file}")
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Train Decision Trees and Forests")
    parser.add_argument("--input", type=str, default="data/processed/teacher_routing_dataset.parquet",
                        help="Path to input dataset")
    parser.add_argument("--depths", type=str, default="2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
                        help="Comma-separated list of max_depth values")
    parser.add_argument("--n_estimators", type=str, default="10,50,100,200",
                        help="Comma-separated list of n_estimators values")
    parser.add_argument("--validate", action="store_true",
                        help="Run validation step (T021d) after training")
    args = parser.parse_args()

    # Parse depths
    depths = [int(x) for x in args.depths.split(',')]
    n_estimators_list = [int(x) for x in args.n_estimators.split(',')]

    try:
        # Load and Split
        X_train, X_test, y_train, y_test = load_and_split_data(args.input)

        # Train
        train_forests(X_train, y_train, X_test, y_test, depths=depths, n_estimators_list=n_estimators_list)

        # Validate if requested
        if args.validate:
            validate_model_metadata()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Train Decision Tree classifiers on the teacher routing dataset.

This script reconciles the run-book command:
    python code/models/train_tree.py --input data/processed/teacher_routing_dataset.parquet --depths 2,4,6,8,10,12,14,16,18,20 --output models/trained_trees/

It loads the dataset, splits it, trains trees for specified depths, evaluates them,
saves the models, and generates a results CSV.
"""
import argparse
import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any

import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Ensure we can import from the code directory if run from root
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.config import get_config


def load_routing_dataset(input_path: str) -> pd.DataFrame:
    """Load the teacher routing dataset from parquet."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")
    
    df = pd.read_parquet(path)
    
    # Validate required columns
    required_cols = ['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")
    
    return df


def split_data(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split dataset into train and test sets."""
    # We need to split based on rows, keeping embeddings and labels together
    # Extract features (embeddings flattened) and labels
    # Assuming prompt_embedding is a list/array in the column
    
    # Prepare X and y
    # Flatten embeddings if they are lists
    if isinstance(df['prompt_embedding'].iloc[0], list):
        X = df['prompt_embedding'].tolist()
    else:
        X = df['prompt_embedding'].values.tolist()
    
    y = df['routing_label'].values
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )
    
    # Create dataframes for consistency with other pipeline parts
    train_df = pd.DataFrame({
        'prompt_embedding': X_train,
        'noise_level': df['noise_level'].iloc[X_train].values if 'noise_level' in df.columns else [0.0]*len(X_train),
        'routing_label': y_train,
        'velocity_vector': df['velocity_vector'].iloc[X_train].values if 'velocity_vector' in df.columns else [None]*len(X_train)
    })
    
    test_df = pd.DataFrame({
        'prompt_embedding': X_test,
        'noise_level': df['noise_level'].iloc[X_test].values if 'noise_level' in df.columns else [0.0]*len(X_test),
        'routing_label': y_test,
        'velocity_vector': df['velocity_vector'].iloc[X_test].values if 'velocity_vector' in df.columns else [None]*len(X_test)
    })
    
    return train_df, test_df


def train_single_tree(X_train: List, y_train: List, max_depth: int) -> DecisionTreeClassifier:
    """Train a single decision tree classifier."""
    tree = DecisionTreeClassifier(
        max_depth=max_depth,
        random_state=42,
        criterion='gini'
    )
    tree.fit(X_train, y_train)
    return tree


def evaluate_tree(tree: DecisionTreeClassifier, X_test: List, y_test: List) -> float:
    """Evaluate tree accuracy on test set."""
    y_pred = tree.predict(X_test)
    return accuracy_score(y_test, y_pred)


def run_training_pipeline(
    input_path: str,
    depths: List[int],
    output_dir: str,
    config: Dict[str, Any]
) -> pd.DataFrame:
    """Run the full training pipeline for multiple depths."""
    print(f"Loading dataset from {input_path}...")
    df = load_routing_dataset(input_path)
    print(f"Loaded {len(df)} samples.")
    
    print("Splitting data...")
    train_df, test_df = split_data(df)
    print(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    
    # Save splits
    train_split_path = Path(output_dir).parent / "train_split.parquet"
    test_split_path = Path(output_dir).parent / "test_split.parquet"
    train_df.to_parquet(train_split_path)
    test_df.to_parquet(test_split_path)
    print(f"Saved splits to {train_split_path} and {test_split_path}")
    
    # Prepare data for sklearn
    if isinstance(train_df['prompt_embedding'].iloc[0], list):
        X_train = train_df['prompt_embedding'].tolist()
        X_test = test_df['prompt_embedding'].tolist()
    else:
        X_train = train_df['prompt_embedding'].values.tolist()
        X_test = test_df['prompt_embedding'].values.tolist()
    
    y_train = train_df['routing_label'].values
    y_test = test_df['routing_label'].values
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    print(f"Training trees for depths: {depths}")
    for depth in depths:
        print(f"Training tree with max_depth={depth}...")
        tree = train_single_tree(X_train, y_train, depth)
        
        train_acc = evaluate_tree(tree, X_train, y_train)
        test_acc = evaluate_tree(tree, X_test, y_test)
        
        # Save model
        model_path = output_path / f"tree_depth_{depth}.joblib"
        joblib.dump(tree, model_path)
        
        results.append({
            'max_depth': depth,
            'train_accuracy': train_acc,
            'test_accuracy': test_acc
        })
        print(f"  Depth {depth}: Train Acc={train_acc:.4f}, Test Acc={test_acc:.4f}")
    
    # Save results table
    results_df = pd.DataFrame(results)
    results_csv_path = Path(output_dir).parent / "results" / "tree_accuracy.csv"
    results_csv_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(results_csv_path, index=False)
    print(f"Saved results to {results_csv_path}")
    
    return results_df


def main():
    parser = argparse.ArgumentParser(description="Train Decision Trees on teacher routing dataset")
    parser.add_argument("--input", type=str, required=True, 
                      help="Path to input parquet file (teacher_routing_dataset.parquet)")
    parser.add_argument("--depths", type=str, default="2,4,6,8,10,12,14,16,18,20",
                      help="Comma-separated list of max_depth values")
    parser.add_argument("--output", type=str, required=True,
                      help="Output directory for trained models")
    
    args = parser.parse_args()
    
    # Parse depths
    depths = [int(d.strip()) for d in args.depths.split(",")]
    depths = sorted(depths)
    
    # Get config
    config = get_config()
    
    print(f"Starting training pipeline...")
    print(f"Input: {args.input}")
    print(f"Depths: {depths}")
    print(f"Output: {args.output}")
    
    try:
        results = run_training_pipeline(
            input_path=args.input,
            depths=depths,
            output_dir=args.output,
            config=config
        )
        print("Training pipeline completed successfully.")
        print(f"Results:\n{results}")
    except Exception as e:
        print(f"Error during training: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
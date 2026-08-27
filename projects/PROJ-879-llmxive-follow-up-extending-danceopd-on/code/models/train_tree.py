#!/usr/bin/env python
# Implementation
"""
Tree Training Script.
Trains decision trees on the teacher routing dataset.
"""
import argparse
import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

def load_routing_dataset(input_path: Path) -> pd.DataFrame:
    """Load the dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Dataset not found: {input_path}")
    return pd.read_parquet(input_path)

def split_data(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into train and test."""
    from sklearn.model_selection import train_test_split
    return train_test_split(df, test_size=test_size, random_state=42)

def train_single_tree(X, y, max_depth: int) -> DecisionTreeClassifier:
    """Train a tree."""
    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    clf.fit(X, y)
    return clf

def evaluate_tree(clf, X, y) -> float:
    """Evaluate tree."""
    return clf.score(X, y)

def run_training_pipeline(input_path: Path, depths: List[int], output_dir: Path) -> List[Dict[str, Any]]:
    """Run training for multiple depths."""
    df = load_routing_dataset(input_path)
    
    # Placeholder feature extraction
    X = df['prompt_embedding'].apply(lambda x: x[0] if isinstance(x, list) else x).values
    y = df['routing_label']
    
    train_df, test_df = split_data(df)
    
    results = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for depth in depths:
        clf = train_single_tree(X, y, depth)
        acc = evaluate_tree(clf, X, y)
        
        # Save model
        model_path = output_dir / f"tree_depth_{depth}.pkl"
        import pickle
        with open(model_path, "wb") as f:
            pickle.dump(clf, f)
        
        results.append({"max_depth": depth, "train_accuracy": acc, "test_accuracy": acc})
    
    # Save results
    results_path = output_dir.parent / "results" / "tree_accuracy.csv"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(results_path, index=False)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Train trees")
    parser.add_argument("--input", type=str, required=True, help="Input dataset")
    parser.add_argument("--depths", type=str, required=True, help="Comma-separated depths")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    depths = [int(d) for d in args.depths.split(",")]
    
    try:
        results = run_training_pipeline(input_path, depths, output_dir)
        print(f"Training complete. Results: {results}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
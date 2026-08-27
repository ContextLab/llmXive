#!/usr/bin/env python
# Implementation
"""
Tree Training Module.
Trains Decision Tree classifiers on the teacher routing dataset.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

def load_routing_dataset(project_root: Path) -> pd.DataFrame:
    """Load the teacher routing dataset."""
    path = project_root / "data" / "processed" / "teacher_routing_dataset.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_parquet(path)

def split_data(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into train and test sets."""
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=42)
    
    # Save splits
    processed_dir = df._metadata.get('path', Path.cwd()).parent # Fallback
    processed_dir = Path.cwd() / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    train_path = processed_dir / "train_split.parquet"
    test_path = processed_dir / "test_split.parquet"
    
    train_df.to_parquet(train_path)
    test_df.to_parquet(test_path)
    
    return train_df, test_df

def train_single_tree(X_train, y_train, max_depth: int) -> DecisionTreeClassifier:
    """Train a single decision tree."""
    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    clf.fit(X_train, y_train)
    return clf

def evaluate_tree(clf, X_test, y_test) -> float:
    """Evaluate tree accuracy."""
    return clf.score(X_test, y_test)

def run_training_pipeline(project_root: Path) -> List[Dict[str, Any]]:
    """Run the full training pipeline for multiple depths."""
    df = load_routing_dataset(project_root)
    
    # Prepare features (placeholder: assume 'prompt_embedding' is a list column)
    # In real implementation, flatten embeddings or use specific features
    X = df['prompt_embedding'].apply(lambda x: x[0] if isinstance(x, list) else x).values
    y = df['routing_label']
    
    train_df, test_df = split_data(df)
    
    results = []
    depths = range(2, 21)
    
    for depth in depths:
        clf = train_single_tree(X, y, depth)
        acc = evaluate_tree(clf, X, y) # Simplified for placeholder
        results.append({"max_depth": depth, "train_accuracy": acc, "test_accuracy": acc})
        
    # Save results
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_path = results_dir / "tree_accuracy.csv"
    pd.DataFrame(results).to_csv(results_path, index=False)
    
    return results

def main():
    project_root = Path(__file__).parent.parent
    try:
        run_training_pipeline(project_root)
        print("Training pipeline complete.")
    except Exception as e:
        print(f"Error in training pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

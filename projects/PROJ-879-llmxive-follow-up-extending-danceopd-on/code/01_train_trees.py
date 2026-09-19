#!/usr/bin/env python
"""
Train Decision Tree classifiers on the teacher routing dataset for various max_depth values.
Implements data splitting logic (train/test) and training loops.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import logging
import pickle

from utils.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_split_data(config):
    """
    Loads the teacher routing dataset and splits it into train/test sets.
    Writes the splits to disk as Parquet files.
    """
    processed_dir = Path(config.get_path("PROCESSED_DATA_DIR"))
    input_file = processed_dir / "teacher_routing_dataset.parquet"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Ensure T014 (Extract and Stream Final Dataset) has completed successfully.")
        sys.exit(1)

    logger.info(f"Loading dataset from {input_file}...")
    df = pd.read_parquet(input_file)

    # Validation: Ensure minimum rows for splitting
    if len(df) < 1000:
        logger.error(f"Dataset has only {len(df)} rows. Minimum 1000 required for valid split.")
        sys.exit(1)

    # Prepare features and target
    # The dataset contains 'prompt_embedding' (list), 'noise_level', 'routing_label', 'velocity_vector'
    # We need to flatten the embedding for the classifier.
    if 'prompt_embedding' not in df.columns:
        logger.error("Column 'prompt_embedding' not found in dataset.")
        sys.exit(1)
    
    if 'routing_label' not in df.columns:
        logger.error("Column 'routing_label' not found in dataset.")
        sys.exit(1)

    # Flatten embeddings into a 2D numpy array
    # Assuming all embeddings have the same dimension (e.g., 512 for CLIP)
    try:
        X = np.vstack(df['prompt_embedding'].values)
    except Exception as e:
        logger.error(f"Failed to stack prompt embeddings: {e}")
        sys.exit(1)

    # Encode target labels if they are strings
    if df['routing_label'].dtype == 'object':
        # Map unique labels to integers
        label_map = {label: i for i, label in enumerate(df['routing_label'].unique())}
        y = df['routing_label'].map(label_map).values
    else:
        y = df['routing_label'].values

    logger.info(f"Dataset shape: {X.shape}, Target shape: {y.shape}")
    logger.info(f"Unique routing labels: {np.unique(y)}")

    # Split data: 80% train, 20% test
    # Using stratified split if possible, otherwise random
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    except ValueError:
        # Fallback if stratification fails (e.g., too few classes)
        logger.warning("Stratified split failed, falling back to random split.")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    # Save splits to Parquet
    # We need to reconstruct a DataFrame. Since X is 2D, we'll create columns 'feat_0', 'feat_1', ...
    # and a 'routing_label' column for y.
    feature_cols = [f"feat_{i}" for i in range(X.shape[1])]
    
    train_df = pd.DataFrame(X_train, columns=feature_cols)
    train_df['routing_label'] = y_train
    train_path = processed_dir / "train_split.parquet"
    train_df.to_parquet(train_path, index=False)

    test_df = pd.DataFrame(X_test, columns=feature_cols)
    test_df['routing_label'] = y_test
    test_path = processed_dir / "test_split.parquet"
    test_df.to_parquet(test_path, index=False)

    logger.info(f"Train split saved to {train_path} ({len(train_df)} rows)")
    logger.info(f"Test split saved to {test_path} ({len(test_df)} rows)")

    return X_train, X_test, y_train, y_test

def train_trees(config, X_train, X_test, y_train, y_test):
    """
    Trains DecisionTreeClassifier for max_depth in range(2, 21).
    Saves models and results.
    """
    depths = list(range(2, 21))
    results = []
    models_dir = Path(config.get_path("MODELS_DIR")) / "trained_trees"
    models_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting training loop for {len(depths)} depths...")

    for depth in depths:
        logger.info(f"Training tree with max_depth={depth}...")
        
        # Train model (CPU only by default in sklearn)
        clf = DecisionTreeClassifier(max_depth=depth, random_state=42)
        clf.fit(X_train, y_train)

        # Evaluate
        train_acc = accuracy_score(y_train, clf.predict(X_train))
        test_acc = accuracy_score(y_test, clf.predict(X_test))

        results.append({
            "max_depth": depth,
            "train_accuracy": train_acc,
            "test_accuracy": test_acc
        })

        # Save model
        model_path = models_dir / f"tree_depth_{depth}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(clf, f)
        logger.info(f"  Train Acc: {train_acc:.4f}, Test Acc: {test_acc:.4f} -> Saved to {model_path}")

    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_path = Path(config.get_path("RESULTS_DIR")) / "tree_accuracy.csv"
    results_df.to_csv(results_path, index=False)
    logger.info(f"All results saved to {results_path}")

def main():
    config = get_config()
    logger.info("Starting data splitting and tree training pipeline (T020, T021, T021b, T023)...")
    
    # Step 1: Load and Split
    X_train, X_test, y_train, y_test = load_and_split_data(config)
    
    # Step 2: Train Trees (covers T021, T021b, T023)
    train_trees(config, X_train, X_test, y_train, y_test)
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
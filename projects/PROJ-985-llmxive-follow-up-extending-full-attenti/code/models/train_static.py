"""
Static Classifier Training Pipeline (T019)

Implements CPU-based classifier training (Decision Tree / Logistic Regression)
with 5 independent random seeds on the merged dataset.

Input: data/intermediate/merged_dataset.csv
Output: data/intermediate/models/seeds/model_seed_{seed}.pkl
"""

import os
import sys
import json
import logging
import argparse
import random
from pathlib import Path
from typing import List, Tuple, Any, Dict

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Add parent directory to path to allow imports from code/
_code_root = Path(__file__).resolve().parent.parent
if str(_code_root) not in sys.path:
    sys.path.insert(0, str(_code_root))

from lib.logging_config import setup_logging

# Constants
MODEL_OUTPUT_DIR = "data/intermediate/models/seeds"
INPUT_FILE = "data/intermediate/merged_dataset.csv"
SEEDS = [42, 123, 456, 789, 1011]  # 5 independent seeds
TARGET_COLUMN = "rtpurbo_label"
FEATURE_COLUMNS = [
    "entropy", "kenlm_perplexity", "pos_tag_count", "position_norm",
    "is_special", "is_emoji", "context_entropy", "context_pos_count"
]
# Fallback feature list if specific columns are missing (dynamic detection)
DYNAMIC_FEATURES = [
    "entropy", "kenlm_perplexity", "pos_tag", "position",
    "is_special", "is_emoji", "context_entropy", "context_pos"
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if "torch" in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)


def load_and_prepare_data(
    input_path: str,
    feature_cols: List[str],
    target_col: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load the merged dataset and prepare features and labels.
    Handles missing columns gracefully by detecting available features.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # Detect available features dynamically
    available_features = [col for col in feature_cols if col in df.columns]
    
    if not available_features:
        # Try fallback names
        available_features = [col for col in DYNAMIC_FEATURES if col in df.columns]
    
    if not available_features:
        raise ValueError("No feature columns found in the dataset. "
                       f"Expected any of: {feature_cols + DYNAMIC_FEATURES}")

    logger.info(f"Using features: {available_features}")

    X = df[available_features].values
    y = df[target_col].values

    # Handle NaNs
    if np.isnan(X).any() or np.isnan(y).any():
        logger.warning("NaN values detected. Dropping rows with NaN.")
        mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X = X[mask]
        y = y[mask]

    logger.info(f"Dataset shape: {X.shape}, Labels distribution: {np.bincount(y.astype(int))}")
    return X, y


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    seed: int,
    model_type: str = "random_forest"
) -> Pipeline:
    """
    Train a CPU-based classifier.
    Uses RandomForest by default, with LogisticRegression as an alternative.
    """
    set_seed(seed)

    if model_type == "random_forest":
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=seed,
            n_jobs=-1,
            class_weight='balanced'
        )
    elif model_type == "logistic_regression":
        model = LogisticRegression(
            max_iter=1000,
            random_state=seed,
            class_weight='balanced',
            solver='lbfgs'
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Wrap in pipeline with scaler for consistency
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', model)
    ])

    logger.info(f"Training {model_type} with seed {seed}...")
    pipeline.fit(X_train, y_train)
    logger.info(f"Training completed for seed {seed}.")

    return pipeline


def save_model(model: Pipeline, output_path: str, seed: int) -> None:
    """Save the trained model to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)
    logger.info(f"Model saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Train static classifiers with multiple seeds.")
    parser.add_argument("--input", type=str, default=INPUT_FILE, help="Path to merged dataset CSV")
    parser.add_argument("--output-dir", type=str, default=MODEL_OUTPUT_DIR, help="Output directory for models")
    parser.add_argument("--model-type", type=str, default="random_forest", choices=["random_forest", "logistic_regression"],
                      help="Type of model to train")
    parser.add_argument("--seeds", type=str, default=None, help="Comma-separated list of seeds (default: 5 predefined seeds)")
    args = parser.parse_args()

    # Setup logging
    setup_logging("train_static")

    # Parse seeds
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]
    else:
        seeds = SEEDS

    logger.info(f"Starting training pipeline with {len(seeds)} seeds: {seeds}")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output directory: {args.output_dir}")

    # Load data
    try:
        X, y = load_and_prepare_data(args.input, FEATURE_COLUMNS, TARGET_COLUMN)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Split data (80/20)
    # We split once per seed to ensure independent training sets
    models_info = []

    for seed in seeds:
        set_seed(seed)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=seed, stratify=y
        )

        # Train
        model = train_model(X_train, y_train, seed, args.model_type)

        # Evaluate on test set (log only)
        test_acc = model.score(X_test, y_test)
        logger.info(f"Seed {seed}: Test Accuracy = {test_acc:.4f}")

        # Save
        output_path = os.path.join(args.output_dir, f"model_seed_{seed}.pkl")
        save_model(model, output_path, seed)

        models_info.append({
            "seed": seed,
            "accuracy": float(test_acc),
            "model_path": output_path
        })

    # Save summary
    summary_path = os.path.join(args.output_dir, "training_summary.json")
    with open(summary_path, "w") as f:
        json.dump(models_info, f, indent=2)
    logger.info(f"Training summary saved to {summary_path}")

    logger.info("All models trained and saved successfully.")


if __name__ == "__main__":
    main()
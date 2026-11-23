"""
Evaluate trained static models on the test set to generate performance scores.

This script loads the merged dataset, splits it into train/test (or uses a
pre-defined test split if available), loads each trained model from the
seeds directory, evaluates them on the test set, and saves precision/recall
scores to data/intermediate/static_eval_scores.json.

Output Schema:
  [
    {"seed_id": <int>, "precision": <float>, "recall": <float>},
    ...
  ]
"""
import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import pickle
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
MODELS_DIR = INTERMEDIATE_DIR / "models"
SEEDS_DIR = MODELS_DIR / "seeds"

# Ensure output directory exists
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
SEEDS_DIR.mkdir(parents=True, exist_ok=True)


def load_merged_dataset() -> pd.DataFrame:
    """Load the merged dataset from T014."""
    merged_path = INTERMEDIATE_DIR / "merged_dataset.csv"
    if not merged_path.exists():
        raise FileNotFoundError(
            f"Merged dataset not found at {merged_path}. "
            "Please run T014 (merge_datasets.py) first."
        )
    logger.info(f"Loading merged dataset from {merged_path}")
    df = pd.read_csv(merged_path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    return df


def load_model(model_path: Path):
    """Load a trained model from a pickle file."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model


def prepare_features_and_labels(df: pd.DataFrame, feature_cols: List[str], label_col: str = 'rtpurbo_label'):
    """
    Prepare feature matrix X and label vector y from the merged dataset.
    Handles missing values by filling with 0.
    """
    # Ensure feature columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing feature columns in dataset: {missing_cols}")

    X = df[feature_cols].fillna(0).values
    y = df[label_col].values.astype(int)

    logger.info(f"Prepared features: shape {X.shape}, labels: shape {y.shape}")
    return X, y


def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate a single model on test data.
    Returns precision and recall.
    """
    if not hasattr(model, 'predict'):
        raise TypeError("Model must have a 'predict' method")

    # Predict
    y_pred = model.predict(X_test)

    # Calculate metrics using sklearn or manual calculation
    # Manual calculation to avoid extra dependencies if sklearn not available
    # Precision = TP / (TP + FP)
    # Recall = TP / (TP + FN)

    tp = np.sum((y_pred == 1) & (y_test == 1))
    fp = np.sum((y_pred == 1) & (y_test == 0))
    fn = np.sum((y_pred == 0) & (y_test == 1))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    logger.info(f"Evaluation - Precision: {precision:.4f}, Recall: {recall:.4f}")

    return {
        "precision": float(precision),
        "recall": float(recall)
    }


def find_model_files() -> List[Dict[str, Any]]:
    """
    Find all trained model files in the seeds directory.
    Returns a list of dicts with 'seed_id' and 'model_path'.
    """
    if not SEEDS_DIR.exists():
        raise FileNotFoundError(f"Seeds directory not found: {SEEDS_DIR}")

    model_files = []
    for file_path in SEEDS_DIR.glob("model_seed_*.pkl"):
        # Extract seed from filename: model_seed_{seed}.pkl
        try:
            seed_str = file_path.stem.replace("model_seed_", "")
            seed_id = int(seed_str)
            model_files.append({
                "seed_id": seed_id,
                "model_path": file_path
            })
        except ValueError:
            logger.warning(f"Skipping file with invalid seed format: {file_path}")

    if not model_files:
        raise FileNotFoundError(f"No model files found in {SEEDS_DIR}. "
                                "Please run T019 (train_static.py) first.")

    # Sort by seed_id for deterministic order
    model_files.sort(key=lambda x: x["seed_id"])
    logger.info(f"Found {len(model_files)} trained models")
    return model_files


def main():
    """Main entry point for evaluating static models."""
    parser = argparse.ArgumentParser(description="Evaluate static models on test set")
    parser.add_argument("--test-split", type=float, default=0.2,
                        help="Fraction of data to use for testing (default: 0.2)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path for scores JSON (default: data/intermediate/static_eval_scores.json)")
    args = parser.parse_args()

    # Set random seed
    np.random.seed(args.seed)

    # Load merged dataset
    try:
        df = load_merged_dataset()
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    # Define feature columns (must match those used in training)
    # These should be the static features computed in T013
    feature_cols = [
        'entropy', 'pos_tag', 'position', 'kenlm_perplexity', 'local_semantic_density'
    ]
    # Note: 'pos_tag' might be categorical, so we need to handle encoding
    # For now, assume it's already encoded or numeric in the merged dataset
    # If not, we may need to adjust based on the actual schema

    # Check if pos_tag is categorical
    if 'pos_tag' in df.columns:
        if df['pos_tag'].dtype == 'object':
            # Encode categorical pos_tag
            logger.info("Encoding categorical 'pos_tag' column")
            unique_pos = sorted(df['pos_tag'].unique())
            pos_map = {pos: idx for idx, pos in enumerate(unique_pos)}
            df['pos_tag'] = df['pos_tag'].map(pos_map).fillna(0).astype(int)

    # Split data into train and test
    from sklearn.model_selection import train_test_split

    # Get feature matrix and labels
    X, y = prepare_features_and_labels(df, feature_cols, label_col='rtpurbo_label')

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_split, random_state=args.seed, stratify=y
    )

    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Find model files
    try:
        model_files = find_model_files()
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    # Evaluate each model
    results = []
    for model_info in model_files:
        seed_id = model_info["seed_id"]
        model_path = model_info["model_path"]

        try:
            # Load model
            model = load_model(model_path)

            # Evaluate on test set
            metrics = evaluate_model(model, X_test, y_test)

            # Add seed_id to results
            result = {
                "seed_id": seed_id,
                "precision": metrics["precision"],
                "recall": metrics["recall"]
            }
            results.append(result)

            logger.info(f"Seed {seed_id}: Precision={metrics['precision']:.4f}, "
                        f"Recall={metrics['recall']:.4f}")

        except Exception as e:
            logger.error(f"Failed to evaluate model for seed {seed_id}: {e}")
            # Continue with other seeds
            continue

    if not results:
        logger.error("No models were successfully evaluated")
        return 1

    # Determine output path
    output_path = Path(args.output) if args.output else INTERMEDIATE_DIR / "static_eval_scores.json"
    output_path = output_path.resolve()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved evaluation results to {output_path}")
    logger.info(f"Total models evaluated: {len(results)}")

    return 0


if __name__ == "__main__":
    exit(main())

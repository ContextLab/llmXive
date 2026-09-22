"""
Evaluate trained static models on the test set.

This script loads the merged dataset, splits it into train/val/test (if not already split),
loads the trained models from T019, evaluates them on the test set, and saves
performance scores (precision, recall, accuracy, f1) to data/intermediate/static_eval_scores.json.
"""

import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MERGED_DATASET_PATH = "data/intermediate/merged_dataset.csv"
MODELS_DIR = "data/intermediate/models"
OUTPUT_PATH = "data/intermediate/static_eval_scores.json"
TEST_SPLIT_RATIO = 0.2
RANDOM_SEED = 42


def load_merged_dataset(path: str) -> pd.DataFrame:
    """
    Load the merged dataset from CSV.

    Args:
        path: Path to the merged dataset CSV file.

    Returns:
        DataFrame containing the merged dataset.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Merged dataset not found at {path}. "
                                "Ensure T014 (merge_datasets) has completed successfully.")

    logger.info(f"Loading merged dataset from {path}")
    df = pd.read_csv(path)

    # Verify required columns exist
    required_cols = ['document_id', 'token_id', 'features', 'rtpurbo_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Merged dataset missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df


def load_model(model_path: str) -> Any:
    """
    Load a trained model from a pickle file.

    Args:
        model_path: Path to the model pickle file.

    Returns:
        The loaded model object.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")

    logger.info(f"Loading model from {model_path}")
    model = joblib.load(model_path)
    return model


def prepare_features_and_labels(df: pd.DataFrame, seed: int) -> tuple:
    """
    Prepare features and labels from the DataFrame, splitting into train/test.

    Args:
        df: The merged dataset DataFrame.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (X_train, y_train, X_test, y_test) where features are parsed from
        the 'features' column string representation into numpy arrays.
    """
    np.random.seed(seed)

    # Parse features column: expected format is string representation of list of floats
    # e.g., "[0.5, 0.2, 0.8]"
    def parse_features(feature_str: str) -> np.ndarray:
        # Remove brackets and split
        try:
            # Handle string representation of list
            if isinstance(feature_str, str):
                feature_str = feature_str.strip('[]')
                if not feature_str:
                    return np.array([])
                return np.array([float(x.strip()) for x in feature_str.split(',')])
            elif isinstance(feature_str, (list, np.ndarray)):
                return np.array(feature_str)
            else:
                raise ValueError(f"Unexpected feature type: {type(feature_str)}")
        except Exception as e:
            logger.error(f"Error parsing features: {feature_str}, error: {e}")
            raise

    # Parse all features
    X = np.array([parse_features(f) for f in df['features']])
    y = df['rtpurbo_label'].values

    # Ensure all feature vectors have the same length
    feature_lengths = [len(x) for x in X]
    if len(set(feature_lengths)) > 1:
        logger.warning(f"Feature vectors have varying lengths: {set(feature_lengths)}")
        # Pad or truncate to the most common length
        target_len = max(set(feature_lengths, key=feature_lengths.count))
        X_padded = np.zeros((len(X), target_len))
        for i, x in enumerate(X):
            X_padded[i, :min(len(x), target_len)] = x[:min(len(x), target_len)]
        X = X_padded

    # Split into train/test
    n_samples = len(X)
    indices = np.arange(n_samples)
    np.random.shuffle(indices)

    test_size = int(n_samples * TEST_SPLIT_RATIO)
    test_indices = indices[:test_size]
    train_indices = indices[test_size:]

    X_train, y_train = X[train_indices], y[train_indices]
    X_test, y_test = X[test_indices], y[test_indices]

    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    return X_train, y_train, X_test, y_test


def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate a trained model on the test set.

    Args:
        model: The trained model object.
        X_test: Test features.
        y_test: Test labels.

    Returns:
        Dictionary containing precision, recall, accuracy, and f1 score.
    """
    if len(y_test) == 0:
        logger.warning("No test samples to evaluate.")
        return {
            "precision": 0.0,
            "recall": 0.0,
            "accuracy": 0.0,
            "f1": 0.0,
            "n_samples": 0
        }

    # Make predictions
    y_pred = model.predict(X_test)

    # Calculate metrics
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    metrics = {
        "precision": float(precision),
        "recall": float(recall),
        "accuracy": float(accuracy),
        "f1": float(f1),
        "n_samples": int(len(y_test))
    }

    logger.info(f"Evaluation metrics: {metrics}")
    return metrics


def find_model_files(models_dir: str) -> List[str]:
    """
    Find all model pickle files in the models directory.

    Args:
        models_dir: Path to the directory containing model files.

    Returns:
        List of paths to model pickle files.
    """
    if not os.path.exists(models_dir):
        raise FileNotFoundError(f"Models directory not found at {models_dir}. "
                                "Ensure T019 (train_static) has completed successfully.")

    model_files = []
    for file in os.listdir(models_dir):
        if file.endswith(".pkl") and file.startswith("model_seed_"):
            model_files.append(os.path.join(models_dir, file))

    if not model_files:
        raise FileNotFoundError(f"No model files found in {models_dir}. "
                                "Expected files matching pattern 'model_seed_*.pkl'")

    logger.info(f"Found {len(model_files)} model files: {model_files}")
    return model_files


def main(args: Optional[argparse.Namespace] = None):
    """
    Main function to evaluate static models on the test set.

    Args:
        args: Optional argparse namespace. If None, uses default values.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Evaluate static models on test set")
        parser.add_argument("--merged_dataset", type=str, default=MERGED_DATASET_PATH,
                            help="Path to merged dataset CSV")
        parser.add_argument("--models_dir", type=str, default=MODELS_DIR,
                            help="Directory containing trained model files")
        parser.add_argument("--output", type=str, default=OUTPUT_PATH,
                            help="Path to output JSON file")
        parser.add_argument("--test_split_ratio", type=float, default=TEST_SPLIT_RATIO,
                            help="Ratio of data to use for testing")
        parser.add_argument("--seed", type=int, default=RANDOM_SEED,
                            help="Random seed for reproducibility")
        args = parser.parse_args()

    logger.info("Starting static model evaluation")

    # Load merged dataset
    df = load_merged_dataset(args.merged_dataset)

    # Prepare features and labels
    X_train, y_train, X_test, y_test = prepare_features_and_labels(df, args.seed)

    # Find model files
    model_files = find_model_files(args.models_dir)

    # Evaluate each model
    results = []
    for model_path in model_files:
        # Extract seed from filename
        filename = os.path.basename(model_path)
        seed = int(filename.replace("model_seed_", "").replace(".pkl", ""))

        logger.info(f"Evaluating model from seed {seed}")

        try:
            # Load model
            model = load_model(model_path)

            # Evaluate
            metrics = evaluate_model(model, X_test, y_test)
            metrics["seed"] = seed
            metrics["model_path"] = model_path

            results.append(metrics)

            logger.info(f"Seed {seed} evaluation complete: {metrics}")

        except Exception as e:
            logger.error(f"Error evaluating model {model_path}: {e}")
            # Record failed evaluation
            results.append({
                "seed": seed,
                "model_path": model_path,
                "error": str(e),
                "precision": None,
                "recall": None,
                "accuracy": None,
                "f1": None,
                "n_samples": 0
            })

    # Save results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Evaluation complete. Results saved to {args.output}")
    print(f"Evaluation complete. Results saved to {args.output}")

    return results


if __name__ == "__main__":
    main()

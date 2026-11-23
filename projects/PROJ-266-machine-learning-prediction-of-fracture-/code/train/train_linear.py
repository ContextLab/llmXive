"""
Training script for Linear Regression baseline model.
Consumes features extracted from microstructure images and trains a Linear Regression model
to predict fracture toughness (K_IC).
"""
import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

# Import project utilities
from code.utils.config import get_config_dict, set_seed
from code.utils.logger import get_logger

# Import baselines module to ensure consistency (though we implement training here)
from code.models.baselines import LinearRegressionModel

def load_features(features_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load features and target values from the features JSON file.
    
    Args:
        features_path: Path to the features JSON file.
        
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        image_ids: List of image IDs corresponding to the samples
    """
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    with open(features_path, 'r') as f:
        data = json.load(f)
    
    # Extract features and targets
    # Expected structure: {"samples": [{"image_id": str, "features": list, "k_ic": float}, ...]}
    if "samples" not in data:
        raise ValueError(f"Invalid features format: expected 'samples' key in {features_path}")
    
    samples = data["samples"]
    if not samples:
        raise ValueError(f"No samples found in {features_path}")
    
    X = []
    y = []
    image_ids = []
    
    for sample in samples:
        if "features" not in sample or "k_ic" not in sample or "image_id" not in sample:
            raise ValueError(f"Sample missing required fields: {sample.get('image_id', 'unknown')}")
        
        X.append(sample["features"])
        y.append(sample["k_ic"])
        image_ids.append(sample["image_id"])
    
    return np.array(X), np.array(y), image_ids

def train_linear_regression(
    X: np.ndarray,
    y: np.ndarray,
    train_size: float = 0.8,
    random_state: int = 42
) -> Tuple[LinearRegression, Dict[str, float], Dict[str, Any]]:
    """
    Train a Linear Regression model on the provided features.
    
    Args:
        X: Feature matrix
        y: Target vector
        train_size: Proportion of data to use for training
        random_state: Random seed for reproducibility
        
    Returns:
        model: Trained Linear Regression model
        metrics: Dictionary of evaluation metrics (R², MAE, RMSE)
        predictions: Dictionary containing train/test predictions and actuals
    """
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=train_size, random_state=random_state
    )
    
    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    metrics = {
        "train_r2": float(r2_score(y_train, y_train_pred)),
        "test_r2": float(r2_score(y_test, y_test_pred)),
        "train_mae": float(mean_absolute_error(y_train, y_train_pred)),
        "test_mae": float(mean_absolute_error(y_test, y_test_pred)),
        "train_rmse": float(np.sqrt(mean_squared_error(y_train, y_train_pred))),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, y_test_pred))),
    }
    
    predictions = {
        "train": {"actual": y_train.tolist(), "predicted": y_train_pred.tolist()},
        "test": {"actual": y_test.tolist(), "predicted": y_test_pred.tolist()}
    }
    
    return model, metrics, predictions

def save_model(
    model: LinearRegression,
    metrics: Dict[str, float],
    output_dir: str,
    feature_names: Optional[List[str]] = None
) -> None:
    """
    Save the trained model and metrics to disk.
    
    Args:
        model: Trained Linear Regression model
        metrics: Evaluation metrics
        output_dir: Directory to save model artifacts
        feature_names: Optional list of feature names for documentation
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save model coefficients and intercept
    model_data = {
        "coefficient_names": feature_names,
        "coef": model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "metrics": metrics,
        "model_type": "LinearRegression",
        "n_features": len(model.coef_),
    }
    
    model_path = os.path.join(output_dir, "model.json")
    with open(model_path, 'w') as f:
        json.dump(model_data, f, indent=2)
    
    # Save metrics separately for easy access
    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logging.info(f"Model saved to {model_path}")
    logging.info(f"Metrics saved to {metrics_path}")

def main():
    """Main entry point for Linear Regression training."""
    parser = argparse.ArgumentParser(description="Train Linear Regression baseline model")
    parser.add_argument(
        "--features",
        type=str,
        default="data/features.json",
        help="Path to features JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/baselines/linear",
        help="Output directory for trained model"
    )
    parser.add_argument(
        "--train-size",
        type=float,
        default=0.8,
        help="Proportion of data to use for training"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger("TRAIN_LINEAR")
    logger.info(f"Starting Linear Regression training")
    logger.info(f"Features file: {args.features}")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    try:
        # Load features
        logger.info("Loading features...")
        X, y, image_ids = load_features(args.features)
        logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
        
        # Generate feature names (if not available, use generic names)
        feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        # Train model
        logger.info("Training Linear Regression model...")
        model, metrics, predictions = train_linear_regression(
            X, y, train_size=args.train_size, random_state=args.seed
        )
        
        # Log metrics
        logger.info(f"Training complete. Metrics: {json.dumps(metrics, indent=2)}")
        
        # Save model
        logger.info("Saving model...")
        save_model(model, metrics, args.output_dir, feature_names)
        
        # Save predictions for debugging/analysis
        predictions_path = os.path.join(args.output_dir, "predictions.json")
        with open(predictions_path, 'w') as f:
            json.dump(predictions, f, indent=2)
        logger.info(f"Predictions saved to {predictions_path}")
        
        logger.info("Linear Regression training completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}")
        raise

if __name__ == "__main__":
    main()
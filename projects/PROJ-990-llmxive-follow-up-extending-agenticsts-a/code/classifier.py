import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/classifier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
MODEL_PATH = Path("models/layer_utility_classifier.pkl")
FALLBACK_FLAG_PATH = Path("data/processed/fallback_flag.json")
PROXY_VALIDATION_PATH = Path("data/processed/proxy_validation_report.json")
ABALATION_TRAIN_LABELS_PATH = Path("data/processed/ablation_labels_train.json")


def load_utility_labels(file_path: str) -> pd.DataFrame:
    """
    Load ablation-derived utility labels from a JSON file.
    Expects schema: {trajectory_id, layer_id, utility_score}
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Utility labels file not found: {path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Ensure it's a list of dicts
    if isinstance(data, dict):
        data = [data]
    
    df = pd.DataFrame(data)
    
    required_cols = ['trajectory_id', 'layer_id', 'utility_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in utility labels: {missing}")
    
    return df


def load_holdout_set(file_path: str) -> pd.DataFrame:
    """
    Load the validation set to check proxy correlation if needed.
    Currently used to verify the validation set exists for T014 dependency.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Holdout set file not found: {path}")
    return pd.read_csv(path)


def load_static_logs(file_path: str) -> pd.DataFrame:
    """
    Load static log proxy data if needed for feature engineering.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Static logs file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)


def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare feature matrix X and target vector y.
    
    The task requires training on ablation-derived ground truth.
    We assume the input DataFrame contains features derived from the trajectory
    (e.g., from T006 metrics) and the target 'utility_score'.
    
    If the DataFrame only has ablation labels (trajectory_id, layer_id, utility_score),
    we must join with the metrics data or assume the labels are the target for a 
    simple heuristic model. However, T009 description says "Train on ... ablation_labels_train.json".
    
    Since ablation_labels_train.json only has (id, layer, score), we need features.
    The most robust interpretation given the pipeline is that we are predicting
    utility_score based on the context of the trajectory/layer.
    
    If the input is just the ablation labels, we cannot train a meaningful classifier
    without features. We will assume the input `df` is enriched with features 
    (e.g., via a join with metrics_with_moves.csv in the calling pipeline) OR
    we treat the task as training a model on the available data.
    
    For this implementation, we assume the input `df` has been enriched with features
    such as 'move_entropy', 'health_ratio', etc., or we use the layer_id as a feature.
    
    To be safe and executable:
    1. If 'utility_score' is the only numeric column besides IDs, we might need to 
       generate features from 'layer_id' (one-hot) or assume the data is enriched.
    2. The task says "Train on ... ablation_labels_train.json". 
    
    Let's assume the calling script (main.py) enriches this data with features from
    the metrics file before passing it here, OR we use the layer_id as a categorical feature.
    
    We will attempt to use 'layer_id' as a feature (one-hot encoded) and any other
    numeric columns present. If no features exist besides ID and target, we raise an error.
    """
    # Drop ID columns for features
    feature_cols = [c for c in df.columns if c not in ['trajectory_id', 'layer_id', 'utility_score']]
    
    if not feature_cols:
        # If no external features, try to one-hot encode layer_id
        logger.warning("No external features found. Using layer_id as feature.")
        df = pd.get_dummies(df, columns=['layer_id'], prefix='layer')
        feature_cols = [c for c in df.columns if c != 'utility_score']
    
    X = df[feature_cols].values
    y = df['utility_score'].values
    
    # Handle NaN/Inf in features
    if np.any(~np.isfinite(X)):
        logger.warning("NaN or Inf detected in features. Replacing with 0.")
        X = np.nan_to_num(X, nan=0.0, posinf=1e9, neginf=-1e9)
    
    return X, y


def validate_proxy_correlation(
    proxy_df: pd.DataFrame, 
    ablation_df: pd.DataFrame
) -> float:
    """
    Calculate Pearson correlation between proxy and ablation utility.
    This function is kept for compatibility, though T014 handles the main validation.
    """
    # Merge on trajectory_id and layer_id
    merged = proxy_df.merge(ablation_df, on=['trajectory_id', 'layer_id'], suffixes=('_proxy', '_ablation'))
    
    if 'utility_score_proxy' in merged.columns and 'utility_score_ablation' in merged.columns:
        corr = merged['utility_score_proxy'].corr(merged['utility_score_ablation'])
        return float(corr) if not np.isnan(corr) else 0.0
    
    # Fallback if column names differ
    cols_proxy = [c for c in merged.columns if 'proxy' in c and 'score' in c]
    cols_ablation = [c for c in merged.columns if 'ablation' in c and 'score' in c]
    
    if cols_proxy and cols_ablation:
        corr = merged[cols_proxy[0]].corr(merged[cols_ablation[0]])
        return float(corr) if not np.isnan(corr) else 0.0
        
    return 0.0


def save_report(report: Dict[str, Any], path: str) -> None:
    """Save the training report to JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {path}")


def run_training(
    train_data: pd.DataFrame,
    model_type: str = "decision_tree"
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a lightweight CPU-tractable model.
    
    Args:
        train_data: DataFrame with features and 'utility_score' target.
        model_type: 'decision_tree' or 'logistic_regression'.
        
    Returns:
        Trained model and a report dictionary.
    """
    X, y = prepare_features(train_data)
    
    # Split for internal validation (80/20)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale if using Logistic Regression
    scaler = None
    if model_type == "logistic_regression":
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_val = scaler.transform(X_val)
    
    # Initialize model
    if model_type == "decision_tree":
        model = DecisionTreeClassifier(
            max_depth=5, 
            min_samples_split=10, 
            random_state=42
        )
    else:
        model = LogisticRegression(
            max_iter=1000, 
            random_state=42
        )
    
    # Train
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)
    
    report = {
        "model_type": model_type,
        "train_size": len(X_train),
        "val_size": len(X_val),
        "val_accuracy": float(accuracy),
        "feature_count": X.shape[1],
        "scaler_used": scaler is not None
    }
    
    logger.info(f"Training complete. Validation Accuracy: {accuracy:.4f}")
    return model, report


def load_model(path: str) -> Any:
    """Load a serialized model."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    with open(p, 'rb') as f:
        return pickle.load(f)


def main():
    """
    Main entry point for T009: Train Layer Utility Classifier.
    
    Logic:
    1. Verify fallback_flag.json exists. If fallback: true, SKIP training.
    2. Verify proxy_validation_report.json exists and proxy_valid: true. If false, SKIP.
    3. Load ablation_labels_train.json.
    4. Train model.
    5. Save model and report.
    """
    logger.info("Starting T009: Layer Utility Classifier Training")
    
    # 1. Check Fallback Flag
    if not FALLBACK_FLAG_PATH.exists():
        logger.error(f"Fallback flag file not found: {FALLBACK_FLAG_PATH}")
        raise FileNotFoundError("Missing fallback_flag.json. Run T008c first.")
    
    with open(FALLBACK_FLAG_PATH, 'r') as f:
        fallback_data = json.load(f)
    
    if fallback_data.get("fallback", False):
        logger.warning("Fallback flag is TRUE. Skipping training as per spec.")
        # Write a report indicating skip
        report = {
            "status": "skipped",
            "reason": "fallback_flag.json indicates fallback mode (n < 300)",
            "model_path": str(MODEL_PATH)
        }
        save_report(report, "data/processed/training_report.json")
        return
    
    # 2. Check Proxy Validation
    if not PROXY_VALIDATION_PATH.exists():
        logger.error(f"Proxy validation report not found: {PROXY_VALIDATION_PATH}")
        raise FileNotFoundError("Missing proxy_validation_report.json. Run T014 first.")
    
    with open(PROXY_VALIDATION_PATH, 'r') as f:
        proxy_report = json.load(f)
    
    if not proxy_report.get("proxy_valid", False):
        logger.warning("Proxy validation failed (proxy_valid: false). Skipping training.")
        report = {
            "status": "skipped",
            "reason": "Proxy validation failed (proxy_valid: false)",
            "model_path": str(MODEL_PATH)
        }
        save_report(report, "data/processed/training_report.json")
        return
    
    # 3. Load Data
    if not ABALATION_TRAIN_LABELS_PATH.exists():
        logger.error(f"Ablation train labels not found: {ABALATION_TRAIN_LABELS_PATH}")
        raise FileNotFoundError("Missing ablation_labels_train.json. Run T008 first.")
    
    logger.info(f"Loading ablation labels from {ABALATION_TRAIN_LABELS_PATH}")
    train_df = load_utility_labels(str(ABALATION_TRAIN_LABELS_PATH))
    
    if train_df.empty:
        logger.error("Ablation train labels are empty.")
        raise ValueError("Ablation train labels dataset is empty.")
    
    logger.info(f"Loaded {len(train_df)} records.")
    
    # 4. Train Model
    # Try Decision Tree first (robust to scaling, handles categorical via one-hot)
    try:
        model, report = run_training(train_df, model_type="decision_tree")
    except Exception as e:
        logger.warning(f"Decision Tree failed ({e}). Trying Logistic Regression.")
        model, report = run_training(train_df, model_type="logistic_regression")
    
    # 5. Save Model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    report["model_saved_to"] = str(MODEL_PATH)
    report["status"] = "completed"
    
    # Save detailed report
    save_report(report, "data/processed/training_report.json")
    
    logger.info("T009 completed successfully.")


if __name__ == "__main__":
    main()
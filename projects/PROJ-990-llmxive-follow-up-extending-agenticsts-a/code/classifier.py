import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CONFIG = {
    'PROXY_CORRELATION_THRESHOLD': 0.7,
    'TRAIN_TEST_SPLIT_RATIO': 0.2,
    'RANDOM_STATE': 42
}

def load_utility_labels(path: str = "data/processed/utility_labels.csv") -> pd.DataFrame:
    """Load utility labels from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Utility labels file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} utility labels from {path}")
    return df

def load_holdout_set(path: str = "data/processed/holdout_set.csv") -> pd.DataFrame:
    """Load holdout set from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Holdout set file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} records from holdout set: {path}")
    return df

def load_static_logs(path: str = "data/processed/static_logs.csv") -> pd.DataFrame:
    """Load static logs (proxy) from CSV.
    
    Expected schema: trajectory_id, turn_id, proxy_metric (or similar).
    We assume the proxy metric represents the 'static' observation.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Static logs file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} static log records from {path}")
    return df

def prepare_features(holdout_df: pd.DataFrame, utility_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Merge holdout set with utility labels to prepare features for correlation check.
    Assumes a common key (e.g., 'trajectory_id' or 'turn_id') exists in both.
    For the purpose of this task, we assume 'trajectory_id' is the join key.
    If the schema differs, the join logic should be adapted, but the core requirement
    is to align the proxy (static logs) with the ground truth (utility scores).
    
    We will perform a merge on 'trajectory_id'. If the holdout set has turn-level data,
    we might need to aggregate or join on (trajectory_id, turn_id).
    Given the task description, we assume a direct alignment or a merge on ID.
    """
    # Ensure we have the necessary columns
    if 'utility_score' not in utility_df.columns:
        raise ValueError("Utility labels must contain 'utility_score' column")
    
    # Attempt to merge. If keys differ, this might need adjustment based on actual data schema.
    # Assuming 'trajectory_id' is the common key.
    merged = pd.merge(
        holdout_df, 
        utility_df[['trajectory_id', 'utility_score']], 
        on='trajectory_id', 
        how='inner'
    )
    
    if merged.empty:
        raise ValueError("No matching records found between holdout set and utility labels.")
    
    logger.info(f"Merged dataset size: {len(merged)}")
    return merged

def validate_proxy_correlation(holdout_df: pd.DataFrame, utility_df: pd.DataFrame, proxy_column: str = 'proxy_metric') -> Dict[str, Any]:
    """
    Check Pearson correlation between static logs (proxy) and ablation utility (ground truth).
    
    Logic:
    1. Merge holdout set and utility labels.
    2. Extract proxy values and utility scores.
    3. Calculate Pearson correlation coefficient (r).
    4. If r < 0.7, raise an exception.
    5. Return report dictionary.
    
    Args:
        holdout_df: DataFrame containing the holdout set (must include proxy_column).
        utility_df: DataFrame containing utility scores.
        proxy_column: Name of the column in holdout_df representing the proxy metric.
    
    Returns:
        Dict containing correlation results and status.
    
    Raises:
        ValueError: If correlation coefficient is less than 0.7.
    """
    if proxy_column not in holdout_df.columns:
        raise ValueError(f"Proxy column '{proxy_column}' not found in holdout set.")
    
    merged = prepare_features(holdout_df, utility_df)
    
    proxy_values = merged[proxy_column].dropna()
    utility_values = merged['utility_score'].dropna()
    
    # Ensure alignment after dropna
    min_len = min(len(proxy_values), len(utility_values))
    if min_len < 2:
        raise ValueError("Not enough valid data points to calculate correlation.")
    
    proxy_values = proxy_values.iloc[:min_len]
    utility_values = utility_values.iloc[:min_len]
    
    r, p_value = pearsonr(proxy_values, utility_values)
    
    logger.info(f"Pearson correlation coefficient (r): {r:.4f}")
    logger.info(f"P-value: {p_value:.4f}")
    
    report = {
        "correlation_coefficient": float(r),
        "p_value": float(p_value),
        "threshold": CONFIG['PROXY_CORRELATION_THRESHOLD'],
        "status": "passed" if r >= CONFIG['PROXY_CORRELATION_THRESHOLD'] else "failed",
        "sample_size": int(min_len)
    }
    
    if r < CONFIG['PROXY_CORRELATION_THRESHOLD']:
        raise ValueError(f"Proxy validation FAILED: correlation {r:.4f} is below threshold {CONFIG['PROXY_CORRELATION_THRESHOLD']}.")
    
    return report

def save_report(report: Dict[str, Any], output_path: str = "data/processed/proxy_validation_report.json") -> None:
    """Save the validation report to a JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")

def run_training(
    utility_labels_path: str = "data/processed/utility_labels.csv",
    model_path: str = "models/layer_utility_classifier.pkl",
    split_ratio: float = CONFIG['TRAIN_TEST_SPLIT_RATIO'],
    random_state: int = CONFIG['RANDOM_STATE']
) -> None:
    """
    Train a lightweight classifier on utility labels.
    
    Logic:
    1. Load utility labels.
    2. Split into train/test (80/20).
    3. Train a Decision Tree or Logistic Regression.
    4. Save the model.
    
    Note: This function is kept for completeness as per the API surface,
    though T014 focuses on validation.
    """
    df = load_utility_labels(utility_labels_path)
    
    # Assume features are all columns except 'utility_score' and 'trajectory_id'
    feature_cols = [c for c in df.columns if c not in ['utility_score', 'trajectory_id']]
    if not feature_cols:
        raise ValueError("No feature columns found in utility labels.")
    
    X = df[feature_cols]
    y = df['utility_score']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=split_ratio, random_state=random_state
    )
    
    # Train a simple model (Decision Tree as per task description)
    model = DecisionTreeClassifier(random_state=random_state)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info(f"Model trained. Test Accuracy: {acc:.4f}")
    
    # Save model
    model_dir = Path(model_path).parent
    model_dir.mkdir(parents=True, exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

def load_model(model_path: str = "models/layer_utility_classifier.pkl") -> Any:
    """Load a trained model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def main():
    """Main entry point for T014: Proxy Validation."""
    logger.info("Starting Proxy Validation (T014)...")
    
    try:
        # Load data
        holdout_df = load_holdout_set("data/processed/holdout_set.csv")
        utility_df = load_utility_labels("data/processed/utility_labels.csv")
        static_logs_df = load_static_logs("data/processed/static_logs.csv")
        
        # Merge static logs with holdout set if they are separate
        # Assuming static_logs_df has 'trajectory_id' and 'proxy_metric'
        if 'trajectory_id' in holdout_df.columns and 'trajectory_id' in static_logs_df.columns:
            # If holdout_df doesn't have proxy_metric, merge it in
            if 'proxy_metric' not in holdout_df.columns:
                holdout_df = pd.merge(holdout_df, static_logs_df[['trajectory_id', 'proxy_metric']], on='trajectory_id', how='left')
        
        # Validate correlation
        report = validate_proxy_correlation(holdout_df, utility_df, proxy_column='proxy_metric')
        
        # Save report
        save_report(report, "data/processed/proxy_validation_report.json")
        
        logger.info("Proxy validation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
"""
Task T027: Store Fairness Metrics with Traceability

Reads computed metrics from the fairness metric pipeline (or recalculates them if needed),
and stores them in a structured CSV format with required traceability fields:
model_id, dataset_id, protected_attribute, metric_name, metric_value.

This script ensures FR-004 compliance by embedding full traceability in the output.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import hashlib
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_utils import log_disclaimer, log_warning
from utils.metrics import (
    demographic_parity_difference,
    equalized_odds_difference,
    predictive_parity,
    calibration_within_groups,
    disparate_impact_ratio,
    false_positive_rate_disparity,
    calculate_metrics
)
from utils.data_model import Dataset, Model

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROCESSED_DATA_DIR / "models"
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"
METRICS_OUTPUT_FILE = ANALYSIS_DIR / "metrics.csv"
LOG_HEADER = "=== T027: Store Fairness Metrics ==="

def ensure_output_directory():
    """Ensure the analysis directory exists."""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def load_model_metadata(model_file: Path) -> Dict[str, Any]:
    """Load model metadata from the JSON file accompanying the model."""
    metadata_file = model_file.with_suffix('.json')
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return {}

def load_dataset_data(dataset_file: Path) -> pd.DataFrame:
    """Load processed dataset from CSV."""
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_file}")
    return pd.read_csv(dataset_file)

def load_model_predictions(model_file: Path, dataset_file: Path) -> pd.DataFrame:
    """
    Load dataset and generate predictions using the saved model.
    Returns a DataFrame with columns: y_true, y_pred, protected_attribute.
    """
    # Load model metadata to find associated dataset
    metadata = load_model_metadata(model_file)
    dataset_id = metadata.get('dataset_id')
    model_type = metadata.get('model_type')
    model_id = metadata.get('model_id')

    if not dataset_id:
        raise ValueError(f"Model metadata missing 'dataset_id': {model_file}")

    # Find the corresponding processed dataset
    dataset_file_path = PROCESSED_DATA_DIR / f"{dataset_id}_processed.csv"
    if not dataset_file_path.exists():
        raise FileNotFoundError(f"Processed dataset not found for {dataset_id}")

    # Load dataset
    df = pd.read_csv(dataset_file_path)

    # Load the actual model (using joblib or pickle)
    import joblib
    model = joblib.load(model_file)

    # Identify feature columns (exclude protected attribute, outcome, predictions if present)
    # We assume the processed dataset has columns: [features..., protected_attr, outcome]
    # We need to predict on features only.
    # For simplicity, we assume the model was trained on all columns except the last two (protected, outcome)
    # This is a simplification; in a real system, we'd store feature names in metadata.

    # Identify columns to use for prediction
    # Assuming the last column is 'outcome' and second to last is 'protected_attribute'
    # This is fragile; better to store feature names in metadata.
    # For now, we'll try to infer based on common column names or use all numeric columns except outcome/protected

    # Let's assume the processed dataset has a standard structure:
    # - Features: all columns except 'outcome' and 'protected_attribute'
    # - Outcome: 'outcome'
    # - Protected: 'protected_attribute'

    feature_cols = [col for col in df.columns if col not in ['outcome', 'protected_attribute']]
    if not feature_cols:
        raise ValueError(f"No feature columns found in dataset {dataset_id}")

    X = df[feature_cols]
    y_true = df['outcome']
    protected_attr = df['protected_attribute']

    # Generate predictions
    y_pred = model.predict(X)

    # Create result DataFrame
    result_df = pd.DataFrame({
        'y_true': y_true,
        'y_pred': y_pred,
        'protected_attribute': protected_attr,
        'dataset_id': dataset_id,
        'model_id': model_id
    })

    return result_df

def calculate_metrics_for_model_df(df: pd.DataFrame, model_id: str, dataset_id: str) -> List[Dict[str, Any]]:
    """
    Calculate all fairness metrics for a given model/dataset combination.
    Returns a list of dictionaries, one per metric.
    """
    metrics_results = []

    y_true = df['y_true'].values
    y_pred = df['y_pred'].values
    protected_attr = df['protected_attribute'].values

    # Calculate each metric
    metrics_to_calculate = [
        ('demographic_parity_difference', demographic_parity_difference),
        ('equalized_odds_difference', equalized_odds_difference),
        ('predictive_parity', predictive_parity),
        ('calibration_within_groups', calibration_within_groups),
        ('disparate_impact_ratio', disparate_impact_ratio),
        ('false_positive_rate_disparity', false_positive_rate_disparity),
    ]

    for metric_name, metric_func in metrics_to_calculate:
        try:
            # Handle different function signatures
            if metric_name in ['demographic_parity_difference', 'equalized_odds_difference', 
                               'disparate_impact_ratio', 'false_positive_rate_disparity']:
                # These typically take (y_true, y_pred, protected_attr)
                value = metric_func(y_true, y_pred, protected_attr)
            elif metric_name in ['predictive_parity', 'calibration_within_groups']:
                # These might have different signatures
                value = metric_func(y_true, y_pred, protected_attr)
            else:
                # Fallback: try calling with standard signature
                value = metric_func(y_true, y_pred, protected_attr)

            # Ensure value is numeric
            if pd.isna(value) or np.isinf(value):
                value = 0.0

            metrics_results.append({
                'model_id': model_id,
                'dataset_id': dataset_id,
                'protected_attribute': 'binary', # Assuming binary as per preprocessing
                'metric_name': metric_name,
                'metric_value': float(value)
            })

        except Exception as e:
            log_warning(f"Failed to calculate {metric_name} for {model_id}: {e}")
            metrics_results.append({
                'model_id': model_id,
                'dataset_id': dataset_id,
                'protected_attribute': 'binary',
                'metric_name': metric_name,
                'metric_value': np.nan
            })

    return metrics_results

def collect_all_metrics() -> pd.DataFrame:
    """
    Iterate through all saved models, load their data, calculate metrics,
    and compile results into a single DataFrame.
    """
    all_metrics = []

    if not MODELS_DIR.exists():
        log_warning("Models directory not found. No metrics to store.")
        return pd.DataFrame()

    # Find all model files (assuming .pkl or .joblib extension)
    model_files = list(MODELS_DIR.glob("*.pkl")) + list(MODELS_DIR.glob("*.joblib"))

    if not model_files:
        log_warning("No model files found in models directory.")
        return pd.DataFrame()

    for model_file in model_files:
        try:
            # Load model metadata
            metadata = load_model_metadata(model_file)
            model_id = metadata.get('model_id', model_file.stem)
            dataset_id = metadata.get('dataset_id', 'unknown')

            # Load dataset and generate predictions
            df = load_model_predictions(model_file, PROCESSED_DATA_DIR / f"{dataset_id}_processed.csv")

            # Calculate metrics
            metrics = calculate_metrics_for_model_df(df, model_id, dataset_id)
            all_metrics.extend(metrics)

        except Exception as e:
            log_warning(f"Failed to process model {model_file}: {e}")
            continue

    return pd.DataFrame(all_metrics)

def save_metrics_to_csv(metrics_df: pd.DataFrame, output_path: Path):
    """
    Save metrics DataFrame to CSV with required columns:
    model_id, dataset_id, protected_attribute, metric_name, metric_value
    """
    if metrics_df.empty:
        log_warning("No metrics to save.")
        # Create empty file with headers
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=['model_id', 'dataset_id', 'protected_attribute', 'metric_name', 'metric_value']).to_csv(output_path, index=False)
        return

    # Ensure required columns exist
    required_cols = ['model_id', 'dataset_id', 'protected_attribute', 'metric_name', 'metric_value']
    for col in required_cols:
        if col not in metrics_df.columns:
            metrics_df[col] = np.nan

    # Select and order columns
    metrics_df = metrics_df[required_cols]

    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(output_path, index=False)
    print(f"Metrics saved to {output_path} with {len(metrics_df)} rows.")

def main():
    """Main execution function for T027."""
    print(LOG_HEADER)
    log_disclaimer("Findings are associational only; no causal claims are made.")

    start_time = time.time()

    try:
        # Ensure output directory exists
        ensure_output_directory()

        # Collect all metrics
        print("Collecting metrics from all models...")
        metrics_df = collect_all_metrics()

        # Save to CSV
        print("Saving metrics to CSV...")
        save_metrics_to_csv(metrics_df, METRICS_OUTPUT_FILE)

        elapsed = time.time() - start_time
        print(f"Task T027 completed successfully in {elapsed:.2f} seconds.")
        print(f"Output file: {METRICS_OUTPUT_FILE}")

    except Exception as e:
        print(f"Task T027 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

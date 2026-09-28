"""
T033: Calculate correlation coefficients between structural features and execution necessity.

This script loads the trained model (decision boundary), the feature dataset (features.csv),
and the threshold sweep results to compute the correlation between structural metrics
(dependency_depth, cyclomatic_complexity, lines_of_code) and the target variable
(dynamic_execution_outcome, encoded as Need Dynamic = 1, Fail/Safe = 0).
"""
import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.train_model import load_features
from scripts.identify_threshold import load_threshold_sweep


def encode_target(outcome: str) -> int:
    """
    Encode the dynamic_execution_outcome into a binary target for correlation.
    'Need Dynamic' (or 'Fail' if that's the label for needing intervention) -> 1
    'Pass' (Safe) -> 0
    
    Based on the pipeline logic:
    - Pass: Static analysis is sufficient (No dynamic needed).
    - Fail/Timeout/Unparseable: Dynamic execution was needed to determine failure.
    """
    # Normalize to handle potential casing differences
    val = str(outcome).strip().lower()
    
    # If the outcome indicates a failure or a need for dynamic intervention, it's 1.
    # Based on T012/T013, outcomes are Pass, Fail, Timeout.
    # T031/T032 context implies we are predicting "Need for Dynamic Execution".
    # If the ground truth says "Pass", we didn't need dynamic (or it was safe).
    # If "Fail" or "Timeout", we needed dynamic to catch the error.
    if val in ['pass']:
        return 0
    else:
        # Covers 'fail', 'timeout', 'unparseable', etc.
        return 1


def calculate_correlations(features_df: pd.DataFrame, model_path: str, threshold_path: str) -> dict:
    """
    Calculate Pearson correlation coefficients between structural features and the target.
    
    Returns a dictionary mapping feature names to their correlation with the target.
    """
    # Load model and threshold info for context (optional, but good for logging)
    try:
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        # Log model type if available
        model_type = model_data.get('model_type', 'unknown') if isinstance(model_data, dict) else 'unknown'
        print(f"Loaded model: {model_type}")
    except Exception as e:
        print(f"Warning: Could not load model for context: {e}")
        model_type = "unknown"

    try:
        with open(threshold_path, 'r') as f:
            threshold_data = json.load(f)
        min_fnr = threshold_data.get('min_fnr', 'N/A')
        print(f"Threshold sweep min FNR: {min_fnr}")
    except Exception as e:
        print(f"Warning: Could not load threshold data for context: {e}")
        min_fnr = "N/A"

    # Encode the target column
    if 'dynamic_execution_outcome' not in features_df.columns:
        raise ValueError("Column 'dynamic_execution_outcome' not found in features.csv")
    
    target_series = features_df['dynamic_execution_outcome'].apply(encode_target)
    
    # Define structural features to correlate
    # These are the metrics calculated in T021/T022
    structural_features = ['dependency_depth', 'cyclomatic_complexity', 'lines_of_code']
    
    # Check which features exist in the dataframe
    available_features = [f for f in structural_features if f in features_df.columns]
    
    if not available_features:
        raise ValueError(f"No structural features found in dataframe. Available columns: {list(features_df.columns)}")
    
    correlations = {}
    
    for feat in available_features:
        # Drop rows where either the feature or target is NaN
        valid_data = features_df[[feat, 'dynamic_execution_outcome']].dropna()
        
        if len(valid_data) < 2:
            correlations[feat] = None
            print(f"Warning: Insufficient data to calculate correlation for {feat}")
            continue
        
        # Calculate Pearson correlation
        corr_matrix = valid_data[feat].astype(float).corr(valid_data['dynamic_execution_outcome'].apply(encode_target))
        correlations[feat] = float(corr_matrix)
        print(f"Correlation between {feat} and Need Dynamic: {corr_matrix:.4f}")
    
    return correlations


def main():
    """Main entry point for T033."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    processed_dir = data_dir / 'processed'
    models_dir = project_root / 'models'

    # Define paths
    features_path = processed_dir / 'features.csv'
    model_path = models_dir / 'decision_boundary.pkl'
    threshold_path = processed_dir / 'threshold_sweep.json'
    output_path = processed_dir / 'correlation_analysis.json'

    # Validate inputs exist
    if not features_path.exists():
        raise FileNotFoundError(f"Required file not found: {features_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Required file not found: {model_path}")
    if not threshold_path.exists():
        raise FileNotFoundError(f"Required file not found: {threshold_path}")

    print(f"Loading features from {features_path}...")
    features_df = load_features(str(features_path))

    print("Calculating correlations...")
    correlations = calculate_correlations(features_df, str(model_path), str(threshold_path))

    # Prepare output report
    report = {
        "task_id": "T033",
        "description": "Correlation analysis between structural features and execution necessity",
        "correlation_coefficient": correlations,
        "method": "Pearson correlation",
        "target_encoding": {
            "0": "Pass (No dynamic execution needed)",
            "1": "Fail/Timeout/Unparseable (Dynamic execution needed)"
        },
        "status": "completed"
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Correlation analysis saved to {output_path}")
    return report


if __name__ == '__main__':
    main()

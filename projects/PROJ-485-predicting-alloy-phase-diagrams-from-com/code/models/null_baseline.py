"""
Null model baseline implementation for alloy phase prediction.

This module implements a global mean baseline model and provides
comparison logic against the trained Random Forest model (FR-009).
"""
import os
import sys
import argparse
import pickle
import json
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)


def load_processed_data(data_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load processed descriptor data and target values.

    Args:
        data_path: Path to the processed CSV file (data/processed/descriptors.csv)

    Returns:
        X: Feature matrix (numpy array)
        y: Target vector (numpy array) - typically temperature or phase boundary
        feature_names: List of feature column names
    """
    import csv

    log_info(logger, f"Loading processed data from {data_path}")

    if not os.path.exists(data_path):
        log_error(logger, f"Data file not found: {data_path}", ErrorCode.DATA_SOURCE_MISSING)
        raise FileNotFoundError(f"Data file not found: {data_path}")

    X_list = []
    y_list = []
    feature_names = []

    with open(data_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        feature_names = reader.fieldnames
        # Assume the last column is the target (temperature)
        target_col = feature_names[-1]
        feature_cols = feature_names[:-1]

        for row in reader:
            features = [float(row[col]) for col in feature_cols]
            X_list.append(features)
            y_list.append(float(row[target_col]))

    X = np.array(X_list)
    y = np.array(y_list)

    log_info(logger, f"Loaded {len(y)} samples with {X.shape[1]} features")

    return X, y, feature_cols


def compute_global_mean(y_train: np.ndarray) -> float:
    """
    Compute the global mean of the training target values.

    Args:
        y_train: Training target values

    Returns:
        Global mean value
    """
    return float(np.mean(y_train))


def predict_null_model(X: np.ndarray, global_mean: float) -> np.ndarray:
    """
    Generate predictions using the global mean baseline.

    Args:
        X: Feature matrix (unused, but required for API consistency)
        global_mean: The global mean value to use for all predictions

    Returns:
        Array of predictions (all equal to global_mean)
    """
    return np.full(X.shape[0], global_mean)


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Evaluate model performance using standard metrics.

    Args:
        y_true: Ground truth values
        y_pred: Predicted values

    Returns:
        Dictionary with MAE and R² metrics
    """
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))

    return {
        'mae': mae,
        'r2': r2
    }


def compare_models(null_metrics: Dict[str, float], rf_metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Compare null model baseline against Random Forest model.

    Args:
        null_metrics: Metrics from the null model
        rf_metrics: Metrics from the Random Forest model

    Returns:
        Comparison results including improvement percentages
    """
    mae_improvement = (null_metrics['mae'] - rf_metrics['mae']) / null_metrics['mae'] * 100 if null_metrics['mae'] > 0 else 0
    r2_improvement = rf_metrics['r2'] - null_metrics['r2']

    comparison = {
        'null_model': null_metrics,
        'rf_model': rf_metrics,
        'mae_improvement_percent': float(mae_improvement),
        'r2_improvement': float(r2_improvement),
        'rf_better': rf_metrics['mae'] < null_metrics['mae'] and rf_metrics['r2'] > null_metrics['r2']
    }

    return comparison


def run_null_baseline_analysis(
    data_path: str,
    rf_model_path: Optional[str] = None,
    output_path: str = 'data/artifacts/null_baseline_comparison.json'
) -> Dict[str, Any]:
    """
    Run complete null baseline analysis and comparison.

    This function:
    1. Loads the processed data
    2. Computes the global mean from training data
    3. Generates null model predictions
    4. Evaluates null model performance
    5. If RF model is provided, compares against it
    6. Saves results to output file

    Args:
        data_path: Path to processed data CSV
        rf_model_path: Optional path to trained RF model for comparison
        output_path: Path to save comparison results

    Returns:
        Dictionary containing all analysis results
    """
    log_info(logger, "Starting null baseline analysis")

    # Load data
    X, y, feature_names = load_processed_data(data_path)

    # For this analysis, we'll use all data to compute global mean
    # In a real scenario, we might split train/test, but for baseline
    # comparison we compute on the full dataset
    global_mean = compute_global_mean(y)
    log_info(logger, f"Computed global mean: {global_mean:.4f}")

    # Generate null predictions
    y_pred_null = predict_null_model(X, global_mean)

    # Evaluate null model
    null_metrics = evaluate_model(y, y_pred_null)
    log_info(logger, f"Null model MAE: {null_metrics['mae']:.4f}, R²: {null_metrics['r2']:.4f}")

    results = {
        'global_mean': global_mean,
        'null_model_metrics': null_metrics,
        'sample_count': len(y),
        'feature_count': len(feature_names)
    }

    # If RF model is provided, load and compare
    if rf_model_path and os.path.exists(rf_model_path):
        log_info(logger, f"Loading RF model from {rf_model_path}")
        try:
            with open(rf_model_path, 'rb') as f:
                rf_model = pickle.load(f)

            # Generate RF predictions
            y_pred_rf = rf_model.predict(X)

            # Evaluate RF model
            rf_metrics = evaluate_model(y, y_pred_rf)
            log_info(logger, f"RF model MAE: {rf_metrics['mae']:.4f}, R²: {rf_metrics['r2']:.4f}")

            # Compare models
            comparison = compare_models(null_metrics, rf_metrics)
            results['rf_model_metrics'] = rf_metrics
            results['comparison'] = comparison

            log_info(logger, f"MAE improvement: {comparison['mae_improvement_percent']:.2f}%")
            log_info(logger, f"R² improvement: {comparison['r2_improvement']:.4f}")
            log_info(logger, f"RF model better: {comparison['rf_better']}")

        except Exception as e:
            log_error(logger, f"Failed to load or evaluate RF model: {str(e)}", ErrorCode.INSUFFICIENT_POWER)
            results['rf_model_error'] = str(e)
    else:
        log_warning(logger, "No RF model provided for comparison, skipping comparison step")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    log_info(logger, f"Results saved to {output_path}")

    return results


def main():
    """Main entry point for null baseline analysis."""
    parser = argparse.ArgumentParser(description='Run null model baseline analysis')
    parser.add_argument('--data', type=str, default='data/processed/descriptors.csv',
                      help='Path to processed data CSV')
    parser.add_argument('--model', type=str, default='data/artifacts/model.pkl',
                      help='Path to trained RF model (optional)')
    parser.add_argument('--output', type=str, default='data/artifacts/null_baseline_comparison.json',
                      help='Path to save comparison results')

    args = parser.parse_args()

    try:
        results = run_null_baseline_analysis(
            data_path=args.data,
            rf_model_path=args.model,
            output_path=args.output
        )

        # Print summary
        print("\n=== Null Baseline Analysis Summary ===")
        print(f"Global Mean: {results['global_mean']:.4f}")
        print(f"Null Model MAE: {results['null_model_metrics']['mae']:.4f}")
        print(f"Null Model R²: {results['null_model_metrics']['r2']:.4f}")

        if 'comparison' in results:
            print(f"\nComparison with RF Model:")
            print(f"  RF Model MAE: {results['rf_model_metrics']['mae']:.4f}")
            print(f"  RF Model R²: {results['rf_model_metrics']['r2']:.4f}")
            print(f"  MAE Improvement: {results['comparison']['mae_improvement_percent']:.2f}%")
            print(f"  R² Improvement: {results['comparison']['r2_improvement']:.4f}")
            print(f"  RF Better: {results['comparison']['rf_better']}")

        print(f"\nResults saved to: {args.output}")

    except Exception as e:
        log_error(logger, f"Null baseline analysis failed: {str(e)}", ErrorCode.INSUFFICIENT_POWER)
        sys.exit(1)


if __name__ == '__main__':
    main()

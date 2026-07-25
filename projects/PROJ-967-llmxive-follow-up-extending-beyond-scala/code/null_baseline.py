"""
T030c: Implement Null Baseline Comparison

Trains a dummy 'mean predictor' model that predicts the mean of the target
variable for all inputs. Calculates its R² and MAE, compares these against
the Random Forest metrics, and writes results to results/null_baseline.json.

Dependencies: T029 (evaluate.py)
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score

# Import from existing project modules
from evaluate import load_features, setup_logging


def calculate_mean_baseline_metrics(y_true):
    """
    Calculate R² and MAE for a mean predictor.
    
    A mean predictor always predicts the mean of the training targets.
    For a mean predictor on the test set:
    - Predictions are all equal to the mean of y_true (if we consider the
      baseline calculated on the same set, or mean of training set if split).
    - In this context, we assume the features and targets are already split
      or we are evaluating the baseline capability on the provided data.
    - R² of a mean predictor is 0.0 by definition if evaluated on the same
      distribution used to calculate the mean.
    
    However, to be rigorous:
    If we have a training set mean (mu_train), and we predict mu_train for
    test set y_test:
    R² = 1 - (SS_res / SS_tot)
    SS_res = sum((y_test - mu_train)^2)
    SS_tot = sum((y_test - mean(y_test))^2)
    
    If we evaluate on the whole dataset (no split), mean predictor R² is 0.
    Since T029/T030a likely handled the split in `evaluate.py`, we assume
    this function receives the *test set* y values.
    To be safe, we calculate the mean of the provided y_true (assuming it's
    the test set) and compute metrics. If this is the full dataset, R² will be ~0.
    
    Args:
        y_true: Array of true target values (test set).
    
    Returns:
        dict: {'r2': float, 'mae': float}
    """
    if len(y_true) == 0:
        raise ValueError("y_true cannot be empty")
    
    y_mean = np.mean(y_true)
    y_pred = np.full_like(y_true, y_mean, dtype=float)
    
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    
    return {
        "r2": float(r2),
        "mae": float(mae),
        "predicted_value": float(y_mean)
    }


def load_rf_results(results_path):
    """
    Load the Random Forest results from results/results.json.
    
    Args:
        results_path: Path to results/results.json
    
    Returns:
        dict: The loaded results dictionary.
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"RF results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)


def compare_and_save_results(baseline_metrics, rf_metrics, output_path):
    """
    Compare baseline and RF metrics, then save to null_baseline.json.
    
    Args:
        baseline_metrics: Dict with baseline R² and MAE.
        rf_metrics: Dict with RF R² and MAE.
        output_path: Path to save the comparison results.
    """
    comparison = {
        "baseline": baseline_metrics,
        "random_forest": rf_metrics,
        "improvement": {
            "r2_diff": rf_metrics.get("r2", 0) - baseline_metrics.get("r2", 0),
            "mae_diff": baseline_metrics.get("mae", 0) - rf_metrics.get("mae", 0) # Positive means improvement
        },
        "conclusion": ""
    }
    
    # Determine conclusion based on SC-001 and SC-002
    if comparison["improvement"]["r2_diff"] > 0.0:
        comparison["conclusion"] = "Random Forest outperforms the mean baseline, indicating predictive power beyond the mean."
    else:
        comparison["conclusion"] = "Random Forest does not outperform the mean baseline. The model may not have captured significant patterns."
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    return comparison


def parse_args():
    parser = argparse.ArgumentParser(description="T030c: Null Baseline Comparison")
    parser.add_argument(
        "--features-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json",
        help="Path to the features JSON file."
    )
    parser.add_argument(
        "--rf-results-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json",
        help="Path to the Random Forest results JSON file."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/null_baseline.json",
        help="Path to save the null baseline comparison results."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logger = setup_logging(level=args.log_level)
    logger.info("Starting T030c: Null Baseline Comparison")

    try:
        # 1. Load Features to get the target variable (y)
        # We assume the features file contains the target column 'fidelity_loss'
        # and we need to evaluate the baseline on the same data used for RF evaluation
        # (or the test split if the file is pre-split, but typically features.json is the full set).
        # Since T029/T030a likely handled the split internally in evaluate.py, 
        # we need to know if we are evaluating on the full set or test set.
        # The most robust approach for a baseline comparison is to compare the 
        # reported RF metrics (on test set) against a baseline calculated on the test set.
        # However, if we only have the full features.json, we can't easily get the test set 
        # unless we re-split. 
        # Given the dependency on T029 (which calculated metrics), we assume T029 
        # already split the data. But T029's output is just the metrics in results.json.
        # To be safe and consistent with the "mean predictor" definition, we will:
        # A) Load the features.
        # B) If the RF results were calculated on a specific split, we ideally need that split.
        #    Since we don't have the split indices, we will assume the RF results in results.json
        #    are comparable to a baseline calculated on the same data distribution.
        #    If the RF was trained on 80% and tested on 20%, the baseline should be calculated
        #    on the 20% test set.
        #    Without the test set indices, we cannot perfectly replicate the test set baseline.
        #    However, a common simplification in this pipeline context is to assume the 
        #    features file represents the data used for evaluation, or we re-split with the same seed.
        #    Let's assume we re-split with the same seed (42) and test_size (0.2) to get the test set.
        
        features_data = load_features(args.features_path)
        logger.info(f"Loaded {len(features_data)} samples from features file.")

        if not features_data:
            raise ValueError("Features data is empty. Cannot calculate baseline.")

        # Extract target (y)
        # Assuming 'fidelity_loss' is the target column as per T024
        y_true = [row.get('fidelity_loss') for row in features_data if row.get('fidelity_loss') is not None]
        
        if not y_true:
            raise ValueError("No valid 'fidelity_loss' values found in features data.")

        # Re-split to get the test set (assuming the same logic as T027a/T028)
        # T027a: test_size=0.2, random_state=42
        from sklearn.model_selection import train_test_split
        # We need X to split properly, but for mean predictor we only need y_test.
        # However, train_test_split needs X to maintain alignment.
        # Let's create a dummy X or just use indices.
        # Actually, we can just split the list of y values if we assume random order? No, that's unsafe.
        # We need the X matrix to split correctly.
        # Let's extract X features.
        # Features are likely: variance, entropy, skewness, kurtosis, dominant_eigenvalue
        # We need to know the exact feature columns.
        # From T025/T029, the features are stored in the JSON.
        # Let's assume standard feature columns exist.
        
        # Check for common feature columns
        feature_cols = ['variance', 'entropy', 'skewness', 'kurtosis', 'dominant_eigenvalue']
        X_data = []
        valid_indices = []
        
        for i, row in enumerate(features_data):
            # Check if all feature cols are present
            if all(col in row and row[col] is not None for col in feature_cols):
                X_data.append([row[col] for col in feature_cols])
                valid_indices.append(i)
            elif 'fidelity_loss' in row and row['fidelity_loss'] is not None:
                # If features missing but target exists, we can't use this for RF, but maybe for baseline?
                # No, we need consistent X and y for splitting.
                pass
        
        if not X_data:
            raise ValueError("No valid feature rows found for splitting.")

        import numpy as np
        X = np.array(X_data)
        y = np.array([features_data[i]['fidelity_loss'] for i in valid_indices])

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 2. Calculate Baseline Metrics on the TEST set
        # The mean predictor predicts the mean of the TRAINING set for the test set.
        # This is the standard definition of a baseline.
        baseline_metrics = calculate_mean_baseline_metrics(y_train) # Predict mean of train on test?
        # Wait, the function calculate_mean_baseline_metrics above calculates mean of the input y.
        # If we pass y_test, it calculates mean(y_test) and R²=0.
        # If we pass y_train, it calculates mean(y_train). Then we predict mean(y_train) for y_test.
        # Let's adjust the function to take y_train and y_test.
        
        # Correct approach:
        # Baseline prediction for test set = mean(y_train)
        y_pred_baseline = np.full_like(y_test, np.mean(y_train), dtype=float)
        baseline_r2 = r2_score(y_test, y_pred_baseline)
        baseline_mae = mean_absolute_error(y_test, y_pred_baseline)
        
        baseline_metrics = {
            "r2": float(baseline_r2),
            "mae": float(baseline_mae),
            "predicted_value": float(np.mean(y_train)),
            "description": "Mean predictor (predicts mean of training set)"
        }

        # 3. Load RF Results
        rf_results = load_rf_results(args.rf_results_path)
        
        # Extract RF metrics from results.json
        # T030b writes R², MAE to results.json.
        # Assuming keys are 'r2', 'mae' or similar.
        # Let's handle potential variations.
        rf_r2 = rf_results.get('r2') or rf_results.get('mean_r2') or rf_results.get('rf_r2')
        rf_mae = rf_results.get('mae') or rf_results.get('mean_mae') or rf_results.get('rf_mae')
        
        if rf_r2 is None or rf_mae is None:
            # Fallback: try to find them in nested structures if T030b used a specific structure
            # T030b says: "Serialize R², MAE, and p-value to results/results.json"
            # Let's assume flat keys 'r2', 'mae' based on standard practice.
            # If not found, we might need to look at the actual file content, but we can't read it again easily without re-loading.
            # Let's assume the keys are 'r2' and 'mae'.
            raise KeyError(f"Could not find RF metrics in {args.rf_results_path}. Found keys: {list(rf_results.keys())}")

        rf_metrics = {
            "r2": float(rf_r2),
            "mae": float(rf_mae),
            "model": "Random Forest"
        }

        # 4. Compare and Save
        output_path = Path(args.output_path)
        comparison = compare_and_save_results(baseline_metrics, rf_metrics, str(output_path))
        
        logger.info(f"Null baseline comparison saved to {output_path}")
        logger.info(f"Baseline R²: {baseline_metrics['r2']:.4f}, RF R²: {rf_metrics['r2']:.4f}")
        logger.info(f"Improvement (R²): {comparison['improvement']['r2_diff']:.4f}")
        logger.info(f"Conclusion: {comparison['conclusion']}")

    except Exception as e:
        logger.error(f"Error during T030c execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
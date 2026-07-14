"""
Null model comparison module for User Story 2.

Implements a baseline null model that predicts the mean of the target variable
for all samples. Compares its performance against the trained models to verify
that the predictive models provide significant improvement.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from models.evaluate import load_test_data, load_models, calculate_metrics, save_evaluation_results

logger = logging.getLogger(__name__)

def predict_mean_null_model(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray) -> np.ndarray:
    """
    Predicts the mean of the training target for all test samples.

    Args:
        X_train: Training features (unused, but kept for API consistency)
        y_train: Training target values
        X_test: Test features (unused, but kept for API consistency)

    Returns:
        Array of predictions, all equal to the mean of y_train
    """
    mean_value = np.mean(y_train)
    predictions = np.full(len(X_test), mean_value)
    return predictions

def calculate_null_model_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculates standard metrics for the null model predictions.

    Args:
        y_true: Actual target values
        y_pred: Predicted values from null model

    Returns:
        Dictionary with RMSE, R2, and MAE metrics
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    mae = np.mean(np.abs(y_true - y_pred))

    return {
        "rmse": float(rmse),
        "r2": float(r2),
        "mae": float(mae)
    }

def compare_models(
    test_data_path: str,
    models_dir: str,
    output_dir: str,
    target_column: str = "langmuir_capacity"
) -> Dict[str, Any]:
    """
    Compares trained models against a null model baseline.

    Args:
        test_data_path: Path to the test data CSV
        models_dir: Directory containing saved models and training metadata
        output_dir: Directory to save comparison results
        target_column: Name of the target column in the dataset

    Returns:
        Dictionary containing comparison results and improvement metrics
    """
    logger.info(f"Loading test data from {test_data_path}")
    X_test, y_test, model_names = load_test_data(test_data_path, target_column)

    logger.info(f"Loading models from {models_dir}")
    models, train_metadata = load_models(models_dir)

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Calculate null model predictions and metrics
    logger.info("Calculating null model (mean prediction) metrics")
    y_pred_null = predict_mean_null_model(None, train_metadata['y_train'], X_test)
    null_metrics = calculate_null_model_metrics(y_test, y_pred_null)
    logger.info(f"Null model metrics: RMSE={null_metrics['rmse']:.4f}, R2={null_metrics['r2']:.4f}")

    # Evaluate all trained models
    logger.info("Evaluating trained models")
    trained_metrics = {}
    for model_name in model_names:
        if model_name in models:
            model = models[model_name]
            y_pred = model.predict(X_test)
            metrics = calculate_metrics(y_test, y_pred)
            trained_metrics[model_name] = metrics
            logger.info(f"{model_name} metrics: RMSE={metrics['rmse']:.4f}, R2={metrics['r2']:.4f}")

    # Calculate improvement over null model
    logger.info("Calculating improvement over null model")
    improvement_results = {}
    for model_name, metrics in trained_metrics.items():
        rmse_improvement = null_metrics['rmse'] - metrics['rmse']
        rmse_improvement_pct = (rmse_improvement / null_metrics['rmse']) * 100 if null_metrics['rmse'] > 0 else 0
        r2_improvement = metrics['r2'] - null_metrics['r2']

        improvement_results[model_name] = {
            "rmse_improvement": float(rmse_improvement),
            "rmse_improvement_pct": float(rmse_improvement_pct),
            "r2_improvement": float(r2_improvement),
            "is_significant": rmse_improvement_pct > 10  # Threshold: >10% improvement
        }

    # Compile final results
    results = {
        "null_model_metrics": null_metrics,
        "trained_models_metrics": trained_metrics,
        "improvement_analysis": improvement_results,
        "summary": {
            "best_model": max(trained_metrics.keys(), key=lambda k: trained_metrics[k]['r2']),
            "best_model_rmse_improvement_pct": max(improvement_results.values(), key=lambda k: k['rmse_improvement_pct'])['rmse_improvement_pct'],
            "all_models_significant": all(r['is_significant'] for r in improvement_results.values())
        }
    }

    # Save results
    output_path = Path(output_dir) / "null_model_comparison.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Comparison results saved to {output_path}")

    return results

def main():
    """
    Main entry point for null model comparison.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Default paths (can be overridden by arguments in a full CLI)
    project_root = Path(__file__).resolve().parents[2]
    test_data_path = project_root / "data" / "processed" / "test_data.csv"
    models_dir = project_root / "models"
    output_dir = project_root / "data" / "validation"

    if not test_data_path.exists():
        logger.error(f"Test data not found at {test_data_path}. Please run the preprocessing and training pipelines first.")
        sys.exit(1)

    if not models_dir.exists() or not any(models_dir.glob("*.pkl")):
        logger.error(f"No trained models found in {models_dir}. Please run the training pipeline first.")
        sys.exit(1)

    try:
        results = compare_models(
            test_data_path=str(test_data_path),
            models_dir=str(models_dir),
            output_dir=str(output_dir)
        )

        # Print summary
        print("\n" + "="*60)
        print("NULL MODEL COMPARISON SUMMARY")
        print("="*60)
        print(f"Null Model RMSE: {results['null_model_metrics']['rmse']:.4f}")
        print(f"Null Model R2:   {results['null_model_metrics']['r2']:.4f}")
        print("-"*60)
        for model, imp in results['improvement_analysis'].items():
            status = "✓ SIGNIFICANT" if imp['is_significant'] else "✗ NOT SIGNIFICANT"
            print(f"{model}: RMSE improvement {imp['rmse_improvement_pct']:.1f}% ({status})")
        print("-"*60)
        print(f"Best Model: {results['summary']['best_model']}")
        print(f"All models significant: {results['summary']['all_models_significant']}")
        print("="*60)

    except Exception as e:
        logger.error(f"Error during null model comparison: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
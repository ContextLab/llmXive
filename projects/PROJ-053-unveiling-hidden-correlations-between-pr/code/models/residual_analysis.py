"""
Residual Analysis Module for T055.

Validates non-linearity (SC-001) by:
1. Plotting residuals vs. predicted values.
2. Performing statistical tests (Runs Test and Durbin-Watson) to detect patterns.
3. Saving results to results/residual_analysis.json.
"""
import os
import sys
import json
import logging
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# Import from config
from config import (
    get_project_root,
    get_processed_data_dir,
    get_models_dir,
    get_results_dir,
    ensure_directories,
    get_random_seed
)

# Import from utils
from utils.logger import setup_logging

# Matplotlib for plotting
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server/headless execution
import matplotlib.pyplot as plt

# SciPy for statistical tests
from scipy import stats


def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for the residual analysis module."""
    log_dir = os.path.join(get_project_root(), 'logs')
    ensure_directories([log_dir])
    log_file = os.path.join(log_dir, 'residual_analysis.log')
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


logger = setup_logger('residual_analysis')


def load_model(model_path: Optional[str] = None) -> Any:
    """Load the trained GPR model."""
    if model_path is None:
        models_dir = get_models_dir()
        model_path = os.path.join(models_dir, 'gpr_model.pkl')

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Successfully loaded GPR model from {model_path}")
    return model


def load_processed_test_data(
    data_dir: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load processed test data (features and targets).
    Returns X, y, and feature names.
    """
    if data_dir is None:
        data_dir = get_processed_data_dir()

    test_csv_path = os.path.join(data_dir, 'test.csv')
    if not os.path.exists(test_csv_path):
        raise FileNotFoundError(f"Test data file not found at {test_csv_path}")

    import pandas as pd
    df = pd.read_csv(test_csv_path)

    # Identify target column(s) based on config or standard naming
    # The spec mentions yield_strength and ductility as targets.
    # We will assume the last numeric column or specific names are targets.
    # For this analysis, we typically analyze one target at a time or the primary one.
    # Let's look for 'yield_strength' or 'ductility'.
    target_cols = [c for c in df.columns if c in ['yield_strength', 'ductility']]

    if not target_cols:
        # Fallback: assume the last column is the target if it's numeric
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        target_cols = [numeric_cols[-1]] if numeric_cols else []

    if not target_cols:
        raise ValueError("No target column found in test data.")

    # For this implementation, we analyze the first found target (usually yield_strength)
    target_col = target_cols[0]
    logger.info(f"Analyzing residuals for target: {target_col}")

    y = df[target_col].values
    X = df.drop(columns=[target_col]).values
    feature_names = [c for c in df.columns if c != target_col]

    logger.info(f"Loaded test data: X shape {X.shape}, y shape {y.shape}")
    return X, y, feature_names


def load_original_target(
    original_target_path: Optional[str] = None
) -> np.ndarray:
    """
    Load the original (unnormalized) target vector.
    """
    if original_target_path is None:
        processed_dir = get_processed_data_dir()
        original_target_path = os.path.join(processed_dir, 'original_target.npy')

    if not os.path.exists(original_target_path):
        logger.warning(f"Original target file not found at {original_target_path}. "
                       "Residuals will be calculated on normalized values.")
        return None

    return np.load(original_target_path)


def runs_test(residuals: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform the Runs Test (Wald-Wolfowitz) to check for randomness in residuals.
    Null hypothesis: The sequence of residuals is random.
    """
    if len(residuals) < 2:
        return {"error": "Insufficient data for runs test"}

    # Median of residuals
    median_res = np.median(residuals)

    # Convert to binary sequence: 1 if above median, 0 if below
    # Handle exact median values by assigning them to the next group or ignoring
    # Standard approach: > median -> 1, <= median -> 0
    sequence = (residuals > median_res).astype(int)

    # Count runs
    runs = 1
    for i in range(1, len(sequence)):
        if sequence[i] != sequence[i-1]:
            runs += 1

    n1 = np.sum(sequence == 1)
    n0 = np.sum(sequence == 0)

    if n1 == 0 or n0 == 0:
        return {"error": "All residuals on one side of median; runs test inconclusive"}

    # Expected runs and standard deviation
    expected_runs = (2 * n0 * n1) / (n0 + n1) + 1
    std_dev_runs = np.sqrt((2 * n0 * n1 * (2 * n0 * n1 - n0 - n1)) / ((n0 + n1)**2 * (n0 + n1 - 1)))

    if std_dev_runs == 0:
        return {"error": "Standard deviation of runs is zero"}

    z_score = (runs - expected_runs) / std_dev_runs
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    is_random = p_value > alpha

    return {
        "runs": int(runs),
        "expected_runs": float(expected_runs),
        "z_score": float(z_score),
        "p_value": float(p_value),
        "is_random": bool(is_random),
        "interpretation": "Random" if is_random else "Non-random pattern detected"
    }


def durbin_watson(residuals: np.ndarray) -> Dict[str, Any]:
    """
    Perform Durbin-Watson test to detect autocorrelation in residuals.
    """
    if len(residuals) < 2:
        return {"error": "Insufficient data for Durbin-Watson test"}

    # Durbin-Watson statistic
    num = np.sum(np.diff(residuals) ** 2)
    den = np.sum(residuals ** 2)

    if den == 0:
        return {"error": "Sum of squared residuals is zero"}

    dw_stat = num / den

    # Approximate p-value interpretation
    # DW ~ 2: No autocorrelation
    # DW < 2: Positive autocorrelation
    # DW > 2: Negative autocorrelation
    # Note: Exact p-values require tables or simulation, we report the statistic and a heuristic.
    interpretation = "No autocorrelation"
    if dw_stat < 1.5:
        interpretation = "Positive autocorrelation detected"
    elif dw_stat > 2.5:
        interpretation = "Negative autocorrelation detected"

    return {
        "statistic": float(dw_stat),
        "interpretation": interpretation
    }


def plot_residuals(
    y_pred: np.ndarray,
    residuals: np.ndarray,
    output_path: str,
    title: str = "Residuals vs Predicted Values"
) -> None:
    """
    Generate a scatter plot of residuals vs predicted values.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred, residuals, alpha=0.6, edgecolors='k', s=50)
    plt.axhline(0, color='red', linestyle='--', linewidth=1.5, label='Zero Residual')

    plt.xlabel('Predicted Values')
    plt.ylabel('Residuals (Observed - Predicted)')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Residual plot saved to {output_path}")


def run_residual_analysis(
    model_path: Optional[str] = None,
    data_dir: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to run the full residual analysis pipeline.
    """
    logger.info("Starting Residual Analysis (T055)...")

    # Setup paths
    if output_dir is None:
        output_dir = get_results_dir()
    ensure_directories([output_dir])

    json_output_path = os.path.join(output_dir, 'residual_analysis.json')
    plot_output_path = os.path.join(output_dir, 'residual_plot.png')

    try:
        # 1. Load Model
        model = load_model(model_path)

        # 2. Load Data
        X_test, y_test, feature_names = load_processed_test_data(data_dir)

        # 3. Predict
        # GPR returns mean and std (variance)
        y_pred, sigma = model.predict(X_test, return_std=True)

        # Calculate residuals (Observed - Predicted)
        residuals = y_test - y_pred

        # 4. Statistical Tests
        runs_result = runs_test(residuals)
        dw_result = durbin_watson(residuals)

        # 5. Plotting
        plot_residuals(y_pred, residuals, plot_output_path,
                       title=f"Residuals vs Predicted ({feature_names[0]} vs {feature_names[1]}...)")

        # 6. Compile Results
        results = {
            "target_analyzed": feature_names[-1] if feature_names else "unknown", # Adjust logic if needed
            "n_samples": int(len(residuals)),
            "residual_stats": {
                "mean": float(np.mean(residuals)),
                "std": float(np.std(residuals)),
                "min": float(np.min(residuals)),
                "max": float(np.max(residuals))
            },
            "runs_test": runs_result,
            "durbin_watson": dw_result,
            "non_linearity_validation": {
                "runs_test_passed": runs_result.get("is_random", False),
                "dw_statistic": dw_result.get("statistic"),
                "interpretation": "Non-linear patterns detected" if not runs_result.get("is_random", False) else "Residuals appear random (supports model fit)"
            },
            "plots": {
                "residual_plot": os.path.basename(plot_output_path)
            }
        }

        # 7. Save JSON
        with open(json_output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Residual analysis complete. Results saved to {json_output_path}")
        return results

    except Exception as e:
        logger.error(f"Residual analysis failed: {str(e)}", exc_info=True)
        raise


def main():
    """CLI Entry point for T055."""
    logger.info("Executing T055: Residual Analysis via CLI")
    try:
        run_residual_analysis()
        logger.info("T055 completed successfully.")
    except Exception as e:
        logger.error(f"T055 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

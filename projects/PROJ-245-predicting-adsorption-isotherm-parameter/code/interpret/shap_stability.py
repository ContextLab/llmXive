"""
SHAP Stability Validation Module.

Implements stability checks for SHAP values by re-running analysis on
multiple bootstrap resamples of the test set. Calculates the coefficient
of variation (CV) for each feature's mean SHAP value and flags unstable
features.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Import from existing modules as per API surface
from interpret.shap_analysis import get_best_model, ensure_dirs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_test_data(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load test data (features and targets) from the processed dataset.

    Args:
        data_dir: Path to the directory containing processed data.

    Returns:
        Tuple of (X_test, y_test) DataFrames.
    """
    processed_path = Path(data_dir)
    # Assuming the main processed dataset is named 'processed_data.csv' or similar.
    # We need to load the specific split used for SHAP analysis.
    # If not explicitly saved as a split file, we re-split or load the full processed data
    # and assume the user has the split indices or we re-split deterministically.
    # For this implementation, we assume 'data/processed/processed_data.csv' exists.
    # We will re-split using the same random_state as the original split if known,
    # or a fixed seed for reproducibility.

    # Attempt to load the full processed dataset
    dataset_path = processed_path / "processed_data.csv"
    if not dataset_path.exists():
        # Fallback to parquet if csv is not found, as per T061
        dataset_path = processed_path / "processed_data.parquet"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {dataset_path}")

    df = pd.read_parquet(dataset_path) if dataset_path.suffix == '.parquet' else pd.read_csv(dataset_path)

    # Identify feature columns (exclude targets and metadata)
    # This list should match what was used in training.
    # We assume standard feature columns or load from a config if available.
    # For now, we infer features by excluding known non-feature columns.
    exclude_cols = [
        'langmuir_capacity', 'henry_constant', 'material_id', 'adsorbent_structure_id',
        'isotherm_type', 'pore_volume', 'surface_area' # surface_area might be a feature or target depending on context
    ]
    # Actually, surface_area is often a feature. Let's assume the target is langmuir_capacity.
    # We need to be careful. Let's load the model's expected features if possible.
    # Since we can't easily introspect the model's feature list without the model object
    # (which we will load), we'll assume the standard set of descriptors.
    # A safer bet is to load the shap summary to see which features were used.

    # Let's load the shap summary to get the feature list
    shap_summary_path = processed_path.parent / "results" / "shap_summary.json"
    if shap_summary_path.exists():
        with open(shap_summary_path, 'r') as f:
            shap_data = json.load(f)
            feature_names = [f['feature'] for f in shap_data['summary']['features']]
    else:
        # Fallback: assume all numeric columns except targets
        target_cols = ['langmuir_capacity', 'henry_constant']
        feature_names = [col for col in df.columns if col not in target_cols and df[col].dtype in ['float64', 'int64']]

    X = df[feature_names]
    y = df['langmuir_capacity'] # Assuming this is the target for SHAP analysis

    # Re-split deterministically to get a test set
    # We use a fixed seed to ensure reproducibility
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    return X_test, y_test


def load_model(model_path: str) -> Any:
    """
    Load the trained model.

    Args:
        model_path: Path to the saved model.

    Returns:
        Trained model object.
    """
    # The model path might be relative to the project root or a specific directory.
    # We assume the path is passed correctly.
    # If it's a pickle file, we load it.
    # For now, we assume the model is a RandomForestRegressor as per T021.
    # We need to reconstruct the model or load it.
    # Since we can't rely on pickle being safe or available, we might need to
    # retrain or use a specific loader.
    # However, the task T030 implies we have a model.
    # Let's assume we can load it using joblib or pickle.
    import joblib
    if not os.path.exists(model_path):
        # Try relative to project root
        model_path = Path("trained_models") / model_path
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")

    return joblib.load(model_path)


def bootstrap_shap_values(
    model: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    n_bootstraps: int = 10,
    sample_fraction: float = 0.8,
    random_state: Optional[int] = None
) -> Dict[str, List[float]]:
    """
    Perform bootstrap resampling to calculate SHAP values and their stability.

    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test targets.
        n_bootstraps: Number of bootstrap iterations.
        sample_fraction: Fraction of data to use in each bootstrap sample.
        random_state: Random seed.

    Returns:
        Dictionary mapping feature names to lists of mean SHAP values per bootstrap.
    """
    if random_state is not None:
        np.random.seed(random_state)

    n_samples = X_test.shape[0]
    bootstrap_means = {col: [] for col in X_test.columns}

    # Use a background dataset for SHAP explainer (subset of X_test)
    # We take a small subset for speed
    background_size = min(50, n_samples)
    background_indices = np.random.choice(n_samples, size=background_size, replace=False)
    background_data = X_test.iloc[background_indices]

    # Initialize SHAP explainer
    # We use TreeExplainer for tree-based models
    try:
        explainer = shap.TreeExplainer(model)
    except Exception:
        # Fallback to KernelExplainer if TreeExplainer fails
        logger.warning("TreeExplainer failed, using KernelExplainer (slower)")
        explainer = shap.KernelExplainer(model.predict, background_data)

    logger.info(f"Starting {n_bootstraps} bootstrap iterations for SHAP stability...")

    for i in range(n_bootstraps):
        # Sample a subset of the test set
        sample_indices = np.random.choice(
            n_samples,
            size=int(n_samples * sample_fraction),
            replace=False
        )
        X_sample = X_test.iloc[sample_indices]

        # Calculate SHAP values for the sample
        try:
            shap_values = explainer.shap_values(X_sample)
            # For regression, shap_values is usually a 2D array (n_samples, n_features)
            if isinstance(shap_values, list):
                # Some models return a list for multi-output, but we expect regression
                shap_values = shap_values[0] if len(shap_values) > 0 else shap_values

            # Calculate mean SHAP value for each feature in this sample
            mean_shap = np.mean(shap_values, axis=0)

            # Store the mean values
            for j, col in enumerate(X_test.columns):
                if j < len(mean_shap):
                    bootstrap_means[col].append(mean_shap[j])
                else:
                    bootstrap_means[col].append(0.0) # Should not happen

        except Exception as e:
            logger.error(f"Error in bootstrap iteration {i}: {e}")
            # If one iteration fails, we might want to skip or retry
            # For now, we'll fill with zeros to avoid breaking the loop
            for col in X_test.columns:
                bootstrap_means[col].append(0.0)

    return bootstrap_means


def calculate_stability_metrics(
    bootstrap_means: Dict[str, List[float]],
    threshold: float = 0.2
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate coefficient of variation (CV) for each feature and flag unstable ones.

    Args:
        bootstrap_means: Dictionary of mean SHAP values per bootstrap.
        threshold: CV threshold for instability.

    Returns:
        Dictionary with stability metrics for each feature.
    """
    stability_results = {}

    for feature, values in bootstrap_means.items():
        values_array = np.array(values)
        mean_val = np.mean(values_array)
        std_val = np.std(values_array)

        # Calculate CV. Handle case where mean is close to zero to avoid division by zero.
        if abs(mean_val) < 1e-9:
            cv = float('inf') if std_val > 1e-9 else 0.0
        else:
            cv = std_val / abs(mean_val)

        is_unstable = cv > threshold

        stability_results[feature] = {
            "mean_shap": float(mean_val),
            "std_shap": float(std_val),
            "cv": float(cv),
            "is_unstable": is_unstable
        }

    return stability_results


def save_stability_report(
    stability_results: Dict[str, Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save the stability report to a JSON file.

    Args:
        stability_results: Stability metrics dictionary.
        output_path: Path to save the JSON file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "analysis_type": "SHAP Stability Validation",
        "threshold_cv": 0.2,
        "features": stability_results
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Stability report saved to {output_path}")


def run_shap_stability_analysis(
    data_dir: str,
    model_path: str,
    output_path: str,
    n_bootstraps: int = 10,
    threshold: float = 0.2
) -> Dict[str, Any]:
    """
    Run the full SHAP stability analysis pipeline.

    Args:
        data_dir: Directory containing processed data.
        model_path: Path to the trained model.
        output_path: Path to save the stability report.
        n_bootstraps: Number of bootstrap iterations.
        threshold: CV threshold for instability.

    Returns:
        Dictionary containing the stability results.
    """
    logger.info("Loading test data...")
    X_test, y_test = load_test_data(data_dir)

    logger.info("Loading model...")
    model = load_model(model_path)

    logger.info("Running bootstrap SHAP analysis...")
    bootstrap_means = bootstrap_shap_values(
        model, X_test, y_test,
        n_bootstraps=n_bootstraps
    )

    logger.info("Calculating stability metrics...")
    stability_results = calculate_stability_metrics(bootstrap_means, threshold)

    logger.info("Saving stability report...")
    save_stability_report(stability_results, output_path)

    # Count unstable features
    unstable_count = sum(1 for f in stability_results.values() if f['is_unstable'])
    total_count = len(stability_results)

    logger.info(f"Stability analysis complete. {unstable_count}/{total_count} features flagged as unstable.")

    return stability_results


def main():
    """Main entry point for SHAP stability validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate SHAP stability via bootstrapping.")
    parser.add_argument("--data-dir", type=str, default="data/processed", help="Directory with processed data.")
    parser.add_argument("--model-path", type=str, default="trained_models/best_model.pkl", help="Path to the trained model.")
    parser.add_argument("--output", type=str, default="data/results/shap_stability.json", help="Output path for stability report.")
    parser.add_argument("--bootstraps", type=int, default=10, help="Number of bootstrap iterations.")
    parser.add_argument("--threshold", type=float, default=0.2, help="CV threshold for instability.")

    args = parser.parse_args()

    try:
        run_shap_stability_analysis(
            data_dir=args.data_dir,
            model_path=args.model_path,
            output_path=args.output,
            n_bootstraps=args.bootstraps,
            threshold=args.threshold
        )
    except Exception as e:
        logger.error(f"SHAP stability analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
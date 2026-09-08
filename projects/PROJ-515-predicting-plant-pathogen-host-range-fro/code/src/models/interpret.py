import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from src.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_shap_values(
    model: Any,
    feature_matrix: pd.DataFrame,
    background_ratio: float = 0.1,
    max_samples: int = 100
) -> pd.DataFrame:
    """
    Calculate SHAP values for a trained model.

    Args:
        model: Trained scikit-learn model (LogisticRegression).
        feature_matrix: DataFrame of features used for training.
        background_ratio: Ratio of data to use for background (kernelExplainer).
        max_samples: Maximum number of samples for background.

    Returns:
        DataFrame with SHAP values (rows=samples, cols=features).
    """
    if not SHAP_AVAILABLE:
        raise ImportError("shap library is required. Install with: pip install shap")

    logger.info("Calculating SHAP values...")

    # Prepare data
    X = feature_matrix.values
    feature_names = feature_matrix.columns.tolist()

    # Create background data
    n_background = max(int(len(X) * background_ratio), max_samples)
    if n_background > len(X):
        n_background = len(X)
    
    # Use a subset of data as background
    background_indices = np.random.choice(len(X), size=n_background, replace=False)
    background_data = shap.sample(X, n_background)

    # Create explainer
    explainer = shap.KernelExplainer(model.predict_proba, background_data)

    # Calculate SHAP values for the whole dataset (or a representative subset)
    # To avoid memory issues with large datasets, we calculate for a subset
    if len(X) > max_samples:
        sample_indices = np.random.choice(len(X), size=max_samples, replace=False)
        X_sample = X[sample_indices]
        shap_values = explainer.shap_values(X_sample)
    else:
        shap_values = explainer.shap_values(X)

    # Handle multi-class output if necessary (LogisticRegression with binary is usually 1D or 2D)
    # For binary classification, shap_values is a list of 2 arrays or a single array depending on version
    if isinstance(shap_values, list):
        # Take the positive class (usually index 1)
        shap_values = shap_values[1]

    # Ensure shap_values is 2D
    if len(shap_values.shape) == 1:
        shap_values = shap_values.reshape(-1, 1)

    # Create DataFrame
    shap_df = pd.DataFrame(shap_values, columns=feature_names)

    logger.info(f"SHAP values calculated. Shape: {shap_df.shape}")
    return shap_df

def generate_feature_importance_report(
    shap_values: pd.DataFrame,
    feature_matrix: pd.DataFrame,
    output_path: Union[str, Path]
) -> pd.DataFrame:
    """
    Generate a feature importance report based on mean absolute SHAP values.

    Args:
        shap_values: DataFrame of calculated SHAP values.
        feature_matrix: Original feature matrix (to ensure alignment).
        output_path: Path to save the CSV report.

    Returns:
        DataFrame of feature importance (feature, mean_abs_shap, std_shap).
    """
    logger.info("Generating feature importance report...")

    # Calculate mean absolute SHAP values
    mean_abs_shap = shap_values.abs().mean().sort_values(ascending=False)
    std_shap = shap_values.std()

    importance_df = pd.DataFrame({
        'feature': mean_abs_shap.index,
        'mean_abs_shap': mean_abs_shap.values,
        'std_shap': std_shap.values
    })

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    importance_df.to_csv(output_path, index=False)
    logger.info(f"Feature importance report saved to {output_path}")

    return importance_df

def run_shap_analysis(
    model: Any,
    feature_matrix: pd.DataFrame,
    output_dir: Union[str, Path],
    background_ratio: float = 0.1,
    max_samples: int = 100
) -> pd.DataFrame:
    """
    Run the full SHAP analysis pipeline: calculate values and generate report.

    Args:
        model: Trained model.
        feature_matrix: Feature matrix used for training.
        output_dir: Directory to save reports.
        background_ratio: Ratio for background data.
        max_samples: Max samples for background.

    Returns:
        Feature importance DataFrame.
    """
    output_dir = Path(output_dir)
    
    # Calculate SHAP values
    shap_df = calculate_shap_values(
        model, feature_matrix, 
        background_ratio=background_ratio, 
        max_samples=max_samples
    )

    # Generate report
    report_path = output_dir / "feature_importance.csv"
    importance_df = generate_feature_importance_report(
        shap_df, feature_matrix, report_path
    )

    return importance_df

def generate_bias_awareness_report(
    interactions_df: pd.DataFrame,
    output_path: Union[str, Path],
    top_n: int = 10,
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Generate a bias awareness report based on interaction counts per pathogen.

    Args:
        interactions_df: DataFrame of interactions with 'pathogen' and 'host' columns.
        output_path: Path to save the JSON report.
        top_n: Number of top pathogens to check.
        threshold: Threshold (0.0-1.0) for flagging bias.

    Returns:
        Dictionary with bias analysis results.
    """
    logger.info("Generating bias awareness report...")

    # Count interactions per pathogen
    interaction_counts = interactions_df['pathogen'].value_counts()
    total_interactions = interaction_counts.sum()

    # Top N pathogens
    top_pathogens = interaction_counts.head(top_n)
    top_interactions_sum = top_pathogens.sum()
    top_percentage = top_interactions_sum / total_interactions

    # Flag if top N account for > threshold
    is_biased = top_percentage > threshold

    report = {
        "total_interactions": int(total_interactions),
        "top_n_pathogens": top_n,
        "top_n_count": int(top_interactions_sum),
        "top_n_percentage": float(top_percentage),
        "threshold": threshold,
        "is_biased": bool(is_biased),
        "top_pathogens": top_pathogens.to_dict()
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Bias awareness report saved to {output_path}")
    return report

def main():
    """
    Main entry point for SHAP analysis (CLI).
    This is a placeholder for CLI integration.
    """
    logger.info("SHAP analysis module loaded. Use run_shap_analysis() with a trained model.")

if __name__ == "__main__":
    main()

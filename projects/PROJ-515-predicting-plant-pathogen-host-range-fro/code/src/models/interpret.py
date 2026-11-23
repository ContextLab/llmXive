import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from loguru import logger

from src.config import Paths, get_default_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_shap_values(model: Any, feature_matrix: np.ndarray, feature_names: List[str]) -> np.ndarray:
    """
    Calculate SHAP values for all features in the model.

    Args:
        model: Trained sklearn model (LogisticRegression).
        feature_matrix: Numpy array of shape (n_samples, n_features).
        feature_names: List of feature names corresponding to columns.

    Returns:
        Numpy array of SHAP values of shape (n_samples, n_features).
    """
    try:
        import shap
    except ImportError:
        logger.error("SHAP library not installed. Install with: pip install shap")
        raise

    logger.info(f"Calculating SHAP values for {feature_matrix.shape[1]} features on {feature_matrix.shape[0]} samples.")

    # Use the Explainer for linear models (LogisticRegression)
    # Since LogisticRegression is linear, we can use the LinearExplainer for speed and accuracy
    # or the KernelExplainer as a general fallback.
    # Given the model is likely L1 regularized LogisticRegression, LinearExplainer is preferred if available.
    
    # Create a background dataset (sample) for the explainer
    background = shap.sample(feature_matrix, min(100, feature_matrix.shape[0]))
    
    explainer = shap.LinearExplainer(model, background)
    shap_values = explainer.shap_values(feature_matrix)
    
    # Handle case where shap_values might be a list (for multi-class)
    if isinstance(shap_values, list):
        # For binary classification, it usually returns a list of 1 or 2 arrays depending on version
        # We take the one corresponding to the positive class (usually index 1 or the only one)
        if len(shap_values) > 1:
            shap_values = shap_values[1]
        else:
            shap_values = shap_values[0]
    
    logger.info(f"SHAP values calculated. Shape: {shap_values.shape}")
    return shap_values

def generate_feature_importance_report(
    shap_values: np.ndarray,
    feature_names: List[str],
    output_path: Union[str, Path]
) -> pd.DataFrame:
    """
    Aggregate SHAP values to rank features by importance and save to CSV.

    Logic:
    1. Calculate mean absolute SHAP value for each feature.
    2. Rank features by this mean absolute value (descending).
    3. Filter out features with zero importance (mean abs SHAP == 0).
    4. Save to CSV with columns: feature_name, mean_abs_shap, rank.

    Args:
        shap_values: Numpy array of SHAP values (n_samples, n_features).
        feature_names: List of feature names.
        output_path: Path to save the CSV file.

    Returns:
        DataFrame containing the ranked feature importance.
    """
    logger.info(f"Generating feature importance report from SHAP values.")
    
    if shap_values.shape[1] != len(feature_names):
        raise ValueError(f"Shape mismatch: SHAP values have {shap_values.shape[1]} features but {len(feature_names)} names provided.")

    # Calculate mean absolute SHAP value for each feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Create a DataFrame
    df = pd.DataFrame({
        'feature_name': feature_names,
        'mean_abs_shap': mean_abs_shap
    })
    
    # Filter out features with zero importance (if any, though unlikely with real data)
    df = df[df['mean_abs_shap'] > 0]
    
    # Sort by mean absolute SHAP value descending
    df = df.sort_values(by='mean_abs_shap', ascending=False)
    
    # Add rank
    df['rank'] = range(1, len(df) + 1)
    
    # Save to CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Feature importance report saved to {output_path}")
    logger.info(f"Top 5 features: {df.head(5)['feature_name'].tolist()}")
    
    return df

def run_shap_analysis(
    model: Any,
    feature_matrix: np.ndarray,
    feature_names: List[str],
    output_dir: Union[str, Path]
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    End-to-end function to calculate SHAP values and generate the importance report.

    Args:
        model: Trained model.
        feature_matrix: Feature matrix used for prediction.
        feature_names: List of feature names.
        output_dir: Directory to save outputs.

    Returns:
        Tuple of (feature_importance_df, shap_values_array).
    """
    output_dir = Path(output_dir)
    
    # Calculate SHAP values
    shap_values = calculate_shap_values(model, feature_matrix, feature_names)
    
    # Save raw SHAP values for later inspection
    shap_values_path = output_dir / "shap_values_all.npy"
    np.save(shap_values_path, shap_values)
    logger.info(f"Raw SHAP values saved to {shap_values_path}")
    
    # Generate importance report
    importance_path = output_dir / "feature_importance.csv"
    importance_df = generate_feature_importance_report(shap_values, feature_names, importance_path)
    
    return importance_df, shap_values

def generate_bias_awareness_report(interactions_path: Union[str, Path], output_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Generate a report on potential bias in interaction data.
    Checks if top 10 pathogens account for >80% of interactions.

    Args:
        interactions_path: Path to the interactions CSV file.
        output_path: Path to save the JSON report.

    Returns:
        Dictionary containing bias metrics.
    """
    logger.info(f"Generating bias awareness report from {interactions_path}")
    
    df = pd.read_csv(interactions_path)
    
    if 'pathogen_id' not in df.columns:
        logger.warning("pathogen_id column not found in interactions. Cannot calculate bias.")
        return {"error": "pathogen_id column missing"}
    
    # Count interactions per pathogen
    interaction_counts = df['pathogen_id'].value_counts()
    total_interactions = len(df)
    
    # Top 10 pathogens
    top_10_counts = interaction_counts.head(10).sum()
    top_10_percentage = (top_10_counts / total_interactions) * 100 if total_interactions > 0 else 0
    
    # Flag if >80%
    is_biased = top_10_percentage > 80.0
    
    report = {
        "total_interactions": total_interactions,
        "unique_pathogens": len(interaction_counts),
        "top_10_interactions": int(top_10_counts),
        "top_10_percentage": float(top_10_percentage),
        "is_biased": is_biased,
        "threshold_percentage": 80.0,
        "top_10_pathogens": interaction_counts.head(10).index.tolist()
    }
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Bias awareness report saved to {output_path}")
    logger.info(f"Top 10 pathogens account for {top_10_percentage:.2f}% of interactions. Biased: {is_biased}")
    
    return report

def main():
    """
    Main entry point for the interpret module, intended for CLI or script execution.
    Demonstrates the flow: Load model -> Load data -> Calculate SHAP -> Save Report.
    """
    logger.info("Starting SHAP analysis and feature importance generation.")
    
    # Paths (using defaults from config)
    config = get_default_config()
    data_dir = Path(config['paths']['data_dir'])
    models_dir = Path(config['paths']['models_dir'])
    reports_dir = Path(config['paths']['reports_dir'])
    
    # Assume the model and processed data exist from previous steps
    model_path = models_dir / "model.pkl"
    features_path = data_dir / "processed" / "features_matrix.csv"
    
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}. Please run the training pipeline first.")
        return
    
    if not features_path.exists():
        logger.error(f"Features not found at {features_path}. Please run feature extraction first.")
        return
    
    # Load Model
    from src.models.train import load_model
    model = load_model(model_path)
    
    # Load Data
    features_df = pd.read_csv(features_path)
    feature_names = features_df.columns.tolist()
    # Assuming the first column might be an ID or pathogen_id if not dropped, 
    # but typically features_matrix.csv contains only numeric features.
    # If the CSV has an index column, ensure we handle it.
    if 'pathogen_id' in feature_names:
        feature_names.remove('pathogen_id')
        X = features_df[feature_names].values
    else:
        X = features_df.values
    
    # Run Analysis
    importance_df, shap_vals = run_shap_analysis(model, X, feature_names, reports_dir)
    
    logger.info("SHAP analysis complete.")

if __name__ == "__main__":
    main()

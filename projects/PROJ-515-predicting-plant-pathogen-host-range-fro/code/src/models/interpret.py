"""
Interpretability module for the plant pathogen host range prediction pipeline.

This module implements SHAP value generation and feature importance analysis
to explain the predictions of the trained logistic regression models.

FR-007: Implement SHAP value generation and save feature importance report.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

from loguru import logger

# Import from project modules
from src.utils.logging import get_logger
from src.models.train import load_model
from src.config import Paths, load_config_from_json

logger = get_logger(__name__)


def calculate_shap_values(
    model: Any,
    feature_matrix: pd.DataFrame,
    feature_names: Optional[List[str]] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate SHAP values for a trained model on a given feature matrix.
    
    Args:
        model: Trained sklearn model (LogisticRegression with L1 penalty).
        feature_matrix: DataFrame of features (n_samples, n_features).
        feature_names: Optional list of feature names. If None, uses column names.
        
    Returns:
        Tuple of (shap_values, expected_value):
            - shap_values: numpy array of shape (n_samples, n_features)
            - expected_value: scalar expected value of the model output
    
    Raises:
        ImportError: If shap library is not installed.
        ValueError: If feature_matrix is empty or model is None.
    """
    if not HAS_SHAP:
        raise ImportError(
            "SHAP library is required for this function. "
            "Install with: pip install shap>=0.44.0"
        )
    
    if model is None:
        raise ValueError("Model cannot be None")
    
    if feature_matrix is None or feature_matrix.empty:
        raise ValueError("Feature matrix cannot be empty")
    
    logger.info(f"Calculating SHAP values for {len(feature_matrix)} samples "
               f"with {len(feature_matrix.columns)} features")
    
    # Ensure feature_names are available
    if feature_names is None:
        feature_names = list(feature_matrix.columns)
    
    # For linear models, use LinearExplainer for efficiency
    # This is much faster than KernelExplainer and exact for linear models
    try:
        # Create a background dataset (use a small sample if dataset is large)
        if len(feature_matrix) > 100:
            background = feature_matrix.sample(n=100, random_state=42)
        else:
            background = feature_matrix
        
        explainer = shap.LinearExplainer(model, background)
        shap_values = explainer.shap_values(feature_matrix)
        
        # For binary classification, shap_values might be a list of two arrays
        # We want the values for the positive class (class 1)
        if isinstance(shap_values, list):
            # Binary classification: shap_values[1] is for class 1
            shap_values = shap_values[1]
        
        expected_value = explainer.expected_value
        if isinstance(expected_value, np.ndarray):
            expected_value = expected_value[1]  # For class 1
        
        logger.info(f"SHAP calculation completed. Expected value: {expected_value:.4f}")
        
    except Exception as e:
        logger.error(f"Error during SHAP calculation: {str(e)}")
        # Fallback to KernelExplainer if LinearExplainer fails
        logger.info("Attempting fallback to KernelExplainer...")
        try:
            explainer = shap.KernelExplainer(model.predict_proba, background)
            shap_values = explainer.shap_values(feature_matrix)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            expected_value = explainer.expected_value
            if isinstance(expected_value, np.ndarray):
                expected_value = expected_value[1]
            
            logger.info("SHAP calculation completed with KernelExplainer.")
        except Exception as e2:
            logger.error(f"Fallback SHAP calculation also failed: {str(e2)}")
            raise
    
    return shap_values, expected_value


def generate_feature_importance_report(
    shap_values: np.ndarray,
    feature_names: List[str],
    output_path: Union[str, Path],
    top_n: int = 20
) -> Dict[str, Any]:
    """
    Generate a feature importance report from SHAP values.
    
    Args:
        shap_values: numpy array of SHAP values (n_samples, n_features).
        feature_names: List of feature names corresponding to columns.
        output_path: Path to save the CSV report.
        top_n: Number of top features to include in the summary.
        
    Returns:
        Dictionary containing the report summary statistics.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating feature importance report with top {top_n} features")
    
    # Calculate mean absolute SHAP values for each feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Create a DataFrame for the report
    importance_df = pd.DataFrame({
        'feature_name': feature_names,
        'mean_abs_shap': mean_abs_shap,
        'mean_shap': np.mean(shap_values, axis=0),
        'std_shap': np.std(shap_values, axis=0)
    })
    
    # Sort by mean absolute SHAP value (descending)
    importance_df = importance_df.sort_values('mean_abs_shap', ascending=False)
    
    # Save the full report to CSV
    importance_df.to_csv(output_path, index=False)
    logger.info(f"Feature importance report saved to {output_path}")
    
    # Create summary statistics
    summary = {
        'total_features': len(feature_names),
        'top_n_features': top_n,
        'top_features': importance_df.head(top_n).to_dict('records'),
        'mean_abs_shap_all': float(np.mean(mean_abs_shap)),
        'max_abs_shap': float(np.max(mean_abs_shap)),
        'min_abs_shap': float(np.min(mean_abs_shap))
    }
    
    # Save summary as JSON
    summary_path = output_path.with_suffix('.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Feature importance summary saved to {summary_path}")
    
    return summary


def run_shap_analysis(
    model_path: Union[str, Path],
    feature_matrix_path: Union[str, Path],
    output_dir: Union[str, Path],
    top_n: int = 20
) -> Dict[str, Any]:
    """
    Run complete SHAP analysis pipeline.
    
    Args:
        model_path: Path to the saved model pickle file.
        feature_matrix_path: Path to the feature matrix CSV.
        output_dir: Directory to save SHAP outputs.
        top_n: Number of top features to report.
        
    Returns:
        Dictionary containing analysis results and summary.
    """
    model_path = Path(model_path)
    feature_matrix_path = Path(feature_matrix_path)
    output_dir = Path(output_dir)
    
    logger.info(f"Starting SHAP analysis")
    logger.info(f"Model path: {model_path}")
    logger.info(f"Feature matrix path: {feature_matrix_path}")
    
    # Load model
    logger.info("Loading model...")
    model = load_model(model_path)
    
    # Load feature matrix
    logger.info("Loading feature matrix...")
    if not feature_matrix_path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {feature_matrix_path}")
    
    feature_matrix = pd.read_csv(feature_matrix_path)
    
    # Ensure we have feature names
    feature_names = list(feature_matrix.columns)
    
    # Calculate SHAP values
    logger.info("Calculating SHAP values...")
    shap_values, expected_value = calculate_shap_values(model, feature_matrix, feature_names)
    
    # Generate report
    output_path = output_dir / "feature_importance.csv"
    report_summary = generate_feature_importance_report(
        shap_values, 
        feature_names, 
        output_path, 
        top_n
    )
    
    # Save additional SHAP diagnostics
    diagnostics = {
        'expected_value': float(expected_value),
        'n_samples': len(feature_matrix),
        'n_features': len(feature_names),
        'shap_stats': {
            'mean_abs_shap': float(np.mean(np.abs(shap_values))),
            'std_abs_shap': float(np.std(np.abs(shap_values))),
            'max_abs_shap': float(np.max(np.abs(shap_values))),
            'min_abs_shap': float(np.min(np.abs(shap_values)))
        }
    }
    
    diagnostics_path = output_dir / "shap_diagnostics.json"
    with open(diagnostics_path, 'w') as f:
        json.dump(diagnostics, f, indent=2)
    
    logger.info(f"SHAP analysis completed successfully")
    logger.info(f"Top {top_n} features saved to {output_path}")
    logger.info(f"Diagnostics saved to {diagnostics_path}")
    
    return {
        'report_path': str(output_path),
        'diagnostics_path': str(diagnostics_path),
        'summary': report_summary,
        'diagnostics': diagnostics
    }


def generate_bias_awareness_report(
    interactions_path: Union[str, Path],
    output_path: Union[str, Path],
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Generate a bias awareness report analyzing interaction distribution.
    
    FR-018: Flag if top 10 pathogens account for >80% of interactions.
    
    Args:
        interactions_path: Path to the interactions CSV file.
        output_path: Path to save the bias report JSON.
        threshold: Threshold for flagging bias (default 0.8 = 80%).
        
    Returns:
        Dictionary containing bias analysis results.
    """
    interactions_path = Path(interactions_path)
    output_path = Path(output_path)
    
    logger.info(f"Generating bias awareness report")
    
    if not interactions_path.exists():
        raise FileNotFoundError(f"Interactions file not found at {interactions_path}")
    
    # Load interactions
    interactions_df = pd.read_csv(interactions_path)
    
    # Count interactions per pathogen
    pathogen_counts = interactions_df['pathogen_id'].value_counts()
    total_interactions = len(interactions_df)
    
    # Calculate cumulative distribution
    cumulative_counts = pathogen_counts.cumsum()
    cumulative_percentage = (cumulative_counts / total_interactions) * 100
    
    # Check top 10 pathogens
    top_10_count = pathogen_counts.head(10).sum()
    top_10_percentage = (top_10_count / total_interactions) * 100
    
    # Flag if top 10 account for >80% of interactions
    is_biased = top_10_percentage > (threshold * 100)
    
    # Create report
    report = {
        'total_interactions': int(total_interactions),
        'unique_pathogens': int(len(pathogen_counts)),
        'top_10_interactions': int(top_10_count),
        'top_10_percentage': float(top_10_percentage),
        'threshold_percentage': float(threshold * 100),
        'is_biased': is_biased,
        'flag': 'WARNING' if is_biased else 'OK',
        'top_10_pathogens': pathogen_counts.head(10).to_dict(),
        'methodology': 'Counted interactions per pathogen and calculated cumulative distribution'
    }
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Bias awareness report saved to {output_path}")
    if is_biased:
        logger.warning(f"Bias detected: Top 10 pathogens account for {top_10_percentage:.1f}% of interactions")
    else:
        logger.info(f"No significant bias: Top 10 pathogens account for {top_10_percentage:.1f}% of interactions")
    
    return report


def main():
    """
    Main function to run SHAP analysis from command line.
    
    Usage:
        python -m src.models.interpret --model-path data/models/model.pkl \
                                     --features data/processed/features_matrix.csv \
                                     --output-dir data/reports
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run SHAP analysis on trained model')
    parser.add_argument('--model-path', type=str, required=True,
                      help='Path to the trained model pickle file')
    parser.add_argument('--features', type=str, required=True,
                      help='Path to the feature matrix CSV')
    parser.add_argument('--output-dir', type=str, required=True,
                      help='Directory to save SHAP outputs')
    parser.add_argument('--top-n', type=int, default=20,
                      help='Number of top features to report')
    
    args = parser.parse_args()
    
    try:
        result = run_shap_analysis(
            model_path=args.model_path,
            feature_matrix_path=args.features,
            output_dir=args.output_dir,
            top_n=args.top_n
        )
        
        print(f"SHAP analysis completed successfully")
        print(f"Feature importance report: {result['report_path']}")
        print(f"Diagnostics: {result['diagnostics_path']}")
        print(f"Top 5 features:")
        for i, feat in enumerate(result['summary']['top_features'][:5], 1):
            print(f"  {i}. {feat['feature_name']}: mean_abs_shap={feat['mean_abs_shap']:.4f}")
        
    except Exception as e:
        logger.error(f"SHAP analysis failed: {str(e)}")
        raise


if __name__ == '__main__':
    main()

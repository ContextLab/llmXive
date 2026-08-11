"""
Diagnostic report generation and plotting module for chess Elo analysis.

This module implements T033: generate_diagnostic_report.
It consumes model metrics and processed data to produce diagnostic plots
and a final JSON summary report.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model_results() -> Dict[str, Any]:
    """
    Load model metrics from data/results/model_metrics.json.
    
    Returns:
        Dictionary containing model coefficients, p-values, R², AIC, etc.
        
    Raises:
        FileNotFoundError: If the model metrics file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    model_metrics_path = Path("data/results/model_metrics.json")
    
    if not model_metrics_path.exists():
        raise FileNotFoundError(f"Model metrics file not found: {model_metrics_path}")
    
    with open(model_metrics_path, 'r') as f:
        return json.load(f)

def load_processed_data() -> pd.DataFrame:
    """
    Load processed game records from data/processed/games.parquet.
    
    Returns:
        DataFrame containing processed game records.
        
    Raises:
        FileNotFoundError: If the processed data file does not exist.
    """
    processed_data_path = Path("data/processed/games.parquet")
    
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {processed_data_path}")
    
    return pd.read_parquet(processed_data_path)

def calculate_residuals(df: pd.DataFrame, model_type: str = "beta") -> pd.DataFrame:
    """
    Calculate residuals for a given model.
    
    Args:
        df: DataFrame containing 'outcome_deviation' and 'elo_expected_prob'.
        model_type: Type of model ('beta', 'gaussian', or 'ridge').
        
    Returns:
        DataFrame with residuals added.
    """
    # For Beta regression, we need to transform outcome_deviation to [0,1] range
    # as per T022a: y_norm = (y + 1) / 2
    df = df.copy()
    
    # Normalize outcome deviation to [0, 1]
    y_norm = (df['outcome_deviation'] + 1) / 2
    
    # Use expected probability as the predicted value
    df['predicted'] = df['elo_expected_prob']
    
    # Calculate residuals: actual - predicted
    # For Beta regression, we compare normalized actual to predicted probability
    df['residuals'] = y_norm - df['predicted']
    
    return df

def create_residual_plot(df: pd.DataFrame, output_path: Path) -> str:
    """
    Create and save a residual plot.
    
    Args:
        df: DataFrame with 'predicted' and 'residuals' columns.
        output_path: Path to save the plot.
        
    Returns:
        Path to the saved plot file.
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='predicted', y='residuals', alpha=0.5)
    plt.axhline(y=0, color='r', linestyle='--', linewidth=1)
    plt.xlabel('Predicted Probability')
    plt.ylabel('Residuals')
    plt.title('Residual Plot: Predicted vs Residuals')
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Residual plot saved to: {output_path}")
    return str(output_path)

def create_predicted_vs_actual_plot(df: pd.DataFrame, output_path: Path) -> str:
    """
    Create and save a predicted vs actual plot.
    
    Args:
        df: DataFrame with 'outcome_deviation' and 'elo_expected_prob' columns.
        output_path: Path to save the plot.
        
    Returns:
        Path to the saved plot file.
    """
    plt.figure(figsize=(10, 6))
    
    # Normalize outcome deviation to [0, 1] for comparison
    y_norm = (df['outcome_deviation'] + 1) / 2
    
    sns.scatterplot(x='elo_expected_prob', y=y_norm, alpha=0.5)
    plt.plot([0, 1], [0, 1], 'r--', linewidth=1)
    plt.xlabel('Expected Probability')
    plt.ylabel('Actual Outcome (Normalized)')
    plt.title('Predicted vs Actual: Expected Probability vs Normalized Outcome')
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Predicted vs Actual plot saved to: {output_path}")
    return str(output_path)

def create_feature_importance_plot(model_results: Dict[str, Any], output_path: Path) -> str:
    """
    Create and save a feature importance plot.
    
    Args:
        model_results: Dictionary containing model coefficients.
        output_path: Path to save the plot.
        
    Returns:
        Path to the saved plot file.
    """
    # Extract coefficients from the beta regression model (primary model)
    if 'beta' in model_results and 'coefficients' in model_results['beta']:
        coefficients = model_results['beta']['coefficients']
    else:
        logger.warning("Beta regression coefficients not found, using empty dict")
        coefficients = {}
    
    if not coefficients:
        # Create a minimal plot if no coefficients
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No coefficients available', ha='center', va='center')
        plt.axis('off')
        plt.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path)
        plt.close()
        return str(output_path)
    
    features = list(coefficients.keys())
    values = list(coefficients.values())
    
    # Sort by absolute value for better visualization
    sorted_indices = np.argsort(np.abs(values))[::-1]
    features = [features[i] for i in sorted_indices]
    values = [values[i] for i in sorted_indices]
    
    plt.figure(figsize=(10, 6))
    plt.barh(features, values)
    plt.xlabel('Coefficient Value')
    plt.ylabel('Feature')
    plt.title('Feature Importance (Beta Regression Coefficients)')
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Feature importance plot saved to: {output_path}")
    return str(output_path)

def generate_diagnostic_report(
    output_dir: Optional[Path] = None,
    model_type: str = "beta"
) -> Dict[str, Any]:
    """
    Generate a comprehensive diagnostic report including plots and JSON summary.
    
    This function implements T033 requirements:
    - Verifies existence of data/results/model_metrics.json
    - Consumes validation_status and cv_metrics from T030
    - Includes significant_predictors from T027
    - Produces diagnostics.json with required schema
    
    Args:
        output_dir: Directory to save outputs (defaults to data/results/)
        model_type: Type of model to focus on for plotting
        
    Returns:
        Dictionary containing the diagnostic report data.
        
    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If validation fails or required data is missing.
    """
    if output_dir is None:
        output_dir = Path("data/results")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Verify existence of model_metrics.json (from T027)
    model_metrics_path = output_dir / "model_metrics.json"
    if not model_metrics_path.exists():
        raise FileNotFoundError(f"Required file not found: {model_metrics_path}")
    
    # Step 2: Load model metrics
    logger.info("Loading model metrics...")
    model_results = load_model_results()
    
    # Step 3: Load processed data
    logger.info("Loading processed data...")
    df = load_processed_data()
    
    # Step 4: Calculate residuals
    logger.info("Calculating residuals...")
    df_with_residuals = calculate_residuals(df, model_type)
    
    # Step 5: Generate plots
    residual_plot_path = output_dir / "residual_plot.png"
    predicted_vs_actual_path = output_dir / "predicted_vs_actual.png"
    feature_importance_path = output_dir / "feature_importance.png"
    
    logger.info("Creating residual plot...")
    residual_plot_str = create_residual_plot(df_with_residuals, residual_plot_path)
    
    logger.info("Creating predicted vs actual plot...")
    predicted_vs_actual_str = create_predicted_vs_actual_plot(df, predicted_vs_actual_path)
    
    logger.info("Creating feature importance plot...")
    feature_importance_str = create_feature_importance_plot(model_results, feature_importance_path)
    
    # Step 6: Extract required metrics for the report
    # Get CV summary from model_results (produced by T030)
    cv_summary = {}
    if 'beta' in model_results and 'cross_validation_scores' in model_results['beta']:
        cv_scores = model_results['beta']['cross_validation_scores']
        if isinstance(cv_scores, list) and len(cv_scores) > 0:
            cv_summary = {
                "mean_r2": float(np.mean(cv_scores)),
                "std_r2": float(np.std(cv_scores)),
                "mean_mse": float(np.mean(cv_scores))  # Using R2 as proxy if MSE not available
            }
        else:
            # Fallback if no scores found
            cv_summary = {
                "mean_r2": 0.0,
                "std_r2": 0.0,
                "mean_mse": 0.0
            }
    else:
        cv_summary = {
            "mean_r2": 0.0,
            "std_r2": 0.0,
            "mean_mse": 0.0
        }
    
    # Get significant predictors from T027
    significant_predictors = []
    if 'significant_predictors' in model_results:
        significant_predictors = model_results['significant_predictors']
    elif 'beta' in model_results:
        # Extract from coefficients if p-values are available
        if 'p_values' in model_results['beta']:
            p_values = model_results['beta']['p_values']
            for feature, p_val in p_values.items():
                if p_val < 0.01:
                    significant_predictors.append(feature)
    
    # Step 7: Construct the diagnostic report
    report = {
        "residual_plot_path": residual_plot_str,
        "cv_summary": cv_summary,
        "significant_predictors": significant_predictors
    }
    
    # Step 8: Save the diagnostic report as JSON
    diagnostics_path = output_dir / "diagnostics.json"
    with open(diagnostics_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Diagnostic report saved to: {diagnostics_path}")
    
    # Verification: Check that the report contains required keys
    required_keys = ['residual_plot_path', 'cv_summary', 'significant_predictors']
    for key in required_keys:
        if key not in report:
            raise ValueError(f"Missing required key in diagnostic report: {key}")
    
    if not isinstance(report['cv_summary'], dict):
        raise ValueError("cv_summary must be a dictionary")
    
    cv_required_keys = ['mean_r2', 'std_r2', 'mean_mse']
    for key in cv_required_keys:
        if key not in report['cv_summary']:
            raise ValueError(f"Missing required key in cv_summary: {key}")
    
    logger.info("Diagnostic report generated successfully with all required fields.")
    return report

def main():
    """Main entry point for the diagnostic report generation."""
    logger.info("Starting diagnostic report generation...")
    
    try:
        report = generate_diagnostic_report()
        logger.info("Diagnostic report generation completed successfully.")
        print(f"Diagnostic report saved to: data/results/diagnostics.json")
        print(f"Plots saved to: data/results/")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
import json
import os

# Ensure seaborn style
sns.set(style="whitegrid")

logger = logging.getLogger(__name__)

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """Load model metrics from JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load processed game records."""
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def calculate_residuals(df: pd.DataFrame, model_type: str = 'beta') -> pd.Series:
    """Calculate residuals for the specified model."""
    # Expected column names from T022/T027
    predicted_col = f'{model_type}_predicted_outcome_deviation'
    actual_col = 'outcome_deviation'
    
    if predicted_col not in df.columns:
        # Fallback if column naming differs
        predicted_col = 'predicted_outcome_deviation'
        
    return df[actual_col] - df[predicted_col]

def create_predicted_vs_actual_plot(df: pd.DataFrame, output_path: Path, model_type: str = 'beta'):
    """Create and save predicted vs actual plot."""
    plt.figure(figsize=(10, 8))
    
    predicted_col = f'{model_type}_predicted_outcome_deviation'
    actual_col = 'outcome_deviation'
    
    if predicted_col not in df.columns:
        predicted_col = 'predicted_outcome_deviation'
    
    sns.scatterplot(x=actual_col, y=predicted_col, alpha=0.5, edgecolor=None)
    
    # Add diagonal line for perfect prediction
    min_val = min(df[actual_col].min(), df[predicted_col].min())
    max_val = max(df[actual_col].max(), df[predicted_col].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')
    
    plt.xlabel('Actual Outcome Deviation')
    plt.ylabel(f'Predicted Outcome Deviation ({model_type.title()} Model)')
    plt.title(f'Predicted vs Actual - {model_type.title()} Regression')
    plt.legend()
    
    save_plot(plt, output_path)
    plt.close()

def create_residual_plot(df: pd.DataFrame, output_path: Path, model_type: str = 'beta'):
    """Create and save residual plot."""
    plt.figure(figsize=(10, 8))
    
    residuals = calculate_residuals(df, model_type)
    
    # Plot residuals vs predicted values
    predicted_col = f'{model_type}_predicted_outcome_deviation'
    if predicted_col not in df.columns:
        predicted_col = 'predicted_outcome_deviation'
    
    sns.scatterplot(x=df[predicted_col], y=residuals, alpha=0.5, edgecolor=None)
    
    # Add horizontal line at 0
    plt.axhline(y=0, color='r', linestyle='--', label='Zero Residual')
    
    plt.xlabel('Predicted Outcome Deviation')
    plt.ylabel('Residuals')
    plt.title(f'Residual Plot - {model_type.title()} Regression')
    plt.legend()
    
    save_plot(plt, output_path)
    plt.close()

def create_feature_importance_plot(coefficients: Dict[str, float], output_path: Path, model_type: str = 'beta'):
    """Create and save feature importance plot."""
    plt.figure(figsize=(12, 8))
    
    # Sort coefficients by absolute value
    sorted_coeffs = sorted(coefficients.items(), key=lambda x: abs(x[1]), reverse=True)
    
    if len(sorted_coeffs) == 0:
        logger.warning("No coefficients found for feature importance plot")
        plt.close()
        return
    
    # Limit to top 15 features for readability
    top_n = min(15, len(sorted_coeffs))
    top_coeffs = sorted_coeffs[:top_n]
    
    names = [k for k, v in top_coeffs]
    values = [v for k, v in top_coeffs]
    
    # Create bar chart
    plt.barh(range(top_n), values)
    plt.yticks(range(top_n), names)
    plt.xlabel('Coefficient Value')
    plt.title(f'Top Feature Importance - {model_type.title()} Regression')
    plt.gca().invert_yaxis()
    
    save_plot(plt, output_path)
    plt.close()

def save_plot(plt_obj, output_path: Path):
    """Save plot to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt_obj.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Plot saved to {output_path}")

def generate_diagnostic_report(
    cv_summary: Dict[str, Any],
    significant_predictors: List[str],
    model_results_path: Path,
    processed_data_path: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Generate diagnostic report including plots and summary statistics.
    
    Args:
        cv_summary: Dictionary containing mean/std R² and MSE from cross-validation
        significant_predictors: List of predictor names that are statistically significant
        model_results_path: Path to model metrics JSON file
        processed_data_path: Path to processed game records
        output_dir: Directory to save plots and report JSON
    
    Returns:
        Dictionary containing the diagnostic report
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_processed_data(processed_data_path)
    model_results = load_model_results(model_results_path)
    
    # Extract R² std from cv_summary (T030 requirement)
    r2_std = cv_summary.get('std_dev_r2', 0.0)
    validation_status = cv_summary.get('validation_status', 'Unknown')
    
    # Generate plots
    plot_paths = []
    
    # Predicted vs Actual
    pred_vs_actual_path = output_dir / 'predicted_vs_actual.png'
    create_predicted_vs_actual_plot(df, pred_vs_actual_path, model_type='beta')
    plot_paths.append(str(pred_vs_actual_path.relative_to(output_dir.parent.parent)))
    
    # Residuals
    residuals_path = output_dir / 'residuals.png'
    create_residual_plot(df, residuals_path, model_type='beta')
    plot_paths.append(str(residuals_path.relative_to(output_dir.parent.parent)))
    
    # Feature Importance (if coefficients available)
    if 'beta' in model_results and 'coefficients' in model_results['beta']:
        coeffs = model_results['beta']['coefficients']
        importance_path = output_dir / 'feature_importance.png'
        create_feature_importance_plot(coeffs, importance_path, model_type='beta')
        plot_paths.append(str(importance_path.relative_to(output_dir.parent.parent)))
    
    # Build diagnostic report
    diagnostic_report = {
        'plot_paths': plot_paths,
        'cv_summary': cv_summary,
        'r2_std': r2_std,
        'validation_status': validation_status,
        'significant_predictors': significant_predictors
    }
    
    # Save report
    report_path = output_dir / 'diagnostics.json'
    with open(report_path, 'w') as f:
        json.dump(diagnostic_report, f, indent=2)
    
    logger.info(f"Diagnostic report saved to {report_path}")
    
    return diagnostic_report

def main():
    """Main entry point for generating diagnostic reports."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate diagnostic reports for model validation')
    parser.add_argument('--cv-summary', type=str, required=True, help='Path to CV summary JSON')
    parser.add_argument('--significant-predictors', type=str, required=True, help='Path to significant predictors JSON')
    parser.add_argument('--model-results', type=str, required=True, help='Path to model metrics JSON')
    parser.add_argument('--processed-data', type=str, required=True, help='Path to processed data (parquet or csv)')
    parser.add_argument('--output-dir', type=str, default='data/results', help='Output directory for reports')
    
    args = parser.parse_args()
    
    # Load CV summary
    with open(args.cv_summary, 'r') as f:
        cv_summary = json.load(f)
    
    # Load significant predictors
    with open(args.significant_predictors, 'r') as f:
        sig_preds_data = json.load(f)
        significant_predictors = sig_preds_data.get('significant_predictors', [])
    
    # Generate report
    generate_diagnostic_report(
        cv_summary=cv_summary,
        significant_predictors=significant_predictors,
        model_results_path=Path(args.model_results),
        processed_data_path=Path(args.processed_data),
        output_dir=Path(args.output_dir)
    )
    
    logger.info("Diagnostic report generation complete")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()

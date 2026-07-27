"""
Module for generating diagnostic plots and reports for the chess Elo analysis pipeline.
Produces residual plots, predicted vs actual scatterplots, and feature importance rankings.
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

# Ensure matplotlib uses a non-interactive backend for server environments
import matplotlib
matplotlib.use('Agg')

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """
    Load model metrics from the JSON file produced by save_metrics.py.
    
    Args:
        results_path: Path to the model_metrics.json file
        
    Returns:
        Dictionary containing model results
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """
    Load the processed game records dataset.
    
    Args:
        data_path: Path to the processed games parquet or csv file
        
    Returns:
        DataFrame with processed game records
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def calculate_residuals(processed_df: pd.DataFrame, 
                        model_results: Dict[str, Any],
                        model_type: str = 'ridge') -> pd.Series:
    """
    Calculate residuals between actual outcomes and model predictions.
    
    Args:
        processed_df: DataFrame with processed game records
        model_results: Dictionary containing model coefficients and metrics
        model_type: Type of model ('ridge' or 'glm')
        
    Returns:
        Series of residuals
    """
    if model_type not in model_results:
        raise ValueError(f"Model type '{model_type}' not found in results")
    
    model_data = model_results[model_type]
    coefficients = model_data.get('coefficients', {})
    
    # Prepare features based on model coefficients
    # We need to reconstruct predictions using the coefficients
    # This assumes the processed_df contains the same features used during training
    
    # Identify feature columns (exclude non-feature columns)
    exclude_cols = ['game_id', 'outcome', 'eco_code', 'eco_family', 'elo_expected_prob']
    feature_cols = [col for col in processed_df.columns if col not in exclude_cols]
    
    # Calculate predictions
    predictions = pd.Series(0.0, index=processed_df.index)
    
    for feature, coef in coefficients.items():
        if feature in processed_df.columns:
            predictions += processed_df[feature] * coef
    
    # Add intercept if present
    if 'intercept' in coefficients:
        predictions += coefficients['intercept']
    
    # Calculate residuals: actual - predicted
    # Map outcome to numeric: 1=white win, 0.5=draw, 0=black win
    outcome_map = {'1-0': 1.0, '1/2-1/2': 0.5, '0-1': 0.0}
    actual_outcomes = processed_df['outcome'].map(outcome_map)
    
    residuals = actual_outcomes - predictions
    return residuals

def create_residual_plot(residuals: pd.Series, 
                         predictions: pd.Series,
                         output_path: Path) -> None:
    """
    Create a residual plot showing residuals vs predicted values.
    
    Args:
        residuals: Series of residual values
        predictions: Series of predicted values
        output_path: Path to save the plot
    """
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=predictions, y=residuals, alpha=0.5, edgecolors=None)
    
    # Add horizontal line at y=0
    plt.axhline(y=0, color='red', linestyle='--', linewidth=2, label='Zero residual')
    
    plt.xlabel('Predicted Outcome')
    plt.ylabel('Residual (Actual - Predicted)')
    plt.title('Residual Plot: Predicted vs Actual Outcomes')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Residual plot saved to: {output_path}")

def create_predicted_vs_actual_plot(processed_df: pd.DataFrame,
                                    predictions: pd.Series,
                                    output_path: Path) -> None:
    """
    Create a scatter plot of predicted vs actual outcomes.
    
    Args:
        processed_df: DataFrame with actual outcomes
        predictions: Series of predicted values
        output_path: Path to save the plot
    """
    # Map outcome to numeric
    outcome_map = {'1-0': 1.0, '1/2-1/2': 0.5, '0-1': 0.0}
    actual_outcomes = processed_df['outcome'].map(outcome_map)
    
    plt.figure(figsize=(10, 10))
    sns.scatterplot(x=predictions, y=actual_outcomes, alpha=0.5, edgecolors=None)
    
    # Add diagonal line (perfect prediction)
    min_val = min(predictions.min(), actual_outcomes.min())
    max_val = max(predictions.max(), actual_outcomes.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    
    plt.xlabel('Predicted Outcome')
    plt.ylabel('Actual Outcome')
    plt.title('Predicted vs Actual Outcomes')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Predicted vs Actual plot saved to: {output_path}")

def create_feature_importance_plot(coefficients: Dict[str, float],
                                   output_path: Path,
                                   top_n: int = 20) -> None:
    """
    Create a bar plot of feature importance (absolute coefficient values).
    
    Args:
        coefficients: Dictionary of feature names to coefficient values
        output_path: Path to save the plot
        top_n: Number of top features to display
    """
    # Convert to DataFrame and sort by absolute value
    coef_df = pd.DataFrame({
        'feature': list(coefficients.keys()),
        'coefficient': list(coefficients.values())
    })
    coef_df['abs_coefficient'] = coef_df['coefficient'].abs()
    coef_df = coef_df.sort_values('abs_coefficient', ascending=False).head(top_n)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(data=coef_df, x='coefficient', y='feature', hue='coefficient', palette='coolwarm', legend=False)
    
    plt.xlabel('Coefficient Value')
    plt.ylabel('Feature')
    plt.title(f'Top {top_n} Feature Importance (Absolute Coefficient Values)')
    plt.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Feature importance plot saved to: {output_path}")

def generate_diagnostic_report(processed_df: pd.DataFrame,
                               model_results: Dict[str, Any],
                               residuals: pd.Series,
                               predictions: pd.Series,
                               output_path: Path) -> Dict[str, Any]:
    """
    Generate a comprehensive diagnostic report in JSON format.
    
    Args:
        processed_df: DataFrame with processed game records
        model_results: Dictionary containing model results
        residuals: Series of residuals
        predictions: Series of predictions
        output_path: Path to save the JSON report
        
    Returns:
        Dictionary containing the diagnostic report
    """
    # Map outcome to numeric for calculations
    outcome_map = {'1-0': 1.0, '1/2-1/2': 0.5, '0-1': 0.0}
    actual_outcomes = processed_df['outcome'].map(outcome_map)
    
    # Calculate metrics
    mse = np.mean(residuals ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(residuals))
    
    # R-squared calculation
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((actual_outcomes - actual_outcomes.mean()) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    # Residual statistics
    residual_stats = {
        'mean': float(residuals.mean()),
        'std': float(residuals.std()),
        'min': float(residuals.min()),
        'max': float(residuals.max()),
        'median': float(residuals.median())
    }
    
    # Prediction statistics
    prediction_stats = {
        'mean': float(predictions.mean()),
        'std': float(predictions.std()),
        'min': float(predictions.min()),
        'max': float(predictions.max())
    }
    
    # Model performance summary
    report = {
        'dataset_info': {
            'num_samples': len(processed_df),
            'num_features': len(processed_df.columns)
        },
        'performance_metrics': {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r_squared': float(r_squared)
        },
        'residual_statistics': residual_stats,
        'prediction_statistics': prediction_stats,
        'model_summary': {
            model_type: {
                'r_squared': model_data.get('r_squared', 0.0),
                'aic': model_data.get('aic', 0.0),
                'num_predictors': len(model_data.get('coefficients', {}))
            }
            for model_type, model_data in model_results.items()
            if isinstance(model_data, dict)
        }
    }
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Diagnostic report saved to: {output_path}")
    return report

def main():
    """
    Main function to generate all diagnostic plots and reports.
    """
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data'
    results_dir = data_dir / 'results'
    processed_data_path = data_dir / 'processed' / 'games.parquet'
    model_results_path = results_dir / 'model_metrics.json'
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting diagnostic plot generation...")
    
    try:
        # Load data
        logger.info("Loading processed data...")
        processed_df = load_processed_data(processed_data_path)
        
        logger.info("Loading model results...")
        model_results = load_model_results(model_results_path)
        
        # Process each model type available
        models_to_process = []
        if 'ridge' in model_results:
            models_to_process.append('ridge')
        if 'glm' in model_results:
            models_to_process.append('glm')
        
        if not models_to_process:
            raise ValueError("No valid model results found (expected 'ridge' or 'glm')")
        
        # Generate plots for each model
        for model_type in models_to_process:
            logger.info(f"Processing {model_type} model...")
            model_data = model_results[model_type]
            coefficients = model_data.get('coefficients', {})
            
            # Calculate predictions and residuals
            logger.info(f"Calculating predictions and residuals for {model_type}...")
            residuals = calculate_residuals(processed_df, model_results, model_type)
            
            # Recalculate predictions for plotting
            exclude_cols = ['game_id', 'outcome', 'eco_code', 'eco_family', 'elo_expected_prob']
            feature_cols = [col for col in processed_df.columns if col not in exclude_cols]
            
            predictions = pd.Series(0.0, index=processed_df.index)
            for feature, coef in coefficients.items():
                if feature in processed_df.columns:
                    predictions += processed_df[feature] * coef
            if 'intercept' in coefficients:
                predictions += coefficients['intercept']
            
            # Create plots
            logger.info("Creating residual plot...")
            residual_plot_path = results_dir / f'{model_type}_residuals.png'
            create_residual_plot(residuals, predictions, residual_plot_path)
            
            logger.info("Creating predicted vs actual plot...")
            pva_plot_path = results_dir / f'{model_type}_predicted_vs_actual.png'
            create_predicted_vs_actual_plot(processed_df, predictions, pva_plot_path)
            
            logger.info("Creating feature importance plot...")
            importance_plot_path = results_dir / f'{model_type}_feature_importance.png'
            create_feature_importance_plot(coefficients, importance_plot_path)
        
        # Generate diagnostic report
        logger.info("Generating diagnostic report...")
        # Use the first available model for the report
        primary_model = models_to_process[0]
        residuals_for_report = calculate_residuals(processed_df, model_results, primary_model)
        
        # Recalculate predictions for report
        model_data = model_results[primary_model]
        coefficients = model_data.get('coefficients', {})
        predictions_for_report = pd.Series(0.0, index=processed_df.index)
        for feature, coef in coefficients.items():
            if feature in processed_df.columns:
                predictions_for_report += processed_df[feature] * coef
        if 'intercept' in coefficients:
            predictions_for_report += coefficients['intercept']
        
        report_path = results_dir / 'diagnostics.json'
        diagnostic_report = generate_diagnostic_report(
            processed_df, model_results, residuals_for_report, predictions_for_report, report_path
        )
        
        logger.info("Diagnostic plot generation completed successfully.")
        logger.info(f"Reports and plots saved to: {results_dir}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during plot generation: {e}")
        raise

if __name__ == "__main__":
    main()
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """Load model metrics from JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load processed game records from parquet or csv."""
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def calculate_residuals(df: pd.DataFrame, model_type: str = 'beta') -> pd.Series:
    """Calculate residuals for the specified model."""
    if model_type == 'beta':
        # For Beta regression, we predict outcome_deviation
        if 'outcome_deviation' not in df.columns:
            raise ValueError("Dataset missing 'outcome_deviation' column")
        if 'predicted_outcome_deviation_beta' not in df.columns:
            raise ValueError("Dataset missing 'predicted_outcome_deviation_beta' column")
        return df['outcome_deviation'] - df['predicted_outcome_deviation_beta']
    elif model_type == 'ridge':
        if 'predicted_outcome_deviation_ridge' not in df.columns:
            raise ValueError("Dataset missing 'predicted_outcome_deviation_ridge' column")
        return df['outcome_deviation'] - df['predicted_outcome_deviation_ridge']
    elif model_type == 'gaussian':
        if 'predicted_outcome_deviation_gaussian' not in df.columns:
            raise ValueError("Dataset missing 'predicted_outcome_deviation_gaussian' column")
        return df['outcome_deviation'] - df['predicted_outcome_deviation_gaussian']
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def create_predicted_vs_actual_plot(
    df: pd.DataFrame, 
    model_type: str, 
    output_path: Path,
    sample_size: int = 10000
) -> str:
    """Create scatter plot of predicted vs actual outcome deviation."""
    logger.info(f"Creating predicted vs actual plot for {model_type} model")
    
    # Sample data if too large for plotting
    if len(df) > sample_size:
        df_sample = df.sample(n=sample_size, random_state=42)
    else:
        df_sample = df
    
    plt.figure(figsize=(10, 8))
    
    if model_type == 'beta':
        actual_col = 'outcome_deviation'
        pred_col = 'predicted_outcome_deviation_beta'
    elif model_type == 'ridge':
        actual_col = 'outcome_deviation'
        pred_col = 'predicted_outcome_deviation_ridge'
    elif model_type == 'gaussian':
        actual_col = 'outcome_deviation'
        pred_col = 'predicted_outcome_deviation_gaussian'
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Check if columns exist
    if actual_col not in df_sample.columns or pred_col not in df_sample.columns:
        logger.warning(f"Columns {actual_col} or {pred_col} not found in dataset. Skipping plot.")
        plt.close()
        return str(output_path)
    
    sns.scatterplot(
        x=df_sample[pred_col],
        y=df_sample[actual_col],
        alpha=0.3,
        s=10,
        edgecolors='none'
    )
    
    # Add diagonal line
    min_val = min(df_sample[pred_col].min(), df_sample[actual_col].min())
    max_val = max(df_sample[pred_col].max(), df_sample[actual_col].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    
    plt.xlabel(f'Predicted Outcome Deviation ({model_type.title()})')
    plt.ylabel('Actual Outcome Deviation')
    plt.title(f'Predicted vs Actual: {model_type.title()} Regression')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved predicted vs actual plot to {output_path}")
    return str(output_path)

def create_residual_plot(
    df: pd.DataFrame,
    model_type: str,
    output_path: Path,
    sample_size: int = 10000
) -> str:
    """Create residual plot (residuals vs predicted values)."""
    logger.info(f"Creating residual plot for {model_type} model")
    
    # Sample data if too large
    if len(df) > sample_size:
        df_sample = df.sample(n=sample_size, random_state=42)
    else:
        df_sample = df
    
    plt.figure(figsize=(10, 8))
    
    if model_type == 'beta':
        pred_col = 'predicted_outcome_deviation_beta'
    elif model_type == 'ridge':
        pred_col = 'predicted_outcome_deviation_ridge'
    elif model_type == 'gaussian':
        pred_col = 'predicted_outcome_deviation_gaussian'
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    if pred_col not in df_sample.columns or 'outcome_deviation' not in df_sample.columns:
        logger.warning(f"Required columns not found. Skipping residual plot.")
        plt.close()
        return str(output_path)
    
    residuals = df_sample['outcome_deviation'] - df_sample[pred_col]
    
    sns.scatterplot(
        x=df_sample[pred_col],
        y=residuals,
        alpha=0.3,
        s=10,
        edgecolors='none'
    )
    
    # Add horizontal line at 0
    plt.axhline(y=0, color='r', linestyle='--', linewidth=2)
    
    plt.xlabel(f'Predicted Outcome Deviation ({model_type.title()})')
    plt.ylabel('Residuals')
    plt.title(f'Residual Plot: {model_type.title()} Regression')
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved residual plot to {output_path}")
    return str(output_path)

def create_feature_importance_plot(
    model_metrics: Dict[str, Any],
    output_path: Path,
    model_type: str = 'beta'
) -> str:
    """Create feature importance ranking plot based on model coefficients."""
    logger.info(f"Creating feature importance plot for {model_type} model")
    
    plt.figure(figsize=(12, 8))
    
    # Extract coefficients based on model type
    if model_type not in model_metrics:
        logger.warning(f"Model type '{model_type}' not found in metrics. Skipping plot.")
        plt.close()
        return str(output_path)
    
    coefficients = model_metrics[model_type].get('coefficients', {})
    
    if not coefficients:
        logger.warning("No coefficients found in model metrics. Skipping plot.")
        plt.close()
        return str(output_path)
    
    # Convert to DataFrame for sorting
    coef_df = pd.DataFrame(list(coefficients.items()), columns=['Feature', 'Coefficient'])
    coef_df = coef_df[coef_df['Feature'] != 'intercept']
    
    # Sort by absolute value of coefficient
    coef_df = coef_df.sort_values('Coefficient', key=abs, ascending=True)
    
    # Plot top 15 features
    top_n = min(15, len(coef_df))
    coef_top = coef_df.tail(top_n)
    
    plt.barh(coef_top['Feature'], coef_top['Coefficient'])
    plt.xlabel('Coefficient Value')
    plt.ylabel('Feature')
    plt.title(f'Top {top_n} Feature Importance ({model_type.title()} Regression)')
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3, axis='x')
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved feature importance plot to {output_path}")
    return str(output_path)

def generate_diagnostic_report(
    plot_paths: List[str],
    cv_summary: Dict[str, Any],
    r2_std: float,
    validation_status: str,
    significant_predictors: List[str],
    output_path: Path
) -> str:
    """Generate a JSON diagnostic report summarizing all plots and metrics."""
    logger.info("Generating diagnostic report")
    
    report = {
        "plot_paths": plot_paths,
        "cv_summary": cv_summary,
        "r2_std": r2_std,
        "validation_status": validation_status,
        "significant_predictors": significant_predictors
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved diagnostic report to {output_path}")
    return str(output_path)

def main():
    """Main function to generate all diagnostic plots and report."""
    logger.info("Starting diagnostic plot generation")
    
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "processed" / "games.parquet"
    results_path = base_path / "data" / "results" / "model_metrics.json"
    diagnostics_path = base_path / "data" / "results" / "diagnostics.json"
    plots_dir = base_path / "data" / "results"
    
    # Ensure plots directory exists
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        logger.info(f"Loading processed data from {data_path}")
        df = load_processed_data(data_path)
        
        logger.info(f"Loading model metrics from {results_path}")
        model_metrics = load_model_results(results_path)
        
        # Load CV summary from model_metrics if available
        cv_summary = model_metrics.get('cv_summary', {
            'mean_r2': 0.0,
            'std_r2': 0.0,
            'mean_mse': 0.0
        })
        r2_std = cv_summary.get('std_r2', 0.0)
        validation_status = cv_summary.get('validation_status', 'Unknown')
        
        # Get significant predictors from model metrics
        significant_predictors = []
        if 'beta' in model_metrics:
            # Extract predictors with p-values < 0.05 (if available)
            p_values = model_metrics['beta'].get('p_values', {})
            for feat, p_val in p_values.items():
                if isinstance(p_val, (int, float)) and p_val < 0.05:
                    significant_predictors.append(feat)
        
        # Generate plots
        plot_paths = []
        
        # 1. Predicted vs Actual plots for all models
        for model_type in ['beta', 'ridge', 'gaussian']:
            plot_path = plots_dir / f"predicted_vs_actual_{model_type}.png"
            try:
                path_str = create_predicted_vs_actual_plot(df, model_type, plot_path)
                plot_paths.append(path_str)
            except Exception as e:
                logger.warning(f"Failed to create {model_type} predicted vs actual plot: {e}")
        
        # 2. Residual plots for all models
        for model_type in ['beta', 'ridge', 'gaussian']:
            plot_path = plots_dir / f"residuals_{model_type}.png"
            try:
                path_str = create_residual_plot(df, model_type, plot_path)
                plot_paths.append(path_str)
            except Exception as e:
                logger.warning(f"Failed to create {model_type} residual plot: {e}")
        
        # 3. Feature importance plot (beta model)
        feature_importance_path = plots_dir / "feature_importance_beta.png"
        try:
            path_str = create_feature_importance_plot(model_metrics, feature_importance_path, 'beta')
            plot_paths.append(path_str)
        except Exception as e:
            logger.warning(f"Failed to create feature importance plot: {e}")
        
        # Generate diagnostic report
        generate_diagnostic_report(
            plot_paths=plot_paths,
            cv_summary=cv_summary,
            r2_std=r2_std,
            validation_status=validation_status,
            significant_predictors=significant_predictors,
            output_path=diagnostics_path
        )
        
        logger.info("Diagnostic plot generation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating diagnostic plots: {e}")
        raise

if __name__ == "__main__":
    main()

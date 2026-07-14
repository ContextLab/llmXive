import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import logging

from src.config import ensure_directories

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure plotting backend is non-interactive for script execution
plt.switch_backend('Agg')

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """Load model metrics from JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load processed game data from parquet or CSV."""
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def calculate_residuals(df: pd.DataFrame, model_type: str = 'ridge') -> pd.DataFrame:
    """Calculate residuals for the specified model."""
    # Determine actual outcome column name based on data schema
    outcome_col = 'outcome'
    predicted_col = f'outcome_predicted_{model_type}'
    
    if predicted_col not in df.columns:
        # Fallback: try to find any predicted column if naming differs
        pred_cols = [c for c in df.columns if 'predicted' in c.lower()]
        if not pred_cols:
            raise ValueError(f"No predicted outcome column found for {model_type}")
        predicted_col = pred_cols[0]
    
    df = df.copy()
    df['residual'] = df[outcome_col] - df[predicted_col]
    return df

def create_predicted_vs_actual_plot(df: pd.DataFrame, model_type: str, output_path: Path) -> None:
    """Create scatter plot of predicted vs actual outcomes."""
    outcome_col = 'outcome'
    predicted_col = f'outcome_predicted_{model_type}'
    
    if predicted_col not in df.columns:
        pred_cols = [c for c in df.columns if 'predicted' in c.lower()]
        if pred_cols:
            predicted_col = pred_cols[0]
        else:
            logger.warning(f"Predicted column {predicted_col} not found, skipping plot")
            return

    plt.figure(figsize=(10, 8))
    sns.scatterplot(
        x=predicted_col, 
        y=outcome_col, 
        data=df, 
        alpha=0.6, 
        edgecolor=None
    )
    
    # Add identity line
    min_val = min(df[predicted_col].min(), df[outcome_col].min())
    max_val = max(df[predicted_col].max(), df[outcome_col].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')
    
    plt.title(f'Predicted vs Actual Outcomes ({model_type.title()})')
    plt.xlabel('Predicted Probability')
    plt.ylabel('Actual Outcome (0=Loss, 0.5=Draw, 1=Win)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved predicted vs actual plot to {output_path}")

def create_residual_plot(df: pd.DataFrame, model_type: str, output_path: Path) -> None:
    """Create residual plot (residuals vs predicted values)."""
    outcome_col = 'outcome'
    predicted_col = f'outcome_predicted_{model_type}'
    residual_col = 'residual'
    
    if predicted_col not in df.columns:
        pred_cols = [c for c in df.columns if 'predicted' in c.lower()]
        if pred_cols:
            predicted_col = pred_cols[0]
        else:
            logger.warning(f"Predicted column {predicted_col} not found, skipping residual plot")
            return

    df = calculate_residuals(df, model_type)
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        x=predicted_col, 
        y=residual_col, 
        data=df, 
        alpha=0.6, 
        edgecolor=None
    )
    
    # Add zero line
    plt.axhline(y=0, color='r', linestyle='--', label='Zero Residual')
    
    plt.title(f'Residuals vs Predicted Values ({model_type.title()})')
    plt.xlabel('Predicted Probability')
    plt.ylabel('Residual (Actual - Predicted)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved residual plot to {output_path}")

def create_feature_importance_plot(df: pd.DataFrame, output_path: Path) -> None:
    """Create feature importance ranking plot based on absolute coefficients."""
    # Assuming model results contain coefficients
    # This function assumes we have a way to get coefficients, usually from model_output.json
    # For this implementation, we'll derive importance from correlation with outcome if coefficients aren't directly available
    # Or we expect the model results JSON to be loaded separately. 
    
    # For now, let's create a placeholder that uses correlation as a proxy for importance
    # In a real scenario, we'd load coefficients from the saved model artifacts
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    outcome_col = 'outcome'
    
    if outcome_col not in numeric_cols:
        logger.warning("Outcome column not found, skipping feature importance")
        return
        
    correlations = df[numeric_cols].corr()[outcome_col].abs().sort_values(ascending=True)
    correlations = correlations[correlations != 0] # Remove self-correlation and zero
    
    plt.figure(figsize=(10, 8))
    plt.barh(range(len(correlations)), correlations.values, color='steelblue')
    plt.yticks(range(len(correlations)), correlations.index)
    plt.xlabel('Absolute Correlation with Outcome')
    plt.title('Feature Importance (Absolute Correlation)')
    plt.gca().invert_yaxis() # Most important at top
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved feature importance plot to {output_path}")

def generate_diagnostic_report(
    df: pd.DataFrame, 
    model_results: Dict[str, Any], 
    output_path: Path
) -> Dict[str, Any]:
    """Generate a comprehensive diagnostic report in JSON format."""
    report = {
        "report_metadata": {
            "generated_at": pd.Timestamp.now().isoformat(),
            "total_games_analyzed": len(df),
            "models_evaluated": list(model_results.keys())
        },
        "data_quality": {
            "missing_values": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "outcome_distribution": df['outcome'].value_counts().to_dict() if 'outcome' in df.columns else {}
        },
        "model_performance": {},
        "diagnostic_checks": {}
    }

    # Populate model performance from loaded results
    for model_name, metrics in model_results.items():
        report["model_performance"][model_name] = {
            "r_squared": metrics.get("r_squared"),
            "mse": metrics.get("mse"),
            "mae": metrics.get("mae"),
            "cross_validation_scores": metrics.get("cross_validation_scores", []),
            "significant_predictors": metrics.get("significant_predictors", [])
        }

    # Calculate additional diagnostics
    if 'outcome' in df.columns:
        mean_outcome = float(df['outcome'].mean())
        std_outcome = float(df['outcome'].std())
        report["diagnostic_checks"]["outcome_statistics"] = {
            "mean": mean_outcome,
            "std": std_outcome,
            "skewness": float(df['outcome'].skew()),
            "kurtosis": float(df['outcome'].kurtosis())
        }

    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Saved diagnostic report to {output_path}")
    return report

def main():
    """Main entry point to generate all plots and the diagnostic report."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    results_dir = data_dir / "results"
    
    # Ensure directories exist
    ensure_directories()
    
    # Define input/output paths
    processed_data_path = data_dir / "processed" / "games.parquet"
    model_results_path = results_dir / "model_metrics.json"
    
    # Output paths for plots and report
    plots_dir = results_dir
    predicted_vs_actual_path = plots_dir / "predicted_vs_actual_ridge.png"
    residual_path = plots_dir / "residuals_ridge.png"
    feature_importance_path = plots_dir / "feature_importance.png"
    diagnostic_report_path = results_dir / "diagnostics.json"
    
    logger.info(f"Starting diagnostic plot generation. Data: {processed_data_path}, Results: {model_results_path}")
    
    # Check if input files exist
    if not processed_data_path.exists():
        logger.error(f"Processed data not found at {processed_data_path}. Cannot generate plots.")
        return
    
    if not model_results_path.exists():
        logger.error(f"Model results not found at {model_results_path}. Cannot generate plots.")
        return

    # Load data
    try:
        df = load_processed_data(processed_data_path)
        logger.info(f"Loaded {len(df)} game records.")
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        return

    # Load model results
    try:
        model_results = load_model_results(model_results_path)
        logger.info(f"Loaded model results for models: {list(model_results.keys())}")
    except Exception as e:
        logger.error(f"Failed to load model results: {e}")
        return

    # Generate plots for Ridge model (primary model per plan)
    model_type = 'ridge'
    
    # 1. Predicted vs Actual
    try:
        create_predicted_vs_actual_plot(df, model_type, predicted_vs_actual_path)
    except Exception as e:
        logger.error(f"Error generating predicted vs actual plot: {e}")
    
    # 2. Residual Plot
    try:
        create_residual_plot(df, model_type, residual_path)
    except Exception as e:
        logger.error(f"Error generating residual plot: {e}")
    
    # 3. Feature Importance
    try:
        create_feature_importance_plot(df, feature_importance_path)
    except Exception as e:
        logger.error(f"Error generating feature importance plot: {e}")
    
    # 4. Generate Diagnostic Report
    try:
        generate_diagnostic_report(df, model_results, diagnostic_report_path)
    except Exception as e:
        logger.error(f"Error generating diagnostic report: {e}")
    
    logger.info("Diagnostic plot generation completed.")

if __name__ == "__main__":
    main()
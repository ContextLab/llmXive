"""
generate_plots.py

Generates diagnostic plots for the chess Elo analysis pipeline.
Specifically implements:
- Predicted vs Actual deviation scatterplots (T032)
- Residual plots (T031)
- Feature importance plots (T031)
- Diagnostic report generation (T033)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure consistent plotting style
plt.style.use('seaborn-v0_8-whitegrid')

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """
    Load model results from a JSON file.

    Args:
        results_path: Path to the model results JSON file.

    Returns:
        Dictionary containing model results.

    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")

    with open(results_path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """
    Load processed game data from a Parquet or CSV file.

    Args:
        data_path: Path to the processed data file.

    Returns:
        DataFrame containing processed game data.

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the file format is unsupported.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_path}")

    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}. Use .parquet or .csv")

def calculate_residuals(df: pd.DataFrame, model_type: str = 'ridge') -> pd.DataFrame:
    """
    Calculate residuals for the given model.

    Args:
        df: DataFrame containing game data and model predictions.
        model_type: Type of model ('ridge' or 'glm').

    Returns:
        DataFrame with added 'residual' column.
    """
    pred_col = f'predicted_{model_type}'
    actual_col = 'outcome'

    if pred_col not in df.columns:
        raise ValueError(f"Column '{pred_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")
    if actual_col not in df.columns:
        raise ValueError(f"Column '{actual_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")

    df = df.copy()
    df['residual'] = df[actual_col] - df[pred_col]
    return df

def create_predicted_vs_actual_plot(df: pd.DataFrame, model_type: str = 'ridge', output_path: Optional[Path] = None) -> Path:
    """
    Create a predicted vs. actual deviation scatterplot (T032).

    This plot visualizes the relationship between predicted probabilities
    and actual outcomes, with a diagonal line representing perfect prediction.

    Args:
        df: DataFrame containing game data with predictions.
        model_type: Type of model ('ridge' or 'glm').
        output_path: Optional path to save the plot. If None, plot is shown but not saved.

    Returns:
        Path to the saved plot file.
    """
    pred_col = f'predicted_{model_type}'
    actual_col = 'outcome'

    if pred_col not in df.columns:
        raise ValueError(f"Column '{pred_col}' not found in DataFrame.")
    if actual_col not in df.columns:
        raise ValueError(f"Column '{actual_col}' not found in DataFrame.")

    # Create the figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot of predicted vs actual
    sns.scatterplot(
        x=df[pred_col],
        y=df[actual_col],
        alpha=0.6,
        edgecolor=None,
        ax=ax,
        label='Games'
    )

    # Add diagonal line (perfect prediction)
      # Create a range from min to max of predictions
    min_val = min(df[pred_col].min(), df[actual_col].min())
    max_val = max(df[pred_col].max(), df[actual_col].max())
    x_line = np.linspace(min_val, max_val, 100)
    ax.plot(x_line, x_line, 'r--', linewidth=2, label='Perfect Prediction')

    # Labels and title
    ax.set_xlabel(f'Predicted Probability ({model_type.capitalize()})', fontsize=12)
    ax.set_ylabel('Actual Outcome (1=Win, 0.5=Draw, 0=Loss)', fontsize=12)
    ax.set_title(f'Predicted vs. Actual Outcome Deviation ({model_type.capitalize()} Model)', fontsize=14)
    ax.legend(loc='upper left')

    # Set axis limits to [0, 1] for better visualization
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)

    # Save or show
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Predicted vs Actual plot saved to: {output_path}")
    else:
        plt.show()

    plt.close(fig)
    return output_path

def create_residual_plot(df: pd.DataFrame, model_type: str = 'ridge', output_path: Optional[Path] = None) -> Path:
    """
    Create a residual plot showing residuals vs. predicted values.

    Args:
        df: DataFrame containing game data and residuals.
        model_type: Type of model ('ridge' or 'glm').
        output_path: Optional path to save the plot.

    Returns:
        Path to the saved plot file.
    """
    pred_col = f'predicted_{model_type}'
    res_col = 'residual'

    if pred_col not in df.columns:
        raise ValueError(f"Column '{pred_col}' not found in DataFrame.")
    if res_col not in df.columns:
        raise ValueError(f"Column '{res_col}' not found in DataFrame. Run calculate_residuals first.")

    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter plot of residuals vs predictions
    sns.scatterplot(
        x=df[pred_col],
        y=df[res_col],
        alpha=0.6,
        edgecolor=None,
        ax=ax
    )

    # Add horizontal line at 0
    ax.axhline(y=0, color='r', linestyle='--', linewidth=2, label='Zero Residual')

    # Labels and title
    ax.set_xlabel(f'Predicted Probability ({model_type.capitalize()})', fontsize=12)
    ax.set_ylabel('Residual (Actual - Predicted)', fontsize=12)
    ax.set_title(f'Residual Plot ({model_type.capitalize()} Model)', fontsize=14)
    ax.legend()

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Residual plot saved to: {output_path}")
    else:
        plt.show()

    plt.close(fig)
    return output_path

def create_feature_importance_plot(coefficients: Dict[str, float], output_path: Optional[Path] = None) -> Path:
    """
    Create a feature importance plot based on model coefficients.

    Args:
        coefficients: Dictionary of feature names to coefficient values.
        output_path: Optional path to save the plot.

    Returns:
        Path to the saved plot file.
    """
    if not coefficients:
        raise ValueError("Coefficients dictionary is empty.")

    # Convert to DataFrame for easier plotting
    coef_df = pd.DataFrame(list(coefficients.items()), columns=['feature', 'coefficient'])
    coef_df = coef_df.sort_values('coefficient', ascending=True)

    fig, ax = plt.subplots(figsize=(12, 10))

    # Horizontal bar chart
    sns.barplot(
        x='coefficient',
        y='feature',
        data=coef_df,
        palette='viridis',
        ax=ax
    )

    # Labels and title
    ax.set_xlabel('Coefficient Value', fontsize=12)
    ax.set_ylabel('Feature', fontsize=12)
    ax.set_title('Feature Importance (Model Coefficients)', fontsize=14)

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7, axis='x')

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Feature importance plot saved to: {output_path}")
    else:
        plt.show()

    plt.close(fig)
    return output_path

def generate_diagnostic_report(
    df: pd.DataFrame,
    model_results: Dict[str, Any],
    output_path: Path
) -> Path:
    """
    Generate a comprehensive diagnostic report in JSON format.

    Args:
        df: DataFrame containing processed game data.
        model_results: Dictionary containing model metrics and coefficients.
        output_path: Path to save the diagnostic report.

    Returns:
        Path to the saved report file.
    """
    report = {
        "dataset_info": {
            "total_games": len(df),
            "columns": df.columns.tolist(),
            "outcome_distribution": df['outcome'].value_counts().to_dict() if 'outcome' in df.columns else {}
        },
        "model_metrics": model_results,
        "data_quality": {
            "missing_values": df.isnull().sum().to_dict(),
            "null_counts_by_column": df.isnull().sum().to_dict()
        }
    }

    # Calculate additional statistics if available
    if 'predicted_ridge' in df.columns and 'outcome' in df.columns:
        report["ridge_model_stats"] = {
            "mean_absolute_error": (df['outcome'] - df['predicted_ridge']).abs().mean(),
            "mean_squared_error": ((df['outcome'] - df['predicted_ridge']) ** 2).mean(),
            "r_squared": df['outcome'].corr(df['predicted_ridge']) ** 2
        }

    if 'predicted_glm' in df.columns and 'outcome' in df.columns:
        report["glm_model_stats"] = {
            "mean_absolute_error": (df['outcome'] - df['predicted_glm']).abs().mean(),
            "mean_squared_error": ((df['outcome'] - df['predicted_glm']) ** 2).mean(),
            "r_squared": df['outcome'].corr(df['predicted_glm']) ** 2
        }

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Diagnostic report saved to: {output_path}")
    return output_path

def main():
    """
    Main entry point for generating diagnostic plots and reports.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data"
    results_dir = data_dir / "results"

    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)

    # File paths
    processed_data_path = data_dir / "processed" / "games.parquet"
    model_results_path = results_dir / "model_metrics.json"
    output_plots_dir = results_dir / "plots"

    try:
        # Load data
        logger.info("Loading processed data...")
        df = load_processed_data(processed_data_path)

        logger.info("Loading model results...")
        model_results = load_model_results(model_results_path)

        # Calculate residuals for Ridge model
        logger.info("Calculating residuals...")
        df = calculate_residuals(df, model_type='ridge')

        # Generate plots
        logger.info("Generating predicted vs actual plot...")
        pred_vs_actual_path = output_plots_dir / "predicted_vs_actual_ridge.png"
        create_predicted_vs_actual_plot(df, model_type='ridge', output_path=pred_vs_actual_path)

        logger.info("Generating residual plot...")
        residual_path = output_plots_dir / "residuals_ridge.png"
        create_residual_plot(df, model_type='ridge', output_path=residual_path)

        # Generate feature importance plot if coefficients are available
        if 'ridge' in model_results and 'coefficients' in model_results['ridge']:
            logger.info("Generating feature importance plot...")
            importance_path = output_plots_dir / "feature_importance_ridge.png"
            create_feature_importance_plot(
                model_results['ridge']['coefficients'],
                output_path=importance_path
            )

        # Generate diagnostic report
        logger.info("Generating diagnostic report...")
        report_path = results_dir / "diagnostics.json"
        generate_diagnostic_report(df, model_results, report_path)

        logger.info("All plots and reports generated successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        raise

if __name__ == "__main__":
    main()
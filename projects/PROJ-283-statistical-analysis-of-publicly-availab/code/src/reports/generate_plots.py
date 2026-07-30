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

# Set style for plots
sns.set(style="whitegrid")

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """Load model metrics from JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load processed game data from Parquet or CSV."""
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def calculate_residuals(df: pd.DataFrame, model_type: str) -> pd.Series:
    """Calculate residuals for a given model."""
    if model_type not in df.columns or 'outcome' not in df.columns:
        raise ValueError(f"Required columns not found for {model_type}")
    
    return df['outcome'] - df[model_type]

def create_predicted_vs_actual_plot(
    df: pd.DataFrame, 
    model_type: str, 
    output_path: Path,
    title: str = "Predicted vs Actual Outcome"
) -> Path:
    """Create scatter plot of predicted vs actual values."""
    plt.figure(figsize=(10, 8))
    
    predicted = df[model_type]
    actual = df['outcome']
    
    plt.scatter(actual, predicted, alpha=0.6, edgecolors='w', linewidth=0.5)
    plt.plot([actual.min(), actual.max()], [actual.min(), actual.max()], 'r--', lw=2, label='Perfect Prediction')
    
    plt.xlabel('Actual Outcome')
    plt.ylabel(f'Predicted Outcome ({model_type})')
    plt.title(title)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved predicted vs actual plot to {output_path}")
    return output_path

def create_residual_plot(
    residuals: pd.Series, 
    output_path: Path,
    title: str = "Residual Plot"
) -> Path:
    """Create residual plot to check for patterns."""
    plt.figure(figsize=(10, 6))
    
    indices = range(len(residuals))
    plt.scatter(indices, residuals, alpha=0.6, edgecolors='w', linewidth=0.5)
    plt.axhline(y=0, color='r', linestyle='--', linewidth=2)
    
    plt.xlabel('Game Index')
    plt.ylabel('Residuals')
    plt.title(title)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved residual plot to {output_path}")
    return output_path

def create_feature_importance_plot(
    coefficients: Dict[str, float], 
    output_path: Path,
    title: str = "Feature Importance"
) -> Path:
    """Create bar plot of feature importance (absolute coefficients)."""
    # Convert to DataFrame for easier plotting
    df_importance = pd.DataFrame({
        'feature': list(coefficients.keys()),
        'coefficient': list(coefficients.values())
    })
    
    # Sort by absolute value
    df_importance = df_importance.sort_values('coefficient', key=abs, ascending=False)
    
    plt.figure(figsize=(12, 8))
    plt.barh(df_importance['feature'], df_importance['coefficient'], color='skyblue')
    plt.xlabel('Coefficient Value')
    plt.ylabel('Feature')
    plt.title(title)
    
    # Add value labels
    for i, v in enumerate(df_importance['coefficient']):
        plt.text(v, i, f"{v:.3f}", va='center')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved feature importance plot to {output_path}")
    return output_path

def generate_diagnostic_report(
    model_metrics: Dict[str, Any],
    residuals_stats: Dict[str, Dict[str, float]],
    plots_info: Dict[str, str],
    output_path: Path
) -> Dict[str, Any]:
    """Generate a comprehensive diagnostic report as JSON."""
    report = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "model_metrics": model_metrics,
        "residuals_statistics": residuals_stats,
        "plots_generated": list(plots_info.keys()),
        "plot_file_paths": plots_info,
        "summary": {
            "total_models_evaluated": len(model_metrics),
            "total_plots_created": len(plots_info),
            "residuals_mean_all": np.mean([stats['mean'] for stats in residuals_stats.values()]),
            "residuals_std_all": np.mean([stats['std'] for stats in residuals_stats.values()])
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Saved diagnostic report to {output_path}")
    return report

def main():
    """Main function to generate all diagnostic plots and report."""
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    results_dir = base_dir / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Paths to input files
    processed_data_path = base_dir / "data" / "processed" / "games.parquet"
    model_metrics_path = results_dir / "model_metrics.json"
    
    # Output paths
    plots_dir = results_dir
    diagnostics_json_path = results_dir / "diagnostics.json"
    
    # Verify input files exist
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_data_path}")
    if not model_metrics_path.exists():
        raise FileNotFoundError(f"Model metrics not found at {model_metrics_path}")
    
    # Load data
    logger.info("Loading processed data...")
    df = load_processed_data(processed_data_path)
    
    logger.info("Loading model metrics...")
    model_metrics = load_model_results(model_metrics_path)
    
    # Identify models in the data
    # We expect columns like 'predicted_outcome_GLM' and 'predicted_outcome_Ridge'
    # or similar naming convention based on fit.py
    model_columns = [col for col in df.columns if col.startswith('predicted_outcome_')]
    
    if not model_columns:
        raise ValueError("No predicted outcome columns found in the processed data. "
                       "Expected columns like 'predicted_outcome_GLM' or 'predicted_outcome_Ridge'.")
    
    logger.info(f"Found model columns: {model_columns}")
    
    plots_info = {}
    residuals_stats = {}
    
    for model_col in model_columns:
        model_name = model_col.replace('predicted_outcome_', '')
        logger.info(f"Processing model: {model_name}")
        
        # Calculate residuals
        residuals = calculate_residuals(df, model_col)
        
        # Store statistics
        residuals_stats[model_name] = {
            "mean": float(residuals.mean()),
            "std": float(residuals.std()),
            "min": float(residuals.min()),
            "max": float(residuals.max())
        }
        
        # 1. Predicted vs Actual Plot
        plot_path = plots_dir / f"predicted_vs_actual_{model_name}.png"
        create_predicted_vs_actual_plot(
            df, 
            model_col, 
            plot_path, 
            title=f"Predicted vs Actual - {model_name}"
        )
        plots_info[f"predicted_vs_actual_{model_name}"] = str(plot_path.relative_to(base_dir))
        
        # 2. Residual Plot
        plot_path = plots_dir / f"residuals_{model_name}.png"
        create_residual_plot(
            residuals, 
            plot_path, 
            title=f"Residuals - {model_name}"
        )
        plots_info[f"residuals_{model_name}"] = str(plot_path.relative_to(base_dir))
        
        # 3. Feature Importance Plot (if coefficients are available in model_metrics)
        # Check if coefficients exist for this model in the loaded metrics
        model_metrics_flat = model_metrics.get('models', {})
        # Try to find coefficients for this model
        # The structure might be {'Gaussian GLM': {...}, 'Ridge': {...}}
        # We need to map model_name (e.g., "GLM") to the key in metrics
        # Heuristic: Look for keys containing the model name or common aliases
        coeff_key = None
        for key in model_metrics_flat:
            if model_name.lower() in key.lower() or key.lower() in model_name.lower():
                coeff_key = key
                break
        
        if coeff_key and 'coefficients' in model_metrics_flat[coeff_key]:
            coeffs = model_metrics_flat[coeff_key]['coefficients']
            plot_path = plots_dir / f"feature_importance_{model_name}.png"
            create_feature_importance_plot(
                coeffs, 
                plot_path, 
                title=f"Feature Importance - {model_name}"
            )
            plots_info[f"feature_importance_{model_name}"] = str(plot_path.relative_to(base_dir))
        else:
            logger.warning(f"Coefficients not found for model {model_name} in model_metrics, skipping feature importance plot.")
    
    # Generate final diagnostic report
    logger.info("Generating diagnostic report...")
    report = generate_diagnostic_report(
        model_metrics,
        residuals_stats,
        plots_info,
        diagnostics_json_path
    )
    
    logger.info("All plots and report generated successfully.")
    print(f"Diagnostic report saved to: {diagnostics_json_path}")
    print(f"Plots saved to: {plots_dir}")
    
    return report

if __name__ == "__main__":
    main()

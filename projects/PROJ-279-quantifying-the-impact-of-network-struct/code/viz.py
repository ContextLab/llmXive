import logging
import json
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from config.env_config import get_processed_dir
from logging_config import get_logger

# Configure matplotlib to use non-interactive backend for headless environments
matplotlib.use('Agg')

logger = get_logger(__name__)

def load_regression_results() -> Dict[str, Any]:
    """
    Load regression results from the processed results directory.
    Expects 'results/regression_metrics.json' to exist.
    """
    processed_dir = get_processed_dir()
    results_path = processed_dir / 'results' / 'regression_metrics.json'
    
    if not results_path.exists():
        raise FileNotFoundError(f"Regression results not found at {results_path}. "
                                "Ensure T031-T034 have been executed successfully.")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def identify_top_predictor(results: Dict[str, Any]) -> Tuple[str, float]:
    """
    Identify the top predictor based on average absolute feature importance.
    Returns (feature_name, importance_value).
    """
    if 'feature_importance' not in results:
        raise ValueError("Feature importance data missing in regression results.")
    
    importance_data = results['feature_importance']
    # Expecting list of dicts with 'feature', 'mean_importance', 'std_importance'
    if not importance_data:
        raise ValueError("Feature importance list is empty.")
    
    # Sort by mean absolute importance (assuming importance is already signed or we take abs)
    # The task implies we want the top predictor, usually the one with highest magnitude impact.
    # Assuming mean_importance holds the average coefficient/importance value.
    sorted_features = sorted(
        importance_data, 
        key=lambda x: abs(x['mean_importance']), 
        reverse=True
    )
    
    top = sorted_features[0]
    return top['feature'], top['mean_importance']

def generate_scatter_plot(
    results: Dict[str, Any], 
    output_path: Path, 
    top_feature_name: str
) -> None:
    """
    Generate a scatter plot of the top predictor vs thermal conductivity.
    Includes regression line and Pearson r.
    (Existing logic for T035, preserved for context)
    """
    if 'data' not in results or 'X' not in results['data'] or 'y' not in results['data']:
        logger.warning("Raw data for scatter plot not found in results. Skipping scatter plot generation.")
        return

    df = pd.DataFrame(results['data'])
    if top_feature_name not in df.columns or 'thermal_conductivity' not in df.columns:
        logger.error(f"Columns {top_feature_name} or 'thermal_conductivity' not found in data.")
        return

    x = df[top_feature_name].values
    y = df['thermal_conductivity'].values

    plt.figure(figsize=(10, 8))
    plt.scatter(x, y, alpha=0.6, label='Data Points', color='blue')
    
    # Regression line (using the model from results if available, or simple linear fit)
    if 'model' in results:
        # Assuming we can reconstruct prediction or just use the coefficients if available
        # For T035, we usually just fit a line for visualization if model object isn't serializable
        coeffs = results.get('model_coefficients', None)
        if coeffs and len(coeffs) == len(df.columns) - 1: 
            # This is tricky without knowing exact column order. 
            # Fallback to simple linear regression for the plot line
            pass
        
    # Simple linear fit for visualization line
    m, c = np.polyfit(x, y, 1)
    x_line = np.linspace(min(x), max(x), 100)
    plt.plot(x_line, m * x_line + c, 'r-', label=f'Linear Fit (r={np.corrcoef(x, y)[0,1]:.2f})')

    plt.xlabel(f'Top Predictor: {top_feature_name}')
    plt.ylabel('Thermal Conductivity (W/m·K)')
    plt.title(f'Relation between {top_feature_name} and Thermal Conductivity')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Scatter plot saved to {output_path}")

def generate_feature_importance_plot(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate a feature importance bar chart with error bars (std dev across folds).
    Requirement: T036 - Generate feature importance bar chart with error bars.
    """
    if 'feature_importance' not in results:
        raise ValueError("Feature importance data missing in regression results.")
    
    importance_data = results['feature_importance']
    if not importance_data:
        logger.warning("No feature importance data to plot.")
        return

    # Extract data for plotting
    features = [item['feature'] for item in importance_data]
    means = [item['mean_importance'] for item in importance_data]
    stds = [item['std_importance'] for item in importance_data]
    
    # Sort by mean importance for better visualization
    sorted_indices = np.argsort(means)[::-1]
    features = [features[i] for i in sorted_indices]
    means = [means[i] for i in sorted_indices]
    stds = [stds[i] for i in sorted_indices]

    plt.figure(figsize=(12, 8))
    
    # Create bar chart
    # Using a color map for visual appeal
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(features)))
    
    y_pos = np.arange(len(features))
    plt.barh(y_pos, means, xerr=stds, align='center', color=colors, capsize=5, alpha=0.8)
    
    plt.yticks(y_pos, features)
    plt.xlabel('Feature Importance (Mean ± Std Dev)')
    plt.title('Feature Importance from Ridge Regression (Cross-Validation)')
    plt.gca().invert_yaxis()  # Highest importance at top
    
    # Add value labels on bars if not too crowded
    if len(features) <= 15:
        for i, (mean, std) in enumerate(zip(means, stds)):
            plt.text(mean + (std if std > 0 else 0), i, f' {mean:.3f}±{std:.3f}', 
                     va='center', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Feature importance plot saved to {output_path}")

def save_plot_metadata(output_path: Path, results: Dict[str, Any]) -> None:
    """
    Save metadata about the generated plots.
    """
    metadata_path = output_path.parent / f"{output_path.stem}_metadata.json"
    metadata = {
        "plot_type": "feature_importance",
        "generated_at": str(pd.Timestamp.now()),
        "num_features": len(results.get('feature_importance', [])),
        "top_feature": results.get('top_feature', 'Unknown')
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to {metadata_path}")

def main():
    """
    Main entry point for generating visualizations.
    Executes T035 (Scatter Plot) and T036 (Feature Importance Plot).
    """
    setup_logger = get_logger(__name__)
    processed_dir = get_processed_dir()
    results_dir = processed_dir / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load results
        results = load_regression_results()
        
        # T035: Scatter Plot
        top_feature, _ = identify_top_predictor(results)
        scatter_path = results_dir / 'scatter_top_predictor.png'
        generate_scatter_plot(results, scatter_path, top_feature)
        
        # T036: Feature Importance Bar Chart
        importance_path = results_dir / 'feature_importance.png'
        generate_feature_importance_plot(results, importance_path)
        
        # Save metadata
        save_plot_metadata(importance_path, results)
        
        logger.info("All visualization tasks (T035, T036) completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during visualization generation: {e}")
        raise

if __name__ == "__main__":
    main()
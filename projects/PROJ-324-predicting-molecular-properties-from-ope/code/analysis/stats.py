import os
import sys
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from scipy.stats import wilcoxon

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"

# Ensure logging is configured
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def ensure_dirs():
    """Ensure required directories exist."""
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def load_baseline_predictions(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load baseline predictions (Crippen's additive model).
    Expected path: data/derived/baseline_test_predictions.csv
    """
    if filepath is None:
        filepath = DATA_DERIVED_DIR / "baseline_test_predictions.csv"
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Baseline predictions file not found: {path}")
    df = pd.read_csv(path)
    # Ensure required columns exist
    required_cols = ['smiles', 'property_name', 'experimental_value', 'predicted_value']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {path}")
    return df

def load_rf_predictions(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load Random Forest predictions.
    Expected path: data/derived/rf_test_predictions.csv
    """
    if filepath is None:
        filepath = DATA_DERIVED_DIR / "rf_test_predictions.csv"
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"RF predictions file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['smiles', 'property_name', 'experimental_value', 'predicted_value']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {path}")
    return df

def load_metadata(filepath: Optional[str] = None) -> Dict[str, Any]:
    """Load dataset metadata."""
    if filepath is None:
        filepath = PROJECT_ROOT / "data" / "raw" / "dataset_metadata.json"
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"Metadata file not found: {path}. Returning empty dict.")
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def calculate_absolute_errors(baseline_df: pd.DataFrame, rf_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate absolute errors for both models on the held-out test set.
    Merges by 'smiles' and 'property_name'.
    """
    # Filter for test set if not already (assuming input is test set)
    # Ensure we only compare matching rows
    merged = pd.merge(
        baseline_df[['smiles', 'property_name', 'experimental_value', 'predicted_value']].rename(
            columns={'predicted_value': 'baseline_pred', 'experimental_value': 'exp_val'}
        ),
        rf_df[['smiles', 'property_name', 'predicted_value']].rename(
            columns={'predicted_value': 'rf_pred'}
        ),
        on=['smiles', 'property_name'],
        how='inner'
    )

    if merged.empty:
        raise ValueError("No matching rows found between baseline and RF predictions.")

    merged['baseline_error'] = np.abs(merged['exp_val'] - merged['baseline_pred'])
    merged['rf_error'] = np.abs(merged['exp_val'] - merged['rf_pred'])
    return merged

def calculate_metrics(errors_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calculate MAE and RMSE for Baseline and RF models per property.
    """
    metrics = {}
    for prop in errors_df['property_name'].unique():
        subset = errors_df[errors_df['property_name'] == prop]
        
        baseline_mae = subset['baseline_error'].mean()
        baseline_rmse = np.sqrt((subset['baseline_error'] ** 2).mean())
        
        rf_mae = subset['rf_error'].mean()
        rf_rmse = np.sqrt((subset['rf_error'] ** 2).mean())
        
        metrics[prop] = {
            'baseline': {'mae': baseline_mae, 'rmse': baseline_rmse},
            'rf': {'mae': rf_mae, 'rmse': rf_rmse}
        }
    return metrics

def perform_wilcoxon_test(errors_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Perform paired Wilcoxon signed-rank test on absolute errors.
    Returns p-values and statistic per property.
    """
    results = {}
    for prop in errors_df['property_name'].unique():
        subset = errors_df[errors_df['property_name'] == prop]
        # Filter out rows where either error is NaN
        subset = subset.dropna(subset=['baseline_error', 'rf_error'])
        
        if len(subset) < 2:
            logger.warning(f"Not enough data for Wilcoxon test on {prop}. Skipping.")
            results[prop] = {'statistic': np.nan, 'pvalue': np.nan, 'n': len(subset)}
            continue

        stat, pval = wilcoxon(subset['baseline_error'], subset['rf_error'])
        results[prop] = {
            'statistic': float(stat),
            'pvalue': float(pval),
            'n': len(subset)
        }
    return results

def run_statistical_comparison(baseline_path: Optional[str] = None, rf_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full statistical comparison pipeline.
    """
    ensure_dirs()
    baseline_df = load_baseline_predictions(baseline_path)
    rf_df = load_rf_predictions(rf_path)
    
    errors_df = calculate_absolute_errors(baseline_df, rf_df)
    metrics = calculate_metrics(errors_df)
    wilcoxon_results = perform_wilcoxon_test(errors_df)
    
    return {
        'errors_df': errors_df,
        'metrics': metrics,
        'wilcoxon_results': wilcoxon_results
    }

def save_comparison_results(results: Dict[str, Any], filepath: Optional[str] = None):
    """Save comparison results to JSON."""
    if filepath is None:
        filepath = DATA_DERIVED_DIR / "model_comparison_results.json"
    
    # Convert numpy types to native python for JSON serialization
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(i) for i in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    serializable = convert_types(results)
    
    with open(filepath, 'w') as f:
        json.dump(serializable, f, indent=2)
    logger.info(f"Saved comparison results to {filepath}")

def generate_residual_plot(errors_df: pd.DataFrame, filepath: Optional[str] = None):
    """
    Generate and save residual distribution plots for Baseline vs RF.
    """
    if filepath is None:
        filepath = DATA_DERIVED_DIR / "model_residuals.png"
    
    plt.figure(figsize=(12, 8))
    
    for prop in errors_df['property_name'].unique():
        subset = errors_df[errors_df['property_name'] == prop]
        
        # Plot Baseline residuals
        plt.subplot(2, 1, 1)
        plt.hist(subset['baseline_error'], bins=30, alpha=0.6, label=f'Baseline ({prop})', color='blue')
        plt.xlabel('Absolute Error')
        plt.ylabel('Frequency')
        plt.title(f'Residual Distribution: {prop}')
        plt.legend()
        
        # Plot RF residuals
        plt.subplot(2, 1, 2)
        plt.hist(subset['rf_error'], bins=30, alpha=0.6, label=f'Random Forest ({prop})', color='green')
        plt.xlabel('Absolute Error')
        plt.ylabel('Frequency')
        plt.title(f'Residual Distribution: {prop}')
        plt.legend()
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved residual plot to {filepath}")

def generate_comparison_plots(metrics: Dict[str, Dict[str, float]], filepath: Optional[str] = None):
    """
    Generate comparison plots (Baseline vs RF MAE/RMSE) using the held-out test set.
    Saves to data/derived/model_comparison.png
    """
    if filepath is None:
        filepath = DATA_DERIVED_DIR / "model_comparison.png"
    
    ensure_dirs()
    
    # Prepare data for plotting
    properties = list(metrics.keys())
    if not properties:
        logger.warning("No properties found in metrics. Cannot generate plot.")
        return

    # Extract metrics
    baseline_mae = [metrics[p]['baseline']['mae'] for p in properties]
    baseline_rmse = [metrics[p]['baseline']['rmse'] for p in properties]
    rf_mae = [metrics[p]['rf']['mae'] for p in properties]
    rf_rmse = [metrics[p]['rf']['rmse'] for p in properties]

    x = np.arange(len(properties))
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # MAE Plot
    bars1 = ax1.bar(x - width/2, baseline_mae, width, label='Baseline MAE', color='skyblue', edgecolor='black')
    bars2 = ax1.bar(x + width/2, rf_mae, width, label='RF MAE', color='lightcoral', edgecolor='black')
    ax1.set_ylabel('Mean Absolute Error (MAE)')
    ax1.set_title('Model Comparison: Mean Absolute Error')
    ax1.set_xticks(x)
    ax1.set_xticklabels(properties)
    ax1.legend()
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=9)

    # RMSE Plot
    bars3 = ax2.bar(x - width/2, baseline_rmse, width, label='Baseline RMSE', color='skyblue', edgecolor='black')
    bars4 = ax2.bar(x + width/2, rf_rmse, width, label='RF RMSE', color='lightcoral', edgecolor='black')
    ax2.set_ylabel('Root Mean Square Error (RMSE)')
    ax2.set_title('Model Comparison: Root Mean Square Error')
    ax2.set_xticks(x)
    ax2.set_xticklabels(properties)
    ax2.legend()
    ax2.grid(axis='y', linestyle='--', alpha=0.7)

    # Add value labels on bars
    for bar in bars3:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    for bar in bars4:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved model comparison plot to {filepath}")

def generate_validation_protocol_summary(metadata: Dict[str, Any], test_size: int, filepath: Optional[str] = None):
    """
    Generate a Validation Protocol Summary section in the final report.
    """
    if filepath is None:
        filepath = DATA_DERIVED_DIR / "validation_protocol_summary.txt"
    
    ensure_dirs()
    
    with open(filepath, 'w') as f:
        f.write("VALIDATION PROTOCOL SUMMARY\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Held-out Test Set Size: {test_size} molecules\n\n")
        
        f.write("Source of Experimental Values:\n")
        source = metadata.get('source', 'Not Specified')
        f.write(f"  - {source}\n\n")
        
        f.write("Measurement Uncertainty:\n")
        uncertainty_status = metadata.get('measurement_uncertainty_status', 'Not Available in Source')
        f.write(f"  - Status: {uncertainty_status}\n")
        if uncertainty_status == "Not Available in Source":
            f.write("  - Note: Measurement uncertainty data was not available in the source dataset.\n")
            f.write("  - Per Marie Curie Review Response (T043), this limitation is explicitly reported.\n")
        f.write("\n")
        
        f.write("Validation Methodology:\n")
        f.write("  - Predictions compared against experimental values on a strictly held-out test set.\n")
        f.write("  - Statistical significance assessed via paired Wilcoxon signed-rank test.\n")
        f.write("  - Results framed as associational correlations, not causal mechanisms.\n")
    
    logger.info(f"Saved validation protocol summary to {filepath}")

def main():
    """
    Main entry point for T022: Generate comparison plots (Baseline vs RF).
    """
    try:
        logger.info("Starting T022: Model Comparison Plot Generation")
        
        # 1. Run statistical comparison to get metrics
        results = run_statistical_comparison()
        
        # 2. Save metrics to JSON
        save_comparison_results(results)
        
        # 3. Generate comparison plots (MAE/RMSE bar charts)
        generate_comparison_plots(results['metrics'])
        
        # 4. Generate residual distribution plot
        generate_residual_plot(results['errors_df'])
        
        # 5. Generate Validation Protocol Summary
        metadata = load_metadata()
        # Estimate test size from errors_df if available
        test_size = len(results['errors_df'].drop_duplicates(subset=['smiles'])) if not results['errors_df'].empty else 0
        generate_validation_protocol_summary(metadata, test_size)
        
        logger.info("T022 completed successfully.")
        
    except Exception as e:
        logger.error(f"T022 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
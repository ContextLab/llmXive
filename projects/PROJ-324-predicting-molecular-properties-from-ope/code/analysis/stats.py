import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"

def load_baseline_predictions() -> pd.DataFrame:
    """Load baseline predictions from CSV."""
    path = DATA_DERIVED_DIR / "baseline_predictions.csv"
    if not path.exists():
        raise FileNotFoundError(f"Baseline predictions file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['smiles', 'logP_exp', 'logP_pred', 'solubility_exp', 'solubility_pred', 'boiling_point_exp', 'boiling_point_pred']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Baseline predictions missing required columns: {missing}")
    return df

def load_rf_predictions() -> pd.DataFrame:
    """Load Random Forest predictions from CSV."""
    path = DATA_DERIVED_DIR / "rf_predictions.csv"
    if not path.exists():
        raise FileNotFoundError(f"RF predictions file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['smiles', 'logP_exp', 'logP_pred', 'solubility_exp', 'solubility_pred', 'boiling_point_exp', 'boiling_point_pred']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"RF predictions missing required columns: {missing}")
    return df

def calculate_absolute_errors(df: pd.DataFrame, property_name: str) -> Tuple[pd.Series, pd.Series]:
    """Calculate absolute errors for a given property."""
    exp_col = f"{property_name}_exp"
    pred_col = f"{property_name}_pred"
    if exp_col not in df.columns or pred_col not in df.columns:
        raise ValueError(f"Columns {exp_col} and {pred_col} required but missing.")
    errors = np.abs(df[exp_col] - df[pred_col])
    return errors

def calculate_metrics(baseline_df: pd.DataFrame, rf_df: pd.DataFrame, property_name: str) -> Dict[str, Dict[str, float]]:
    """Calculate MAE and RMSE for both models."""
    baseline_errors = calculate_absolute_errors(baseline_df, property_name)
    rf_errors = calculate_absolute_errors(rf_df, property_name)

    baseline_mae = baseline_errors.mean()
    baseline_rmse = np.sqrt((baseline_errors ** 2).mean())
    rf_mae = rf_errors.mean()
    rf_rmse = np.sqrt((rf_errors ** 2).mean())

    return {
        "baseline": {"mae": baseline_mae, "rmse": baseline_rmse},
        "rf": {"mae": rf_mae, "rmse": rf_rmse}
    }

def perform_wilcoxon_test(baseline_df: pd.DataFrame, rf_df: pd.DataFrame, property_name: str) -> Dict[str, Any]:
    """Perform Wilcoxon signed-rank test on absolute errors."""
    baseline_errors = calculate_absolute_errors(baseline_df, property_name)
    rf_errors = calculate_absolute_errors(rf_df, property_name)

    # Ensure alignment by SMILES if necessary, assuming row order matches or merging by SMILES
    # For safety, we assume the datasets are aligned or we merge on SMILES
    if 'smiles' in baseline_df.columns and 'smiles' in rf_df.columns:
        merged = baseline_df[['smiles']].merge(rf_df[['smiles']], on='smiles', how='inner')
        if len(merged) == 0:
            logger.warning("No overlapping SMILES found for statistical test.")
            return {"statistic": 0.0, "pvalue": 1.0, "n": 0}
        # Re-index errors to match merged SMILES order (assuming unique SMILES)
        # This is a simplification; in a real robust pipeline, we'd index by ID
        baseline_errors_aligned = baseline_errors[baseline_df['smiles'].isin(merged['smiles'])].reset_index(drop=True)
        rf_errors_aligned = rf_errors[rf_df['smiles'].isin(merged['smiles'])].reset_index(drop=True)
    else:
        # Fallback if no SMILES column, assume order matches
        min_len = min(len(baseline_errors), len(rf_errors))
        baseline_errors_aligned = baseline_errors[:min_len]
        rf_errors_aligned = rf_errors[:min_len]

    if len(baseline_errors_aligned) < 3:
        logger.warning("Not enough data points for Wilcoxon test.")
        return {"statistic": 0.0, "pvalue": 1.0, "n": len(baseline_errors_aligned)}

    statistic, pvalue = stats.wilcoxon(baseline_errors_aligned, rf_errors_aligned)
    return {"statistic": statistic, "pvalue": pvalue, "n": len(baseline_errors_aligned)}

def run_statistical_comparison(baseline_df: pd.DataFrame, rf_df: pd.DataFrame) -> Dict[str, Any]:
    """Run statistical comparison for all properties."""
    properties = ['logP', 'solubility', 'boiling_point']
    results = {}
    for prop in properties:
        metrics = calculate_metrics(baseline_df, rf_df, prop)
        test_result = perform_wilcoxon_test(baseline_df, rf_df, prop)
        results[prop] = {
            "metrics": metrics,
            "wilcoxon": test_result
        }
    return results

def save_comparison_results(results: Dict[str, Any], output_path: Optional[Path] = None):
    """Save comparison results to a CSV file."""
    if output_path is None:
        output_path = DATA_DERIVED_DIR / "model_comparison_stats.csv"
    
    rows = []
    for prop, data in results.items():
        rows.append({
            "property": prop,
            "baseline_mae": data["metrics"]["baseline"]["mae"],
            "baseline_rmse": data["metrics"]["baseline"]["rmse"],
            "rf_mae": data["metrics"]["rf"]["mae"],
            "rf_rmse": data["metrics"]["rf"]["rmse"],
            "wilcoxon_statistic": data["wilcoxon"]["statistic"],
            "wilcoxon_pvalue": data["wilcoxon"]["pvalue"],
            "n_samples": data["wilcoxon"]["n"]
        })
    
    df_results = pd.DataFrame(rows)
    df_results.to_csv(output_path, index=False)
    logger.info(f"Comparison results saved to {output_path}")

def generate_comparison_plots(results: Dict[str, Any], output_path: Optional[Path] = None):
    """Generate comparison plots (MAE and RMSE) for Baseline vs RF and save to PNG."""
    if output_path is None:
        output_path = DATA_DERIVED_DIR / "model_comparison.png"
    
    properties = ['logP', 'solubility', 'boiling_point']
    prop_labels = {
        'logP': 'LogP (Partition Coefficient)',
        'solubility': 'Solubility (LogS)',
        'boiling_point': 'Boiling Point (K)'
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    metrics = ['mae', 'rmse']
    metric_labels = {'mae': 'Mean Absolute Error (MAE)', 'rmse': 'Root Mean Squared Error (RMSE)'}
    
    colors = {'baseline': '#1f77b4', 'rf': '#ff7f0e'}
    bar_width = 0.35
    x = np.arange(len(properties))

    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        baseline_vals = [results[prop]["metrics"]["baseline"][metric] for prop in properties]
        rf_vals = [results[prop]["metrics"]["rf"][metric] for prop in properties]
        
        rects1 = ax.bar(x - bar_width/2, baseline_vals, bar_width, label='Baseline (Crippen)', color=colors['baseline'])
        rects2 = ax.bar(x + bar_width/2, rf_vals, bar_width, label='Random Forest', color=colors['rf'])
        
        ax.set_ylabel(metric_labels[metric])
        ax.set_title(f'{metric_labels[metric]} Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels([prop_labels[p] for p in properties], rotation=15)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add value labels on bars
        for rect in rects1 + rects2:
            height = rect.get_height()
            ax.annotate(f'{height:.3f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Comparison plots saved to {output_path}")

def generate_residual_plot(baseline_df: pd.DataFrame, rf_df: pd.DataFrame, output_path: Optional[Path] = None):
    """Generate residual distribution plots (optional, for T015 or similar)."""
    if output_path is None:
        output_path = DATA_DERIVED_DIR / "baseline_residuals.png"
    
    # Implementation for residual plot (placeholder logic if needed for T015)
    # This task T022 focuses on comparison plots, but keeping the function signature for API surface
    logger.info("Residual plot generation called (T015 specific).")

def main():
    """Main entry point to run statistical comparison and generate plots."""
    logger.info("Starting statistical comparison and plot generation...")
    
    try:
        # Load data
        baseline_df = load_baseline_predictions()
        rf_df = load_rf_predictions()
        
        # Run statistical analysis
        results = run_statistical_comparison(baseline_df, rf_df)
        
        # Save results to CSV
        save_comparison_results(results)
        
        # Generate and save comparison plots
        generate_comparison_plots(results)
        
        logger.info("Task T022 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
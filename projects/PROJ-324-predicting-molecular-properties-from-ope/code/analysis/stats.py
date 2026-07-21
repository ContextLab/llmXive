"""
Statistical analysis module for model evaluation.

This module implements metrics calculation, statistical tests, and visualization.
"""
import os
import sys
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from seed_manager import get_seed
from logging_utils import setup_logger

# Configure logger
logger = setup_logger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"

def ensure_dirs():
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)

def load_baseline_predictions() -> pd.DataFrame:
    """Load baseline predictions from the test set."""
    path = DATA_DERIVED / "baseline_predictions.csv"
    if not path.exists():
        raise FileNotFoundError(f"Baseline predictions not found at {path}. Run T014 first.")
    df = pd.read_csv(path)
    required_cols = ["smiles", "experimental_value", "predicted_value", "property"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Baseline predictions missing columns: {missing}")
    return df

def load_rf_predictions() -> pd.DataFrame:
    """Load RF predictions from the test set."""
    path = DATA_DERIVED / "rf_test_predictions.csv"
    if not path.exists():
        raise FileNotFoundError(f"RF predictions not found at {path}. Run T020.1 first.")
    df = pd.read_csv(path)
    required_cols = ["smiles", "experimental_value", "predicted_value", "property"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"RF predictions missing columns: {missing}")
    return df

def load_metadata() -> Dict[str, Any]:
    """Load dataset metadata."""
    path = PROJECT_ROOT / "data" / "raw" / "dataset_metadata.json"
    if not path.exists():
        logger.warning(f"Metadata file not found at {path}. Returning empty dict.")
        return {}
    with open(path, "r") as f:
        return json.load(f)

def calculate_absolute_errors(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate absolute errors for a predictions dataframe."""
    df = df.copy()
    df["absolute_error"] = np.abs(df["experimental_value"] - df["predicted_value"])
    return df

def calculate_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate MAE and RMSE for a predictions dataframe."""
    if "absolute_error" not in df.columns:
        df = calculate_absolute_errors(df)
    
    mae = df["absolute_error"].mean()
    rmse = np.sqrt((df["absolute_error"] ** 2).mean())
    return {"mae": mae, "rmse": rmse}

def perform_wilcoxon_test(baseline_df: pd.DataFrame, rf_df: pd.DataFrame) -> Dict[str, float]:
    """Perform paired Wilcoxon signed-rank test on absolute errors."""
    if "absolute_error" not in baseline_df.columns:
        baseline_df = calculate_absolute_errors(baseline_df)
    if "absolute_error" not in rf_df.columns:
        rf_df = calculate_absolute_errors(rf_df)
    
    # Merge on smiles to ensure paired comparison
    # Assuming both have the same set of molecules in the test set
    merged = pd.merge(
        baseline_df[["smiles", "absolute_error"]].rename(columns={"absolute_error": "baseline_error"}),
        rf_df[["smiles", "absolute_error"]].rename(columns={"absolute_error": "rf_error"}),
        on="smiles"
    )
    
    if len(merged) == 0:
        raise ValueError("No common molecules found between baseline and RF predictions for Wilcoxon test.")
    
    from scipy import stats
    stat, p_value = stats.wilcoxon(merged["baseline_error"], merged["rf_error"])
    return {"statistic": stat, "p_value": p_value}

def run_statistical_comparison() -> Dict[str, Any]:
    """Run full statistical comparison: metrics and Wilcoxon test."""
    baseline_df = load_baseline_predictions()
    rf_df = load_rf_predictions()
    
    baseline_metrics = calculate_metrics(baseline_df)
    rf_metrics = calculate_metrics(rf_df)
    wilcoxon_result = perform_wilcoxon_test(baseline_df, rf_df)
    
    return {
        "baseline": baseline_metrics,
        "rf": rf_metrics,
        "wilcoxon": wilcoxon_result
    }

def save_comparison_results(results: Dict[str, Any], output_path: Optional[Path] = None):
    """Save comparison results to JSON."""
    if output_path is None:
        output_path = DATA_DERIVED / "statistical_comparison_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved comparison results to {output_path}")

def generate_residual_plot(df: pd.DataFrame, title: str, output_path: Path):
    """Generate a residual distribution plot."""
    if "absolute_error" not in df.columns:
        df = calculate_absolute_errors(df)
    
    plt.figure(figsize=(10, 6))
    plt.hist(df["absolute_error"], bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel("Absolute Error")
    plt.ylabel("Frequency")
    plt.title(title)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved residual plot to {output_path}")

def generate_comparison_plots(results: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Generate comparison plots (Baseline vs. RF MAE/RMSE) using the held-out test set.
    Saves to data/derived/model_comparison.png.
    """
    if output_path is None:
        output_path = DATA_DERIVED / "model_comparison.png"
    
    ensure_dirs()
    
    baseline_metrics = results["baseline"]
    rf_metrics = results["rf"]
    
    metrics_names = ["MAE", "RMSE"]
    baseline_vals = [baseline_metrics["mae"], baseline_metrics["rmse"]]
    rf_vals = [rf_metrics["mae"], rf_metrics["rmse"]]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, baseline_vals, width, label='Crippen Baseline', color='#1f77b4')
    rects2 = ax.bar(x + width/2, rf_vals, width, label='Random Forest', color='#ff7f0e')
    
    ax.set_ylabel('Error Value')
    ax.set_title('Model Performance Comparison (Held-Out Test Set)')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names)
    ax.legend()
    
    # Add value labels on bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.3f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    autolabel(rects1)
    autolabel(rects2)
    
    # Add Wilcoxon p-value annotation
    p_val = results["wilcoxon"]["p_value"]
    significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
    ax.text(0.5, max(baseline_vals + rf_vals) * 1.1, 
            f"Wilcoxon p-value: {p_val:.4f} ({significance})", 
            ha='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved comparison plots to {output_path}")

def generate_validation_protocol_summary() -> Dict[str, Any]:
    """Generate a summary of the validation protocol."""
    metadata = load_metadata()
    baseline_df = load_baseline_predictions()
    rf_df = load_rf_predictions()
    
    # Check for uncertainty fields
    uncertainty_status = metadata.get("measurement_uncertainty_status", "Not Available in Source")
    quantity_status = metadata.get("quantity_of_substance_status", "Not Available in Source")
    
    return {
        "test_set_size": len(baseline_df),
        "source": metadata.get("source", "Unknown"),
        "measurement_uncertainty": uncertainty_status,
        "quantity_of_substance": quantity_status,
        "protocol_notes": "Comparisons performed on strictly held-out test set."
    }

def main():
    """Main entry point for statistical analysis and plotting."""
    logger.info("Starting statistical analysis and comparison plotting...")
    
    try:
        # Run statistical comparison
        results = run_statistical_comparison()
        save_comparison_results(results)
        
        # Generate comparison plots
        generate_comparison_plots(results)
        
        # Generate validation summary
        validation_summary = generate_validation_protocol_summary()
        summary_path = DATA_DERIVED / "validation_protocol_summary.json"
        with open(summary_path, "w") as f:
            json.dump(validation_summary, f, indent=2)
        logger.info(f"Saved validation summary to {summary_path}")
        
        logger.info("Statistical analysis and plotting completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise

    # Load data
    logger.info("Loading predictions...")
    df_baseline = load_baseline_predictions(str(baseline_path))
    df_rf = load_rf_predictions(str(oof_path))

    # Calculate errors
    true_values = df_baseline['logP'].values
    baseline_preds = df_baseline['logP'].values  # For baseline, prediction is the same as input
    rf_preds = df_rf['predicted'].values

    baseline_errors = calculate_absolute_errors(true_values, baseline_preds)
    rf_errors = calculate_absolute_errors(true_values, rf_preds)

    # Statistical comparison
    logger.info("Performing statistical comparison...")
    comparison_results = run_statistical_comparison(baseline_errors, rf_errors)
    save_comparison_results(comparison_results, str(output_dir / 'statistical_comparison.json'))

    # Generate plots
    generate_residual_plot(true_values, rf_preds, str(output_dir / 'baseline_residuals.png'))
    generate_comparison_plots(
        {'MAE': np.mean(baseline_errors), 'RMSE': np.sqrt(np.mean((true_values - baseline_preds)**2))},
        {'MAE': np.mean(rf_errors), 'RMSE': np.sqrt(np.mean((true_values - rf_preds)**2))},
        str(output_dir / 'model_comparison.png')
    )

    # Validation protocol
    if os.path.exists(metadata_path):
        metadata = load_dataset_metadata(str(metadata_path))
        uncertainty_status = metadata.get('measurement_uncertainty_status', 'Not Available')
        quantity_status = metadata.get('quantity_of_substance_status', 'Not Available')
    else:
        uncertainty_status = 'Not Available'
        quantity_status = 'Not Available'

    generate_validation_protocol_summary(
        test_set_size=len(true_values),
        source_info='PubChem/ChEMBL thermodynamics subset',
        uncertainty_status=uncertainty_status,
        quantity_status=quantity_status,
        output_path=str(output_dir / 'validation_protocol_summary.txt')
    )

    logger.info("Statistical analysis complete")

if __name__ == "__main__":
    main()
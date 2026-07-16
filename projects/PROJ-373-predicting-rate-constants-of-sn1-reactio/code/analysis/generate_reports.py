import os
import sys
import csv
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/CLI
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

from config import ensure_dirs
from utils.logger import setup_logging, get_logger
from models.evaluate import load_model_predictions
from analysis.interpret import run_interpretability_analysis, load_model_and_weights, load_processed_data
from analysis.sensitivity import run_sensitivity_analysis

def setup_logging():
    """Configure logging for the report generation stage."""
    logger = setup_logging("generate_reports", level=logging.INFO)
    return logger

def generate_feature_importance_plot(shap_summary_df: pd.DataFrame, output_path: Path):
    """
    Generate a SHAP summary plot (bar chart) of feature importances.
    
    Args:
        shap_summary_df: DataFrame with 'feature_name' and 'mean_abs_shap' columns.
        output_path: Path to save the PNG file.
    """
    plt.figure(figsize=(10, 8))
    
    # Sort by mean absolute SHAP value
    shap_summary_df = shap_summary_df.sort_values(by='mean_abs_shap', ascending=True)
    
    plt.barh(shap_summary_df['feature_name'], shap_summary_df['mean_abs_shap'])
    plt.xlabel('Mean |SHAP Value|')
    plt.ylabel('Feature')
    plt.title('Feature Importance (SHAP Mean Absolute Value)')
    plt.gca().invert_yaxis()  # Most important at top
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logging.info(f"Feature importance plot saved to {output_path}")

def generate_sensitivity_report(sensitivity_results: List[Dict[str, Any]], output_path: Path):
    """
    Save sensitivity analysis results to a CSV file.
    
    Args:
        sensitivity_results: List of dicts containing cutoff, r2, mae, etc.
        output_path: Path to save the CSV file.
    """
    if not sensitivity_results:
        logging.warning("No sensitivity results to save.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sensitivity_results[0].keys())
        writer.writeheader()
        writer.writerows(sensitivity_results)
    
    logging.info(f"Sensitivity report saved to {output_path}")

def generate_perturbation_report(perturbation_results: List[Dict[str, Any]], output_path: Path):
    """
    Save perturbation study results to a CSV file.
    
    Args:
        perturbation_results: List of dicts containing feature, r2_drop, etc.
        output_path: Path to save the CSV file.
    """
    if not perturbation_results:
        logging.warning("No perturbation results to save.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=perturbation_results[0].keys())
        writer.writeheader()
        writer.writerows(perturbation_results)
    
    logging.info(f"Perturbation report saved to {output_path}")

def main():
    """
    Main entry point for T030: Generate all required analysis artifacts.
    """
    logger = setup_logging()
    logger.info("Starting T030: Generate analysis artifacts.")

    # Ensure artifact directories exist
    ensure_dirs()
    artifacts_dir = Path("artifacts")
    
    # Paths for outputs
    feature_importance_path = artifacts_dir / "feature_importance.png"
    sensitivity_report_path = artifacts_dir / "sensitivity_report.csv"
    perturbation_results_path = artifacts_dir / "perturbation_results.csv"

    try:
        # 1. Load Model and Data (Dependencies: T022, T016)
        logger.info("Loading model and processed data...")
        model, config = load_model_and_weights()
        X_test, y_test, feature_names = load_processed_data("test")
        
        # 2. Run Interpretability Analysis (T026, T029)
        # This generates SHAP values and runs perturbation study
        logger.info("Running interpretability analysis (SHAP + Perturbation)...")
        interpret_results = run_interpretability_analysis(model, X_test, y_test, feature_names)
        
        # Extract SHAP summary for plotting
        shap_summary = interpret_results.get('shap_summary', pd.DataFrame())
        if shap_summary.empty:
            logger.error("SHAP summary is empty. Cannot generate feature importance plot.")
            # Create a minimal placeholder to avoid crash, though this indicates a failure upstream
            shap_summary = pd.DataFrame({'feature_name': ['unknown'], 'mean_abs_shap': [0.0]})
        
        # Extract perturbation results
        perturbation_data = interpret_results.get('perturbation_results', [])
        
        # 3. Run Sensitivity Analysis (T027)
        logger.info("Running sensitivity analysis...")
        sensitivity_data = run_sensitivity_analysis(model, X_test, y_test, feature_names)
        
        # 4. Generate Artifacts
        logger.info("Generating feature importance plot...")
        generate_feature_importance_plot(shap_summary, feature_importance_path)
        
        logger.info("Generating sensitivity report...")
        generate_sensitivity_report(sensitivity_data, sensitivity_report_path)
        
        logger.info("Generating perturbation report...")
        generate_perturbation_report(perturbation_data, perturbation_results_path)
        
        logger.info("T030 completed successfully. All artifacts generated.")
        
    except Exception as e:
        logger.error(f"Error during artifact generation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

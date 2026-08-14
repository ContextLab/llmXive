"""
T037: Save all analysis artifacts (plots, reports, SHAP values) to data/processed/analysis/.

This script aggregates outputs from previous analysis tasks (T032-T036) and ensures
they are saved to the correct directory with proper naming conventions.
"""
import os
import sys
import json
import logging
import pickle
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, set_log_level
from models.interpret import save_shap_values, generate_shap_summary_plot, generate_feature_report
from models.stability_report import load_bootstrap_results, generate_stability_report, save_report
from models.stability_analysis import run_stability_analysis
from data.loader import iterate_smiles
from utils.config import get_config_summary

def ensure_analysis_dir():
    """Ensure the analysis output directory exists."""
    analysis_dir = project_root / "data" / "processed" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    return analysis_dir

def save_shap_artifacts(analysis_dir: Path):
    """Save SHAP values, summary plot, and feature report."""
    logger = get_logger(__name__)
    
    # Load model and data
    model_path = project_root / "data" / "processed" / "model.pkl"
    data_path = project_root / "data" / "processed" / "descriptors.parquet"
    
    if not model_path.exists() or not data_path.exists():
        logger.warning("Model or descriptors file not found. Skipping SHAP artifacts.")
        return
    
    # Save SHAP values
    shap_values_path = analysis_dir / "shap_values.pkl"
    save_shap_values(model_path, data_path, shap_values_path)
    logger.info(f"Saved SHAP values to {shap_values_path}")
    
    # Generate and save SHAP summary plot
    plot_path = analysis_dir / "shap_summary_plot.png"
    generate_shap_summary_plot(model_path, data_path, plot_path)
    logger.info(f"Saved SHAP summary plot to {plot_path}")
    
    # Generate and save feature report
    report_path = analysis_dir / "feature_importance_report.json"
    generate_feature_report(model_path, data_path, report_path)
    logger.info(f"Saved feature importance report to {report_path}")

def save_stability_artifacts(analysis_dir: Path):
    """Save stability analysis results and reports."""
    logger = get_logger(__name__)
    
    model_path = project_root / "data" / "processed" / "model.pkl"
    data_path = project_root / "data" / "processed" / "descriptors.parquet"
    
    if not model_path.exists() or not data_path.exists():
        logger.warning("Model or descriptors file not found. Skipping stability artifacts.")
        return
    
    # Run stability analysis (if not already done)
    bootstrap_results_path = analysis_dir / "bootstrap_results.pkl"
    
    # Check if bootstrap results already exist
    if not bootstrap_results_path.exists():
        logger.info("Running stability analysis...")
        # Run stability analysis and save results
        # This assumes T033a/T033b/T034a/T034b/T035 have been run
        # We'll call the stability analysis function
        try:
            # Import and run stability analysis
            from models.stability_analysis import run_stability_analysis
            results = run_stability_analysis(model_path, data_path, n_bootstrap=10)
            with open(bootstrap_results_path, 'wb') as f:
                pickle.dump(results, f)
            logger.info(f"Saved bootstrap results to {bootstrap_results_path}")
        except Exception as e:
            logger.warning(f"Could not run stability analysis: {e}. Skipping.")
            return
    
    # Generate and save stability report
    report_path = analysis_dir / "stability_report.json"
    try:
        results = load_bootstrap_results(bootstrap_results_path)
        report = generate_stability_report(results)
        save_report(report, report_path)
        logger.info(f"Saved stability report to {report_path}")
    except Exception as e:
        logger.warning(f"Could not generate stability report: {e}")

def save_metadata(analysis_dir: Path):
    """Save project metadata and configuration summary."""
    logger = get_logger(__name__)
    
    metadata = {
        "project": "PROJ-091-predicting-molecular-polarity-from-smile",
        "task": "T037",
        "description": "Save all analysis artifacts (plots, reports, SHAP values)",
        "config_summary": get_config_summary(),
        "artifacts": [
            "shap_values.pkl",
            "shap_summary_plot.png",
            "feature_importance_report.json",
            "bootstrap_results.pkl",
            "stability_report.json",
            "metadata.json"
        ]
    }
    
    metadata_path = analysis_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

def main():
    """Main entry point for saving analysis artifacts."""
    # Setup logging
    set_log_level(logging.INFO)
    logger = get_logger(__name__)
    
    logger.info("Starting T037: Save analysis artifacts")
    
    # Ensure analysis directory exists
    analysis_dir = ensure_analysis_dir()
    logger.info(f"Analysis directory: {analysis_dir}")
    
    # Save SHAP artifacts
    save_shap_artifacts(analysis_dir)
    
    # Save stability artifacts
    save_stability_artifacts(analysis_dir)
    
    # Save metadata
    save_metadata(analysis_dir)
    
    logger.info("T037 completed successfully")

if __name__ == "__main__":
    main()
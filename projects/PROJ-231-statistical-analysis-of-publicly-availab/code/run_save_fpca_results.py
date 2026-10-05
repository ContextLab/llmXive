"""
Script to save FPCA results (eigenvalues, eigenfunctions, variance metrics) to disk.
This script is the entry point for Task T024.
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path

from fpca import load_b_spline_coefficients, perform_fpca, reconstruct_eigenfunctions, calculate_cumulative_variance, run_fpca_pipeline
from config import get_project_root, get_data_dir, get_artifacts_dir
from logging_config import setup_logging, get_logger
from update_state import update_state

def save_fpca_results(fpca_results: dict, output_dir: Path, logger: logging.Logger) -> None:
    """
    Save FPCA results to the specified output directory.
    
    Args:
        fpca_results: Dictionary containing eigenvalues, eigenfunctions, variance metrics, etc.
        output_dir: Path to the directory where results will be saved.
        logger: Logger instance.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save eigenvalues
    eigenvalues_path = output_dir / "eigenvalues.pkl"
    with open(eigenvalues_path, 'wb') as f:
        pickle.dump(fpca_results['eigenvalues'], f)
    logger.info(f"Saved eigenvalues to {eigenvalues_path}")
    
    # Save eigenfunctions
    eigenfunctions_path = output_dir / "eigenfunctions.pkl"
    with open(eigenfunctions_path, 'wb') as f:
        pickle.dump(fpca_results['eigenfunctions'], f)
    logger.info(f"Saved eigenfunctions to {eigenfunctions_path}")
    
    # Save variance metrics (JSON)
    variance_metrics_path = output_dir / "variance_metrics.json"
    with open(variance_metrics_path, 'w') as f:
        json.dump(fpca_results['variance_metrics'], f, indent=2)
    logger.info(f"Saved variance metrics to {variance_metrics_path}")
    
    # Save full results for downstream tasks (e.g., robustness)
    full_results_path = output_dir / "fpca_full_results.pkl"
    with open(full_results_path, 'wb') as f:
        pickle.dump(fpca_results, f)
    logger.info(f"Saved full FPCA results to {full_results_path}")

def main():
    """
    Main entry point for saving FPCA results.
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting FPCA results saving process (Task T024).")
    
    # Get directories
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    
    # Check if input data exists
    coefficients_path = processed_dir / "b_spline_coefficients.pkl"
    if not coefficients_path.exists():
        logger.error(f"B-spline coefficients not found at {coefficients_path}. "
                     "Please run the ingestion and basis expansion pipeline first.")
        sys.exit(1)
    
    # Load B-spline coefficients
    logger.info(f"Loading B-spline coefficients from {coefficients_path}")
    coefficients_data = load_b_spline_coefficients(coefficients_path)
    
    # Perform FPCA
    logger.info("Performing FPCA...")
    fpca_results = run_fpca_pipeline(coefficients_data)
    
    # Save results
    logger.info("Saving FPCA results...")
    save_fpca_results(fpca_results, processed_dir, logger)
    
    # Update state
    logger.info("Updating project state...")
    update_state()
    
    logger.info("FPCA results saving process completed successfully.")

if __name__ == "__main__":
    main()
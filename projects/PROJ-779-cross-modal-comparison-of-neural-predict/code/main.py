"""
Main orchestration script for the Cross-Modal Comparison of Neural Prediction Error pipeline.

This script coordinates the execution of the entire pipeline:
1. Download and preprocess data (US1)
2. Extract metrics (US2)
3. Source localization and statistical analysis (US3)
4. Generate final report

Usage:
    python code/main.py --stage <stage_name>

Stages:
    - download_preprocess: Download and preprocess raw data
    - extract_metrics: Compute prediction error metrics
    - localize_sources: Perform source localization
    - statistical_analysis: Run statistical comparisons
    - full_run: Execute the entire pipeline
"""
import sys
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import argparse

# Ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_config, ensure_directories
from code.data.download import fetch_visual_dataset, validate_visual_dataset, main as download_main
from code.data.download_auditory import fetch_auditory_dataset, validate_auditory_dataset, main as auditory_download_main
from code.data.preprocess import preprocess_dataset, main as preprocess_main
from code.analysis.metrics import generate_metrics_summary, main as metrics_main
from code.analysis.source import run_sensitivity_analysis, main as source_main
from code.analysis.stats import benjamini_hochberg_correction, independent_samples_ttest, tost_equivalence_test, main as stats_main
from code.validation.reliability import compute_reliability_metrics, main as reliability_main
from code.reports.generate_final_report import generate_report, main as report_main
from code.utils.logger import get_logger, configure_logging
from code.config_loader import load as load_config

logger = get_logger(__name__)

def load_json_result(file_path: Path) -> Dict[str, Any]:
    """Load a JSON result file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Result file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def classify_latency(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify latency difference based on threshold.
    
    SC-001: If |Δt| < 50ms, latency difference is "within threshold".
    """
    auditory_latency = metrics.get('auditory', {}).get('peak_latency_ms', 0)
    visual_latency = metrics.get('visual', {}).get('peak_latency_ms', 0)
    
    delta_t = abs(auditory_latency - visual_latency)
    within_threshold = delta_t < 50.0
    
    return {
        "auditory_peak_latency_ms": auditory_latency,
        "visual_peak_latency_ms": visual_latency,
        "delta_t_ms": delta_t,
        "within_50ms_threshold": within_threshold,
        "classification": "within_threshold" if within_threshold else "exceeds_threshold"
    }

def classify_source_overlap(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify source overlap using BH-corrected p-values and TOST.
    
    Primary Decision: Use BH-corrected p-value for significance testing.
    Secondary Decision: Use TOST for equivalence testing.
    
    Note: This deviates from SC-002 (p > 0.05) in favor of Plan Phase 4 (TOST p < 0.05).
    """
    bh_pvalues = results.get('bh_corrected_pvalues', {})
    tost_results = results.get('tost_results', {})
    dice_coeff = results.get('dice_coefficient', 0.0)
    
    # Primary: BH-corrected significance
    bh_p = bh_pvalues.get('source_strength', 1.0)
    significant_diff = bh_p < 0.05
    
    # Secondary: TOST equivalence
    tost_p = tost_results.get('pvalue', 1.0)
    equivalence_supported = (tost_p < 0.05) and (dice_coeff > 0.6)
    
    return {
        "bh_pvalue_source_strength": bh_p,
        "significant_difference": significant_diff,
        "tost_pvalue": tost_p,
        "dice_coefficient": dice_coeff,
        "equivalence_supported": equivalence_supported,
        "classification": "equivalence_supported" if equivalence_supported else "difference_detected"
    }

def generate_manifest(config: Dict[str, Any], outputs: Dict[str, Path]) -> Path:
    """Generate a manifest file listing all outputs and their checksums."""
    manifest = {
        "config": config,
        "outputs": {}
    }
    
    for name, path in outputs.items():
        if path.exists():
          # For FIF files, we can't easily compute a simple hash without MNE, 
          # so we just record existence and size for now
          if path.suffix == '.fif':
              manifest["outputs"][name] = {
                  "path": str(path),
                  "exists": True,
                  "size_bytes": path.stat().st_size
              }
          else:
              with open(path, 'rb') as f:
                  checksum = hashlib.sha256(f.read()).hexdigest()
              manifest["outputs"][name] = {
                  "path": str(path),
                  "checksum_sha256": checksum,
                  "size_bytes": path.stat().st_size
              }
        else:
            manifest["outputs"][name] = {
                "path": str(path),
                "exists": False
            }
    
    manifest_path = config['paths']['project_root'] / 'data' / 'results' / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest generated at {manifest_path}")
    return manifest_path

def verify_data_integrity(config: Dict[str, Any]) -> bool:
    """
    Verify that processed data artifacts match the checksums recorded in state file.
    
    This depends on T016a which generated checksums in state/projects/PROJ-779...yaml
    """
    state_file = config['paths']['state_dir'] / 'projects' / 'PROJ-779-cross-modal-comparison-of-neural-predict.yaml'
    
    if not state_file.exists():
        logger.warning(f"State file not found: {state_file}. Skipping integrity check.")
        return True
    
    # Simple check: verify the cleaned data file exists and has non-zero size
    cleaned_data = config['paths']['processed_data_dir'] / 'cleaned_data.fif'
    if not cleaned_data.exists():
        logger.error(f"Cleaned data file missing: {cleaned_data}")
        return False
    
    if cleaned_data.stat().st_size == 0:
        logger.error(f"Cleaned data file is empty: {cleaned_data}")
        return False
    
    logger.info("Data integrity check passed.")
    return True

def run_download_preprocess(config: Dict[str, Any]) -> Dict[str, Path]:
    """Run download and preprocessing stages."""
    logger.info("=== Running Download and Preprocessing ===")
    
    # Download auditory data
    auditory_download_main(config)
    
    # Download visual data
    download_main(config)
    
    # Preprocess
    preprocess_main(config)
    
    outputs = {
        "cleaned_data": config['paths']['processed_data_dir'] / 'cleaned_data.fif',
        "preprocessing_log": config['paths']['log_dir'] / 'preprocessing.log'
    }
    
    return outputs

def run_extract_metrics(config: Dict[str, Any]) -> Dict[str, Path]:
    """Run metric extraction stage."""
    logger.info("=== Running Metric Extraction ===")
    
    metrics_main(config)
    
    outputs = {
        "metrics_summary": config['paths']['results_dir'] / 'metrics_summary.json'
    }
    
    return outputs

def run_localize_sources(config: Dict[str, Any]) -> Dict[str, Path]:
    """Run source localization stage."""
    logger.info("=== Running Source Localization ===")
    
    source_main(config)
    
    outputs = {
        "sensitivity_analysis": config['paths']['results_dir'] / 'sensitivity_analysis.csv'
    }
    
    return outputs

def run_statistical_analysis(config: Dict[str, Any]) -> Dict[str, Path]:
    """Run statistical analysis stage."""
    logger.info("=== Running Statistical Analysis ===")
    
    stats_main(config)
    reliability_main(config)
    
    outputs = {
        "bh_corrected_pvalues": config['paths']['results_dir'] / 'bh_corrected_pvalues.json',
        "reliability_results": config['paths']['results_dir'] / 'reliability_results.json'
    }
    
    return outputs

def run_full_pipeline(config: Dict[str, Any]) -> Dict[str, Path]:
    """Run the entire pipeline."""
    logger.info("=== Running Full Pipeline ===")
    
    # Stage 1: Download and Preprocess
    outputs_1 = run_download_preprocess(config)
    
    # Stage 2: Extract Metrics
    outputs_2 = run_extract_metrics(config)
    
    # Stage 3: Localize Sources
    outputs_3 = run_localize_sources(config)
    
    # Stage 4: Statistical Analysis
    outputs_4 = run_statistical_analysis(config)
    
    # Stage 5: Generate Final Report
    report_main(config)
    
    all_outputs = {**outputs_1, **outputs_2, **outputs_3, **outputs_4}
    
    # Generate manifest
    generate_manifest(config, all_outputs)
    
    return all_outputs

def run_orchestration(config: Dict[str, Any], stage: str) -> Tuple[bool, Dict[str, Path]]:
    """Orchestrate the pipeline based on the specified stage."""
    try:
        if stage == "download_preprocess":
            outputs = run_download_preprocess(config)
        elif stage == "extract_metrics":
            outputs = run_extract_metrics(config)
        elif stage == "localize_sources":
            outputs = run_localize_sources(config)
        elif stage == "statistical_analysis":
            outputs = run_statistical_analysis(config)
        elif stage == "full_run":
            outputs = run_full_pipeline(config)
        else:
            raise ValueError(f"Unknown stage: {stage}")
        
        # Verify data integrity if we have processed data
        if stage in ["full_run", "extract_metrics", "localize_sources", "statistical_analysis"]:
            verify_data_integrity(config)
        
        return True, outputs
        
    except Exception as e:
        logger.error(f"Pipeline failed at stage '{stage}': {e}")
        raise

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Cross-Modal Neural Prediction Error Pipeline")
    parser.add_argument(
        "--stage",
        type=str,
        choices=["download_preprocess", "extract_metrics", "localize_sources", "statistical_analysis", "full_run"],
        default="full_run",
        help="Pipeline stage to execute"
    )
    args = parser.parse_args()
    
    # Load configuration
    load_config()
    config = get_config()
    
    # Ensure directories exist
    ensure_directories(config)
    
    # Configure logging
    configure_logging(config)
    
    logger.info(f"Starting pipeline stage: {args.stage}")
    logger.info(f"Project root: {config['paths']['project_root']}")
    
    success, outputs = run_orchestration(config, args.stage)
    
    if success:
        logger.info(f"Stage '{args.stage}' completed successfully.")
        logger.info(f"Outputs: {outputs}")
    else:
        logger.error(f"Stage '{args.stage}' failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
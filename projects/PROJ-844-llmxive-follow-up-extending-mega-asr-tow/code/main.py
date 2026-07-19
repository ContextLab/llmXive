"""
Main orchestration script for the llmXive Mega-ASR Semantic Collapse Threshold pipeline.
Handles pre-flight checks, stress curve generation, and result aggregation.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import traceback

# Import from sibling modules using verified API surface
from config import get_config
from data_loader import load_librispeech_subset, load_coraa_mupe_asr_subset, verify_dataset_coverage_for_scenarios
from distortion_engine import DistortionEngine, generate_all_distortion_vectors
from metrics import MetricsCalculator, compute_baseline_sss_and_wer, compute_hvcm_target
from human_validation import generate_annotation_csv
from models import generate_interaction_terms, validate_hvcm_target
from statistics import apply_bonferroni_correction, generate_pvalue_report
from analysis import check_threshold_stability, generate_stability_report
from monitor_resources import monitor_resources
from hash_updater import update_hashes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def pre_flight_data_check(config: Dict[str, Any]) -> bool:
    """
    T038: Pre-flight check to validate real dataset availability.
    Ensures LibriSpeech and CORAA-MUPE-ASR are downloadable and accessible
    before initiating the distortion loop. Raises RuntimeError if download fails.
    """
    logger.info("Starting pre-flight data validation...")
    
    # Check LibriSpeech
    logger.info(f"Checking LibriSpeech availability at: {config['raw_path']}/librispeech")
    try:
        # Attempt to load a small subset to verify connectivity and integrity
        # This forces the actual download logic in data_loader.py to run
        librispeech_data = load_librispeech_subset(config)
        if not librispeech_data or len(librispeech_data) == 0:
            raise RuntimeError("LibriSpeech dataset loaded but contains no data.")
        logger.info(f"✓ LibriSpeech verified: {len(librispeech_data)} samples accessible.")
    except Exception as e:
        logger.error(f"✗ LibriSpeech verification failed: {e}")
        raise RuntimeError(f"CRITICAL: Real dataset LibriSpeech is not accessible. {e}") from e

    # Check CORAA-MUPE-ASR
    logger.info(f"Checking CORAA-MUPE-ASR availability at: {config['raw_path']}/coraa")
    try:
        coraa_data = load_coraa_mupe_asr_subset(config)
        if not coraa_data or len(coraa_data) == 0:
            raise RuntimeError("CORAA-MUPE-ASR dataset loaded but contains no data.")
        logger.info(f"✓ CORAA-MUPE-ASR verified: {len(coraa_data)} samples accessible.")
    except Exception as e:
        logger.error(f"✗ CORAA-MUPE-ASR verification failed: {e}")
        raise RuntimeError(f"CRITICAL: Real dataset CORAA-MUPE-ASR is not accessible. {e}") from e

    # Verify distortion coverage logic
    logger.info("Verifying distortion scenario coverage...")
    try:
        verify_dataset_coverage_for_scenarios(config)
        logger.info("✓ Distortion scenario coverage verified.")
    except Exception as e:
        logger.warning(f"Distortion coverage check produced warnings: {e}")
        # We allow this to proceed with warnings as per FR-001 edge cases,
        # but we log it clearly.

    logger.info("Pre-flight data validation PASSED.")
    return True

def run_stress_curve_generation(config: Dict[str, Any]) -> None:
    """
    Orchestrates the generation of stress curves, collapse points, and HVCM targets.
    """
    logger.info("Starting stress curve generation pipeline...")
    
    # 1. Pre-flight check (T038)
    pre_flight_data_check(config)

    # 2. Load Data
    logger.info("Loading stratified subsets...")
    librispeech_data = load_librispeech_subset(config)
    coraa_data = load_coraa_mupe_asr_subset(config)
    combined_data = librispeech_data + coraa_data
    logger.info(f"Total samples loaded: {len(combined_data)}")

    # 3. Generate Distortion Vectors
    logger.info("Generating distortion vectors...")
    distortion_vectors = generate_all_distortion_vectors(config)
    logger.info(f"Generated {len(distortion_vectors)} distortion vectors.")

    # 4. Initialize Metrics Calculator
    calculator = MetricsCalculator(config)
    
    # 5. Generate Stress Curves (T015)
    stress_curves = []
    logger.info("Applying distortions and computing metrics...")
    for clip in combined_data:
        for vector in distortion_vectors:
            try:
                curve_row = calculator.generate_stress_curve_for_clip(clip, vector)
                if curve_row:
                    stress_curves.append(curve_row)
            except Exception as e:
                logger.warning(f"Failed to process clip {clip.get('id', 'unknown')} with vector {vector.id}: {e}")
                continue
    
    # Save stress curves
    stress_curve_path = Path(config['derived_path']) / 'stress_curves.parquet'
    calculator.save_stress_curves(stress_curves, stress_curve_path)
    logger.info(f"Saved stress curves to {stress_curve_path}")

    # 6. Compute Baselines (T020b, T020c)
    logger.info("Computing baseline SSS and WER...")
    baselines = compute_baseline_sss_and_wer(stress_curves, config)
    baseline_sss_path = Path(config['derived_path']) / 'baseline_sss.json'
    baseline_wer_path = Path(config['derived_path']) / 'baseline_wer.json'
    with open(baseline_sss_path, 'w') as f:
        json.dump(baselines['sss'], f, indent=2)
    with open(baseline_wer_path, 'w') as f:
        json.dump(baselines['wer'], f, indent=2)
    logger.info(f"Saved baselines to {baseline_sss_path} and {baseline_wer_path}")

    # 7. Identify Collapse Points (T022)
    logger.info("Identifying collapse points...")
    collapse_points = calculator.identify_collapse_points(stress_curves, baselines)
    collapse_path = Path(config['derived_path']) / 'collapse_points.parquet'
    calculator.save_collapse_points(collapse_points, collapse_path)
    logger.info(f"Saved collapse points to {collapse_path}")

    # 8. Human Validation (T030a)
    logger.info("Generating human validation annotations...")
    human_annotations_path = Path(config['validation_path']) / 'human_annotations.csv'
    generate_annotation_csv(combined_data, distortion_vectors, human_annotations_path, config)
    logger.info(f"Saved human annotations to {human_annotations_path}")

    # 9. Compute HVCM (T030b)
    logger.info("Computing Human-Validated Collapse Margin (HVCM)...")
    hvcm_data = compute_hvcm_target(stress_curves, collapse_points, human_annotations_path, config)
    
    # 10. Generate Interaction Terms & Train Model (T025a, T026)
    logger.info("Generating interaction terms and training regression model...")
    features, targets = generate_interaction_terms(hvcm_data, config)
    validate_hvcm_target(targets) # FR-011 Safety Check
    
    regression_results = calculator.train_regression_model(features, targets, config)
    regression_results_path = Path(config['derived_path']) / 'regression_results.json'
    with open(regression_results_path, 'w') as f:
        json.dump(regression_results, f, indent=2)
    logger.info(f"Saved regression results to {regression_results_path}")

    # 11. Statistical Correction (T025)
    logger.info("Applying statistical corrections...")
    corrected_pvalues = apply_bonferroni_correction(regression_results, config)
    pvalue_path = Path(config['derived_path']) / 'corrected_pvalues.json'
    with open(pvalue_path, 'w') as f:
        json.dump(corrected_pvalues, f, indent=2)
    logger.info(f"Saved corrected p-values to {pvalue_path}")

    # 12. Sensitivity Analysis (T027, T043)
    logger.info("Running sensitivity analysis...")
    sensitivity_results = check_threshold_stability(regression_results, hvcm_data, config)
    sensitivity_path = Path(config['derived_path']) / 'sensitivity_analysis.csv'
    generate_stability_report(sensitivity_results, sensitivity_path)
    logger.info(f"Saved sensitivity analysis to {sensitivity_path}")

    # 13. Cross-Model Similarity (T028)
    # Note: Assuming single model for now as per CPU constraints, but structure allows expansion
    logger.info("Skipping cross-model similarity (single model run).")

    logger.info("Pipeline execution completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="llmXive Mega-ASR Semantic Collapse Pipeline")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--check-only', action='store_true', help='Run only pre-flight checks')
    args = parser.parse_args()

    try:
        config = get_config(args.config)
        
        if args.check_only:
            pre_flight_data_check(config)
            logger.info("Pre-flight check passed. Exiting.")
            return

        # Run the full pipeline with resource monitoring
        monitor_resources(run_stress_curve_generation, config)
        
        # Update hashes for reproducibility
        update_hashes(config)

    except RuntimeError as e:
        logger.critical(f"Pipeline failed due to runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed with unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
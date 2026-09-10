import argparse
import logging
import sys
from pathlib import Path
import json

from utils.config import get_config, load_config_from_yaml, set_seed
from utils.logger import get_logger, setup_file_logging
from utils.io import load_json, save_json

# US1 Imports
from preprocessing.data_validation import validate_dataset_structure, validate_participant_data
from preprocessing.data_download import DataDownloadError, get_dataset_client, get_participant_list, check_participant_assets, download_participant_data, write_exclusions
from preprocessing.motion_correction import calculate_framewise_displacement, extract_motion_parameters, correct_motion
from preprocessing.normalization import normalize_to_mni, normalize_participant
from preprocessing.smoothing import smooth_volume, smooth_participant_data
from preprocessing.roi_extraction import load_roi_masks, extract_roi_timeseries
from preprocessing.qc_filter import calculate_motion_exclusion_metrics, apply_qc_filter
from preprocessing.qc_reporter import QCReportError, load_exclusion_data, calculate_exclusion_rate, assess_stability, generate_qc_summary

# US2 Imports
from modeling.synthetic_data_generator import generate_trial_data, generate_synthetic_dataset
from modeling.runtime_enforcer import RuntimeLimitExceeded, SampleSizeReductionRequired, RuntimeEnforcer, main as runtime_main
from modeling.belief_updater import load_behavioral_data, prepare_model_data, build_hierarchical_model, run_mcmc_sampling, extract_posterior_samples, save_model_results
from modeling.validation import check_convergence, validate_and_restart, save_validation_report
from modeling.convergence_reporter import ConvergenceReportError, load_valid_participants, load_convergence_logs, calculate_convergence_rate, verify_threshold, generate_convergence_report
from modeling.prediction import PredictionError, load_posterior_samples, load_behavioral_data_for_prediction, predict_choice, generate_predictions, compute_accuracy, run_prediction_pipeline
from modeling.model_output import ModelOutputError, load_posterior_samples as load_posterior_samples_model, extract_individual_alphas, extract_group_hyperparameters, save_model_output, generate_model_output

# US3 Imports (P3)
# Note: The actual analysis modules (glm_analysis, partial_correlation, etc.) are not yet implemented.
# This integration task sets up the data flow from P2 results to the analysis stage.
from analysis.glm_analysis import GLMAnalysisError, run_glm_analysis
from analysis.partial_correlation import PartialCorrelationError, run_partial_correlation
from analysis.permutation_test import PermutationTestError, run_permutation_test
from analysis.confound_control import run_confound_control
from analysis.loso_validation import run_loso_validation
from analysis.sensitivity_sweeper import run_sensitivity_sweep
from analysis.sensitivity_reporter import run_sensitivity_reporting

# Reporting Imports (P4/P5)
from reporting.generate_stats import generate_final_stats
from reporting.generate_figures import generate_figures
from reporting.generate_research_doc import generate_research_document

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Neural Mechanisms Adaptive Decision-Making Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--stage", type=str, choices=["p1", "p2", "p3", "all"], default="all",
                        help="Which stage to run: P1 (Data), P2 (Model), P3 (Analysis), or All")
    parser.add_argument("--data-root", type=str, default="data", help="Root directory for data")
    parser.add_argument("--state-root", type=str, default="state", help="Root directory for state files")
    parser.add_argument("--output-root", type=str, default="data", help="Root directory for outputs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def run_p1_integration(args):
    """
    Execute User Story 1: Data Acquisition and Preprocessing Pipeline.
    """
    logger.info("Starting P1 Integration: Data Acquisition and Preprocessing")
    
    # 1. Validate and Download
    logger.info("Validating dataset structure...")
    validate_dataset_structure(args.data_root)
    
    # 2. Motion Correction, Normalization, Smoothing, ROI Extraction
    # (Implementation details depend on specific participant lists from data_download)
    # This block assumes T013-T017 are functional and produce intermediate files.
    # T018 (QC Filter) and T018b (QC Reporter) must run here.
    
    logger.info("Running QC and generating summary report...")
    # This calls the reporter which should write to data/reports/qc_summary.json
    generate_qc_summary(args.data_root, args.output_root)
    
    logger.info("P1 Integration complete.")


def run_p2_integration(args):
    """
    Execute User Story 2: Computational Modeling of Belief Updating.
    """
    logger.info("Starting P2 Integration: Belief Updating Modeling")
    
    # 1. Load valid participants from P1
    valid_participants = load_valid_participants(args.output_root)
    
    # 2. Run Belief Updater (T024)
    logger.info("Running hierarchical Bayesian model...")
    # Assumes run_mcmc_sampling handles the runtime constraints via RuntimeEnforcer
    results = run_mcmc_sampling(valid_participants, args.data_root, args.output_root)
    
    # 3. Validate Convergence (T025)
    logger.info("Validating model convergence...")
    convergence_report = generate_convergence_report(args.output_root)
    
    # 4. Generate Model Output (T027)
    logger.info("Saving model outputs...")
    save_model_output(results, args.output_root)
    
    logger.info("P2 Integration complete. Alpha parameters saved.")
    return convergence_report


def run_p3_integration(args):
    """
    Execute User Story 3: Neural-Behavioral Correlation and Hypothesis Testing.
    This task (T037) specifically ensures data flow from P2 (alpha parameters) to P3.
    """
    logger.info("Starting P3 Integration: Neural-Behavioral Correlation Analysis")
    
    # 1. Load P2 Results (Alpha Parameters)
    logger.info("Loading alpha parameters from P2...")
    try:
        alphas = extract_individual_alphas(args.output_root)
        logger.info(f"Loaded alpha parameters for {len(alphas)} participants.")
    except FileNotFoundError as e:
        logger.error("P2 results not found. Ensure P2 integration has run successfully.")
        raise RuntimeError("P2 results missing. Cannot proceed with P3.") from e
    
    # 2. Load P1 Preprocessed Data (ROI Time-series)
    logger.info("Loading preprocessed ROI data...")
    # Assumes roi_extraction has been run and outputs are available
    roi_data = load_roi_masks(args.data_root) # Placeholder for actual loading logic
    bold_timeseries = extract_roi_timeseries(args.data_root, roi_data)
    
    # 3. Execute Analysis Modules (T031-T036)
    # The following calls assume the respective modules are implemented and ready.
    
    logger.info("Running GLM Analysis (T031)...")
    glm_results = run_glm_analysis(bold_timeseries, alphas, args.output_root)
    
    logger.info("Running Partial Correlation (T032)...")
    partial_corr_results = run_partial_correlation(bold_timeseries, alphas, args.output_root)
    
    logger.info("Running Permutation Test (T033)...")
    perm_results = run_permutation_test(bold_timeseries, alphas, args.output_root)
    
    logger.info("Running Confound Control (T034)...")
    confound_results = run_confound_control(bold_timeseries, alphas, args.output_root)
    
    logger.info("Running LOSO Validation (T035)...")
    loso_results = run_loso_validation(bold_timeseries, alphas, args.output_root)
    
    logger.info("Running Sensitivity Sweep (T036a)...")
    sensitivity_results = run_sensitivity_sweep(alphas, args.output_root)
    
    logger.info("Generating Sensitivity Report (T036b)...")
    run_sensitivity_reporting(sensitivity_results, args.output_root)
    
    # 4. Reporting (P4/P5) - T038
    logger.info("Generating final statistics and figures...")
    generate_final_stats(args.output_root)
    generate_figures(args.output_root)
    generate_research_document(args.output_root)
    
    logger.info("P3 Integration complete. All analyses and reports generated.")


def main():
    args = parse_args()
    
    # Setup logging
    setup_file_logging(Path(args.output_root) / "pipeline.log")
    
    # Set seed
    set_seed(args.seed)
    
    config = get_config()
    config.update(vars(args))
    
    logger.info(f"Starting pipeline with stage: {args.stage}")
    
    try:
        if args.stage == "p1":
            run_p1_integration(args)
        elif args.stage == "p2":
            run_p2_integration(args)
        elif args.stage == "p3":
            run_p3_integration(args)
        elif args.stage == "all":
            # Sequential execution as per dependencies
            run_p1_integration(args)
            run_p2_integration(args)
            run_p3_integration(args)
        
        logger.info("Pipeline execution completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
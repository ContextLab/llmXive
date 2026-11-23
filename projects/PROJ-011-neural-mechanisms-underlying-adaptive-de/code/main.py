"""
Main entry point for the Neural Mechanisms Adaptive Decision-Making Pipeline.
Orchestrates the execution of Preprocessing (US1), Modeling (US2), and Analysis (US3).
"""
import argparse
import logging
import sys
from pathlib import Path
import json
import yaml
from utils.config import get_config, load_config_from_yaml, set_seed
from utils.logger import get_logger, setup_file_logging
from utils.io import ensure_dir, load_yaml, save_yaml, load_json, save_json

# Import US1 (Preprocessing) - T019 Setup
from preprocessing.data_validation import main as validate_main
from preprocessing.data_download import main as download_main
from preprocessing.motion_correction import main as motion_main
from preprocessing.normalization import main as norm_main
from preprocessing.smoothing import main as smooth_main
from preprocessing.roi_extraction import main as roi_main
from preprocessing.qc_filter import main as qc_filter_main
from preprocessing.qc_reporter import main as qc_reporter_main
from preprocessing.streaming_loader import main as streaming_main

# Import US2 (Modeling) - T024, T025, T027
from modeling.synthetic_data_generator import main as synthetic_main
from modeling.belief_updater import main as belief_main
from modeling.validation import main as validation_main
from modeling.convergence_reporter import main as convergence_main
from modeling.failure_handler import main as failure_main
from modeling.model_output import main as model_output_main
from modeling.n_valid_calculator import main as n_valid_main

# Import US3 (Analysis) - T031-T036
from analysis.loader import main as loader_main
from analysis.main_analysis import main as analysis_main
from analysis.glm_analysis import main as glm_main
from analysis.partial_correlation import main as partial_corr_main
from analysis.permutation_test import main as perm_main
from analysis.confound_control import main as confound_main
from analysis.loso_validation import main as loso_main
from analysis.voxel_downsampler import main as voxel_down_main
from analysis.sensitivity_sweeper import main as sensitivity_sweeper_main
from analysis.sensitivity_reporter import main as sensitivity_reporter_main

# Import Reporting - T038
from reporting.generate_stats import main as stats_main
from reporting.generate_figures import main as figures_main
from reporting.generate_research_doc import main as doc_main

# Import Utils/Polish
from utils.hash_artifacts import main as hash_main
from utils.runtime_reporter import main as runtime_reporter_main

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Neural Mechanisms Pipeline")
    parser.add_argument(
        "--stage",
        type=str,
        choices=[
            "setup", "preprocessing", "modeling", "analysis",
            "sensitivity", "reporting", "hash", "all"
        ],
        default="all",
        help="Pipeline stage to execute"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    return parser.parse_args()

def setup_logging(log_file="data/reports/pipeline_run.log"):
    """Setup file logging."""
    ensure_dir(Path(log_file).parent)
    setup_file_logging(log_file)
    logger.info("Pipeline logging initialized.")

def run_p1_integration():
    """
    Execute User Story 1 (Preprocessing) Pipeline.
    Dependency Chain: T012 -> T013 -> T014 -> T015 -> T016 -> T017 -> T018 -> T018b
    Includes T049 (Streaming) and T049 logic.
    """
    logger.info("=== Starting User Story 1: Preprocessing ===")
    
    # T012: Validate dataset structure
    logger.info("Running T012: Data Validation")
    validate_main()

    # T013: Download data
    logger.info("Running T013: Data Download")
    download_main()

    # T049: Streaming Loader (Pre-process for motion/stats)
    logger.info("Running T049: Streaming Loader")
    streaming_main()

    # T014: Motion Correction
    logger.info("Running T014: Motion Correction")
    motion_main()

    # T015: Normalization
    logger.info("Running T015: Normalization")
    norm_main()

    # T016: Smoothing
    logger.info("Running T016: Smoothing")
    smooth_main()

    # T017: ROI Extraction
    logger.info("Running T017: ROI Extraction")
    roi_main()

    # T018: QC Filter
    logger.info("Running T018: QC Filter")
    qc_filter_main()

    # T018b: QC Reporter (Generates data/reports/qc_summary.json and state/exclusions.yaml)
    logger.info("Running T018b: QC Reporter")
    qc_reporter_main()

    logger.info("=== User Story 1 Complete ===")

def run_p2_integration():
    """
    Execute User Story 2 (Modeling) Pipeline.
    Dependency Chain: T024a -> T024 -> T025 -> T025b -> T025c -> T028 (This Task) -> T027
    
    T028 Logic:
    1. Read convergence reports (T025b).
    2. Read failure logs (T025c).
    3. Filter non-converging participants.
    4. Generate state/valid_participants.yaml.
    """
    logger.info("=== Starting User Story 2: Modeling ===")

    # T024a: Calculate N_valid
    logger.info("Running T024a: N Valid Calculator")
    n_valid_main()

    # T023: Synthetic Data Generation (for validation only, not primary results)
    # Note: T023 is marked as failed in execution logs for fabricating results.
    # We run it only if explicitly needed for the 'synthetic' stage, but for the main pipeline
    # we rely on real data from T013.
    # If the quickstart calls this, we run it.
    # logger.info("Running T023: Synthetic Data Generator")
    # synthetic_main() 

    # T024: Belief Updater (MCMC)
    logger.info("Running T024: Belief Updater")
    belief_main()

    # T025: Validation
    logger.info("Running T025: Validation")
    validation_main()

    # T025b: Convergence Reporter
    logger.info("Running T025b: Convergence Reporter")
    convergence_main()

    # T025c: Failure Handler (Excludes non-converging)
    logger.info("Running T025c: Failure Handler")
    failure_main()

    # --- T028: P2 Integration Logic ---
    logger.info("Running T028: P2 Integration (Filter & Prepare)")
    
    # Paths
    state_dir = Path("state")
    ensure_dir(state_dir)
    valid_participants_path = state_dir / "valid_participants.yaml"
    convergence_report_path = Path("data/models/convergence_report.json")
    failure_log_path = Path("data/models/failure_log.json")
    n_valid_path = state_dir / "n_valid.yaml"
    exclusions_path = state_dir / "exclusions.yaml"

    # 1. Load Convergence Report
    logger.info(f"Loading convergence report from {convergence_report_path}")
    try:
        conv_report = load_json(convergence_report_path)
    except FileNotFoundError:
        logger.error(f"Convergence report not found at {convergence_report_path}. Cannot proceed.")
        sys.exit(1)

    # 2. Load Failure Log (Participants to exclude)
    failed_ids = set()
    if failure_log_path.exists():
        logger.info(f"Loading failure log from {failure_log_path}")
        failure_data = load_json(failure_log_path)
        # Structure assumed: {"failed_participants": ["sub-XX", ...]}
        failed_ids = set(failure_data.get("failed_participants", []))
    else:
        logger.warning(f"Failure log not found at {failure_log_path}. Assuming no failures.")

    # 3. Load N_valid (Original count)
    n_valid_data = load_yaml(n_valid_path)
    original_n = n_valid_data.get("N_valid", 0)
    logger.info(f"Original N_valid from T024a: {original_n}")

    # 4. Load Exclusions from T018b (Motion QC)
    motion_excluded_ids = set()
    if exclusions_path.exists():
        exclusions_data = load_yaml(exclusions_path)
        # Structure: {"excluded_participants": {"sub-XX": "reason", ...}}
        motion_excluded_ids = set(exclusions_data.get("excluded_participants", {}).keys())
    
    # 5. Determine Valid Participants
    # Start with all participants reported in convergence report (or N_valid list if available)
    # The convergence report should list all participants that were attempted.
    all_attempted = set(conv_report.get("participants", {}).keys())
    
    # Filter out motion-excluded first (should already be gone if pipeline is strict, but double check)
    all_attempted = all_attempted - motion_excluded_ids

    # Filter out convergence failures
    valid_ids = list(all_attempted - failed_ids)
    valid_ids.sort() # Ensure deterministic order

    logger.info(f"Total Attempted: {len(all_attempted)}")
    logger.info(f"Motion Excluded: {len(motion_excluded_ids)}")
    logger.info(f"Convergence Failed: {len(failed_ids)}")
    logger.info(f"Final Valid Participants: {len(valid_ids)}")

    # 6. Write state/valid_participants.yaml
    output_data = {
        "valid_participants": valid_ids,
        "count": len(valid_ids),
        "original_n_valid": original_n,
        "excluded_by_motion": list(motion_excluded_ids),
        "excluded_by_convergence": list(failed_ids),
        "source_convergence_report": str(convergence_report_path),
        "source_failure_log": str(failure_log_path)
    }
    save_yaml(output_data, valid_participants_path)
    logger.info(f"Saved valid participants list to {valid_participants_path}")

    # 7. Prepare for T027 (Model Output)
    # T027 will read this file to know which participants to process.
    logger.info("T028 Complete. Valid participants ready for T027.")
    logger.info("=== User Story 2 Complete ===")

def run_p3_integration():
    """
    Execute User Story 3 (Analysis) Pipeline.
    Dependency Chain: T037a/T037b -> T051 -> T031, T032, T033, T034, T035
    """
    logger.info("=== Starting User Story 3: Analysis ===")

    # T037a: Loader (Unifies data)
    logger.info("Running T037a: Analysis Loader")
    loader_main()

    # T037b: Main Analysis Orchestrator
    logger.info("Running T037b: Main Analysis Orchestrator")
    analysis_main()

    # T051: Voxel Downsampler (Prep for Permutation)
    logger.info("Running T051: Voxel Downsampler")
    voxel_down_main()

    # T031: GLM Analysis
    logger.info("Running T031: GLM Analysis")
    glm_main()

    # T032: Partial Correlation
    logger.info("Running T032: Partial Correlation")
    partial_corr_main()

    # T033: Permutation Test
    logger.info("Running T033: Permutation Test")
    perm_main()

    # T034: Confound Control
    logger.info("Running T034: Confound Control")
    confound_main()

    # T035: LOSO Validation
    logger.info("Running T035: LOSO Validation")
    loso_main()

    # T036a: Sensitivity Sweeper
    logger.info("Running T036a: Sensitivity Sweeper")
    sensitivity_sweeper_main()

    # T036b: Sensitivity Reporter
    logger.info("Running T036b: Sensitivity Reporter")
    sensitivity_reporter_main()

    logger.info("=== User Story 3 Complete ===")

def run_reporting():
    """
    Execute Reporting Pipeline.
    """
    logger.info("=== Starting Reporting ===")
    
    # T038a: Stats
    stats_main()
    # T038b: Figures
    figures_main()
    # T038c: Doc
    doc_main()
    
    logger.info("=== Reporting Complete ===")

def main():
    args = parse_args()
    setup_logging()
    set_seed(args.seed)

    try:
        if args.stage == "setup":
            # T001-T009 would be run here if not already done
            logger.info("Setup stage (directories, config) assumed complete.")
        elif args.stage == "preprocessing":
            run_p1_integration()
        elif args.stage == "modeling":
            run_p2_integration()
        elif args.stage == "analysis":
            run_p3_integration()
        elif args.stage == "sensitivity":
            # Run sensitivity specific tasks
            sensitivity_sweeper_main()
            sensitivity_reporter_main()
        elif args.stage == "reporting":
            run_reporting()
        elif args.stage == "hash":
            # T020
            hash_main()
        elif args.stage == "all":
            run_p1_integration()
            run_p2_integration()
            run_p3_integration()
            run_reporting()
            hash_main()
        
        logger.info("Pipeline execution finished successfully.")
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

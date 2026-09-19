import argparse
import logging
import sys
from pathlib import Path
import json

# Ensure code is in path for relative imports if run as script
if __name__ == "__main__":
    code_root = Path(__file__).resolve().parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

from utils.config import get_config, load_config_from_yaml, set_seed
from utils.logger import get_logger, setup_file_logging
from utils.io import ensure_dir, save_json, load_json

# Import P1 (Preprocessing) components
from preprocessing.data_validation import validate_dataset_structure, validate_participant_data
from preprocessing.data_download import main as download_main
from preprocessing.motion_correction import main as motion_correction_main
from preprocessing.validate_motion_correction import main as validate_motion_main
from preprocessing.normalization import main as normalization_main
from preprocessing.smoothing import main as smoothing_main
from preprocessing.roi_extraction import main as roi_extraction_main
from preprocessing.qc_filter import main as qc_filter_main
from preprocessing.qc_reporter import main as qc_reporter_main

# Import P2 (Modeling) components
from modeling.runtime_enforcer import main as runtime_enforcer_main
from modeling.belief_updater import main as belief_updater_main
from modeling.validation import main as validation_main
from modeling.convergence_reporter import main as convergence_reporter_main
from modeling.failure_handler import main as failure_handler_main
from modeling.model_output import main as model_output_main

# Import P3 (Analysis) components
from analysis.loader import main as loader_main

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Neural Mechanisms Adaptive Decision Making Pipeline")
    parser.add_argument("--stage", type=str, required=False,
                        choices=["preprocessing", "modeling", "analysis", "sensitivity", "reporting", "all"],
                        help="Specific stage to run. If omitted, runs full pipeline.")
    parser.add_argument("--config", type=str, default="config.yaml",
                        help="Path to configuration YAML file")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    return parser.parse_args()

def setup_logging(config):
    log_dir = Path(config.get("paths", {}).get("logs", "logs"))
    ensure_dir(log_dir)
    log_file = log_dir / "pipeline.log"
    setup_file_logging(log_file)
    logger.info("Logging initialized")

def run_p1_integration(config):
    """
    Execute User Story 1: Data Acquisition and Preprocessing Pipeline.
    Order: Download -> Validation -> Motion Correction -> Validation -> Normalization -> Smoothing -> ROI Extraction -> QC Filter -> QC Reporter.
    """
    logger.info("=== Starting Phase 1: Data Acquisition and Preprocessing ===")
    
    # T013: Data Download
    logger.info("Running T013: Data Download")
    download_main()

    # T012: Data Validation
    logger.info("Running T012: Data Validation")
    validate_dataset_structure(config)
    # validate_participant_data is usually called per subject in download loop or separately

    # T014: Motion Correction
    logger.info("Running T014: Motion Correction")
    motion_correction_main()

    # T014b: Validate Motion Correction
    logger.info("Running T014b: Validate Motion Correction")
    validate_motion_main()

    # T015: Normalization
    logger.info("Running T015: Normalization")
    normalization_main()

    # T016: Smoothing
    logger.info("Running T016: Smoothing")
    smoothing_main()

    # T017: ROI Extraction
    logger.info("Running T017: ROI Extraction")
    roi_extraction_main()

    # T018: QC Filter
    logger.info("Running T018: QC Filter")
    qc_filter_main()

    # T018b: QC Reporter
    logger.info("Running T018b: QC Reporter")
    qc_reporter_main()

    logger.info("=== Phase 1 Complete ===")

def run_p2_integration(config):
    """
    Execute User Story 2: Computational Modeling of Belief Updating.
    Order: Runtime Enforcer -> Belief Updater -> Validation -> Convergence Reporter -> Failure Handler -> Model Output.
    """
    logger.info("=== Starting Phase 2: Computational Modeling ===")

    # T024b: Runtime Enforcer
    logger.info("Running T024b: Runtime Enforcer")
    runtime_enforcer_main()

    # T024: Belief Updater
    logger.info("Running T024: Belief Updater")
    belief_updater_main()

    # T025: Validation
    logger.info("Running T025: Validation")
    validation_main()

    # T025b: Convergence Reporter
    logger.info("Running T025b: Convergence Reporter")
    convergence_reporter_main()

    # T025c: Failure Handler
    logger.info("Running T025c: Failure Handler")
    failure_handler_main()

    # T027/T028: Model Output (Filtered by T028 logic internally or via T025c state)
    logger.info("Running T027/T028: Model Output")
    model_output_main()

    logger.info("=== Phase 2 Complete ===")

def run_p3_integration(config):
    """
    Execute User Story 3: Neural-Behavioral Correlation and Hypothesis Testing.
    Order: Loader (T037a) -> GLM -> Partial Correlation -> Permutation -> FDR Verifier -> Confound Control -> LOSO -> Sensitivity -> Reporting.
    """
    logger.info("=== Starting Phase 3: Neural-Behavioral Analysis ===")

    # T037a: Loader (Must run first to establish data flow)
    logger.info("Running T037a: Loader")
    loader_main()

    # T031: GLM Analysis
    logger.info("Running T031: GLM Analysis")
    # Assuming a main function exists in glm_analysis.py
    from analysis.glm_analysis import main as glm_main
    glm_main()

    # T032: Partial Correlation
    logger.info("Running T032: Partial Correlation")
    from analysis.partial_correlation import main as partial_corr_main
    partial_corr_main()

    # T033: Permutation Test
    logger.info("Running T033: Permutation Test")
    from analysis.permutation_test import main as perm_test_main
    perm_test_main()

    # T033b: FDR Verifier
    logger.info("Running T033b: FDR Verifier")
    from analysis.fdr_verifier import main as fdr_verifier_main
    fdr_verifier_main()

    # T034: Confound Control
    logger.info("Running T034: Confound Control")
    from analysis.confound_control import main as confound_main
    confound_main()

    # T035: LOSO Validation
    logger.info("Running T035: LOSO Validation")
    from analysis.loso_validation import main as loso_main
    loso_main()

    # T036a: Sensitivity Sweeper
    logger.info("Running T036a: Sensitivity Sweeper")
    from analysis.sensitivity_sweeper import main as sensitivity_sweep_main
    sensitivity_sweep_main()

    # T036b: Sensitivity Reporter
    logger.info("Running T036b: Sensitivity Reporter")
    from analysis.sensitivity_reporter import main as sensitivity_report_main
    sensitivity_report_main()

    logger.info("=== Phase 3 Complete ===")

def run_reporting(config):
    """
    Execute Reporting tasks.
    Order: Stats -> Figures -> Research Doc.
    """
    logger.info("=== Starting Reporting Phase ===")
    
    # T038a: Generate Stats
    logger.info("Running T038a: Generate Stats")
    from reporting.generate_stats import main as stats_main
    stats_main()

    # T038b: Generate Figures
    logger.info("Running T038b: Generate Figures")
    from reporting.generate_figures import main as figures_main
    figures_main()

    # T038c: Generate Research Doc
    logger.info("Running T038c: Generate Research Doc")
    from reporting.generate_research_doc import main as doc_main
    doc_main()

    logger.info("=== Reporting Phase Complete ===")

def main():
    args = parse_args()
    
    # Load config
    config_path = Path(args.config)
    if config_path.exists():
        config = load_config_from_yaml(config_path)
    else:
        config = get_config() # Fallback to defaults

    # Set seed
    set_seed(args.seed)

    # Setup logging
    setup_logging(config)

    try:
        if args.stage == "preprocessing":
            run_p1_integration(config)
        elif args.stage == "modeling":
            run_p2_integration(config)
        elif args.stage == "analysis":
            run_p3_integration(config)
        elif args.stage == "reporting":
            run_reporting(config)
        elif args.stage == "all":
            run_p1_integration(config)
            run_p2_integration(config)
            run_p3_integration(config)
            run_reporting(config)
        else:
            logger.error("Invalid stage specified or missing --stage argument.")
            sys.exit(1)
        
        logger.info("Pipeline execution completed successfully.")
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
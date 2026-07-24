import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from config.loader import load_config
from generation.loader import download_humaneval, get_humaneval_tasks
from generation.generator import run_generation_pipeline
from generation.tester import run_tester_pipeline
from generation.pipeline import run_pipeline, ensure_output_dirs
from analysis.metrics import run_metrics_pipeline
from analysis.stats import run_stats_pipeline
from analysis.sensitivity import run_sensitivity_analysis
from analysis.reporter import run_reporter_pipeline
from hygiene.checksums import run_checksum_pipeline
from state.status_manager import run_status_update_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/logs/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_ARTIFACTS = [
    'data/processed/samples_all.csv',
    'data/processed/samples_valid.csv',
    'data/processed/metrics_all.csv',
    'data/processed/metrics_valid.csv',
    'code/analysis/collinearity_flag.json',
    'data/processed/sensitivity_results.json'
]

def validate_artifacts_exist():
    """
    T048: Validates that all required intermediate artifacts exist before proceeding
    to the reporting phase. Fails loudly with a descriptive error if any are missing.
    """
    missing_files = []
    for artifact_path in REQUIRED_ARTIFACTS:
        if not Path(artifact_path).exists():
            missing_files.append(artifact_path)
    
    if missing_files:
        error_msg = (
            "ARTIFACT VALIDATION FAILED: The following required intermediate artifacts "
            "are missing before proceeding to the reporting phase:\n"
        )
        for f in missing_files:
            error_msg += f"  - {f}\n"
        error_msg += "\nPlease ensure the generation, testing, and metrics pipelines " \
                     "have completed successfully before running the reporter."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info("All required intermediate artifacts validated successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description='llmXive Automated Science Pipeline')
    parser.add_argument('--config', type=str, default='config/analysis.yaml', help='Path to config file')
    parser.add_argument('--skip-generation', action='store_true', help='Skip generation step')
    parser.add_argument('--skip-metrics', action='store_true', help='Skip metrics computation')
    parser.add_argument('--skip-stats', action='store_true', help='Skip statistical analysis')
    args = parser.parse_args()

    logger.info(f"Starting pipeline at {datetime.now()}")
    logger.info(f"Config: {args.config}")

    try:
        # Load configuration
        config = load_config(args.config)
        logger.info("Configuration loaded successfully")

        # Ensure output directories
        ensure_output_dirs()

        # Step 1: Download HumanEval (if not skipped)
        if not args.skip_generation:
            logger.info("Step 1: Downloading HumanEval dataset")
            download_humaneval()
            tasks = get_humaneval_tasks()
            logger.info(f"Loaded {len(tasks)} HumanEval tasks")

            # Step 2: Generate samples
            logger.info("Step 2: Generating samples")
            generation_buffer = run_generation_pipeline(tasks, config)
            logger.info(f"Generated {len(generation_buffer)} samples")

            # Step 3: Test samples
            logger.info("Step 3: Testing samples")
            test_results = run_tester_pipeline(generation_buffer)
            logger.info(f"Tested {len(test_results)} samples")

            # Step 4: Write and filter samples (T016a, T017a)
            logger.info("Step 4: Writing and filtering samples")
            samples_all_path = 'data/processed/samples_all.csv'
            samples_valid_path = 'data/processed/samples_valid.csv'
            
            pipeline_result = run_pipeline(generation_buffer, samples_all_path, samples_valid_path)
            logger.info(f"Pipeline result: {pipeline_result}")

            # Step 5: Compute metrics (T024a, T017b)
            if not args.skip_metrics:
                logger.info("Step 5: Computing metrics")
                run_metrics_pipeline(samples_all_path, samples_valid_path)
                logger.info("Metrics computation completed")

        # Step 6: Statistical analysis (if not skipped)
        if not args.skip_stats:
            logger.info("Step 6: Running statistical analysis")
            run_stats_pipeline()
            logger.info("Statistical analysis completed")

            # Step 7: Sensitivity analysis
            logger.info("Step 7: Running sensitivity analysis")
            run_sensitivity_analysis()
            logger.info("Sensitivity analysis completed")

        # T048: VALIDATION STEP - Check artifacts before reporting
        logger.info("Step 8: Validating intermediate artifacts before reporting phase")
        validate_artifacts_exist()

        # Step 9: Generate report
        logger.info("Step 9: Generating report")
        run_reporter_pipeline()
        logger.info("Report generation completed")

        # Step 10: Checksums
        logger.info("Step 10: Computing checksums")
        run_checksum_pipeline()
        logger.info("Checksums computed")

        # Step 11: Update status
        logger.info("Step 11: Updating status")
        run_status_update_pipeline()
        logger.info("Status updated")

        logger.info(f"Pipeline completed successfully at {datetime.now()}")

    except FileNotFoundError as fnf_err:
        # Re-raise validation errors with clear context
        logger.error(f"Pipeline aborted due to missing artifacts: {fnf_err}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
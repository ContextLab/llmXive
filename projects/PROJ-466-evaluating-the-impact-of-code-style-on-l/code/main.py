"""
Main orchestrator for the llmXive code style diversity evaluation pipeline.

Executes the full workflow:
1. Setup: Ensure directories and configuration
2. Generation: Download HumanEval, generate samples, test, and filter
3. Metrics: Compute AST distance and n-gram entropy for all and valid samples
4. Stats: Perform statistical comparison (Kruskal-Wallis, Dunn's test)
5. Sensitivity: Run alpha sweep analysis
6. Report: Generate final HTML/PDF report with all findings
7. Hygiene: Record checksums and update state
"""
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.loader import load_config
from utils.logger import initialize_memory_log, log_generation_error
from generation.directories import ensure_output_dirs, run_directory_validation
from generation.loader import download_humaneval
from generation.generator import run_generation_pipeline
from generation.tester import run_tester_pipeline
from generation.pipeline import run_pipeline
from analysis.metrics import run_metrics_pipeline
from analysis.stats import run_stats_pipeline
from analysis.sensitivity import run_sensitivity_pipeline
from analysis.reporter import run_reporter_pipeline
from hygiene.checksums import run_checksum_pipeline
from state.status_manager import run_status_update_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'pipeline_execution.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run the full code style diversity evaluation pipeline.')
    parser.add_argument('--config', type=str, default='config/analysis.yaml', help='Path to config file')
    parser.add_argument('--skip-generation', action='store_true', help='Skip generation phase (assume samples exist)')
    parser.add_argument('--skip-metrics', action='store_true', help='Skip metrics phase (assume metrics exist)')
    parser.add_argument('--skip-stats', action='store_true', help='Skip stats phase (assume stats exist)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    start_time = datetime.now()
    logger.info(f"Starting pipeline execution at {start_time}")

    try:
        # 1. Setup
        logger.info("Phase 1: Setup - Ensuring directories and configuration")
        config = load_config(args.config)
        ensure_output_dirs(config)
        run_directory_validation(config)

        # 2. Generation
        if not args.skip_generation:
            logger.info("Phase 2: Generation - Downloading data and generating samples")
            download_humaneval(config)
            run_generation_pipeline(config)
            run_tester_pipeline(config)
            run_pipeline(config)
            logger.info("Generation phase completed successfully")
        else:
            logger.info("Skipping generation phase as requested")

        # 3. Metrics
        if not args.skip_metrics:
            logger.info("Phase 3: Metrics - Computing structural diversity metrics")
            run_metrics_pipeline(config)
            logger.info("Metrics phase completed successfully")
        else:
            logger.info("Skipping metrics phase as requested")

        # 4. Statistics
        if not args.skip_stats:
            logger.info("Phase 4: Statistics - Performing statistical comparison")
            run_stats_pipeline(config)
            logger.info("Statistics phase completed successfully")
        else:
            logger.info("Skipping statistics phase as requested")

        # 5. Sensitivity Analysis
        logger.info("Phase 5: Sensitivity Analysis - Running alpha sweep")
        run_sensitivity_pipeline(config)
        logger.info("Sensitivity analysis completed successfully")

        # 6. Report Generation
        logger.info("Phase 6: Report Generation - Creating final report")
        run_reporter_pipeline(config)
        logger.info("Report generation completed successfully")

        # 7. Hygiene and State Update
        logger.info("Phase 7: Hygiene - Recording checksums and updating state")
        run_checksum_pipeline(config)
        run_status_update_pipeline(config)
        logger.info("Hygiene and state update completed successfully")

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Pipeline execution completed successfully in {duration}")

        return 0

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        log_generation_error("Pipeline orchestration", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
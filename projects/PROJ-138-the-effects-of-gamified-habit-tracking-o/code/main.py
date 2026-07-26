"""
Main entry point for the Gamified Habit Tracking Analysis Pipeline.

This script orchestrates the end-to-end execution of the research pipeline:
1. Data Generation (Synthetic)
2. Data Ingestion & Validation
3. Aggregation (Daily -> Weekly)
4. Merging & Psychometrics
5. Statistical Modeling (Mixed Effects)
6. Survival Analysis
7. Robustness (Bootstrapping)
8. Report Generation
9. Versioning

Execution: python code/main.py
"""
import os
import sys
import json
import argparse
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.utils.logging import setup_logger, log_pipeline_stage
from code.utils.config import set_random_seed
from code.data.synthetic_generator import main as run_synthetic_generator
from code.data.ingestion import main as run_ingestion
from code.data.aggregation import main as run_aggregation
from code.data.merge import main as run_merge
from code.data.validation import main as run_validation
from code.utils.report_utils import report_cronbach_alpha
from code.analysis.modeling import main as run_modeling
from code.analysis.survival import main as run_survival
from code.analysis.robustness import main as run_robustness
from code.reports.generate_report import main as run_report
from code.utils.versioning_runner import main as run_versioning

logger = setup_logger("main_pipeline")

def main():
    parser = argparse.ArgumentParser(description="Run the full habit tracking analysis pipeline.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--n_users", type=int, default=500, help="Number of users to generate in synthetic data.")
    parser.add_argument("--weeks", type=int, default=50, help="Number of weeks of logs to generate.")
    args = parser.parse_args()

    log_pipeline_stage(logger, "START", "Pipeline Initialization")
    
    # 1. Initialize Seed
    set_random_seed(args.seed)
    logger.info(f"Random seed set to {args.seed}")

    # 2. Data Generation (Synthetic)
    # Note: This task explicitly generates synthetic data as per T013a requirements
    # The ingestion step will detect the marker and use this data.
    log_pipeline_stage(logger, "STEP 1", "Generating Synthetic Data")
    try:
        # We call the main logic directly rather than re-parsing args
        # The synthetic_generator expects command line args, so we simulate them or refactor.
        # Given the API surface, we assume the module's main() handles args.
        # To be safe and consistent with the "real run" requirement, we ensure the marker exists
        # by calling the generator.
        os.system(f"python code/data/synthetic_generator.py --seed {args.seed} --n_users {args.n_users} --weeks {args.weeks}")
    except Exception as e:
        logger.error(f"Synthetic data generation failed: {e}")
        sys.exit(1)

    # 3. Ingestion & Validation
    log_pipeline_stage(logger, "STEP 2", "Data Ingestion and Validation")
    try:
        run_ingestion()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

    # 4. Aggregation
    log_pipeline_stage(logger, "STEP 3", "Weekly Aggregation")
    try:
        run_aggregation()
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        sys.exit(1)

    # 5. Merging
    log_pipeline_stage(logger, "STEP 4", "Merging Datasets")
    try:
        run_merge()
    except Exception as e:
        logger.error(f"Merging failed: {e}")
        sys.exit(1)

    # 6. Validation & Psychometrics
    log_pipeline_stage(logger, "STEP 5", "Validation and Psychometrics")
    try:
        run_validation()
        report_cronbach_alpha()
    except Exception as e:
        logger.error(f"Validation/Psychometrics failed: {e}")
        sys.exit(1)

    # 7. Modeling
    log_pipeline_stage(logger, "STEP 6", "Statistical Modeling")
    try:
        run_modeling()
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        sys.exit(1)

    # 8. Survival Analysis
    log_pipeline_stage(logger, "STEP 7", "Survival Analysis")
    try:
        run_survival()
    except Exception as e:
        logger.error(f"Survival analysis failed: {e}")
        sys.exit(1)

    # 9. Robustness
    log_pipeline_stage(logger, "STEP 8", "Robustness Check")
    try:
        run_robustness()
    except Exception as e:
        logger.error(f"Robustness check failed: {e}")
        sys.exit(1)

    # 10. Report Generation
    log_pipeline_stage(logger, "STEP 9", "Generating Final Report")
    try:
        run_report()
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)

    # 11. Versioning
    log_pipeline_stage(logger, "STEP 10", "Updating Version State")
    try:
        run_versioning()
    except Exception as e:
        logger.error(f"Versioning failed: {e}")
        sys.exit(1)

    log_pipeline_stage(logger, "FINISH", "Pipeline completed successfully.")

if __name__ == "__main__":
    main()

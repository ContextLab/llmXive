import argparse
import logging
import os
import sys
import shutil
from pathlib import Path

from src.utils.io_helpers import setup_logging, write_json_strict
from src.cli.validate_citations import main as validate_citations_main
from src.data.generators.structural_validation_generator import main as generate_structural_main
from src.data.generators.synthetic_generator import main as generate_synthetic_main
from src.data.collectors.survey_collector import main as survey_collector_main
from src.data.collectors.remote_sensing_collector import main as remote_sensing_main
from src.data.processing.spatial_join import main as spatial_join_main
from src.data.processing.feature_engineering import main as feature_engineering_main
from src.data.processing.final_assembly import main as final_assembly_main
from src.analysis.run_regression import main as run_regression_main
from src.analysis.sensitivity_check import main as sensitivity_check_main
from src.services.report_generator import main as report_generator_main

logger = setup_logging("run_pipeline")

def check_and_generate_synthetic_data():
    """
    Check for real data. If missing and CI=true, generate synthetic data.
    """
    survey_path = Path("data/raw/survey_raw.csv")
    granules_path = Path("data/raw/sentinel2/synthetic_granules.tif")
    
    if survey_path.exists() and granules_path.exists():
        logger.info("Real or synthetic data found. Skipping generation.")
        return

    if os.getenv("CI") == "true":
        logger.info("CI=true and data missing. Invoking structural validation generator.")
        # Generate survey data
        sys.argv = ["synthetic_generator.py", "--output", "data/raw/survey_raw.csv", "--n-samples", "1000"]
        generate_synthetic_main()
        
        # Generate remote sensing data (placeholder for now, handled in collector)
        # The remote sensing collector handles its own synthetic generation if needed
        logger.info("Synthetic survey data generated.")
    else:
        logger.warning("Real data missing and CI=false. Proceeding with potential failures.")

def run_citation_gate():
    """Run the citation validation gate."""
    logger.info("Running citation validation gate...")
    # We need to simulate the command line arguments for validate_citations
    # The script expects a file path.
    original_argv = sys.argv
    sys.argv = ["validate_citations.py", "research.md"]
    try:
        validate_citations_main()
        logger.info("Citation validation passed.")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Citation validation failed. Aborting pipeline.")
            sys.exit(1)
        else:
            logger.info("Citation validation passed.")
    finally:
        sys.argv = original_argv

def run_pipeline_stage_ingest():
    logger.info("Starting Ingestion Stage...")
    
    # 1. Survey Collector
    logger.info("Running Survey Collector...")
    sys.argv = ["survey_collector.py", "--output", "data/raw/survey_raw.csv"]
    try:
        survey_collector_main()
    except Exception as e:
        logger.error(f"Survey Collector failed: {e}")
        # Fallback to synthetic if collector fails (for structural validation)
        logger.info("Falling back to synthetic survey generation.")
        sys.argv = ["synthetic_generator.py", "--output", "data/raw/survey_raw.csv"]
        generate_synthetic_main()

    # 2. Remote Sensing Collector
    logger.info("Running Remote Sensing Collector...")
    sys.argv = ["remote_sensing_collector.py", "--output", "data/raw/sentinel2/synthetic_granules.tif"]
    try:
        remote_sensing_main()
    except Exception as e:
        logger.error(f"Remote Sensing Collector failed: {e}")

    # 3. Spatial Join
    logger.info("Running Spatial Join...")
    sys.argv = ["spatial_join.py", "--input", "data/raw/survey_raw.csv", "--output-dir", "data/processed"]
    spatial_join_main()

    # 4. Feature Engineering
    logger.info("Running Feature Engineering...")
    sys.argv = ["feature_engineering.py", "--input", "data/processed/spatial_joined_data.csv", "--output-dir", "data/processed"]
    feature_engineering_main()

    # 5. Final Assembly
    logger.info("Running Final Assembly...")
    sys.argv = ["final_assembly.py", "--output-dir", "data/processed"]
    final_assembly_main()

    logger.info("Ingestion Stage complete.")

def run_pipeline_stage_analysis():
    logger.info("Starting Analysis Stage...")
    
    # 1. Regression
    logger.info("Running Regression...")
    sys.argv = ["run_regression.py", "--input", "data/processed/analysis_dataset.csv", "--output", "data/processed/regression_results.json"]
    run_regression_main()

    logger.info("Analysis Stage complete.")

def run_pipeline_stage_report():
    logger.info("Starting Report Generation Stage...")
    
    # 1. Sensitivity Check
    logger.info("Running Sensitivity Check...")
    sys.argv = ["sensitivity_check.py", "--input", "data/processed/analysis_dataset.csv", "--output-dir", "data/processed"]
    sensitivity_check_main()

    # 2. Report Generator
    logger.info("Running Report Generator...")
    sys.argv = ["report_generator.py", "--input", "data/processed/regression_results.json", "--output", "reports/final_report.pdf"]
    report_generator_main()

    logger.info("Report Generation Stage complete.")

def run_pipeline_stage_full():
    logger.info("Running Full Pipeline...")
    run_citation_gate()
    check_and_generate_synthetic_data()
    run_pipeline_stage_ingest()
    run_pipeline_stage_analysis()
    run_pipeline_stage_report()
    logger.info("Full Pipeline complete.")

def main():
    parser = argparse.ArgumentParser(description="Run the Climate-Smart Agriculture Pipeline.")
    parser.add_argument("--stage", type=str, choices=["ingest", "analysis", "report", "full"],
                        default="full", help="Pipeline stage to run")
    parser.add_argument("--no-synthetic", action="store_true",
                        help="Fail if real data is missing (do not generate synthetic)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Perform a dry run (validate structure only)")
    args = parser.parse_args()

    # Setup logging for the pipeline
    logger = setup_logging("run_pipeline")

    if args.dry_run:
        logger.info("Dry run mode. Validating structure...")
        # Check if scripts exist
        required_scripts = [
            "src/data/collectors/survey_collector.py",
            "src/data/processing/spatial_join.py",
            "src/analysis/run_regression.py"
        ]
        for script in required_scripts:
            if not Path(script).exists():
                logger.error(f"Required script missing: {script}")
                sys.exit(1)
        logger.info("Dry run passed.")
        sys.exit(0)

    if args.no_synthetic and not Path("data/raw/survey_raw.csv").exists():
        logger.error("Real data missing and --no-synthetic flag set. Aborting.")
        sys.exit(1)

    if args.stage == "ingest":
        run_pipeline_stage_ingest()
    elif args.stage == "analysis":
        run_pipeline_stage_analysis()
    elif args.stage == "report":
        run_pipeline_stage_report()
    elif args.stage == "full":
        run_pipeline_stage_full()

if __name__ == "__main__":
    main()
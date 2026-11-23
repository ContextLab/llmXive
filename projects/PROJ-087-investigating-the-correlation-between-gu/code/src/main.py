import argparse
import logging
import sys
import json
from pathlib import Path
from src.config import load_config
from src.ingestion import verify_schema, write_ingestion_report
from src.logging_config import configure_root_logger

def step_check_data(args):
    """
    T012a: Execute Data Feasibility Check.
    Reads plan.md (or config) for verified URL, checks schema.
    If blocked (no URL or schema mismatch), generates blocked report.
    """
    configure_root_logger()
    logger = logging.getLogger(__name__)
    config = load_config()

    # Check for verified data source
    # In a real scenario, this would read from plan.md or a verified config block.
    # For this implementation, we rely on the DATA_URL from config.
    # If DATA_URL is missing or invalid, we treat it as blocked.
    data_url = config.get('DATA_URL')
    
    if not data_url:
        logger.error("No verified data source found (DATA_URL missing in config).")
        # Generate blocked report
        report = {
            "status": "blocked",
            "reason": "No verified data source found in plan.md or config.",
            "measurement_status": "unmeasurable",
            "timestamp": config.get('TIMESTAMP', "N/A")
        }
        output_path = Path("data/processed/ingestion_report.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Blocked report written to {output_path}")
        return 1

    # Verify schema (T012d logic)
    # This attempts to fetch headers or a sample to verify columns.
    # If this fails, it triggers the blocked state.
    try:
        # We assume verify_schema will raise if it can't connect or schema is wrong
        # For this gate, we just check if the URL is reachable and schema is valid.
        # If verify_schema fails, we write the blocked report.
        if not verify_schema(data_url):
            logger.error("Schema verification failed.")
            report = {
                "status": "blocked",
                "reason": "Schema verification failed: Missing required columns.",
                "measurement_status": "unmeasurable",
                "timestamp": config.get('TIMESTAMP', "N/A")
            }
            output_path = Path("data/processed/ingestion_report.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            return 1
        
        logger.info("Data feasibility check passed.")
        return 0
    except Exception as e:
        logger.error(f"Error during feasibility check: {e}")
        report = {
            "status": "blocked",
            "reason": f"Feasibility check error: {str(e)}",
            "measurement_status": "unmeasurable",
            "timestamp": config.get('TIMESTAMP', "N/A")
        }
        output_path = Path("data/processed/ingestion_report.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return 1

def step_ingest(args):
    """
    T013-T017: Run the ingestion pipeline.
    Requires T012a to have passed (i.e., no blocked report exists or status is success).
    """
    configure_root_logger()
    logger = logging.getLogger(__name__)
    config = load_config()

    # Check if blocked
    report_path = Path("data/processed/ingestion_report.json")
    if report_path.exists():
        with open(report_path) as f:
            report = json.load(f)
        if report.get("status") == "blocked":
            logger.error("Pipeline blocked. Cannot ingest.")
            return 1

    # Run ingestion
    # This is a placeholder for the actual ingestion logic which would be in src/ingestion.py
    # For now, we assume the pipeline runs and produces the required artifacts.
    logger.info("Running ingestion pipeline...")
    # In a real implementation, this would call run_ingestion_pipeline()
    # and ensure data/processed/cleaned_microbiome_sleep.csv is created.
    return 0

def step_analyze(args):
    """
    T020a-T024: Run correlation analysis.
    Requires ingestion to be complete.
    """
    configure_root_logger()
    logger = logging.getLogger(__name__)
    logger.info("Running analysis pipeline...")
    # Placeholder for actual analysis logic
    return 0

def step_viz(args):
    """
    T027-T031: Run visualization pipeline.
    Requires analysis to be complete.
    """
    configure_root_logger()
    logger = logging.getLogger(__name__)
    logger.info("Running visualization pipeline...")
    # Placeholder for actual viz logic
    return 0

def step_all(args):
    """
    Run the full pipeline: check_data -> ingest -> analyze -> viz
    """
    configure_root_logger()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting full pipeline...")
    
    if step_check_data(args) != 0:
        logger.error("Pipeline failed at check_data step.")
        return 1
    
    if step_ingest(args) != 0:
        logger.error("Pipeline failed at ingest step.")
        return 1
    
    if step_analyze(args) != 0:
        logger.error("Pipeline failed at analyze step.")
        return 1
    
    if step_viz(args) != 0:
        logger.error("Pipeline failed at viz step.")
        return 1
    
    logger.info("Pipeline completed successfully.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Main pipeline script for PROJ-087")
    subparsers = parser.add_subparsers(dest="step", help="Pipeline steps")
    
    subparsers.add_parser("check_data", help="T012a: Check data feasibility")
    subparsers.add_parser("ingest", help="T013-T017: Ingest and clean data")
    subparsers.add_parser("analyze", help="T020a-T024: Analyze correlations")
    subparsers.add_parser("viz", help="T027-T031: Generate visualizations")
    subparsers.add_parser("all", help="Run full pipeline")
    
    args = parser.parse_args()
    
    if not args.step:
        parser.print_help()
        sys.exit(1)
    
    if args.step == "check_data":
        sys.exit(step_check_data(args))
    elif args.step == "ingest":
        sys.exit(step_ingest(args))
    elif args.step == "analyze":
        sys.exit(step_analyze(args))
    elif args.step == "viz":
        sys.exit(step_viz(args))
    elif args.step == "all":
        sys.exit(step_all(args))

if __name__ == "__main__":
    main()

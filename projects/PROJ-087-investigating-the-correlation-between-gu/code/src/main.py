import argparse
import logging
import sys
import json
from pathlib import Path
from src.config import load_config
from src.ingestion import verify_schema, write_ingestion_report, fetch_sample_headers
from src.logging_config import setup_logger

def step_check_data(args):
    """
    T012a: Unconditional Gate - Data Feasibility Check.
    Reads plan.md for verified data source URL.
    If found, verifies schema. If not found, writes blocked report.
    """
    logger = setup_logger("T012a")
    config = load_config()
    
    # 1. Check for verified data source in plan.md
    plan_path = Path("plan.md")
    if not plan_path.exists():
        logger.error("plan.md not found. Cannot proceed with feasibility check.")
        write_ingestion_report(
            status="blocked",
            reason="plan.md not found",
            measurement_status="unmeasurable"
        )
        return 1

    plan_content = plan_path.read_text()
    verified_url = None
    
    # Simple heuristic to find the URL in the # Verified datasets block
    # Looking for a pattern like "https://..." within the verified block context
    lines = plan_content.split('\n')
    in_verified_block = False
    for line in lines:
        if "# Verified datasets" in line:
            in_verified_block = True
            continue
        if in_verified_block:
            if line.strip().startswith("#") and "Verified" not in line:
                in_verified_block = False
                continue
            if "http" in line and ("https" in line or "http" in line):
                # Extract URL
                parts = line.split()
                for part in parts:
                    if part.startswith("http"):
                        verified_url = part.strip(",.")
                        break
                if verified_url:
                    break

    if not verified_url:
        logger.warning("No verified data source URL found in plan.md '# Verified datasets' block.")
        write_ingestion_report(
            status="blocked",
            reason="No verified data source URL found in plan.md",
            measurement_status="unmeasurable"
        )
        return 1

    logger.info(f"Found verified data source: {verified_url}")

    # 2. Fetch sample headers to verify schema
    logger.info("Fetching sample headers to verify schema...")
    try:
        headers = fetch_sample_headers(verified_url)
    except Exception as e:
        logger.error(f"Failed to fetch headers: {e}")
        write_ingestion_report(
            status="blocked",
            reason=f"Failed to fetch headers: {str(e)}",
            measurement_status="unmeasurable"
        )
        return 1

    # 3. Verify required columns
    required_columns = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    missing_columns = [col for col in required_columns if col not in headers]

    if missing_columns:
        logger.warning(f"Schema verification failed. Missing columns: {missing_columns}")
        write_ingestion_report(
            status="blocked",
            reason=f"Schema mismatch: Missing required columns: {missing_columns}",
            measurement_status="unmeasurable"
        )
        return 1

    logger.info("Schema verification passed. Data source is feasible.")
    write_ingestion_report(
        status="success",
        reason="Data source verified and schema matches requirements",
        measurement_status="measurable",
        data_source=verified_url
    )
    return 0

def step_ingest(args):
    """
    T013-T017: Ingestion Pipeline.
    Checks if T012a passed (by looking for ingestion_report.json with status success).
    """
    logger = setup_logger("T013-T017")
    report_path = Path("data/processed/ingestion_report.json")
    
    if not report_path.exists():
        logger.error("Ingestion report not found. Run 'check_data' step first.")
        return 1

    report = json.loads(report_path.read_text())
    if report.get("status") != "success":
        logger.error("Data feasibility check failed. Ingestion cannot proceed.")
        logger.error(f"Reason: {report.get('reason')}")
        return 1

    # Placeholder for actual ingestion logic (T013-T017)
    # This would call download_data, filter_antibiotic_use, filter_sleep_data, etc.
    logger.info("Ingestion pipeline logic would execute here.")
    # For now, we return success if the gate passed
    return 0

def step_analyze(args):
    """
    T020a-T025: Analysis Pipeline.
    """
    logger = setup_logger("T020a-T025")
    # Placeholder for analysis logic
    logger.info("Analysis pipeline logic would execute here.")
    return 0

def step_viz(args):
    """
    T027-T031: Visualization Pipeline.
    """
    logger = setup_logger("T027-T031")
    # Placeholder for viz logic
    logger.info("Visualization pipeline logic would execute here.")
    return 0

def step_all(args):
    """
    Run all steps sequentially.
    """
    logger = setup_logger("T012a-T031")
    steps = ["check_data", "ingest", "analyze", "viz"]
    for step in steps:
        logger.info(f"Running step: {step}")
        if step == "check_data":
            ret = step_check_data(args)
        elif step == "ingest":
            ret = step_ingest(args)
        elif step == "analyze":
            ret = step_analyze(args)
        elif step == "viz":
            ret = step_viz(args)
        
        if ret != 0:
            logger.error(f"Step {step} failed with code {ret}. Stopping.")
            return ret
    logger.info("All steps completed successfully.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Main pipeline orchestrator")
    parser.add_argument("--step", choices=["check_data", "ingest", "analyze", "viz", "all"], required=True,
                        help="Pipeline step to execute")
    
    args = parser.parse_args()
    
    if args.step == "check_data":
        return step_check_data(args)
    elif args.step == "ingest":
        return step_ingest(args)
    elif args.step == "analyze":
        return step_analyze(args)
    elif args.step == "viz":
        return step_viz(args)
    elif args.step == "all":
        return step_all(args)
    
    return 1

if __name__ == "__main__":
    sys.exit(main())

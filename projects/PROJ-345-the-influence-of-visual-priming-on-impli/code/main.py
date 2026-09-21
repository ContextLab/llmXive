import logging
import sys
import os
import re
import json
from pathlib import Path

from code.config import Config, ensure_directories
from code.security.pii_scanner import scan_directory_for_pii

def setup_logging():
    """Configure logging to output to stdout and file."""
    log_dir = Path(Config.CODE_DIR) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file))
        ]
    )
    return logging.getLogger(__name__)

def scan_for_pii(data_path: str) -> dict:
    """
    Scan CSV files in data_path for PII using regex patterns.
    Returns a dict with leaks found.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Scanning for PII in {data_path}")
    
    # Delegate to the security module which handles the actual scanning
    result = scan_directory_for_pii(data_path)
    return result

def main():
    """
    Main entry point for the pipeline.
    Supports --action download, --action run, --action metrics, --action scan-pii
    """
    import argparse
    parser = argparse.ArgumentParser(description="llmXive Pipeline Runner")
    parser.add_argument('--action', type=str, required=True, 
                        choices=['download', 'run', 'metrics', 'scan-pii'],
                        help='Action to perform')
    args = parser.parse_args()

    logger = setup_logging()
    ensure_directories()

    if args.action == 'download':
        logger.info("Starting data download (T013)...")
        from code.data.ingest import main as ingest_main
        try:
            ingest_main()
        except Exception as e:
            logger.error(f"Download failed: {e}")
            sys.exit(1)

    elif args.action == 'run':
        logger.info("Running full pipeline (T014 -> T016 -> T017)...")
        from code.data.ingest import main as ingest_main
        ingest_main()
        from code.data.generate_linked_trials import main as generate_linked_main
        generate_linked_main()
        logger.info("Pipeline run complete.")

    elif args.action == 'metrics':
        logger.info("Calculating ingest metrics (T018a)...")
        from code.data.calculate_ingest_metrics import main as metrics_main
        metrics_main()

    elif args.action == 'scan-pii':
        logger.info("Scanning for PII (T010/T042)...")
        # Use the scan_for_pii function defined above
        result = scan_for_pii(str(Config.DATA_PROCESSED))
        # Save result to reports/pii_scan.json
        reports_dir = Path(Config.CODE_DIR).parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_file = reports_dir / "pii_scan.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"PII scan complete. Results saved to {output_file}")
        # Verify expected output for T042
        if result.get("leaks") == []:
            logger.info("Verification PASSED: No PII leaks detected.")
        else:
            logger.warning(f"Verification WARNING: {len(result.get('leaks', []))} PII leaks detected.")

    else:
        logger.error(f"Unknown action: {args.action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
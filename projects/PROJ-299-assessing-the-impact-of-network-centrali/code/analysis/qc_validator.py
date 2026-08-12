"""
QC Validator

Validates that the number of usable participants meets the power requirement (N >= 85).
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging_config import setup_logging, get_logger
from code.utils.io_utils import write_json, read_json

def validate_qc():
    """
    Validate QC counts.
    """
    logger = get_logger("qc_validator")
    logger.info("Validating QC Counts")

    qc_log_path = project_root / "data" / "analysis" / "qc_log.json"
    if not qc_log_path.exists():
        logger.error("QC log not found.")
        return 1

    qc_log = read_json(qc_log_path)
    included_count = len(qc_log.get("included", []))

    logger.info(f"Usable participants: {included_count}")

    # Power requirement: N >= 85
    if included_count < 85:
        logger.error(f"Insufficient power: N={included_count} < 85. Aborting.")
        return 2

    # Write summary
    summary = {
        "usable_count": included_count,
        "threshold": 85,
        "status": "PASS" if included_count >= 85 else "FAIL"
    }

    summary_path = project_root / "data" / "analysis" / "qc_summary.json"
    write_json(summary_path, summary)

    logger.info(f"Wrote QC summary to {summary_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Validate QC Counts")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return validate_qc()

if __name__ == "__main__":
    sys.exit(main())

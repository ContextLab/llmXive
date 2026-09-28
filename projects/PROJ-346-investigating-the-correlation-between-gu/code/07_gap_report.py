import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Import local utilities ensuring compatibility with the API surface
try:
    from utils import (
        get_project_root_path,
        get_data_processed_path,
        get_data_raw_path,
        setup_logger,
        write_json_log
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import (
        get_project_root_path,
        get_data_processed_path,
        get_data_raw_path,
        setup_logger,
        write_json_log
    )

logger = setup_logger("gap_report")

def generate_gap_report(reason: str = "No common participant IDs found"):
    """
    Generate a Data Gap Notification (FR-008 fallback).
    Writes the report to data/processed/data_gap_report.json.
    Triggers T017d (Meta-Analysis) immediately after writing the report.
    """
    logger.info(f"Generating Data Gap Report (FR-008 fallback)...")
    logger.info(f"Reason: {reason}")

    report_data = {
        "timestamp": datetime.now().isoformat(),
        "status": "DATA_GAP",
        "failure_reason": reason,
        "affected_studies": [
            "Qiita Study 10313 (Microbiome)",
            "UK Biobank / NHANES (Cognitive)"
        ],
        "action_taken": "Triggered Secondary Literature Synthesis (T017d)",
        "next_step_script": "code/08_meta_analysis.py",
        "output_file": "data/processed/data_gap_report.json"
    }

    # Ensure the output path is a file, not a directory
    output_dir = get_data_processed_path()
    output_path = output_dir / "data_gap_report.json"
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Fix potential IsADirectoryError by ensuring we write to a file path
    # If a directory exists at this path, remove it to allow file creation
    if output_path.exists() and output_path.is_dir():
        logger.warning(f"Path {output_path} is a directory. Removing it to write file.")
        import shutil
        shutil.rmtree(output_path)

    write_json_log(report_data, output_path)
    logger.info(f"Gap report written to {output_path}")

    # Trigger T017d (Meta-Analysis) immediately
    logger.info("Triggering T017d (Secondary Literature Synthesis)...")
    trigger_meta_analysis()

def trigger_meta_analysis():
    """
    Executes the meta-analysis script (T017d) to generate the fallback report.
    This function is called by generate_gap_report.
    """
    meta_script_path = Path(__file__).parent / "08_meta_analysis.py"
    if meta_script_path.exists():
        logger.info(f"Executing {meta_script_path}...")
        # Run the meta-analysis script as a subprocess to ensure it runs independently
        # and writes its own output files.
        result = os.system(f"python {meta_script_path}")
        if result != 0:
            logger.error(f"Meta-analysis script failed with exit code {result}")
            raise RuntimeError("Secondary literature synthesis (T017d) failed.")
        logger.info("Meta-analysis completed successfully.")
    else:
        logger.warning(f"Meta-analysis script not found at {meta_script_path}. Skipping trigger.")

def main():
    """Main entry point for the gap report generation."""
    try:
        generate_gap_report()
    except Exception as e:
        logger.exception(f"Error generating gap report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

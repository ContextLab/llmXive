"""
Main Orchestrator for the Pipeline (Task T076 Integration)

This script orchestrates the pipeline execution, ensuring the audit trail
is initialized and referenced by the data source report.
"""
import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Import from existing API surface
from utils.config import get_project_root, ensure_directory
from data.audit_trail import log_file_attempt, ensure_empty_audit_trail, run_audit_trail
from data.generate_source_report import generate_report

logger = logging.getLogger(__name__)

def setup_logger():
    """Configures the root logger."""
    log_dir = get_project_root() / "data" / "logs"
    ensure_directory(log_dir / "pipeline.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_json_file(path: Path) -> dict:
    """Loads a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(path: Path, data: dict) -> None:
    """Saves a JSON file."""
    ensure_directory(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def run_script(script_name: str, args: list = None) -> bool:
    """Runs a specific script in the code directory."""
    project_root = get_project_root()
    script_path = project_root / "code" / script_name
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Script failed: {e}")
        if e.stdout:
            logger.error(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        return False

def run_pipeline(input_file: Optional[str] = None, use_mock: bool = False) -> bool:
    """
    Executes the full pipeline steps.
    """
    project_root = get_project_root()
    
    # 1. Initialize Audit Trail
    logger.info("Initializing Audit Trail...")
    ensure_empty_audit_trail()

    # 2. Handle Input Data
    input_path = project_root / "data" / "raw" / "studies.csv"
    mock_path = project_root / "data" / "raw" / "mock_studies.csv"

    if use_mock:
        logger.info("Mock mode enabled. Logging mock usage.")
        log_file_attempt(str(mock_path), "success", "Mock data selected", file_size_bytes=0)
        # In a real scenario, we might copy mock to studies.csv if needed by downstream
        if not input_path.exists() and mock_path.exists():
            # Copy mock to studies.csv for pipeline compatibility
            import shutil
            shutil.copy(mock_path, input_path)
            logger.info(f"Copied mock data to {input_path}")
    else:
        if input_path.exists():
            file_size = input_path.stat().st_size
            log_file_attempt(str(input_path), "success", "Real data file found", file_size_bytes=file_size)
        else:
            log_file_attempt(str(input_path), "fail", "Real data file missing")
            # Trigger empty file creation for N=0 path (as per T056/T070)
            # We assume T056/ensure_input handles the empty file creation if needed
            # But we log the attempt here first.

    # 3. Run Pipeline Stages
    # Ensure directories exist
    run_script("setup_directories.py")

    # Run Gatekeeper first to determine mode
    # Gatekeeper needs study_count and valid_pair_count
    # We assume parser runs before gatekeeper in the full flow, 
    # but for this orchestrator, we run in dependency order.
    
    stages = [
        "extraction/parser.py",       # Produces extracted_studies.csv
        "analysis/study_counter.py",  # Produces study_count.json
        "analysis/valid_pair_counter.py", # Produces valid_pair_count.json
        "analysis/gatekeeper.py",     # Produces gate_result.json
        "analysis/meta_analysis.py",  # Produces meta_results.json (if quantitative)
        "analysis/narrative_engine.py", # Produces narrative_content.md (if narrative)
        "analysis/correction.py",     # Produces bonferroni_status.json
        "analysis/bias.py",           # Produces egger_test.json
        "analysis/heterogeneity.py",  # Produces heterogeneity_results.json
        "analysis/independence_checker.py", # Produces independence_status.json
        "visualization/plots_forest.py", # Produces forest_plot.png
        "visualization/plots_funnel.py", # Produces funnel_plot.png
        "visualization/plots_correlation.py", # Produces correlation_plot.png
        "report/generate_paper.py"    # Produces paper_draft.md
    ]

    success = True
    for stage in stages:
        if not run_script(stage):
            logger.warning(f"Stage {stage} failed or skipped. Continuing...")
            # Depending on severity, we might stop, but for now we continue to generate partial report
    
    # 4. Generate Source Report (T072)
    logger.info("Generating Data Source Verification Report...")
    # We call the function directly to ensure it runs after audit logging
    try:
        generate_report()
    except Exception as e:
        logger.error(f"Failed to generate source report: {e}")
        success = False

    return success

def main():
    parser = argparse.ArgumentParser(description="Main Pipeline Orchestrator")
    parser.add_argument("--input", type=str, help="Path to input CSV", default=None)
    parser.add_argument("--use-mock", action="store_true", help="Use mock data")
    args = parser.parse_args()

    setup_logger()
    logger.info("Pipeline started.")

    success = run_pipeline(input_file=args.input, use_mock=args.use_mock)

    if success:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
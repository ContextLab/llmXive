"""
Run full pipeline orchestrator.
Executes all stages in the correct order.
"""
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from llmxive_toolkit import paths
from config.settings import get_config
from data.download import main as download_main
from data.extract import main as extract_main
from data.validation import main as validation_main
from data.sentiment import main as sentiment_main
from data.metrics import main as metrics_main
from data.modeling import main as modeling_main
from analysis.final_validation import main as final_validation_main
from analysis.generate_final_reports import main as reports_main
from analysis.update_analysis_summary import main as summary_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories."""
    dirs = [
        "data/raw", "data/processed", "data/results",
        "state", "docs", "figures"
    ]
    for d in dirs:
        (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def run_stage(stage_name: str, func):
    """Run a specific stage with timing and error handling."""
    logger.info(f"--- Starting Stage: {stage_name} ---")
    start = time.time()
    try:
        func()
        duration = time.time() - start
        logger.info(f"--- Stage {stage_name} completed in {duration:.2f}s ---")
    except Exception as e:
        logger.error(f"--- Stage {stage_name} FAILED: {e} ---")
        raise

def run_sample_pipeline(sample_n: int):
    """
    Produce a tiny CSV with ``sample_n`` example records using a real public dataset.
    The CSV is written to ``data/results/sample_run.csv``.
    """
    try:
        from datasets import load_dataset
    except ImportError as e:
        logger.error("The 'datasets' library is required for the sample pipeline. Install it via 'pip install datasets'.")
        raise

    logger.info(f"Running sample pipeline for {sample_n} records.")
    # Use a small, publicly available dataset – Reddit comments (real data)
    # Streaming to avoid large downloads.
    ds = load_dataset("reddit_comments", split="train", streaming=True)

    output_path = paths.results("sample_run.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV header
    import csv
    fieldnames = ["id", "subreddit", "created_utc", "body"]
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        count = 0
        for record in ds:
            # Ensure required fields exist; skip if missing
            if not all(k in record for k in fieldnames):
                continue
            writer.writerow({
                "id": record["id"],
                "subreddit": record["subreddit"],
                "created_utc": record["created_utc"],
                "body": record["body"].replace("\\n", " ").strip()
            })
            count += 1
            if count >= sample_n:
                break

    logger.info(f"Sample CSV written to {output_path} with {count} rows.")

def run_full_pipeline(args):
    """Execute the full research pipeline."""
    ensure_directories()
    
    # If sample mode is requested, run the lightweight pipeline and exit.
    if args.sample is not None and args.sample > 0:
        run_sample_pipeline(args.sample)
        return

    # 1. Download
    original_argv = sys.argv.copy()
    try:
        sys.argv = [str(PROJECT_ROOT / "code" / "data" / "download.py")]
        run_stage("Data Download", download_main)
    except SystemExit:
        # download_main may call sys.exit; treat a zero exit as success.
        pass
    finally:
        sys.argv = original_argv

    # 2. Extract
    run_stage("Data Extraction", extract_main)

    # 3. Validation
    run_stage("Ground Truth Validation", validation_main)

    # 4. Sentiment
    run_stage("Sentiment Analysis", sentiment_main)

    # 5. Metrics
    run_stage("Metrics Calculation", metrics_main)

    # 6. Modeling (Includes T061 sensitivity analysis)
    run_stage("Statistical Modeling", modeling_main)

    # 7. Final Validation
    run_stage("Final Validation", final_validation_main)

    # 8. Reports
    run_stage("Generate Reports", reports_main)

    # 9. Summary
    run_stage("Update Summary", summary_main)

    logger.info("Pipeline execution complete.")

def main():
    parser = argparse.ArgumentParser(description="Run the full research pipeline.")
    parser.add_argument("--sample", type=int, default=None,
                        help="Run a lightweight sample pipeline that writes a tiny CSV with the given number of records.")
    parser.add_argument("--threads", action="store_true", help="Limit to N threads for testing.")
    parser.add_argument("--limit", type=int, default=None, help="Max threads to process.")
    args = parser.parse_args()
    
    run_full_pipeline(args)

if __name__ == "__main__":
    main()

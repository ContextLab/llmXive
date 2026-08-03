"""
Main pipeline runner for User Story 1.

Executes the data preprocessing and validation pipeline.
If validation passes (T018), it triggers the artifact hashing (T019).
If validation fails, it halts and writes an error report, skipping hashing.
"""
import json
import sys
from pathlib import Path

from code.data.preprocess import (
    run_validation_pipeline,
    write_error_report,
    load_keywords,
    classify_pr,
    load_dataset_from_fetch,
    filter_nulls,
    compute_basic_stats,
    check_completeness,
    check_power_insufficiency,
    write_stats_report,
)
from code.utils.hash_artifacts import hash_multiple_dirs, main as hash_main
from code.utils.config import set_global_seed
from code.utils.logger import get_logger, log_validation_error

logger = get_logger(__name__)

def main():
    """
    Orchestrates the full US1 pipeline:
    1. Load and preprocess data.
    2. Run validation checks (Completeness & Power).
    3. If validation passes: Generate checksums for artifacts (T019).
    4. If validation fails: Log error and exit (T018 behavior).
    """
    logger.info("Starting User Story 1 Pipeline Execution")
    
    # Set global seed for reproducibility
    set_global_seed(42)

    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    docs_reports_dir = project_root / "docs" / "reports"
    artifacts_to_hash = [
        data_dir,
        docs_reports_dir,
    ]

    # Ensure output directories exist
    docs_reports_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load Keywords
        keywords_path = project_root / "code" / "labeling" / "keywords.yaml"
        logger.info(f"Loading keywords from {keywords_path}")
        keywords = load_keywords(keywords_path)

        # 2. Fetch Dataset (Real Source)
        logger.info("Fetching dataset from HuggingFace...")
        raw_df = load_dataset_from_fetch()
        
        if raw_df is None or raw_df.empty:
            raise ValueError("Dataset fetch returned empty or None.")

        # 3. Preprocess: Filter Nulls
        logger.info("Filtering null values...")
        clean_df = filter_nulls(raw_df)

        # 4. Classify PRs
        logger.info("Classifying PRs based on keywords...")
        classified_df = classify_pr(clean_df, keywords)

        # 5. Compute Basic Stats
        logger.info("Computing basic statistics...")
        basic_stats = compute_basic_stats(classified_df)
        
        # Write stats report
        stats_report_path = docs_reports_dir / "basic_stats.json"
        write_stats_report(basic_stats, stats_report_path)
        logger.info(f"Wrote basic stats to {stats_report_path}")

        # 6. Run Validation Pipeline (T018 Logic)
        # This function internally checks completeness and power insufficiency.
        # It raises ValueError if checks fail.
        logger.info("Running validation checks (Completeness & Power)...")
        
        completeness_ok = check_completeness(classified_df)
        if not completeness_ok:
            # write_error_report is called inside check_completeness if it fails, 
            # but we ensure the pipeline halts here.
            error_msg = "Data completeness check failed (< 95%)."
            write_error_report(error_msg, "completeness", docs_reports_dir)
            logger.error(error_msg)
            raise ValueError(error_msg)

        power_ok = check_power_insufficiency(classified_df)
        if not power_ok:
            error_msg = "Power insufficiency detected (< 500 per group)."
            write_error_report(error_msg, "power", docs_reports_dir)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Validation passed. Proceeding to artifact hashing.")

        # 7. T019: Hash Artifacts (Constitution Principle V)
        # Only runs if validation passed above.
        logger.info("Generating checksums for data and report artifacts...")
        
        checksums = hash_multiple_dirs(artifacts_to_hash, output_dir=docs_reports_dir)
        
        logger.info(f"Successfully generated checksums: {checksums}")
        logger.info("Pipeline completed successfully.")

    except ValueError as e:
        # T018 Validation Failure Path
        logger.error(f"Validation failed: {e}")
        # Ensure error report is written if not already handled
        if not (docs_reports_dir / "error_report.json").exists():
            write_error_report(str(e), "validation_failure", docs_reports_dir)
        logger.info("Pipeline halted due to validation failure. Hashing skipped.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
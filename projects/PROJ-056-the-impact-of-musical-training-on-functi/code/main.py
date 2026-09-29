"""
Main entry point for the llmXive research pipeline: The Impact of Musical Training on Functional Connectivity.

This script orchestrates the entire research workflow, supporting two distinct modes:
1. Verification Mode: Runs the pipeline on synthetic data to validate code correctness,
   data flow, and memory constraints without requiring real biological data.
2. Analysis Mode: Runs the pipeline on real, verified neuroimaging data (e.g., ABCD, HCP)
   to produce scientifically valid results.

Usage:
    python code/main.py --mode verification
    python code/main.py --mode analysis --data-path /path/to/real/data
"""

import argparse
import sys
import os
from pathlib import Path
import logging
import traceback
import time

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

# Add code directory to path for imports
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging import configure_logger, get_logger
from utils.memory_monitor import check_memory_limit, get_memory_usage_report, MemoryLimitExceeded
from data.download import load_data, DataAccessError
from data.preprocess import preprocess_subjects
from data.output_cleaned_subjects import write_cleaned_subjects
from analysis.connectivity import generate_group_connectivity_results
from analysis.stats import process_connectivity_statistics
from analysis.output_connectivity_results import write_connectivity_results
from analysis.run_nbs import run_nbs_analysis
from analysis.output_nbs_results import write_nbs_results
from analysis.correlation import process_correlation_analysis
from analysis.sensitivity import process_sensitivity_analysis
from analysis.output_correlation_results import process_correlation_output

logger = get_logger(__name__)


def run_verification_mode(data_path: str, output_dir: str) -> bool:
    """
    Execute the pipeline using synthetic data for verification.

    Args:
        data_path: Path to store synthetic data (usually ignored as it's generated in-memory).
        output_dir: Directory for processed outputs.

    Returns:
        True if successful, False otherwise.
    """
    logger.info("Starting VERIFICATION MODE pipeline.")
    start_time = time.time()

    try:
        # 1. Load Data (Synthetic)
        logger.info("Loading synthetic dataset...")
        df_subjects = load_data(path=data_path, mode="verification")
        check_memory_limit()

        # 2. Preprocess Data
        logger.info("Preprocessing subjects (filtering, confounder handling)...")
        cleaned_df = preprocess_subjects(df_subjects)
        check_memory_limit()

        # 3. Output Cleaned Subjects
        logger.info("Writing cleaned subjects to CSV...")
        cleaned_path = Path(output_dir) / "subjects_cleaned.csv"
        write_cleaned_subjects(cleaned_df, str(cleaned_path))
        check_memory_limit()

        # 4. Compute Connectivity (Group Level)
        # Note: In verification mode, we assume connectivity matrices are generated
        # or loaded from a simulated state within the downstream modules.
        logger.info("Computing group connectivity results...")
        conn_results = generate_group_connectivity_results(str(cleaned_path))
        check_memory_limit()

        # 5. Statistical Analysis
        logger.info("Running statistical analysis (Welch's t-test, FDR, Cohen's d)...")
        stats_results = process_connectivity_statistics(conn_results)
        check_memory_limit()

        # 6. Output Connectivity Stats
        logger.info("Writing connectivity statistics to CSV...")
        stats_path = Path(output_dir) / "connectivity_results.csv"
        write_connectivity_results(stats_results, str(stats_path))
        check_memory_limit()

        # 7. Network Based Statistic (NBS)
        logger.info("Running Network Based Statistic (NBS)...")
        nbs_results = run_nbs_analysis(str(cleaned_path))
        check_memory_limit()

        # 8. Output NBS Results
        logger.info("Writing NBS results to CSV...")
        nbs_path = Path(output_dir) / "nbs_results.csv"
        write_nbs_results(nbs_results, str(nbs_path))
        check_memory_limit()

        # 9. Correlation Analysis (Musicians only)
        logger.info("Running correlation analysis (Years of Training vs Connectivity)...")
        corr_results = process_correlation_analysis(str(cleaned_path))
        check_memory_limit()

        # 10. Sensitivity Analysis
        logger.info("Running sensitivity analysis...")
        sens_results = process_sensitivity_analysis(corr_results)
        check_memory_limit()

        # 11. Output Correlation & Sensitivity
        logger.info("Writing correlation and sensitivity results...")
        corr_out_path = Path(output_dir) / "correlation_results.csv"
        sens_out_path = Path(output_dir) / "sensitivity_analysis.csv"
        process_correlation_output(corr_results, sens_results, str(corr_out_path), str(sens_out_path))

        elapsed = time.time() - start_time
        logger.info(f"Verification Mode completed successfully in {elapsed:.2f} seconds.")
        logger.info(f"Memory Report: {get_memory_usage_report()}")
        return True

    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded during verification: {e}")
        logger.error(get_memory_usage_report())
        return False
    except Exception as e:
        logger.error(f"Verification Mode failed with unexpected error: {e}")
        logger.error(traceback.format_exc())
        return False


def run_analysis_mode(data_path: str, output_dir: str) -> bool:
    """
    Execute the pipeline using real neuroimaging data.

    Args:
        data_path: Path to the real data directory or manifest.
        output_dir: Directory for processed outputs.

    Returns:
        True if successful, False otherwise.
    """
    logger.info("Starting ANALYSIS MODE pipeline.")
    logger.warning("Analyzing real biological data. Ensure data integrity and privacy compliance.")
    start_time = time.time()

    try:
        # 1. Load Data (Real)
        logger.info(f"Loading real dataset from: {data_path}")
        if not os.path.exists(data_path):
            raise DataAccessError(f"Data Source Missing: Real data required for Analysis Mode at {data_path}")

        df_subjects = load_data(path=data_path, mode="analysis")
        check_memory_limit()

        # 2. Preprocess Data
        logger.info("Preprocessing real subjects (filtering, confounder handling)...")
        cleaned_df = preprocess_subjects(df_subjects)
        check_memory_limit()

        # 3. Output Cleaned Subjects
        logger.info("Writing cleaned subjects to CSV...")
        cleaned_path = Path(output_dir) / "subjects_cleaned.csv"
        write_cleaned_subjects(cleaned_df, str(cleaned_path))
        check_memory_limit()

        # 4. Compute Connectivity (Group Level)
        logger.info("Computing group connectivity results from real data...")
        conn_results = generate_group_connectivity_results(str(cleaned_path))
        check_memory_limit()

        # 5. Statistical Analysis
        logger.info("Running statistical analysis on real data...")
        stats_results = process_connectivity_statistics(conn_results)
        check_memory_limit()

        # 6. Output Connectivity Stats
        logger.info("Writing connectivity statistics to CSV...")
        stats_path = Path(output_dir) / "connectivity_results.csv"
        write_connectivity_results(stats_results, str(stats_path))
        check_memory_limit()

        # 7. Network Based Statistic (NBS)
        logger.info("Running Network Based Statistic (NBS) on real data...")
        nbs_results = run_nbs_analysis(str(cleaned_path))
        check_memory_limit()

        # 8. Output NBS Results
        logger.info("Writing NBS results to CSV...")
        nbs_path = Path(output_dir) / "nbs_results.csv"
        write_nbs_results(nbs_results, str(nbs_path))
        check_memory_limit()

        # 9. Correlation Analysis
        logger.info("Running correlation analysis on real data...")
        corr_results = process_correlation_analysis(str(cleaned_path))
        check_memory_limit()

        # 10. Sensitivity Analysis
        logger.info("Running sensitivity analysis on real data...")
        sens_results = process_sensitivity_analysis(corr_results)
        check_memory_limit()

        # 11. Output Correlation & Sensitivity
        logger.info("Writing correlation and sensitivity results...")
        corr_out_path = Path(output_dir) / "correlation_results.csv"
        sens_out_path = Path(output_dir) / "sensitivity_analysis.csv"
        process_correlation_output(corr_results, sens_results, str(corr_out_path), str(sens_out_path))

        elapsed = time.time() - start_time
        logger.info(f"Analysis Mode completed successfully in {elapsed:.2f} seconds.")
        logger.info(f"Memory Report: {get_memory_usage_report()}")
        return True

    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded during analysis: {e}")
        logger.error(get_memory_usage_report())
        return False
    except DataAccessError as e:
        logger.error(f"Data access error: {e}")
        return False
    except Exception as e:
        logger.error(f"Analysis Mode failed with unexpected error: {e}")
        logger.error(traceback.format_exc())
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Main pipeline for Musical Training Connectivity Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          python code/main.py --mode verification
          python code/main.py --mode analysis --data-path ./data/raw
        """
    )
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["verification", "analysis"],
        help="Mode of operation: 'verification' (synthetic) or 'analysis' (real data)"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="./data/raw",
        help="Path to data directory (required for analysis mode, optional for verification)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/processed",
        help="Directory for output files"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Configure logging
    configure_logger(level=args.log_level)
    logger.info(f"Pipeline initialized. Mode: {args.mode}, Data: {args.data_path}")

    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Execute pipeline
    if args.mode == "verification":
        success = run_verification_mode(args.data_path, args.output_dir)
    elif args.mode == "analysis":
        success = run_analysis_mode(args.data_path, args.output_dir)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

    if success:
        logger.info("Pipeline execution finished successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
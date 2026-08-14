"""
stats_runner.py

Reconciles run-book vs implementation for the analysis phase.
This script is invoked by quickstart.md to perform statistical analysis on
anonymized participant logs.

It reads the cleaned/anonymized dataset, performs the pre-specified
Welch's ANOVA with ANCOVA adjustment (as mandated by the plan),
and writes the results to the specified output file.
"""

import argparse
import json
import os
import sys
import logging
from pathlib import Path

# Import from existing project modules as per API surface
from analysis import (
    load_json_file,
    save_json_file,
    perform_welchs_anova,
    perform_ancova_with_centering,
    generate_final_report,
    handle_incomplete_records,
    remove_pii
)
from utils.monitor import monitor_execution, ActiveMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Run statistical analysis on anonymized task logs.'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to the input JSON file (e.g., data/processed/task_logs_anon.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to write the analysis results JSON (e.g., data/processed/analysis_results.json)'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading data from {input_path}")
    try:
        data = load_json_file(str(input_path))
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    if not data:
        logger.warning("Input data is empty. Generating empty report.")
        empty_report = {
            "status": "no_data",
            "message": "No participant logs found to analyze.",
            "results": {}
        }
        save_json_file(empty_report, str(output_path))
        logger.info(f"Wrote empty report to {output_path}")
        return

    logger.info(f"Processing {len(data)} records")

    # Wrap execution in monitor to satisfy T044 (resource constraints)
    with monitor_execution() as monitor:
        try:
            # 1. Handle incomplete records (T032b logic)
            cleaned_data, dropouts = handle_incomplete_records(data)
            logger.info(f"Excluded {len(dropouts)} incomplete records.")

            # 2. Perform Pre-specified Welch's ANOVA (T036)
            # Note: The spec mandates this regardless of variance homogeneity.
            # Diagnostic checks (Levene/Shapiro) are logged but do not switch the test.
            logger.info("Performing Pre-specified Welch's ANOVA...")
            anova_results = perform_welchs_anova(cleaned_data)

            # 3. Perform ANCOVA with centering (T037c, T059)
            # Requires covariate data which should be merged or available.
            # Assuming the input data includes covariates or they are loaded separately.
            # For this runner, we assume the input 'cleaned_data' has been enriched
            # or we attempt to merge with repo_covariates if available.
            ancova_results = None
            try:
                covariate_path = Path("data/raw/repo_covariates.json")
                covariates = {}
                if covariate_path.exists():
                    covariates = load_json_file(str(covariate_path))
                
                logger.info("Performing ANCOVA with centered covariates...")
                ancova_results = perform_ancova_with_centering(cleaned_data, covariates)
            except Exception as e:
                logger.warning(f"ANCOVA failed (likely missing covariates): {e}. Proceeding with ANOVA results only.")

            # 4. Generate Final Report (T043)
            logger.info("Generating final analysis report...")
            final_report = generate_final_report(
                anova_results,
                ancova_results,
                dropouts,
                monitor.get_stats()
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            sys.exit(1)

    # Save results
    logger.info(f"Saving results to {output_path}")
    save_json_file(final_report, str(output_path))
    
    logger.info("Analysis complete.")


if __name__ == '__main__':
    main()
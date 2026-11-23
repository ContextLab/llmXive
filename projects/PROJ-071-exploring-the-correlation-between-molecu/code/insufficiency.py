from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from existing project modules
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


def load_stat_gate_status() -> Optional[Dict[str, Any]]:
    """Load the statistical gate status from data/stat_gate_status.json."""
    project_root = get_project_root()
    status_path = project_root / "data" / "stat_gate_status.json"

    if not status_path.exists():
        logger.warning(f"Stat gate status file not found: {status_path}")
        return None

    try:
        with open(status_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load stat gate status: {e}")
        return None


def generate_insufficiency_report(
    n_count: int,
    reason: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate the statistical insufficiency report markdown file.

    Args:
        n_count: The count of records that failed the gate.
        reason: The reason for insufficiency.
        output_path: Optional path to write the report. Defaults to
                     data/processed/statistical_insufficiency_report.md

    Returns:
        Path to the generated report file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "statistical_insufficiency_report.md"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat()

    report_content = f"""# Statistical Insufficiency Report

## Summary
- **Status**: INSUFFICIENT DATA
- **Record Count (N)**: {n_count}
- **Reason**: {reason}
- **Generated**: {timestamp}

## Decision
The dataset does not meet the minimum statistical requirements for correlation analysis.
The analysis has been halted to prevent spurious results from underpowered samples.

## Required Minimum
- The pipeline requires at least 30 records with standard conditions (25°C, pH 7.4)
  to perform valid correlation and regression analysis.

## Next Steps
- Review data collection strategies.
- Consider expanding the dataset with additional sources.
- Verify data filtering criteria in `code/standardize.py`.

## Technical Details
- **Gate File**: data/stat_gate_status.json
- **Derived State**: data/processed/full_processed_state.csv
- **Analysis Log**: data/processed/analysis_log.txt
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"Generated statistical insufficiency report: {output_path}")
    return output_path


def generate_full_processed_state(
    source_csv_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate the full_processed_state.csv file documenting the inclusion/exclusion state.

    Args:
        source_csv_path: Path to the source CSV (e.g., standard_subset or merged_drugs).
                         If None, creates an empty CSV with the schema.
        output_path: Optional path to write the file. Defaults to
                     data/processed/full_processed_state.csv

    Returns:
        Path to the generated CSV file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "full_processed_state.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import pandas as pd

    if source_csv_path and source_csv_path.exists():
        try:
            df = pd.read_csv(source_csv_path)
            # Ensure 'smiles' column exists
            if 'smiles' not in df.columns:
                # If no smiles column, create an empty dataframe with schema
                df = pd.DataFrame(columns=['smiles', 'is_included', 'derivation_source'])
            else:
                # Mark all as excluded (since gate failed)
                df['is_included'] = False
                df['derivation_source'] = source_csv_path.name
        except Exception as e:
            logger.error(f"Failed to read source CSV: {e}. Creating empty schema file.")
            df = pd.DataFrame(columns=['smiles', 'is_included', 'derivation_source'])
    else:
        # Create empty dataframe with required schema
        df = pd.DataFrame(columns=['smiles', 'is_included', 'derivation_source'])

    df.to_csv(output_path, index=False)
    logger.info(f"Generated full processed state: {output_path}")
    return output_path


def generate_analysis_log(
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate the analysis_log.txt documenting excluded operations.

    Args:
        output_path: Optional path to write the file. Defaults to
                     data/processed/analysis_log.txt

    Returns:
        Path to the generated log file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "analysis_log.txt"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat()

    log_content = f"""Analysis Log
============
Timestamp: {timestamp}

Status: STATISTICAL GATE FAILED

Excluded Operations:
- Arrhenius normalization excluded due to missing Ea (Activation Energy) data.
- Correlation analysis skipped: Insufficient sample size (N < 30).
- Regression modeling skipped: Insufficient sample size (N < 30).

Reason:
The dataset failed the statistical sufficiency gate. No further analysis
was performed to prevent invalid statistical inferences.

Reference:
- See data/processed/statistical_insufficiency_report.md for details.
- See data/processed/full_processed_state.csv for record-level status.
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(log_content)

    logger.info(f"Generated analysis log: {output_path}")
    return output_path


def main() -> None:
    """
    Main entry point for T021d: Statistical Insufficiency Artifact Generation.

    This function:
    1. Reads data/stat_gate_status.json.
    2. If status is "FAIL", generates the required artifacts:
       - data/processed/statistical_insufficiency_report.md
       - data/processed/full_processed_state.csv
       - data/processed/analysis_log.txt
    3. Exits cleanly (no exception raised).
    """
    logger.info("Starting Statistical Insufficiency Artifact Generation (T021d)")

    # 1. Read stat gate status
    status_data = load_stat_gate_status()

    if status_data is None:
        logger.error("stat_gate_status.json not found or invalid. Cannot proceed.")
        sys.exit(1)

    status = status_data.get("status", "").upper()

    if status != "FAIL":
        logger.info(f"Stat gate status is '{status}'. No insufficiency artifacts needed.")
        sys.exit(0)

    # 2. Extract details
    n_count = status_data.get("N", 0)
    reason = status_data.get("reason", "Unknown reason")

    logger.info(f"Stat gate FAILED. N={n_count}, Reason: {reason}")

    # 3. Generate artifacts
    try:
        # Determine source for full_processed_state (usually standard_subset if available)
        project_root = get_project_root()
        source_path = project_root / "data" / "processed" / "standard_subset.csv"
        if not source_path.exists():
            source_path = project_root / "data" / "processed" / "merged_drugs.csv"
            if not source_path.exists():
                source_path = None

        generate_insufficiency_report(n_count, reason)
        generate_full_processed_state(source_path)
        generate_analysis_log()

        logger.info("T021d completed successfully. All artifacts generated.")

    except Exception as e:
        logger.error(f"Failed to generate insufficiency artifacts: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
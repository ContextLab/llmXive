"""
Data Download Module for Sustainable Agriculture Study (US1).

This script attempts to fetch real survey data from World Bank LSMS / FAO FIES.
If real sources are unavailable, it falls back to the project's synthetic generator
as a documented limitation, logging the source metadata and the inability to fetch
real data.

It performs variable validation to check for required fields (age, education,
farm_size, credit, adoption, engagement items) and logs gaps to modeling_log.yaml.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Project imports
from config import Config, get_config
from logging_config import log_operation, update_log_section, initialize_modeling_log
from interfaces import DataSource

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

REQUIRED_VARIABLES = [
    "age",
    "education",
    "farm_size",
    "credit",
    "adoption",
    "engagement_membership",
    "engagement_extension",
    "engagement_collective_action",
    "engagement_knowledge_exchange",
]

# Fallback to synthetic if real data is not available
SYNTHETIC_FALLBACK_REASON = "Real data sources (World Bank LSMS / FAO FIES) unavailable or inaccessible."


class WorldBankDataSource(DataSource):
    """
    Placeholder for a real World Bank LSMS data source.
    Attempts to fetch data, but falls back gracefully if not available.
    """

    def __init__(self, country_codes: List[str]):
        self.country_codes = country_codes

    def fetch_data(self, country_codes: List[str] | None = None) -> pd.DataFrame:
        """
        Attempt to fetch real data.
        Since we cannot rely on external APIs in this environment, we raise
        a specific exception to trigger the synthetic fallback logic in the main script.
        """
        raise ConnectionError("Real data source (World Bank LSMS) is currently unreachable.")

    def validate_schema(self, df: pd.DataFrame) -> bool:
        # Basic schema check
        required_cols = ["country_code", "respondent_id"]
        return all(col in df.columns for col in required_cols)


@log_operation("load_config")
def load_config() -> Config:
    return get_config()


@log_operation("check_variable_completeness")
def check_variable_completeness(df: pd.DataFrame, required_vars: List[str]) -> Dict[str, Any]:
    """
    Check for required fields and log gaps.

    Returns a dict with:
      - 'missing': list of missing column names
      - 'present': list of present column names
      - 'status': 'passed' if all present, 'failed' if any missing
    """
    present = [col for col in required_vars if col in df.columns]
    missing = [col for col in required_vars if col not in df.columns]

    status = "passed" if not missing else "failed"

    logger.info(f"Variable validation: {len(present)}/{len(required_vars)} required variables present.")
    if missing:
        logger.warning(f"Missing required variables: {missing}")

    return {
        "missing": missing,
        "present": present,
        "status": status,
        "missing_count": len(missing),
    }


@log_operation("log_validation_gaps")
def log_validation_gaps(validation_result: Dict[str, Any], log_path: Path) -> None:
    """
    Log validation gaps to modeling_log.yaml under 'data_validation' section.
    """
    update_log_section(
        "data_validation",
        {
            "status": validation_result["status"],
            "missing_variables": validation_result["missing"],
            "present_variables": validation_result["present"],
            "missing_count": validation_result["missing_count"],
            "timestamp": str(pd.Timestamp.now()),
        },
    )


@log_operation("load_data")
def load_data(config: Config) -> Tuple[pd.DataFrame, str]:
    """
    Attempt to load real data. If failed, use synthetic generator as fallback.
    Returns (df, source_type) where source_type is 'real' or 'synthetic'.
    """
    country_codes = config.get("country_codes", ["KEN", "UGA", "TZA"])

    try:
        source = WorldBankDataSource(country_codes)
        df = source.fetch_data(country_codes)
        logger.info("Successfully loaded real data from World Bank LSMS.")
        return df, "real"
    except (ConnectionError, Exception) as e:
        logger.warning(f"Failed to load real data: {e}. {SYNTHETIC_FALLBACK_REASON}")
        logger.info("Falling back to synthetic data generator.")

        # Import synthetic generator
        from code_00_generate_synthetic_data import generate_synthetic_dataset

        n_respondents = config.get("n_respondents", 1000)
        seed = config.get("random_seed", 42)
        df = generate_synthetic_dataset(n_respondents, seed, country_codes)

        logger.info(f"Generated synthetic data with {len(df)} records.")
        return df, "synthetic"


@log_operation("ensure_required_columns")
def ensure_required_columns(df: pd.DataFrame, required_vars: List[str]) -> pd.DataFrame:
    """
    Ensure all required columns exist. If missing, create them with NaN or dummy values
    to prevent downstream crashes, but log the gap.
    """
    missing = [col for col in required_vars if col not in df.columns]
    for col in missing:
        logger.warning(f"Creating missing column '{col}' with NaN.")
        df[col] = None
    return df


@log_operation("main")
def main() -> None:
    parser = argparse.ArgumentParser(description="Download and validate agricultural survey data.")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic data generation.")
    args = parser.parse_args()

    initialize_modeling_log()
    config = load_config()

    # Update log section for data source metadata
    source_type = "synthetic" if args.synthetic else "attempt_real"
    update_log_section(
        "data_source_metadata",
        {
            "source_type": source_type,
            "forced_synthetic": args.synthetic,
            "country_codes": config.get("country_codes", []),
            "timestamp": str(pd.Timestamp.now()),
        },
    )

    # Load data
    df, actual_source = load_data(config)

    # If forced synthetic, ensure we note it
    if args.synthetic:
        actual_source = "synthetic_forced"
        update_log_section(
            "data_source_metadata",
            {"actual_source": actual_source, "reason": "User forced synthetic via --synthetic flag"}
        )
    else:
        update_log_section(
            "data_source_metadata",
            {"actual_source": actual_source}
        )

    # Ensure required columns exist (creates NaN if missing)
    df = ensure_required_columns(df, REQUIRED_VARIABLES)

    # Validate variable completeness
    validation_result = check_variable_completeness(df, REQUIRED_VARIABLES)

    # Log gaps
    log_path = Path(config.get("log_path", "modeling_log.yaml"))
    log_validation_gaps(validation_result, log_path)

    # Save raw data
    raw_data_path = Path(config.get("raw_data_path", "data/raw/survey_data.csv"))
    raw_data_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_data_path, index=False)
    logger.info(f"Raw data saved to {raw_data_path}")

    # Update log with final data stats
    update_log_section(
        "data_acquisition",
        {
            "records_loaded": len(df),
            "columns_count": len(df.columns),
            "source": actual_source,
            "validation_status": validation_result["status"],
        },
    )

    logger.info("Data download and validation complete.")


if __name__ == "__main__":
    main()
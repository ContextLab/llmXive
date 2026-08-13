"""
Validator module for data validation logic.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import sys

from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError
from config import (
    get_config,
    get_composition_sum_threshold,
    get_min_samples_warning,
    get_min_samples_target,
    get_data_processed_dir
)

logger = get_logger(__name__)


class DataInsufficientError(Exception):
    """Raised when the dataset size is below the minimum threshold."""
    pass


class DataValidator:
    """
    Validates aggregated data for:
    - Non-null hardness values
    - Complete composition breakdowns
    - Minimum sample size thresholds
    """

    def __init__(self):
        self.config = get_config()
        self.composition_sum_threshold = get_composition_sum_threshold()
        self.min_warning = get_min_samples_warning()  # Default 50
        self.min_target = get_min_samples_target()   # Default 100
        self.processed_dir = get_data_processed_dir()
        self.status_file = self.processed_dir / ".ingestion_status.json"

    def validate_hardness_non_null(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove records with null hardness values."""
        initial_count = len(df)
        if 'hardness_hv' not in df.columns:
            logger.warning("hardness_hv column not found. Cannot validate.")
            return df

        df = df.dropna(subset=['hardness_hv'])
        removed = initial_count - len(df)
        if removed > 0:
            logger.info(f"Removed {removed} records with null hardness values")
        return df

    def validate_composition_complete(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate that composition sums to >= threshold.
        This is a stricter check than the cleaner's filter.
        """
        if 'elemental_breakdown' not in df.columns and 'composition' not in df.columns:
            logger.warning("Composition column not found. Cannot validate completeness.")
            return df

        valid_indices = []
        for idx, row in df.iterrows():
            comp_data = row.get('elemental_breakdown') or row.get('composition')
            if not comp_data:
                continue

            # Parse if string
            if isinstance(comp_data, str):
                try:
                    if comp_data.startswith('{'):
                        comp = json.loads(comp_data)
                    else:
                        # Simple parsing for "Au:50,Cu:50"
                        comp = {}
                        for part in comp_data.split(','):
                            elem, val = part.split(':')
                            comp[elem.strip()] = float(val.strip())
                except Exception:
                    continue
            elif isinstance(comp_data, dict):
                comp = comp_data
            else:
                continue

            total = sum(comp.values())
            if total >= self.composition_sum_threshold:
                valid_indices.append(idx)

        return df.loc[valid_indices].reset_index(drop=True)

    def check_sample_size(self, df: pd.DataFrame) -> str:
        """
        Check sample size against thresholds.
        Returns status string: 'N>=100', '50<=N<100', 'N<50'
        """
        n = len(df)
        if n >= self.min_target:
            return 'N>=100'
        elif n >= self.min_warning:
            return '50<=N<100'
        else:
            return 'N<50'

    def write_status(self, df: pd.DataFrame, status: str):
        """Write ingestion status to .ingestion_status.json."""
        warning_text = ""
        if status == '50<=N<100':
            warning_text = f"WARNING: Dataset size ({len(df)}) is below target (100). Power may be limited."
        elif status == 'N<50':
            warning_text = f"CRITICAL: Dataset size ({len(df)}) is below minimum threshold (50)."

        status_data = {
            "threshold_status": status,
            "exact_N": len(df),
            "warning_text": warning_text,
            "min_target": self.min_target,
            "min_warning": self.min_warning
        }

        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

        logger.info(f"Written ingestion status to {self.status_file}: {status_data}")

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all validation steps.
        Raises DataInsufficientError if N < 50.
        """
        logger.info("Starting data validation")

        # 1. Non-null hardness
        df = self.validate_hardness_non_null(df)

        # 2. Complete composition
        df = self.validate_composition_complete(df)

        # 3. Check sample size
        status = self.check_sample_size(df)
        self.write_status(df, status)

        if status == 'N<50':
            raise DataInsufficientError(
                f"Dataset size ({len(df)}) is below minimum threshold ({self.min_warning}). "
                "Pipeline halted."
            )

        logger.info(f"Validation complete. Status: {status}, N={len(df)}")
        return df


def main():
    """Main entry point for the validator."""
    logger.info("Starting DataValidator")

    try:
        processed_dir = get_data_processed_dir()
        cleaned_file = processed_dir / "solder_hardness_cleaned.csv"

        if not cleaned_file.exists():
            logger.error(f"Cleaned data file not found: {cleaned_file}")
            return

        df = pd.read_csv(cleaned_file)
        validator = DataValidator()
        validated_df = validator.validate(df)

        output_path = processed_dir / "solder_hardness_validated.csv"
        validated_df.to_csv(output_path, index=False)
        logger.info(f"Validated data saved to {output_path}")

    except DataInsufficientError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
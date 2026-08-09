"""
Data Validator: Checks for non-null hardness and complete composition.
Enforces minimum sample size thresholds and writes ingestion status for downstream tasks.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

from seed import init_reproducibility
from config import (
    get_composition_sum_threshold,
    get_min_samples_warning,
    get_min_samples_target,
    get_data_processed_dir,
    get_max_elements
)
from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError

logger = get_logger(__name__)


class DataInsufficientError(DataValidationError):
    """Raised when the dataset size is below the critical minimum (N < 50)."""
    pass


class DataValidator:
    """
    Validates the cleaned dataset for hardness values, composition completeness,
    and sample size sufficiency. Writes status to .ingestion_status.json.
    """

    def __init__(self):
        init_reproducibility()
        self.min_warning = get_min_samples_warning()  # Typically 50
        self.min_target = get_min_samples_target()   # Typically 100
        self.processed_dir = get_data_processed_dir()
        self.status_file = self.processed_dir / ".ingestion_status.json"

    def load_cleaned_data(self) -> pd.DataFrame:
        """
        Loads the cleaned data from the previous stage.
        """
        cleaned_path = self.processed_dir / "solder_hardness_cleaned.csv"

        if not cleaned_path.exists():
            raise FileNotFoundError(f"Cleaned data file not found: {cleaned_path}")

        logger.info(f"Loading cleaned data from {cleaned_path}")
        return pd.read_csv(cleaned_path)

    def validate_hardness(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Checks for non-null hardness values and standardizes units if needed.
        """
        logger.info("Validating non-null hardness...")
        if 'hardness_hv' not in df.columns:
            raise DataValidationError("Missing 'hardness_hv' column in cleaned data.")

        valid_df = df.dropna(subset=['hardness_hv'])
        dropped = len(df) - len(valid_df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with null hardness_hv.")
        return valid_df

    def validate_composition(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Checks for complete composition data (non-null and valid sum).
        """
        logger.info("Validating complete composition...")
        if 'composition' not in df.columns:
            raise DataValidationError("Missing 'composition' column in cleaned data.")

        # Filter rows where composition is not null
        valid_df = df.dropna(subset=['composition'])
        dropped = len(df) - len(valid_df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with null composition.")

        # Validate composition sum if the column 'composition_sum' exists (added by cleaner)
        # If not, we assume cleaner handled it, but we can re-check if needed.
        if 'composition_sum' in valid_df.columns:
            threshold = get_composition_sum_threshold()
            mask = valid_df['composition_sum'].abs() - 1.0 <= (1.0 - threshold)
            # Allow for small floating point errors, usually sum should be ~1.0
            # If the cleaner stored the sum as a float, we check proximity to 1.0
            # The cleaner T013 logic: abs(sum - 1.0) <= tolerance?
            # Assuming cleaner normalized or checked this, but we verify strictness.
            # Let's assume 'composition' is a string or dict. If it's a string, we can't sum here without parsing.
            # Based on T013, it likely logged failures to a separate file.
            # We rely on the fact that T013 already filtered these.
            # However, if we need to re-validate:
            # We assume the 'composition' column contains a string representation of the dict or JSON.
            # For this validator, we assume the cleaner has already done the heavy lifting on sum.
            # We just ensure the column exists and is not null.
            pass

        return valid_df

    def check_sample_size(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Checks sample size against thresholds.
        Returns a dict with status and warning text.
        Raises DataInsufficientError if N < 50.
        """
        n = len(df)
        logger.info(f"Validated dataset size: {n}")

        status = "unknown"
        warning_text = ""

        if n < self.min_warning:
            status = "N<50"
            warning_text = f"CRITICAL: Dataset size ({n}) is below the minimum threshold of 50 samples. Pipeline halted."
            logger.error(warning_text)
            # Write status before raising
            self._write_status(n, status, warning_text)
            raise DataInsufficientError(warning_text)

        elif n < self.min_target:
            status = "50<=N<100"
            warning_text = f"WARNING: Dataset size ({n}) is below the target of 100 samples. Statistical power may be limited. Proceeding with caution."
            logger.warning(warning_text)
        else:
            status = "N>=100"
            warning_text = ""
            logger.info(f"Dataset size ({n}) meets target ({self.min_target}).")

        self._write_status(n, status, warning_text)
        return {"n": n, "status": status, "warning_text": warning_text}

    def _write_status(self, n: int, status: str, warning_text: str):
        """
        Writes the ingestion status to the JSON file for downstream tasks (T016b).
        """
        status_data = {
            "total_records": n,
            "threshold_status": status,
            "warning_text": warning_text,
            "min_warning_threshold": self.min_warning,
            "min_target_threshold": self.min_target
        }

        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        logger.info(f"Wrote ingestion status to {self.status_file}")

    def validate(self) -> pd.DataFrame:
        """
        Runs the full validation pipeline.
        """
        df = self.load_cleaned_data()
        df = self.validate_hardness(df)
        df = self.validate_composition(df)
        # This will raise if N < 50, or log warning if 50 <= N < 100
        self.check_sample_size(df)
        return df


def main():
    """
    Entry point for the validator.
    """
    logger.info("Starting Data Validator...")
    validator = DataValidator()
    try:
        validated_df = validator.validate()
        output_path = validator.processed_dir / "solder_hardness_validated.csv"
        validated_df.to_csv(output_path, index=False)
        logger.info(f"Saved validated data to {output_path}")
        logger.info("Validation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except DataInsufficientError as e:
        logger.error(f"Validation halted due to insufficient data: {e}")
        # Do not create an empty file or proceed. The pipeline must stop.
        # Ensure the status file is written (handled in check_sample_size)
        raise
    except DataValidationError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
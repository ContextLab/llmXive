"""
Data Validator: Checks for non-null hardness and complete composition.
Emits warnings if sample size is below target.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

from seed import init_reproducibility
from config import get_composition_sum_threshold, get_min_samples_warning, get_min_samples_target, get_data_processed_dir
from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError

logger = get_logger(__name__)


class DataValidator:
    """
    Validates the cleaned dataset.
    """

    def __init__(self):
        init_reproducibility()
        self.min_warning = get_min_samples_warning()
        self.min_target = get_min_samples_target()

    def load_cleaned_data(self) -> pd.DataFrame:
        """
        Loads the cleaned data.
        """
        processed_dir = get_data_processed_dir()
        cleaned_path = processed_dir / "solder_hardness_cleaned.csv"

        if not cleaned_path.exists():
            raise FileNotFoundError(f"Cleaned data file not found: {cleaned_path}")

        logger.info(f"Loading cleaned data from {cleaned_path}")
        return pd.read_csv(cleaned_path)

    def validate_hardness(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Checks for non-null hardness values.
        """
        logger.info("Validating non-null hardness...")
        if 'hardness_hv' not in df.columns:
            raise DataValidationError("Missing 'hardness_hv' column.")

        valid_df = df.dropna(subset=['hardness_hv'])
        dropped = len(df) - len(valid_df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with null hardness.")
        return valid_df

    def validate_composition(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Checks for complete composition data.
        """
        logger.info("Validating complete composition...")
        if 'composition' not in df.columns:
            raise DataValidationError("Missing 'composition' column.")

        valid_df = df.dropna(subset=['composition'])
        dropped = len(df) - len(valid_df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with null composition.")
        return valid_df

    def check_sample_size(self, df: pd.DataFrame):
        """
        Emits warnings based on sample size.
        """
        n = len(df)
        logger.info(f"Dataset size: {n}")
        if n < self.min_warning:
            logger.error(f"Dataset size ({n}) is below warning threshold ({self.min_warning}).")
            raise DataValidationError(f"Dataset too small: {n} < {self.min_warning}")
        elif n < self.min_target:
            logger.warning(f"Dataset size ({n}) is below target ({self.min_target}) but above warning threshold.")
        else:
            logger.info(f"Dataset size ({n}) meets target ({self.min_target}).")

    def validate(self) -> pd.DataFrame:
        """
        Runs the full validation pipeline.
        """
        df = self.load_cleaned_data()
        df = self.validate_hardness(df)
        df = self.validate_composition(df)
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
        processed_dir = get_data_processed_dir()
        output_path = processed_dir / "solder_hardness_validated.csv"
        validated_df.to_csv(output_path, index=False)
        logger.info(f"Saved validated data to {output_path}")
    except (FileNotFoundError, DataValidationError) as e:
        logger.error(f"Validation failed: {e}")
        # Create empty validated file
        processed_dir = get_data_processed_dir()
        output_path = processed_dir / "solder_hardness_validated.csv"
        pd.DataFrame(columns=['hardness_hv', 'composition']).to_csv(output_path, index=False)
        logger.info(f"Created empty validated data file at {output_path}")
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()

"""
Data Cleaner: Filters and standardizes raw solder data.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional
import os

from seed import init_reproducibility
from config import get_composition_sum_threshold, get_max_elements, get_data_raw_dir, get_data_processed_dir
from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError

logger = get_logger(__name__)


class DataCleaner:
    """
    Cleans and filters raw solder data.
    """

    def __init__(self):
        init_reproducibility()
        self.max_elements = get_max_elements()
        self.composition_sum_threshold = get_composition_sum_threshold()

    def load_raw_data(self) -> pd.DataFrame:
        """
        Loads the raw data from the CSV file.
        """
        raw_dir = get_data_raw_dir()
        raw_path = raw_dir / "solder_hardness_raw.csv"

        if not raw_path.exists():
            raise FileNotFoundError(f"Raw data file not found: {raw_path}")

        logger.info(f"Loading raw data from {raw_path}")
        df = pd.read_csv(raw_path)
        return df

    def filter_elements(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Excludes alloys with more than the maximum allowed elements.
        """
        logger.info(f"Filtering alloys with > {self.max_elements} elements...")
        # Assuming 'composition' is a string like "Sn:60,Ag:38,Cu:2" or a dict string
        # This logic depends on the exact format of the 'composition' column.
        # For now, we assume a helper function to count elements.
        def count_elements(composition_str):
            if not isinstance(composition_str, str):
                return 0
            # Simple heuristic: count commas + 1, or split by known separators
            # This is a placeholder for robust parsing
            parts = [p for p in composition_str.split(',') if ':' in p]
            return len(parts)

        df['element_count'] = df['composition'].apply(count_elements)
        filtered_df = df[df['element_count'] <= self.max_elements].copy()
        logger.info(f"Filtered to {len(filtered_df)} alloys.")
        return filtered_df

    def standardize_hardness(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardizes hardness to HV units.
        """
        logger.info("Standardizing hardness to HV...")
        # Assuming 'hardness_hv' is the target column.
        # If data comes in other units, conversion logic goes here.
        if 'hardness_hv' not in df.columns:
            # Try to map common column names
            possible_names = ['hardness', 'vickers', 'hv', 'hardness_vickers']
            found = False
            for name in possible_names:
                if name in df.columns:
                    df['hardness_hv'] = df[name]
                    found = True
                    break
            if not found:
                logger.warning("No hardness column found. Creating placeholder.")
                df['hardness_hv'] = None

        return df

    def filter_temperature(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filters for room-temperature measurements only.
        """
        logger.info("Filtering for room-temperature measurements...")
        # Placeholder: Assumes a 'temperature' column exists.
        # If not, we keep all rows and log a warning.
        if 'temperature' in df.columns:
            room_temp_df = df[df['temperature'].isna() | (df['temperature'].between(20, 25))]
            logger.info(f"Filtered to {len(room_temp_df)} room-temperature measurements.")
            return room_temp_df
        else:
            logger.warning("No 'temperature' column found. Assuming all are room temperature.")
            return df

    def validate_composition_sum(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates that elemental composition sums to ~100% (or 1.0).
        """
        logger.info(f"Validating composition sum (threshold: {self.composition_sum_threshold})...")
        # This requires parsing the composition string into numeric values.
        # Placeholder logic:
        def parse_sum(composition_str):
            if not isinstance(composition_str, str):
                return 0.0
            try:
                parts = composition_str.split(',')
                total = 0.0
                for part in parts:
                    if ':' in part:
                        val_str = part.split(':')[1]
                        total += float(val_str)
                return total
            except (ValueError, IndexError):
                return 0.0

        df['composition_sum'] = df['composition'].apply(parse_sum)
        valid_df = df[
            (df['composition_sum'] >= self.composition_sum_threshold * 100) |
            (df['composition_sum'] <= (1.0 + self.composition_sum_threshold)) # Handle 0-1 vs 0-100
        ].copy()
        logger.info(f"Validated {len(valid_df)} alloys with correct composition sum.")
        return valid_df

    def clean(self) -> pd.DataFrame:
        """
        Runs the full cleaning pipeline.
        """
        df = self.load_raw_data()
        df = self.filter_elements(df)
        df = self.standardize_hardness(df)
        df = self.filter_temperature(df)
        df = self.validate_composition_sum(df)
        return df

def main():
    """
    Entry point for the cleaner.
    """
    logger.info("Starting Data Cleaner...")
    cleaner = DataCleaner()
    try:
        cleaned_df = cleaner.clean()
        processed_dir = get_data_processed_dir()
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_path = processed_dir / "solder_hardness_cleaned.csv"
        cleaned_df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path}")
    except FileNotFoundError as e:
        logger.error(f"Cleaner failed: {e}")
        # Create empty file to allow pipeline to continue
        processed_dir = get_data_processed_dir()
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_path = processed_dir / "solder_hardness_cleaned.csv"
        pd.DataFrame(columns=['hardness_hv']).to_csv(output_path, index=False)
        logger.info(f"Created empty cleaned data file at {output_path}")
    except Exception as e:
        logger.error(f"Cleaner failed with unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()

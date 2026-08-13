"""
Cleaner module for data cleaning and filtering operations.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import os
import hashlib
import json

from seed import init_reproducibility
from utils.logging_config import get_logger
from config import (
    get_config,
    get_max_elements,
    get_composition_sum_threshold,
    get_data_processed_dir,
    get_data_raw_dir
)

logger = get_logger(__name__)


class DataCleaner:
    """
    Performs data cleaning and filtering operations:
    - Exclude alloys with >5 elements
    - Standardize hardness to HV units
    - Filter for room-temperature measurements
    - Flag records for manual review
    - Validate elemental composition sums
    """

    def __init__(self):
        self.config = get_config()
        self.max_elements = get_max_elements()
        self.composition_sum_threshold = get_composition_sum_threshold()
        self.room_temp_threshold = self.config.get('ROOM_TEMP_THRESHOLD_C', 25)
        self.room_temp_tolerance = self.config.get('ROOM_TEMP_TOLERANCE_C', 5)
        self.processed_dir = get_data_processed_dir()
        self.raw_dir = get_data_raw_dir()

        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        (self.processed_dir / "validation_logs").mkdir(parents=True, exist_ok=True)

    def _calculate_checksum(self, df: pd.DataFrame) -> str:
        """Calculate SHA256 checksum of a DataFrame."""
        # Convert to string and hash
        csv_string = df.to_csv(index=False)
        return hashlib.sha256(csv_string.encode('utf-8')).hexdigest()

    def filter_by_element_count(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Filter out alloys with more than MAX_ELEMENTS.
        Returns (kept_df, filtered_df).
        """
        # Assuming 'composition' or 'elemental_breakdown' contains the element info
        # This logic depends on the actual data structure
        # Placeholder logic: assuming a column 'num_elements' exists or can be derived

        if 'num_elements' not in df.columns:
            # Try to derive from composition string or dict
            # This is a simplified placeholder
            logger.warning("num_elements column not found. Skipping element count filter.")
            return df, pd.DataFrame()

        kept = df[df['num_elements'] <= self.max_elements].copy()
        filtered = df[df['num_elements'] > self.max_elements].copy()

        logger.info(f"Filtered {len(filtered)} records with >{self.max_elements} elements")
        return kept, filtered

    def standardize_hardness(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize hardness values to HV (Vickers) units.
        Assumes input data has 'hardness_hv' or similar column.
        """
        # Placeholder for unit conversion logic
        # If data comes in other units (e.g., HB, HRC), convert to HV here
        if 'hardness_hv' not in df.columns:
            logger.warning("hardness_hv column not found. Skipping standardization.")
            return df

        # Ensure numeric type
        df['hardness_hv'] = pd.to_numeric(df['hardness_hv'], errors='coerce')
        return df

    def filter_by_temperature(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Filter for room-temperature measurements.
        Returns (kept_df, manual_review_df, out_of_range_df).
        """
        if 'measurement_temp_c' not in df.columns:
            logger.warning("measurement_temp_c column not found. Skipping temperature filter.")
            return df, pd.DataFrame(), pd.DataFrame()

        # Calculate deviation from room temp
        df['temp_deviation'] = (df['measurement_temp_c'] - self.room_temp_threshold).abs()

        # Keep: within tolerance
        kept = df[df['temp_deviation'] <= self.room_temp_tolerance].copy()

        # Manual Review: within 2x tolerance but outside tolerance
        manual_review_mask = (df['temp_deviation'] > self.room_temp_tolerance) & \
                             (df['temp_deviation'] <= 2 * self.room_temp_tolerance)
        manual_review = df[manual_review_mask].copy()

        # Out of range: outside 2x tolerance
        out_of_range = df[df['temp_deviation'] > 2 * self.room_temp_tolerance].copy()

        logger.info(f"Temperature filter: {len(kept)} kept, {len(manual_review)} manual review, {len(out_of_range)} out of range")

        return kept, manual_review, out_of_range

    def validate_composition_sum(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Validate that elemental compositions sum to >= COMPOSITION_SUM_THRESHOLD.
        Returns (kept_df, filtered_df).
        """
        # Assuming 'elemental_breakdown' is a JSON string or dict column
        # This logic needs to adapt to the actual data format

        if 'elemental_breakdown' not in df.columns and 'composition' not in df.columns:
            logger.warning("Composition column not found. Skipping composition sum validation.")
            return df, pd.DataFrame()

        valid_records = []
        invalid_records = []

        for idx, row in df.iterrows():
            # Parse composition
            if isinstance(row.get('elemental_breakdown'), str):
                try:
                    comp = json.loads(row['elemental_breakdown'])
                except json.JSONDecodeError:
                    invalid_records.append(row.to_dict())
                    continue
            elif isinstance(row.get('elemental_breakdown'), dict):
                comp = row['elemental_breakdown']
            elif isinstance(row.get('composition'), str):
                # Attempt to parse string format "Au:50,Cu:50"
                try:
                    comp = {}
                    for part in row['composition'].split(','):
                        elem, val = part.split(':')
                        comp[elem.strip()] = float(val.strip())
                except Exception:
                    invalid_records.append(row.to_dict())
                    continue
            else:
                invalid_records.append(row.to_dict())
                continue

            total = sum(comp.values())
            if total >= self.composition_sum_threshold:
                valid_records.append(row.to_dict())
            else:
                invalid_records.append(row.to_dict())

        kept = pd.DataFrame(valid_records)
        filtered = pd.DataFrame(invalid_records)

        logger.info(f"Composition sum validation: {len(kept)} valid, {len(filtered)} invalid")

        return kept, filtered

    def save_filtered_records(self, df: pd.DataFrame, reason: str):
        """Save filtered records to validation_logs/filtered_records.csv with checksum."""
        if df.empty:
            return

        output_path = self.processed_dir / "validation_logs" / "filtered_records.csv"
        df.to_csv(output_path, index=False)

        checksum = self._calculate_checksum(df)
        checksum_path = self.processed_dir.parent / "checksums.txt"

        with open(checksum_path, 'a') as f:
            f.write(f"{checksum}  {output_path.name} (Reason: {reason})\n")

        logger.info(f"Saved {len(df)} filtered records to {output_path} (Checksum: {checksum})")

    def save_manual_review_queue(self, df: pd.DataFrame):
        """Save records flagged for manual review."""
        if df.empty:
            return

        output_path = self.processed_dir / "manual_review_queue.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} records to manual review queue: {output_path}")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all cleaning steps and return the cleaned DataFrame.
        """
        logger.info("Starting data cleaning pipeline")

        # 1. Filter by element count
        df, filtered_elem = self.filter_by_element_count(df)
        if not filtered_elem.empty:
            self.save_filtered_records(filtered_elem, "EXCEEDS_MAX_ELEMENTS")

        # 2. Standardize hardness
        df = self.standardize_hardness(df)

        # 3. Filter by temperature
        df, manual_review, out_of_range = self.filter_by_temperature(df)
        if not manual_review.empty:
            self.save_manual_review_queue(manual_review)
        if not out_of_range.empty:
            self.save_filtered_records(out_of_range, "TEMP_OUT_OF_RANGE")

        # 4. Validate composition sum
        df, filtered_comp = self.validate_composition_sum(df)
        if not filtered_comp.empty:
            self.save_filtered_records(filtered_comp, "COMPOSITION_SUM_LOW")

        logger.info(f"Cleaning complete. Final record count: {len(df)}")
        return df


def main():
    """Main entry point for the cleaner."""
    logger.info("Starting DataCleaner")

    try:
        raw_dir = get_data_raw_dir()
        raw_file = raw_dir / "solder_hardness_raw.csv"

        if not raw_file.exists():
            logger.error(f"Raw data file not found: {raw_file}")
            return

        df = pd.read_csv(raw_file)
        cleaner = DataCleaner()
        cleaned_df = cleaner.clean(df)

        output_path = get_data_processed_dir() / "solder_hardness_cleaned.csv"
        cleaned_df.to_csv(output_path, index=False)
        logger.info(f"Cleaned data saved to {output_path}")

    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        raise


if __name__ == "__main__":
    main()

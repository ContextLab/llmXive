"""
DataCleaner: Cleans and filters solder hardness data.

This module implements the cleaning logic for T013, including:
- Excluding alloys with >5 elements
- Standardizing hardness to HV units
- Filtering for room-temperature measurements
- Manual review flagging
- Composition sum validation
- Logging failed records
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import os
from seed import init_reproducibility

from config import get_config, get_data_processed_dir, get_max_elements, get_composition_sum_threshold
from utils.error_handlers import DataValidationError
from utils.logging_config import get_logger

class DataCleaner:
    """
    Cleans and filters solder hardness data according to project specifications.
    
    Implements T013 requirements:
    - Exclude alloys with >5 elements
    - Standardize hardness to HV units
    - Filter for room-temperature (25°C ± 5°C)
    - Manual review flagging for 25°C ± 5-10°C
    - Validate composition sums >= 95%
    - Log failed records to filtered_records.csv
    - Generate checksums
    """
    
    def __init__(self):
        """Initialize the DataCleaner."""
        self.logger = get_logger("ingestion.cleaner")
        self.logger.info("Initializing DataCleaner")
        
        # Load configuration
        self.config = get_config()
        self.max_elements = get_max_elements()
        self.composition_sum_threshold = get_composition_sum_threshold()
        
        # Temperature thresholds
        self.room_temp_threshold = self.config.get('ROOM_TEMP_THRESHOLD_C', 25)
        self.room_temp_tolerance = self.config.get('ROOM_TEMP_TOLERANCE_C', 5)
        
        # Output paths
        self.processed_dir = get_data_processed_dir()
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Tracking
        self.filter_log: List[Dict[str, Any]] = []
        self.manual_review_records: List[Dict[str, Any]] = []
        
        self.logger.info(f"DataCleaner initialized: max_elements={self.max_elements}, "
                       f"comp_threshold={self.composition_sum_threshold}")
    
    def clean_data(self, data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Clean and filter the input data.
        
        Args:
            data: List of raw data records
        
        Returns:
            Tuple of (cleaned_data, filtered_records)
        """
        self.logger.info(f"Starting data cleaning on {len(data)} records")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            self.logger.warning("Input data is empty")
            return pd.DataFrame(), pd.DataFrame()
        
        # Track initial count
        initial_count = len(df)
        
        # Apply cleaning steps
        df = self._filter_max_elements(df)
        df = self._standardize_hardness(df)
        df, manual_review = self._filter_temperature(df)
        df = self._validate_composition(df)
        
        # Track final count
        final_count = len(df)
        
        self.logger.info(f"Cleaning complete: {initial_count} -> {final_count} records")
        self.logger.info(f"Manual review records: {len(manual_review)}")
        
        # Save manual review queue
        if not manual_review.empty:
            self._save_manual_review_queue(manual_review)
        
        # Save filter log
        self._save_filter_log()
        
        return df, pd.DataFrame(self.filter_log)
    
    def _filter_max_elements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out records with more than MAX_ELEMENTS elements."""
        self.logger.info(f"Filtering records with >{self.max_elements} elements")
        
        # Identify element columns (common solder elements)
        element_cols = ['sn', 'pb', 'ag', 'cu', 'zn', 'bi', 'in', 'sb', 'ni', 'fe']
        element_cols = [col for col in element_cols if col in df.columns]
        
        if not element_cols:
            self.logger.warning("No element columns found in data")
            return df
        
        # Count non-null elements per record
        df['element_count'] = df[element_cols].notna().sum(axis=1)
        
        # Filter
        filtered = df[df['element_count'] <= self.max_elements].copy()
        dropped = df[df['element_count'] > self.max_elements]
        
        for _, row in dropped.iterrows():
            self.filter_log.append({
                'record_id': row.get('id', 'unknown'),
                'reason': 'EXCEEDS_MAX_ELEMENTS',
                'element_count': row['element_count'],
                'max_allowed': self.max_elements
            })
        
        self.logger.info(f"Dropped {len(dropped)} records exceeding max elements")
        return filtered
    
    def _standardize_hardness(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize hardness values to HV units."""
        self.logger.info("Standardizing hardness to HV units")
        
        # Check for existing hardness column
        hardness_cols = ['hardness_hv', 'hv', 'hardness', 'vickers_hardness']
        hardness_col = None
        
        for col in hardness_cols:
            if col in df.columns:
                hardness_col = col
                break
        
        if hardness_col is None:
            self.logger.warning("No hardness column found")
            return df
        
        # Ensure numeric
        df[hardness_col] = pd.to_numeric(df[hardness_col], errors='coerce')
        
        # If column is not named hardness_hv, rename it
        if hardness_col != 'hardness_hv':
            df['hardness_hv'] = df[hardness_col]
            df = df.drop(columns=[hardness_col])
        
        return df
    
    def _filter_temperature(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Filter for room-temperature measurements and flag manual review.
        
        Returns:
            Tuple of (filtered_data, manual_review_data)
        """
        self.logger.info(f"Filtering for room temperature (target: {self.room_temp_threshold}°C, tolerance: ±{self.room_temp_tolerance}°C)")
        
        if 'measurement_temp_c' not in df.columns:
            self.logger.warning("No measurement_temp_c column found - keeping all records")
            return df, pd.DataFrame()
        
        # Ensure numeric
        df['measurement_temp_c'] = pd.to_numeric(df['measurement_temp_c'], errors='coerce')
        
        # Calculate deviation
        df['temp_deviation'] = (df['measurement_temp_c'] - self.room_temp_threshold).abs()
        
        # Filter: keep within tolerance
        within_tolerance = df['temp_deviation'] <= self.room_temp_tolerance
        
        # Manual review: within 2x tolerance but outside normal tolerance
        manual_review_mask = (
            (df['temp_deviation'] > self.room_temp_tolerance) & 
            (df['temp_deviation'] <= 2 * self.room_temp_tolerance)
        )
        
        # Drop outside 2x tolerance
        outside_all = df['temp_deviation'] > 2 * self.room_temp_tolerance
        
        filtered = df[within_tolerance].copy()
        manual_review = df[manual_review_mask].copy()
        
        # Log dropped records
        for idx, row in df[outside_all].iterrows():
            self.filter_log.append({
                'record_id': row.get('id', 'unknown'),
                'reason': 'TEMP_OUTSIDE_RANGE',
                'temperature': row['measurement_temp_c'],
                'deviation': row['temp_deviation']
            })
        
        # Add manual review flag
        if not manual_review.empty:
            manual_review['manual_review_flag'] = 'MANUAL_REVIEW_TEMP'
            self.manual_review_records.extend(manual_review.to_dict('records'))
        
        self.logger.info(f"Temperature filter: {len(df)} -> {len(filtered)} records")
        self.logger.info(f"Manual review queue: {len(manual_review)} records")
        
        # Drop temporary columns
        if 'temp_deviation' in filtered.columns:
            filtered = filtered.drop(columns=['temp_deviation'])
        if 'temp_deviation' in manual_review.columns:
            manual_review = manual_review.drop(columns=['temp_deviation'])
        
        return filtered, manual_review
    
    def _validate_composition(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate that composition sums to >= threshold.
        
        Args:
            df: DataFrame with composition columns
        
        Returns:
            Filtered DataFrame
        """
        self.logger.info(f"Validating composition sums (threshold: {self.composition_sum_threshold})")
        
        # Identify element columns
        element_cols = ['sn', 'pb', 'ag', 'cu', 'zn', 'bi', 'in', 'sb', 'ni', 'fe']
        element_cols = [col for col in element_cols if col in df.columns]
        
        if not element_cols:
            self.logger.warning("No element columns found for composition validation")
            return df
        
        # Calculate sum
        df['composition_sum'] = df[element_cols].sum(axis=1)
        
        # Filter
        valid = df['composition_sum'] >= self.composition_sum_threshold
        
        invalid = df[~valid].copy()
        filtered = df[valid].copy()
        
        # Log invalid records
        for _, row in invalid.iterrows():
            self.filter_log.append({
                'record_id': row.get('id', 'unknown'),
                'reason': 'COMPOSITION_SUM_BELOW_THRESHOLD',
                'composition_sum': row['composition_sum'],
                'threshold': self.composition_sum_threshold
            })
        
        self.logger.info(f"Composition validation: {len(df)} -> {len(filtered)} records")
        
        # Drop temporary column
        if 'composition_sum' in filtered.columns:
            filtered = filtered.drop(columns=['composition_sum'])
        if 'composition_sum' in invalid.columns:
            invalid = invalid.drop(columns=['composition_sum'])
        
        return filtered
    
    def _save_manual_review_queue(self, manual_review: pd.DataFrame):
        """Save manual review records to CSV."""
        output_path = self.processed_dir / "manual_review_queue.csv"
        manual_review.to_csv(output_path, index=False)
        self.logger.info(f"Saved {len(manual_review)} records to {output_path}")
    
    def _save_filter_log(self):
        """Save filter log to CSV."""
        if not self.filter_log:
            return
        
        log_df = pd.DataFrame(self.filter_log)
        output_path = self.processed_dir / "validation_logs" / "filtered_records.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        log_df.to_csv(output_path, index=False)
        self.logger.info(f"Saved {len(log_df)} filtered records to {output_path}")
        
        # Generate checksum
        self._generate_checksum(output_path)
    
    def _generate_checksum(self, file_path: Path):
        """Generate SHA256 checksum for a file."""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        checksum = sha256_hash.hexdigest()
        
        # Append to checksums.txt
        checksum_file = self.processed_dir.parent / "checksums.txt"
        with open(checksum_file, 'a') as f:
            f.write(f"{file_path.name}: {checksum}\n")
        
        self.logger.info(f"Generated checksum for {file_path}: {checksum}")
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of filtering operations."""
        return {
            'total_filtered': len(self.filter_log),
            'manual_review_count': len(self.manual_review_records),
            'filter_reasons': {
                reason: sum(1 for log in self.filter_log if log['reason'] == reason)
                for reason in set(log['reason'] for log in self.filter_log)
            }
        }

def main():
    """Main entry point for the cleaner."""
    logger = get_logger("ingestion.cleaner")
    logger.info("Running DataCleaner main")
    
    try:
        # Load data from raw file
        raw_file = get_data_processed_dir() / "solder_hardness_raw.csv"
        
        if not raw_file.exists():
            # Try data/raw
            raw_file = Path("data/raw/solder_hardness_raw.csv")
        
        if not raw_file.exists():
            logger.error(f"Raw data file not found: {raw_file}")
            return pd.DataFrame(), pd.DataFrame()
        
        logger.info(f"Loading data from {raw_file}")
        df = pd.read_csv(raw_file)
        data = df.to_dict('records')
        
        # Clean data
        cleaner = DataCleaner()
        cleaned_df, filtered_df = cleaner.clean_data(data)
        
        logger.info(f"Cleaning complete: {len(cleaned_df)} valid records")
        
        return cleaned_df, filtered_df
        
    except Exception as e:
        logger.error(f"Error during cleaning: {str(e)}")
        raise

if __name__ == "__main__":
    main()

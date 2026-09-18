"""
Cleaner module for validating and standardizing solder hardness data.
Implements T013: Data cleaning and filtering logic.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import os
import hashlib
import json

# Import project utilities
try:
    from utils.logging_config import get_logger
    from utils.error_handlers import DataValidationError, CompositionSumError
    from config import (
        get_max_elements, 
        get_composition_sum_threshold,
        get_data_processed_dir,
        get_room_temp_threshold,
        get_room_temp_tolerance,
        get_min_n_for_power
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.logging_config import get_logger
    from utils.error_handlers import DataValidationError, CompositionSumError
    from config import (
        get_max_elements, 
        get_composition_sum_threshold,
        get_data_processed_dir,
        get_room_temp_threshold,
        get_room_temp_tolerance,
        get_min_n_for_power
    )


class DataCleaner:
    """
    Cleans and validates solder composition data.
    """

    def __init__(self):
        self.logger = get_logger("ingestion.cleaner")
        self.max_elements = get_max_elements()
        self.composition_threshold = get_composition_sum_threshold()
        self.room_temp_threshold = get_room_temp_threshold()
        self.room_temp_tolerance = get_room_temp_tolerance()
        self.min_n_for_power = get_min_n_for_power()
        self.filtered_records: List[Dict[str, Any]] = []
        self.review_records: List[Dict[str, Any]] = []

    def load_data(self, file_path: Path) -> pd.DataFrame:
        """Load raw data from CSV/JSON."""
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        if file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _identify_element_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Identify columns that represent elemental composition.
        Heuristic: columns starting with 'element_' or containing element symbols.
        """
        # Common element symbols (simplified)
        element_symbols = [
            'Sn', 'Pb', 'Ag', 'Cu', 'Bi', 'In', 'Zn', 'Sb', 'Au', 'Ni',
            'Al', 'Mg', 'Si', 'Fe', 'Co', 'Cr', 'Mn', 'Ti', 'V', 'W', 'Mo'
        ]
        
        element_cols = []
        for col in df.columns:
            # Check if column name starts with 'element_'
            if col.startswith('element_'):
                element_cols.append(col)
            # Check if column name matches an element symbol exactly or is part of it
            elif any(symbol in col for symbol in element_symbols):
                element_cols.append(col)
        
        return element_cols

    def filter_by_element_count(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Exclude alloys with more than MAX_ELEMENTS elements.
        Returns cleaned DataFrame and count of removed records.
        """
        initial_count = len(df)
        element_cols = self._identify_element_columns(df)
        
        if not element_cols:
            self.logger.warning("No elemental columns found. Skipping element count filter.")
            return df, 0
        
        # Count non-null/positive elemental entries per row
        df['element_count'] = (df[element_cols] > 0).sum(axis=1)
        
        # Filter
        mask = df['element_count'] <= self.max_elements
        filtered_df = df[mask].copy()
        removed_count = initial_count - len(filtered_df)
        
        self.logger.info(f"Filtered by element count (max={self.max_elements}): {removed_count} records removed.")
        
        # Drop temporary column
        if 'element_count' in filtered_df.columns:
            filtered_df = filtered_df.drop(columns=['element_count'])
        
        return filtered_df, removed_count

    def standardize_hardness(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize hardness to HV units.
        Uses conversion factors from config if available.
        """
        self.logger.info("Standardizing hardness to HV...")
        
        # Check if unit column exists
        unit_col = 'hardness_unit'
        if unit_col not in df.columns:
            # Assume all are already HV if no unit column
            self.logger.info("No hardness_unit column found. Assuming all values are in HV.")
            return df
        
        # Conversion factors (if not in config, use standard values)
        # 1 GPa = 10.197 HV
        # 1 kgf/mm² = 9.807 HV
        HV_PER_GPA = 10.197
        HV_PER_KGF_MM2 = 9.807
        
        df = df.copy()
        
        # Convert GPa to HV
        mask_gpa = df[unit_col].str.upper().str.contains('GPA', case=False, na=False)
        if mask_gpa.any():
            df.loc[mask_gpa, 'hardness_hv'] = df.loc[mask_gpa, 'hardness_hv'] * HV_PER_GPA
            self.logger.info(f"Converted {mask_gpa.sum()} records from GPa to HV.")
        
        # Convert kgf/mm² to HV
        mask_kgf = df[unit_col].str.upper().str.contains('KGF/MM', case=False, na=False)
        if mask_kgf.any():
            df.loc[mask_kgf, 'hardness_hv'] = df.loc[mask_kgf, 'hardness_hv'] * HV_PER_KGF_MM2
            self.logger.info(f"Converted {mask_kgf.sum()} records from kgf/mm² to HV.")
        
        # Handle other units - log warning
        other_units = ~df[unit_col].str.upper().str.contains('HV|GPA|KGF/MM', case=False, na=False)
        if other_units.any():
            self.logger.warning(f"Found {other_units.sum()} records with unknown hardness units: {df.loc[other_units, unit_col].unique()}")
        
        return df

    def filter_temperature(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Filter for room-temperature measurements.
        Returns (valid_df, manual_review_df).
        """
        self.logger.info(f"Filtering by temperature (target={self.room_temp_threshold}C, tolerance={self.room_temp_tolerance}C)...")
        
        if 'measurement_temp_c' not in df.columns:
            self.logger.warning("No measurement_temp_c column found. Assuming all records are at room temperature.")
            return df, pd.DataFrame()
        
        df = df.copy()
        temp_col = 'measurement_temp_c'
        
        # Calculate absolute difference from room temperature
        df['temp_diff'] = (df[temp_col] - self.room_temp_threshold).abs()
        
        # Valid: within tolerance
        valid_mask = df['temp_diff'] <= self.room_temp_tolerance
        valid_df = df[valid_mask].copy()
        
        # Manual review: outside tolerance but within 2x tolerance
        review_mask = (df['temp_diff'] > self.room_temp_tolerance) & (df['temp_diff'] <= 2 * self.room_temp_tolerance)
        review_df = df[review_mask].copy()
        
        # Outliers: beyond 2x tolerance (excluded)
        # We log them but do not include in valid or review
        outlier_count = (~valid_mask & ~review_mask).sum()
        if outlier_count > 0:
            self.logger.info(f"Excluded {outlier_count} records with temperature outside {2 * self.room_temp_tolerance}C of room temp.")
        
        self.logger.info(f"Temperature filter: {len(valid_df)} valid, {len(review_df)} for manual review.")
        
        # Drop temporary columns
        for col in ['temp_diff']:
            if col in valid_df.columns:
                valid_df = valid_df.drop(columns=[col])
            if col in review_df.columns:
                review_df = review_df.drop(columns=[col])
        
        return valid_df, review_df

    def validate_composition_sum(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Validate that elemental composition sums to >= COMPOSITION_SUM_THRESHOLD.
        Returns (valid_df, invalid_df).
        """
        self.logger.info(f"Validating composition sums (threshold={self.composition_threshold}%)...")
        
        element_cols = self._identify_element_columns(df)
        
        if not element_cols:
            self.logger.warning("No elemental columns found. Skipping composition sum validation.")
            return df, pd.DataFrame()
        
        # Calculate sum of elemental percentages
        df['composition_sum'] = df[element_cols].sum(axis=1)
        
        # Valid: sum >= threshold
        valid_mask = df['composition_sum'] >= self.composition_threshold
        valid_df = df[valid_mask].copy()
        
        # Invalid: sum < threshold
        invalid_df = df[~valid_mask].copy()
        
        # Log invalid records
        if not invalid_df.empty:
            self.logger.warning(f"Excluded {len(invalid_df)} records with composition sum < {self.composition_threshold}%.")
            self.filtered_records = invalid_df.to_dict(orient='records')
        
        self.logger.info(f"Composition sum validation: {len(valid_df)} valid, {len(invalid_df)} excluded.")
        
        # Drop temporary column
        if 'composition_sum' in valid_df.columns:
            valid_df = valid_df.drop(columns=['composition_sum'])
        
        return valid_df, invalid_df

    def clean(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """
        Run full cleaning pipeline.
        Returns status dictionary for downstream tasks.
        """
        self.logger.info(f"Cleaning data from {input_path}...")
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df = self.load_data(input_path)
        initial_n = len(df)
        self.logger.info(f"Loaded {initial_n} records from {input_path}")
        
        # Apply filters
        df, removed_by_elements = self.filter_by_element_count(df)
        df = self.standardize_hardness(df)
        
        valid_df, review_df = self.filter_temperature(df)
        valid_df, invalid_df = self.validate_composition_sum(valid_df)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save cleaned data
        valid_df.to_csv(output_path, index=False)
        self.logger.info(f"Cleaned data saved to {output_path} ({len(valid_df)} records)")
        
        # Save manual review queue
        review_path = get_data_processed_dir() / "manual_review_queue.csv"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        if not review_df.empty:
            review_df.to_csv(review_path, index=False)
            self.logger.info(f"Manual review queue saved to {review_path} ({len(review_df)} records)")
        
        # Save filtered records log
        filtered_logs_dir = get_data_processed_dir() / "validation_logs"
        filtered_logs_dir.mkdir(parents=True, exist_ok=True)
        filtered_log_path = filtered_logs_dir / "filtered_records.csv"
        
        if not invalid_df.empty:
            # Add reason code
            invalid_df_with_reason = invalid_df.copy()
            invalid_df_with_reason['filter_reason'] = 'COMPOSITION_SUM_LOW'
            invalid_df_with_reason.to_csv(filtered_log_path, index=False)
            self.logger.info(f"Filtered records log saved to {filtered_log_path}")
        
        # Calculate final N
        final_n = len(valid_df)
        
        # Determine power limitation status
        power_limitation_warning = None
        if final_n < self.min_n_for_power:
            power_limitation_warning = 'N < 50'
            self.logger.warning(f"CRITICAL: Final N ({final_n}) is below minimum for power ({self.min_n_for_power}).")
        elif final_n < 100:
            self.logger.warning(f"WARNING: Final N ({final_n}) is below target (100). Statistical power may be limited.")
        
        # Prepare status dictionary
        status = {
            'initial_n': initial_n,
            'final_n': final_n,
            'removed_by_element_count': removed_by_elements,
            'removed_by_temperature': initial_n - len(valid_df) - removed_by_elements - len(invalid_df), # Approximate
            'removed_by_composition_sum': len(invalid_df),
            'manual_review_count': len(review_df),
            'power_limitation_warning': power_limitation_warning,
            'threshold_status': 'N>=100' if final_n >= 100 else ('50<=N<100' if final_n >= 50 else 'N<50')
        }
        
        return status

    def save_filtered_logs(self, output_dir: Path) -> None:
        """Save logs of filtered records."""
        if not self.filtered_records:
            self.logger.info("No filtered records to save.")
            return
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        log_path = output_dir / "filtered_records.json"
        with open(log_path, 'w') as f:
            json.dump(self.filtered_records, f, indent=2)
        
        self.logger.info(f"Filtered records log saved to {log_path}")


def main():
    """
    Entry point for the cleaner script.
    Reads from raw data, cleans, and writes to processed.
    """
    logger = get_logger("ingestion.cleaner.main")
    logger.info("Starting cleaner pipeline...")
    
    cleaner = DataCleaner()
    
    # Determine input file - look for raw data from T012g
    data_processed_dir = get_data_processed_dir()
    data_raw_dir = Path(data_processed_dir).parent / "raw"
    
    # Try to find the latest raw file
    raw_files = list(data_raw_dir.glob("*.csv")) + list(data_raw_dir.glob("*.json"))
    if not raw_files:
        # Fallback: check processed for any existing raw-like file
        raw_files = list(data_processed_dir.glob("raw_*.csv")) + list(data_processed_dir.glob("raw_*.json"))
    
    if not raw_files:
        logger.error("No raw data files found. Cannot proceed with cleaning.")
        return
    
    # Sort by modification time and take the latest
    raw_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    input_file = raw_files[0]
    
    output_file = data_processed_dir / "solder_hardness_cleaned.csv"
    
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    
    try:
        status = cleaner.clean(input_file, output_file)
        
        # Write status to ingestion_status.json
        status_file = data_processed_dir / ".ingestion_status.json"
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        logger.info(f"Cleaning completed successfully. Status saved to {status_file}")
        
    except Exception as e:
        logger.error(f"Cleaning failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
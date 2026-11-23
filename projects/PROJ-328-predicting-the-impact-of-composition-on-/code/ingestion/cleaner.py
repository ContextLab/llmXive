import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import os
import hashlib
import json
import sys

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import (
    get_max_elements,
    get_room_temp_threshold,
    get_room_temp_tolerance,
    get_composition_sum_threshold,
    get_data_raw_dir,
    get_data_processed_dir
)
from utils.logging_config import get_logger
from ingestion.logger_setup import setup_ingestion_logging

logger = get_logger(__name__)

class DataCleaner:
    """
    Handles cleaning, filtering, and validation of solder hardness data.
    Implements T013 requirements:
    - Exclude alloys with >5 elements
    - Standardize hardness to HV
    - Filter for room-temperature measurements
    - Flag manual review candidates
    - Validate elemental composition sums
    - Handle N < 50 scenarios
    """

    def __init__(self, config=None):
        self.max_elements = get_max_elements()
        self.room_temp_threshold = get_room_temp_threshold()
        self.room_temp_tolerance = get_room_temp_tolerance()
        self.composition_sum_threshold = get_composition_sum_threshold()
        self.processed_dir = get_data_processed_dir()
        
        # Ensure output directory exists
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_raw_data(self) -> pd.DataFrame:
        """
        Loads all raw data files from data/raw/ and concatenates them.
        Expects files: raw_mp.json, raw_lit.csv, raw_openalloy.json, raw_slr.csv
        """
        raw_dir = get_data_raw_dir()
        if not raw_dir.exists():
            raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
        
        dfs = []
        files_processed = []
        
        # Check for specific expected raw files based on T012g
        expected_patterns = [
            (raw_dir / "raw_mp.json", "json"),
            (raw_dir / "raw_openalloy.json", "json"),
            (raw_dir / "raw_lit.csv", "csv"),
            (raw_dir / "raw_slr.csv", "csv")
        ]
        
        for file_path, file_type in expected_patterns:
            if file_path.exists():
                logger.info(f"Loading raw data from {file_path.name}")
                if file_type == "json":
                    df = pd.read_json(file_path)
                else:
                    df = pd.read_csv(file_path)
                
                # Ensure 'source' column exists to track origin
                if 'source' not in df.columns:
                    df['source'] = file_path.stem
                
                dfs.append(df)
                files_processed.append(file_path.name)
            else:
                logger.warning(f"Expected raw file not found: {file_path.name}")
        
        if not dfs:
            raise RuntimeError("No raw data files found in data/raw/. Ingestion (T012g) must run first.")
        
        combined_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Loaded {len(combined_df)} total records from {len(files_processed)} files")
        return combined_df

    def filter_max_elements(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Excludes alloys with more than MAX_ELEMENTS (5) components.
        Returns cleaned DF and excluded DF.
        """
        # Identify element columns (assuming they start with element names or are specific columns)
        # We need to dynamically identify composition columns.
        # Common pattern: columns like 'Sn', 'Ag', 'Cu', 'Sb', etc. or a generic 'composition' dict.
        # Based on T007 entities, we expect 'elemental_breakdown' or flattened columns.
        
        # Strategy: Check if 'elemental_breakdown' exists (dict-like). If so, count keys.
        # If flattened (e.g., 'Sn_pct', 'Ag_pct'), count non-null percentage columns.
        
        excluded_rows = []
        kept_rows = []
        
        if 'elemental_breakdown' in df.columns:
            # Handle nested dict structure
            def count_elements(row):
                breakdown = row.get('elemental_breakdown', {})
                if isinstance(breakdown, str):
                    try:
                        breakdown = json.loads(breakdown)
                    except:
                        return 0
                return len([k for k, v in breakdown.items() if v > 0])
            
            df['element_count'] = df.apply(count_elements, axis=1)
            mask = df['element_count'] <= self.max_elements
        else:
            # Handle flattened columns: look for columns ending in _pct, _wt, or common element symbols
            # Heuristic: Columns that look like element symbols (uppercase followed by optional lowercase)
            import re
            element_cols = [col for col in df.columns if re.match(r'^[A-Z][a-z]?', col) and ('%' in col or col.endswith('_pct') or col.endswith('_wt'))]
            
            if not element_cols:
                # Fallback: assume all numeric columns except known metadata are elements
                numeric_cols = df.select_dtypes(include=['number']).columns
                exclude_cols = ['hardness_hv', 'measurement_temp_c', 'element_count']
                element_cols = [c for c in numeric_cols if c not in exclude_cols]
            
            def count_elements_row(row):
                return sum(1 for col in element_cols if pd.notna(row[col]) and row[col] > 0)
            
            df['element_count'] = df.apply(count_elements_row, axis=1)
            mask = df['element_count'] <= self.max_elements

        kept_df = df[mask].copy()
        excluded_df = df[~mask].copy()
        
        logger.info(f"Filtered elements: kept {len(kept_df)}, excluded {len(excluded_df)} (> {self.max_elements} elements)")
        return kept_df, excluded_df

    def standardize_hardness(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardizes hardness to HV units.
        Assumes data might have gpa or other units, but spec says 'hardness_hv'.
        If other units exist, convert them. For now, ensure column exists and is numeric.
        """
        if 'hardness_hv' not in df.columns:
            # Try to find alternative columns
            alt_cols = [c for c in df.columns if 'hardness' in c.lower()]
            if alt_cols:
                logger.warning(f"Column 'hardness_hv' not found. Using {alt_cols[0]}")
                df['hardness_hv'] = df[alt_cols[0]]
            else:
                raise KeyError("No hardness column found in dataset")
        
        df['hardness_hv'] = pd.to_numeric(df['hardness_hv'], errors='coerce')
        return df

    def filter_temperature(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Filters for room-temperature measurements.
        Returns: (kept_df, manual_review_df, excluded_df)
        """
        temp_col = 'measurement_temp_c'
        
        if temp_col not in df.columns:
            logger.warning(f"Column '{temp_col}' not found. Assuming all are room temp.")
            df[temp_col] = self.room_temp_threshold
        
        df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
        
        # Define thresholds
        lower_bound = self.room_temp_threshold - self.room_temp_tolerance
        upper_bound = self.room_temp_threshold + self.room_temp_tolerance
        manual_review_lower = self.room_temp_threshold - (2 * self.room_temp_tolerance)
        manual_review_upper = self.room_temp_threshold + (2 * self.room_temp_tolerance)
        
        # Keep if within tolerance
        mask_keep = (df[temp_col] >= lower_bound) & (df[temp_col] <= upper_bound)
        kept_df = df[mask_keep].copy()
        
        # Manual review if within 2x tolerance but outside 1x
        mask_review = ~mask_keep & (
            (df[temp_col] >= manual_review_lower) & (df[temp_col] <= manual_review_upper)
        )
        manual_review_df = df[mask_review].copy()
        
        # Exclude if outside 2x tolerance
        mask_exclude = ~mask_keep & ~mask_review
        excluded_df = df[mask_exclude].copy()
        
        logger.info(f"Temperature filter: kept {len(kept_df)}, manual review {len(manual_review_df)}, excluded {len(excluded_df)}")
        
        return kept_df, manual_review_df, excluded_df

    def validate_composition_sum(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Validates that elemental composition sums to >= COMPOSITION_SUM_THRESHOLD.
        Returns: (kept_df, excluded_df)
        """
        # Identify element columns again
        import re
        element_cols = [col for col in df.columns if re.match(r'^[A-Z][a-z]?', col) and ('%' in col or col.endswith('_pct') or col.endswith('_wt'))]
        
        if not element_cols:
            # Fallback: numeric columns excluding metadata
            numeric_cols = df.select_dtypes(include=['number']).columns
            exclude_cols = ['hardness_hv', 'measurement_temp_c', 'element_count', 'composition_sum']
            element_cols = [c for c in numeric_cols if c not in exclude_cols]
        
        # Calculate sum
        df['composition_sum'] = df[element_cols].sum(axis=1)
        
        # Filter
        mask_valid = df['composition_sum'] >= self.composition_sum_threshold
        kept_df = df[mask_valid].copy()
        excluded_df = df[~mask_valid].copy()
        
        # Add reason code to excluded
        excluded_df['exclusion_reason'] = 'COMPOSITION_SUM_LOW'
        
        logger.info(f"Composition sum filter: kept {len(kept_df)}, excluded {len(excluded_df)} (< {self.composition_sum_threshold}%)")
        
        return kept_df, excluded_df

    def run_cleaning_pipeline(self) -> pd.DataFrame:
        """
        Executes the full cleaning pipeline.
        """
        logger.info("Starting data cleaning pipeline (T013)...")
        
        # 1. Load Raw
        df = self.load_raw_data()
        initial_count = len(df)
        
        # 2. Filter Max Elements
        df, excluded_elements = self.filter_max_elements(df)
        
        # 3. Standardize Hardness
        df = self.standardize_hardness(df)
        df = df.dropna(subset=['hardness_hv']) # Drop rows with no hardness
        
        # 4. Filter Temperature
        df, manual_review, excluded_temp = self.filter_temperature(df)
        
        # 5. Validate Composition Sum
        df, excluded_comp = self.validate_composition_sum(df)
        
        # 6. Final Count Check
        final_count = len(df)
        
        # 7. Write Outputs
        cleaned_path = self.processed_dir / "solder_hardness_cleaned.csv"
        df.to_csv(cleaned_path, index=False)
        logger.info(f"Wrote cleaned data to {cleaned_path} ({final_count} rows)")
        
        # Write manual review queue
        if not manual_review.empty:
            manual_path = self.processed_dir / "manual_review_queue.csv"
            manual_review.to_csv(manual_path, index=False)
            logger.info(f"Wrote manual review queue to {manual_path} ({len(manual_review)} rows)")
        
        # Write excluded records log
        all_excluded = pd.concat([
            excluded_elements.assign(exclusion_reason='TOO_MANY_ELEMENTS'),
            excluded_temp.assign(exclusion_reason='TEMP_OUT_OF_RANGE'),
            excluded_comp
        ], ignore_index=True)
        
        if not all_excluded.empty:
            excluded_path = self.processed_dir / "excluded_records.csv"
            all_excluded.to_csv(excluded_path, index=False)
            logger.info(f"Wrote excluded records to {excluded_path} ({len(all_excluded)} rows)")
        
        # 8. Handle N < 50 Warning
        status = {
            "exact_N": final_count,
            "initial_N": initial_count,
            "excluded_count": len(all_excluded),
            "threshold_status": "N>=100" if final_count >= 100 else ("50<=N<100" if final_count >= 50 else "N<50")
        }
        
        if final_count < 50:
            status["power_limitation_warning"] = "N < 50"
            logger.warning(f"CRITICAL: Final N ({final_count}) is less than 50. Power limitation warning set.")
        elif final_count < 100:
            status["power_limitation_warning"] = "50 <= N < 100 (Reduced Power)"
            logger.warning(f"WARNING: Final N ({final_count}) is between 50 and 100. Reduced power warning set.")
        
        status_path = self.processed_dir / ".ingestion_status.json"
        with open(status_path, 'w') as f:
            json.dump(status, f, indent=2)
        
        logger.info(f"Wrote ingestion status to {status_path}")
        
        return df

def main():
    """
    Entry point for T013 execution.
    """
    setup_ingestion_logging()
    logger.info("Executing T013: Data Cleaning and Filtering")
    
    cleaner = DataCleaner()
    try:
        cleaner.run_cleaning_pipeline()
        logger.info("T013 completed successfully.")
    except Exception as e:
        logger.error(f"T013 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Data Cleaner for Solder Hardness Dataset.

Implements cleaning and filtering logic:
- Exclude alloys with >5 elements
- Standardize hardness to HV units
- Filter for room-temperature measurements
- Validate elemental composition sums
- Flag records for manual review
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import os
import hashlib
import json

from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError
from config import (
    get_max_elements,
    get_composition_sum_threshold,
    get_config
)

logger = get_logger(__name__)

# Conversion factors
GPA_TO_HV = 10.197
KGF_MM2_TO_HV = 9.807

class DataCleaner:
    """Cleans and validates solder hardness data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the cleaner.
        
        Args:
            config: Configuration dictionary. If None, uses defaults from config.py.
        """
        self.config = config or get_config()
        self.max_elements = self.config.get("MAX_ELEMENTS", get_max_elements())
        self.composition_threshold = self.config.get(
            "COMPOSITION_SUM_THRESHOLD", 
            get_composition_sum_threshold()
        )
        self.room_temp_target = self.config.get("ROOM_TEMP_THRESHOLD_C", 25.0)
        self.room_temp_tolerance = self.config.get("ROOM_TEMP_TOLERANCE_C", 5.0)
        
        self.clean_data: Optional[pd.DataFrame] = None
        self.filtered_records: List[Dict[str, Any]] = []
        self.manual_review_records: List[Dict[str, Any]] = []
    
    def load_raw_data(self, input_path: str) -> pd.DataFrame:
        """
        Load raw data from CSV.
        
        Args:
            input_path: Path to the raw data CSV file.
        
        Returns:
            Loaded DataFrame.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Raw data file not found: {input_path}")
        
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
        return df
    
    def filter_by_element_count(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Filter out alloys with more than MAX_ELEMENTS.
        
        Args:
            df: Input DataFrame.
        
        Returns:
            Tuple of (filtered DataFrame, list of filtered records).
        """
        filtered = []
        kept = []
        
        for idx, row in df.iterrows():
            # Parse composition column if it exists
            composition_str = row.get('composition', '{}')
            try:
                composition = json.loads(composition_str) if isinstance(composition_str, str) else composition_str
                element_count = len([k for k, v in composition.items() if v and v > 0])
            except (json.JSONDecodeError, TypeError):
                # Try to count non-null columns that look like elements
                element_count = sum(1 for col in df.columns if col.upper() in ['SN', 'PB', 'SB', 'AG', 'CU', 'ZN', 'IN'] and pd.notna(row.get(col)))
            
            if element_count > self.max_elements:
                filtered.append({
                    'index': idx,
                    'reason': f"Too many elements ({element_count} > {self.max_elements})",
                    'data': row.to_dict()
                })
            else:
                kept.append(idx)
        
        result_df = df.loc[kept].reset_index(drop=True)
        logger.info(f"Filtered {len(filtered)} records with too many elements. Kept {len(result_df)}")
        return result_df, filtered
    
    def standardize_hardness(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize all hardness values to HV units.
        
        Args:
            df: Input DataFrame.
        
        Returns:
            DataFrame with standardized hardness in HV.
        """
        df = df.copy()
        
        # Identify hardness columns
        hardness_cols = [col for col in df.columns if 'hardness' in col.lower() or 'hv' in col.lower()]
        
        if not hardness_cols:
            logger.warning("No hardness column found in data")
            return df
        
        hardness_col = hardness_cols[0]
        unit_col = None
        
        # Find unit column
        for col in df.columns:
            if 'unit' in col.lower() and 'hardness' in col.lower():
                unit_col = col
                break
        
        # If no unit column, assume all are already in HV
        if unit_col is None:
            logger.info("No unit column found, assuming all hardness values are in HV")
            return df
        
        # Convert units
        def convert_hardness(row):
            value = row[hardness_col]
            if pd.isna(value):
                return value
            
            unit = str(row[unit_col]).lower() if unit_col else 'hv'
            
            if 'gpa' in unit:
                return value * GPA_TO_HV
            elif 'kgf/mm' in unit or 'kgf/mm2' in unit:
                return value * KGF_MM2_TO_HV
            elif 'hv' in unit or 'vickers' in unit:
                return value
            else:
                logger.warning(f"Unknown hardness unit: {unit} for value {value}")
                return value
        
        df[hardness_col] = df.apply(convert_hardness, axis=1)
        df[unit_col] = 'HV'  # Standardize unit column
        
        logger.info(f"Standardized hardness values to HV")
        return df
    
    def filter_room_temperature(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Filter for room-temperature measurements and flag borderline cases.
        
        Args:
            df: Input DataFrame.
        
        Returns:
            Tuple of (filtered DataFrame, list of manual review records).
        """
        df = df.copy()
        filtered = []
        manual_review = []
        
        # Find temperature column
        temp_cols = [col for col in df.columns if 'temp' in col.lower() and 'c' in col.lower()]
        if not temp_cols:
            logger.warning("No temperature column found, keeping all records")
            return df, []
        
        temp_col = temp_cols[0]
        
        for idx, row in df.iterrows():
            temp = row.get(temp_col)
            
            if pd.isna(temp):
                # No temperature info - keep but flag
                manual_review.append({
                    'index': idx,
                    'reason': 'Missing temperature data',
                    'data': row.to_dict()
                })
                continue
            
            temp_diff = abs(temp - self.room_temp_target)
            
            if temp_diff <= self.room_temp_tolerance:
                # Within tolerance - keep
                continue
            elif temp_diff <= 2 * self.room_temp_tolerance:
                # Borderline - flag for manual review but keep
                manual_review.append({
                    'index': idx,
                    'reason': f'Temperature {temp}°C is borderline (diff: {temp_diff:.1f}°C)',
                    'data': row.to_dict()
                })
                continue
            else:
                # Outside tolerance - filter out
                filtered.append({
                    'index': idx,
                    'reason': f'Temperature {temp}°C outside tolerance (diff: {temp_diff:.1f}°C)',
                    'data': row.to_dict()
                })
        
        # Keep records that weren't filtered out
        filtered_indices = [f['index'] for f in filtered]
        result_df = df.drop(index=filtered_indices).reset_index(drop=True)
        
        self.manual_review_records = manual_review
        logger.info(f"Filtered {len(filtered)} non-room-temp records. Flagged {len(manual_review)} for review")
        return result_df, manual_review
    
    def validate_composition_sum(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Validate that elemental compositions sum to >= threshold.
        
        Args:
            df: Input DataFrame.
        
        Returns:
            Tuple of (filtered DataFrame, list of invalid records).
        """
        filtered = []
        kept = []
        
        # Identify composition columns (likely element columns)
        element_cols = [col for col in df.columns if col.upper() in ['SN', 'PB', 'SB', 'AG', 'CU', 'ZN', 'IN', 'BI', 'NI', 'MN']]
        
        if not element_cols:
            # Try to parse from composition JSON column
            if 'composition' in df.columns:
                for idx, row in df.iterrows():
                    try:
                        comp = json.loads(row['composition']) if isinstance(row['composition'], str) else row['composition']
                        total = sum(comp.values()) if comp else 0
                        if total < self.composition_threshold:
                            filtered.append({
                                'index': idx,
                                'reason': f'Composition sum {total:.2f}% < {self.composition_threshold}%',
                                'data': row.to_dict()
                            })
                        else:
                            kept.append(idx)
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        filtered.append({
                            'index': idx,
                            'reason': 'Invalid composition format',
                            'data': row.to_dict()
                        })
            else:
                logger.warning("No composition columns found, keeping all records")
                kept = list(df.index)
        else:
            # Sum element columns
            for idx, row in df.iterrows():
                total = sum(row[col] for col in element_cols if pd.notna(row[col]))
                if total < self.composition_threshold:
                    filtered.append({
                        'index': idx,
                        'reason': f'Composition sum {total:.2f}% < {self.composition_threshold}%',
                        'data': row.to_dict()
                    })
                else:
                    kept.append(idx)
        
        result_df = df.loc[kept].reset_index(drop=True)
        logger.info(f"Filtered {len(filtered)} records with invalid composition sums. Kept {len(result_df)}")
        return result_df, filtered
    
    def clean(self, input_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
        """
        Run full cleaning pipeline.
        
        Args:
            input_path: Path to raw data.
            output_path: Path to save cleaned data.
        
        Returns:
            Cleaned DataFrame.
        """
        logger.info("Starting data cleaning pipeline")
        
        # Load data
        df = self.load_raw_data(input_path)
        
        # Step 1: Filter by element count
        df, filtered_elements = self.filter_by_element_count(df)
        self.filtered_records.extend(filtered_elements)
        
        # Step 2: Standardize hardness
        df = self.standardize_hardness(df)
        
        # Step 3: Filter room temperature
        df, manual_review = self.filter_room_temperature(df)
        
        # Step 4: Validate composition sum
        df, filtered_composition = self.validate_composition_sum(df)
        self.filtered_records.extend(filtered_composition)
        
        # Save filtered records
        self._save_filtered_records()
        self._save_manual_review_queue()
        
        # Save cleaned data
        if output_path is None:
            project_root = Path(__file__).parent.parent.parent
            output_path = project_root / "data" / "processed" / "solder_hardness_cleaned.csv"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path} ({len(df)} records)")
        
        self.clean_data = df
        return df
    
    def _save_filtered_records(self):
        """Save filtered records to validation logs."""
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "data" / "processed" / "validation_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        filtered_path = log_dir / "filtered_records.csv"
        
        if self.filtered_records:
            df_filtered = pd.DataFrame(self.filtered_records)
            df_filtered.to_csv(filtered_path, index=False)
            
            # Generate checksum
            with open(filtered_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            
            checksum_path = project_root / "data" / "checksums.txt"
            with open(checksum_path, 'a') as f:
                f.write(f"filtered_records.csv: {checksum}\n")
            
            logger.info(f"Saved {len(self.filtered_records)} filtered records with checksum")
    
    def _save_manual_review_queue(self):
        """Save manual review queue."""
        project_root = Path(__file__).parent.parent.parent
        review_path = project_root / "data" / "processed" / "manual_review_queue.csv"
        
        if self.manual_review_records:
            df_review = pd.DataFrame(self.manual_review_records)
            df_review.to_csv(review_path, index=False)
            logger.info(f"Saved {len(self.manual_review_records)} records to manual review queue")

def main():
    """Main entry point for the cleaner."""
    logger = get_logger(__name__)
    logger.info("Starting Data Cleaner")
    
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "raw" / "solder_hardness_raw.csv"
    output_path = project_root / "data" / "processed" / "solder_hardness_cleaned.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return None
    
    cleaner = DataCleaner()
    cleaned_df = cleaner.clean(str(input_path), str(output_path))
    
    if cleaned_df is not None:
        logger.info(f"Cleaning complete. Output: {output_path}")
        return cleaned_df
    else:
        logger.error("Cleaning failed")
        return None

if __name__ == "__main__":
    main()

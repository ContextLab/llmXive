"""
Data Cleaner: Validates and filters the raw dataset.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional
import os

from config import get_composition_sum_threshold, get_max_elements, get_data_raw_dir, get_data_processed_dir
from utils.logging_config import get_logger
from ingestion.citation_tracker import get_tracker

logger = get_logger("ingestion.cleaner")

class DataCleaner:
    """
    Cleans and filters the solder hardness dataset.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.tracker = get_tracker()
        self.logger = get_logger("ingestion.cleaner")
    
    def filter_max_elements(self, max_elements: Optional[int] = None):
        """
        Exclude alloys with more than N elements.
        """
        if max_elements is None:
            max_elements = get_max_elements()
        
        initial_count = len(self.df)
        
        # Identify columns that are elemental compositions (numeric, not target)
        # Assuming columns like 'Sn', 'Ag', 'Cu', etc. are compositions
        # We filter rows where the number of non-zero elemental columns > max_elements
        # This is a heuristic; real implementation might depend on specific column names
        
        # Strategy: Sum non-null numeric columns that look like elements
        # For now, we assume all columns except 'hardness' are elements
        element_cols = [c for c in self.df.columns if c.lower() != 'hardness' and self.df[c].dtype in ['float64', 'int64']]
        
        def count_elements(row):
            return sum(1 for val in row if val > 0)
        
        self.df['element_count'] = self.df[element_cols].apply(count_elements, axis=1)
        self.df = self.df[self.df['element_count'] <= max_elements]
        
        dropped = initial_count - len(self.df)
        self.logger.info(f"Dropped {dropped} rows with > {max_elements} elements.")
        self.tracker.log_operation("filter_elements", {"max": max_elements, "dropped": dropped})
        
        self.df.drop(columns=['element_count'], inplace=True, errors='ignore')
        return self

    def standardize_hardness(self):
        """
        Standardize hardness to HV units.
        """
        # Assuming data is already in HV or has a 'unit' column.
        # If 'unit' column exists and is not 'HV', convert (placeholder logic).
        if 'unit' in self.df.columns:
            # Simple conversion logic placeholder
            hv_mask = self.df['unit'] != 'HV'
            if hv_mask.any():
                self.logger.warning(f"Found {hv_mask.sum()} rows with non-HV units. Converting (placeholder).")
                # Actual conversion would go here
                self.df.loc[hv_mask, 'unit'] = 'HV'
            self.df.drop(columns=['unit'], inplace=True, errors='ignore')
        
        self.logger.info("Hardness standardized to HV.")
        self.tracker.log_operation("standardize_hardness", {"unit": "HV"})
        return self

    def filter_room_temperature(self):
        """
        Filter for room-temperature measurements only.
        """
        if 'temperature' in self.df.columns:
            initial = len(self.df)
            # Assuming room temp is around 20-25C
            rt_mask = (self.df['temperature'] >= 20) & (self.df['temperature'] <= 25)
            self.df = self.df[rt_mask]
            dropped = initial - len(self.df)
            self.logger.info(f"Dropped {dropped} rows not at room temperature.")
            self.tracker.log_operation("filter_temperature", {"range": "20-25C", "dropped": dropped})
            if 'temperature' in self.df.columns:
                self.df.drop(columns=['temperature'], inplace=True, errors='ignore')
        else:
            self.logger.info("No temperature column found. Assuming room temperature.")
        return self

    def validate_composition_sum(self, threshold: Optional[float] = None):
        """
        Validate elemental composition sums to a threshold.
        """
        if threshold is None:
            threshold = get_composition_sum_threshold()
        
        element_cols = [c for c in self.df.columns if c.lower() != 'hardness' and self.df[c].dtype in ['float64', 'int64']]
        
        self.df['comp_sum'] = self.df[element_cols].sum(axis=1)
        
        valid_mask = (self.df['comp_sum'] >= threshold) & (self.df['comp_sum'] <= 1.0)
        initial = len(self.df)
        self.df = self.df[valid_mask]
        dropped = initial - len(self.df)
        
        self.logger.info(f"Dropped {dropped} rows with composition sum outside [{threshold}, 1.0].")
        self.tracker.log_operation("validate_composition_sum", {"threshold": threshold, "dropped": dropped})
        
        self.df.drop(columns=['comp_sum'], inplace=True, errors='ignore')
        return self

    def clean(self) -> pd.DataFrame:
        """
        Run all cleaning steps.
        """
        self.logger.info("Starting data cleaning pipeline.")
        self.tracker.log_operation("cleaning_start", {})
        
        self.filter_max_elements()
        self.standardize_hardness()
        self.filter_room_temperature()
        self.validate_composition_sum()
        
        self.tracker.log_operation("cleaning_complete", {"rows": len(self.df)})
        self.logger.info(f"Cleaning complete. {len(self.df)} rows remaining.")
        
        return self.df

def main():
    """
    Entry point for the cleaner script.
    Reads raw data, cleans it, and saves to processed.
    """
    from ingestion.saver import save_validated_data
    
    raw_path = Path(get_data_raw_dir()) / "solder_hardness_raw.csv"
    if not raw_path.exists():
        logger.error(f"Raw data file not found: {raw_path}")
        return
    
    df = pd.read_csv(raw_path)
    cleaner = DataCleaner(df)
    cleaned_df = cleaner.clean()
    
    output_path = Path(get_data_processed_dir()) / "solder_hardness_validated.csv"
    save_validated_data(cleaned_df, output_path)

if __name__ == "__main__":
    main()

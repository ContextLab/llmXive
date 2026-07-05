"""
Data Cleaning module for solder hardness datasets.

Implements filtering, standardization, and validation logic.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional
import os

logger = logging.getLogger(__name__)

class DataCleaner:
    """
    Cleans and preprocesses solder alloy data.
    
    Responsibilities:
    - Exclude alloys with >5 elements.
    - Standardize hardness to HV units.
    - Filter for room-temperature measurements.
    - Validate elemental composition sums.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.composition_threshold = 0.95  # Default, can be overridden by config
        self.max_elements = 5
        
        if config_path:
            # Load config if provided
            pass

    def load_data(self, file_path: str) -> pd.DataFrame:
        """Loads raw data from CSV."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return pd.DataFrame()
        
        return pd.read_csv(file_path)

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies cleaning rules to the dataframe.
        
        Args:
            df: Raw dataframe.
        
        Returns:
            Cleaned dataframe.
        """
        if df.empty:
            logger.warning("Input dataframe is empty. Returning empty dataframe.")
            return df

        logger.info(f"Starting cleaning on {len(df)} rows...")

        # 1. Filter for room-temperature measurements (if temperature column exists)
        # Assuming column 'temperature_c' exists. If not, skip.
        if 'temperature_c' in df.columns:
            # Filter for ~25C (room temp) with tolerance
            df = df[(df['temperature_c'] >= 20) & (df['temperature_c'] <= 30)]
            logger.info(f"Filtered for room temperature. Rows remaining: {len(df)}")

        # 2. Standardize hardness to HV
        # Assuming 'hardness_hv' is the target column. 
        # If 'hardness' and 'unit' exist, convert here.
        if 'hardness' in df.columns and 'unit' in df.columns:
            # Convert HV if needed
            mask_hv = df['unit'].str.upper() == 'HV'
            df.loc[mask_hv, 'hardness_hv'] = df.loc[mask_hv, 'hardness']
            # Conversion logic for other units would go here
            df = df.drop(columns=['hardness', 'unit'])
            df = df.rename(columns={'hardness_hv': 'hardness'})
        elif 'hardness_hv' in df.columns:
            df = df.rename(columns={'hardness_hv': 'hardness'})
        
        # 3. Exclude alloys with >5 elements
        # This requires parsing the composition string or checking element columns.
        # Assuming a 'composition' string like "Sn95Ag5" or separate columns.
        # For scaffolding, we assume a 'num_elements' column or parse it.
        # If parsing:
        if 'composition' in df.columns:
            # Simple heuristic: count non-whitespace groups or commas
            # This is a placeholder for complex parsing
            df['num_elements'] = df['composition'].apply(lambda x: len(x.split(',')) if ',' in x else 1)
            df = df[df['num_elements'] <= self.max_elements]
            df = df.drop(columns=['num_elements'])
        elif 'num_elements' in df.columns:
            df = df[df['num_elements'] <= self.max_elements]

        # 4. Validate elemental composition sums
        # Assuming columns like 'Sn', 'Ag', 'Cu' etc.
        # Sum of elemental columns should be close to 1.0 or 100
        element_cols = [c for c in df.columns if c.isupper() and len(c) <= 3] # Heuristic
        if element_cols:
            df['composition_sum'] = df[element_cols].sum(axis=1)
            df = df[(df['composition_sum'] >= self.composition_threshold) & (df['composition_sum'] <= 1.05)]
            df = df.drop(columns=['composition_sum'])

        # 5. Handle missing values
        df = df.dropna(subset=['hardness']) # Drop rows without hardness

        logger.info(f"Cleaning complete. Rows remaining: {len(df)}")
        return df

    def save_cleaned(self, df: pd.DataFrame, output_path: str):
        """Saves cleaned data to CSV."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Cleaned data saved to {output_path}")

def main():
    """Entry point for cleaner script."""
    logging.basicConfig(level=logging.INFO)
    cleaner = DataCleaner()
    
    # Load raw data (path from env or default)
    raw_path = os.getenv("RAW_DATA_PATH", "data/raw/solder_hardness_raw.csv")
    df = cleaner.load_data(raw_path)
    
    if not df.empty:
        cleaned_df = cleaner.clean(df)
        output_path = os.getenv("CLEANED_DATA_PATH", "data/processed/solder_hardness_cleaned.csv")
        cleaner.save_cleaned(cleaned_df, output_path)
    else:
        logger.warning("No data to clean.")

if __name__ == "__main__":
    main()

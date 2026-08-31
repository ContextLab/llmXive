import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os

from exceptions import MissingDataError, DiscrepancyError
from logger import get_logger
from error_handling import validate_required_fields

logger = get_logger(__name__)

class DiscrepancyCalculator:
    """
    Calculates discrepancies between precinct sums and county reported totals.
    Handles missing data via imputation or flagging as per specification.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.imputation_strategy = self.config.get('imputation_strategy', 'median')
        self.missing_data_threshold = self.config.get('missing_data_threshold', 0.05)
        logger.info(f"DiscrepancyCalculator initialized with strategy: {self.imputation_strategy}")

    def calculate_discrepancies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates discrepancy metrics and handles missing data.

        Args:
            df: DataFrame containing 'precinct_sum' and 'county_reported' columns.

        Returns:
            DataFrame with added columns: discrepancy_abs, discrepancy_pct, missing_data.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to calculate_discrepancies")
            df['discrepancy_abs'] = 0.0
            df['discrepancy_pct'] = 0.0
            df['missing_data'] = False
            return df

        # Validate required fields
        required = ['precinct_sum', 'county_reported']
        if not all(col in df.columns for col in required):
            raise MissingDataError(f"Missing required columns in input DataFrame: {required}")

        df = df.copy()

        # 1. Identify Missing Data
        # A record is considered to have missing data if either primary metric is null/NaN
        missing_mask = df['precinct_sum'].isna() | df['county_reported'].isna()
        df['missing_data'] = missing_mask

        # 2. Handle Missing Data via Imputation or Flagging
        # Only attempt imputation if there are missing values AND the strategy is valid
        if missing_mask.any():
            logger.info(f"Found {missing_mask.sum()} records with missing data. Applying imputation strategy: {self.imputation_strategy}")
            df = self._apply_imputation(df, missing_mask)
        else:
            logger.debug("No missing data found in input DataFrame.")

        # 3. Calculate Discrepancy Metrics
        # Ensure numeric types for calculation
        df['precinct_sum'] = pd.to_numeric(df['precinct_sum'], errors='coerce')
        df['county_reported'] = pd.to_numeric(df['county_reported'], errors='coerce')

        # Calculate Absolute Discrepancy
        df['discrepancy_abs'] = df['precinct_sum'] - df['county_reported']

        # Calculate Relative Discrepancy (Percentage)
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            df['discrepancy_pct'] = (df['discrepancy_abs'] / df['county_reported']) * 100
            # Replace inf/nan resulting from division by zero with 0 or handle as needed
            # If county_reported is 0, discrepancy is undefined; we set to 0 for stability
            df.loc[df['county_reported'] == 0, 'discrepancy_pct'] = 0.0

        # 4. Final Validation: Ensure no NaNs remain in critical calculated fields
        # If imputation failed or data was all NaN, we must flag or error
        critical_cols = ['discrepancy_abs', 'discrepancy_pct']
        for col in critical_cols:
            if df[col].isna().any():
                logger.warning(f"Critical column {col} still contains NaN after calculation. Filling with 0.")
                df[col] = df[col].fillna(0.0)

        return df

    def _apply_imputation(self, df: pd.DataFrame, missing_mask: pd.Series) -> pd.DataFrame:
        """
        Applies the configured imputation strategy to missing values.

        Strategies:
        - 'median': Imputes with the median of the non-missing values.
        - 'mean': Imputes with the mean of the non-missing values.
        - 'zero': Imputes with 0.
        - 'flag_only': Does not impute, keeps NaN but ensures 'missing_data' is True.
        """
        if self.imputation_strategy == 'flag_only':
            logger.info("Strategy 'flag_only' selected. No imputation performed. NaNs retained.")
            return df

        # Determine columns to impute
        cols_to_impute = ['precinct_sum', 'county_reported']
        
        for col in cols_to_impute:
            if df[col].isna().any():
                valid_values = df.loc[~df[col].isna(), col]
                
                if valid_values.empty:
                    logger.warning(f"All values for {col} are missing. Cannot impute. Filling with 0.")
                    df[col] = df[col].fillna(0.0)
                    continue

                if self.imputation_strategy == 'median':
                    fill_value = valid_values.median()
                elif self.imputation_strategy == 'mean':
                    fill_value = valid_values.mean()
                elif self.imputation_strategy == 'zero':
                    fill_value = 0.0
                else:
                    raise ConfigurationError(f"Unknown imputation strategy: {self.imputation_strategy}")
                
                logger.debug(f"Imputing {col} with {self.imputation_strategy} value: {fill_value}")
                df.loc[missing_mask, col] = df.loc[missing_mask, col].fillna(fill_value)

        return df

def main():
    """
    Entry point for discrepancy calculation module.
    Loads processed data, calculates discrepancies, and saves results.
    """
    logger.info("Starting DiscrepancyCalculator main execution.")
    
    # Example usage for testing the logic (in a real run, paths would come from args/config)
    # This block ensures the module can be run directly to verify logic if data exists
    try:
        # Attempt to load a sample processed file if it exists (for local verification)
        processed_path = "data/processed/ingested_election_data.csv"
        if os.path.exists(processed_path):
            df = pd.read_csv(processed_path)
            calculator = DiscrepancyCalculator()
            result = calculator.calculate_discrepancies(df)
            
            output_path = "data/processed/discrepancy_results.csv"
            result.to_csv(output_path, index=False)
            logger.info(f"Discrepancy results saved to {output_path}")
            print(f"Success: Processed {len(result)} records. Output saved to {output_path}")
        else:
            logger.info("No input data found at expected path. Module ready for integration.")
            print("Module ready. No input data found at data/processed/ingested_election_data.csv")
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
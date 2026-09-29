import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os

from .exceptions import MissingDataError, DiscrepancyError
from .logger import get_logger_for_module

logger = get_logger_for_module(__name__)

class DiscrepancyCalculator:
    """
    Calculates discrepancies between precinct sums and county reported totals.
    Handles missing data via imputation or flagging as per T020.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.imputation_strategy = self.config.get('imputation_strategy', 'flag')
        # If imputation is numeric, default to median of available data
        self.fill_value = self.config.get('fill_value', None) 

    def calculate_discrepancies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates discrepancy metrics and handles missing data.
        
        Expected columns in input: 'precinct_sum', 'county_reported' (and others).
        Output adds: 'discrepancy_abs', 'discrepancy_pct', 'missing_data'.
        
        T020 Implementation:
        1. Identifies rows where 'precinct_sum' or 'county_reported' is null/NaN.
        2. If imputation_strategy is 'flag': sets 'missing_data' to True.
        3. If imputation_strategy is 'impute': fills with median (or config value) 
           and sets 'missing_data' to False.
        4. Raises MissingDataError if critical columns are entirely missing.
        """
        if df.empty:
            logger.warning("Input DataFrame is empty. Returning empty result.")
            return df

        # Validate required columns exist
        required_cols = ['precinct_sum', 'county_reported']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise DiscrepancyError(f"Missing required columns for discrepancy calculation: {missing_cols}")

        # Initialize missing_data flag column if not exists
        if 'missing_data' not in df.columns:
            df['missing_data'] = False

        # Identify rows with missing data in critical columns
        mask_missing = df['precinct_sum'].isna() | df['county_reported'].isna()
        count_missing = mask_missing.sum()

        if count_missing > 0:
            logger.info(f"Found {count_missing} records with missing data in critical fields.")
            
            if self.imputation_strategy == 'impute':
                logger.info(f"Applying imputation strategy: {self.imputation_strategy}")
                
                # Determine fill values
                # If not explicitly configured, use median of non-null values
                if self.fill_value is None:
                    fill_precinct = df['precinct_sum'].median()
                    fill_county = df['county_reported'].median()
                    
                    if pd.isna(fill_precinct) or pd.isna(fill_county):
                        raise MissingDataError(
                            "Imputation requested but median calculation failed due to all-null columns."
                        )
                    
                    logger.info(f"Imputing precinct_sum with median: {fill_precinct}")
                    logger.info(f"Imputing county_reported with median: {fill_county}")
                else:
                    fill_precinct = self.fill_value
                    fill_county = self.fill_value

                # Apply imputation
                df.loc[mask_missing, 'precinct_sum'] = df.loc[mask_missing, 'precinct_sum'].fillna(fill_precinct)
                df.loc[mask_missing, 'county_reported'] = df.loc[mask_missing, 'county_reported'].fillna(fill_county)
                
                # Mark as not missing since we filled it
                df.loc[mask_missing, 'missing_data'] = False
                
            elif self.imputation_strategy == 'flag':
                logger.info("Flagging records with missing data.")
                df.loc[mask_missing, 'missing_data'] = True
                
                # Note: We do NOT drop them here. The downstream logic (T018/T019)
                # or specific analysis steps should decide how to handle flagged rows.
                # However, for calculation purposes, we cannot compute discrepancy 
                # without values. We will set discrepancy to NaN for flagged rows.
                df.loc[mask_missing, 'discrepancy_abs'] = np.nan
                df.loc[mask_missing, 'discrepancy_pct'] = np.nan
                return df

            else:
                raise ValueError(f"Unknown imputation_strategy: {self.imputation_strategy}. Use 'impute' or 'flag'.")

        # Calculate discrepancies for non-missing rows
        # Ensure numeric types
        df['precinct_sum'] = pd.to_numeric(df['precinct_sum'], errors='coerce')
        df['county_reported'] = pd.to_numeric(df['county_reported'], errors='coerce')

        # Re-check for NaNs that might have appeared after coercion
        if df['precinct_sum'].isna().any() or df['county_reported'].isna().any():
            # These are rows that were either originally missing or failed coercion
            # If strategy was 'impute' and we still have NaNs, it's a hard error
            if self.imputation_strategy == 'impute':
                raise MissingDataError("Critical data remains missing after imputation attempt.")
            
            # If strategy was 'flag', ensure they are marked
            mask_still_missing = df['precinct_sum'].isna() | df['county_reported'].isna()
            df.loc[mask_still_missing, 'missing_data'] = True
            df.loc[mask_still_missing, 'discrepancy_abs'] = np.nan
            df.loc[mask_still_missing, 'discrepancy_pct'] = np.nan

        # Calculate metrics
        df['discrepancy_abs'] = df['precinct_sum'] - df['county_reported']
        
        # Avoid division by zero for percentage calculation
        # If county_reported is 0, discrepancy_pct is undefined (set to NaN or Inf)
        df['discrepancy_pct'] = np.where(
            df['county_reported'] != 0,
            (df['discrepancy_abs'] / df['county_reported']) * 100,
            np.nan
        )

        # Ensure missing_data is False for rows where we successfully calculated
        # (unless the row was flagged earlier and not imputed)
        if self.imputation_strategy == 'impute':
            df.loc[~df['discrepancy_abs'].isna(), 'missing_data'] = False

        return df

    def filter_missing_data(self, df: pd.DataFrame, keep_missing: bool = False) -> pd.DataFrame:
        """
        Helper to filter dataframe based on missing_data flag.
        
        Args:
            df: Input dataframe with 'missing_data' column.
            keep_missing: If True, keep only rows with missing_data=True. 
                          If False, drop rows with missing_data=True.
                          
        Returns:
            Filtered dataframe.
        """
        if 'missing_data' not in df.columns:
            logger.warning("Column 'missing_data' not found. Returning original dataframe.")
            return df

        if keep_missing:
            logger.info(f"Keeping {df['missing_data'].sum()} records with missing data.")
            return df[df['missing_data'] == True]
        else:
            dropped_count = df['missing_data'].sum()
            logger.info(f"Dropping {dropped_count} records with missing data.")
            return df[df['missing_data'] == False]


def main():
    """
    CLI entry point for testing discrepancy calculation and missing data handling.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run discrepancy calculation with missing data handling.")
    parser.add_argument("--input", type=str, default=None, help="Path to input CSV (optional for demo)")
    parser.add_argument("--output", type=str, default="data/processed/discrepancies_demo.csv", help="Path to output CSV")
    parser.add_argument("--strategy", type=str, default="flag", choices=["flag", "impute"], help="Missing data strategy")
    parser.add_argument("--fill", type=float, default=None, help="Specific value to fill if strategy is impute")
    
    args = parser.parse_args()

    # Setup logging
    setup_logging = __import__('logger', fromlist=['setup_logging']).setup_logging
    setup_logging()

    # Create calculator
    config = {'imputation_strategy': args.strategy}
    if args.fill is not None:
        config['fill_value'] = args.fill
    
    calculator = DiscrepancyCalculator(config)

    # If no input file provided, generate a small demo dataset to verify logic
    if args.input is None:
        logger.info("No input file provided. Generating demo dataset to verify T020 logic.")
        data = {
            'jurisdiction': ['A', 'B', 'C', 'D', 'E'],
            'precinct_sum': [1000, 2000, np.nan, 4000, 5000],
            'county_reported': [1000, 1950, 3000, np.nan, 4900]
        }
        df = pd.DataFrame(data)
        logger.info("Demo Data:\n" + df.to_string())
    else:
        df = pd.read_csv(args.input)

    try:
        result = calculator.calculate_discrepancies(df)
        logger.info("Calculation complete.")
        logger.info("Result Preview:\n" + result.head(10).to_string())
        
        # Save output
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        result.to_csv(args.output, index=False)
        logger.info(f"Results saved to {args.output}")
        
        # Verify schema
        expected_cols = ['precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct', 'missing_data']
        missing_schema_cols = [c for c in expected_cols if c not in result.columns]
        if missing_schema_cols:
            raise DiscrepancyError(f"Output schema missing columns: {missing_schema_cols}")
        
        logger.info("Schema validation passed.")

    except MissingDataError as e:
        logger.error(f"Missing data error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()

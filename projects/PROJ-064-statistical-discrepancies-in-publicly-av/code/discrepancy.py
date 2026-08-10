import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os

from exceptions import DiscrepancyError, StatisticalModelError
from logger import get_logger

logger = get_logger(__name__)

class DiscrepancyCalculator:
    """
    Calculates discrepancies between precinct sums and county reported totals.
    Implements logic to flag directional anomalies and handle edge cases.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)

    def calculate_discrepancies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate discrepancy metrics for the input DataFrame.

        Adds columns:
        - precinct_sum: Sum of precinct votes
        - county_reported: Reported county total
        - discrepancy_abs: Absolute difference (precinct_sum - county_reported)
        - discrepancy_pct: Percentage difference relative to county_reported
        - missing_data: Boolean flag for missing data records

        Args:
            df: Input DataFrame with precinct and county vote data

        Returns:
            DataFrame with added discrepancy columns
        """
        if df.empty:
            self.logger.warning("Empty DataFrame provided to calculate_discrepancies")
            return df

        # Validate required columns exist
        required_cols = ['precinct_sum', 'county_reported']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise DiscrepancyError(f"Missing required columns: {missing_cols}")

        # Create a copy to avoid modifying the original
        result_df = df.copy()

        # Calculate absolute discrepancy
        result_df['discrepancy_abs'] = result_df['precinct_sum'] - result_df['county_reported']

        # Calculate percentage discrepancy (handle division by zero)
        with np.errstate(divide='ignore', invalid='ignore'):
            result_df['discrepancy_pct'] = np.where(
                result_df['county_reported'] != 0,
                (result_df['discrepancy_abs'] / result_df['county_reported']) * 100,
                np.nan
            )

        # Flag missing data
        result_df['missing_data'] = (
            result_df['precinct_sum'].isna() |
            result_df['county_reported'].isna()
        )

        return result_df

    def flag_directional_anomalies(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[int]]:
        """
        Flag records where precinct sum exceeds county total (directional anomaly).

        These records violate the non-negative error assumption required for
        Negative Binomial fitting and should be excluded from that analysis.

        Args:
            df: DataFrame with calculated discrepancies (must have 'precinct_sum', 'county_reported')

        Returns:
            Tuple of (DataFrame with 'directional_anomaly' flag, list of flagged indices)
        """
        if df.empty:
            self.logger.warning("Empty DataFrame provided to flag_directional_anomalies")
            return df.copy(), []

        # Ensure required columns exist
        if 'precinct_sum' not in df.columns or 'county_reported' not in df.columns:
            raise DiscrepancyError(
                "Input DataFrame must have 'precinct_sum' and 'county_reported' columns"
            )

        result_df = df.copy()

        # Identify directional anomalies: precinct_sum > county_reported
        # This indicates the sum of precincts is greater than the reported county total,
        # which is physically impossible under normal counting (precincts should sum to county)
        # unless there are data errors, double-counting, or reporting inconsistencies.
        directional_mask = result_df['precinct_sum'] > result_df['county_reported']

        # Add flag column
        result_df['directional_anomaly'] = directional_mask

        # Get indices of flagged records
        flagged_indices = result_df[directional_mask].index.tolist()

        if flagged_indices:
            self.logger.warning(
                f"Found {len(flagged_indices)} directional anomalies (precinct_sum > county_reported). "
                "These will be excluded from Negative Binomial fitting."
            )
            for idx in flagged_indices[:5]:  # Log first 5 as examples
                self.logger.debug(
                    f"Directional anomaly at index {idx}: "
                    f"precinct_sum={result_df.loc[idx, 'precinct_sum']}, "
                    f"county_reported={result_df.loc[idx, 'county_reported']}"
                )

        return result_df, flagged_indices

    def exclude_for_nb_fit(self, df: pd.DataFrame, flagged_indices: List[int]) -> pd.DataFrame:
        """
        Exclude directional anomaly records from a DataFrame for Negative Binomial fitting.

        Args:
            df: Original DataFrame
            flagged_indices: List of indices to exclude (from flag_directional_anomalies)

        Returns:
            Filtered DataFrame excluding directional anomalies
        """
        if not flagged_indices:
            return df.copy()

        # Create mask for non-anomalous records
        mask = ~df.index.isin(flagged_indices)
        filtered_df = df[mask].copy()

        self.logger.info(
            f"Excluded {len(flagged_indices)} directional anomalies from Negative Binomial fit. "
            f"Remaining records: {len(filtered_df)}"
        )

        return filtered_df

    def prepare_for_nb_analysis(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[int]]:
        """
        Full pipeline to prepare data for Negative Binomial analysis:
        1. Calculate discrepancies
        2. Flag directional anomalies
        3. Exclude anomalies from the analysis set

        Args:
            df: Input DataFrame with precinct and county vote data

        Returns:
            Tuple of (filtered DataFrame for NB fit, list of excluded indices)
        """
        # Step 1: Calculate discrepancies
        df_with_discrepancies = self.calculate_discrepancies(df)

        # Step 2: Flag directional anomalies
        df_flagged, flagged_indices = self.flag_directional_anomalies(df_with_discrepancies)

        # Step 3: Exclude anomalies for NB fit
        df_for_nb = self.exclude_for_nb_fit(df_flagged, flagged_indices)

        return df_for_nb, flagged_indices


def main():
    """
    Main entry point for discrepancy calculation and directional anomaly flagging.
    Reads processed data, calculates discrepancies, flags anomalies, and saves results.
    """
    logger.info("Starting discrepancy calculation and directional anomaly flagging")

    # Example usage (in real pipeline, this would read from data/processed/)
    # This is a placeholder for the actual integration point
    try:
        # Simulate loading data (replace with actual data loading in production)
        sample_data = pd.DataFrame({
            'jurisdiction_id': ['J001', 'J002', 'J003', 'J004'],
            'precinct_sum': [1000, 2000, 1500, 3000],
            'county_reported': [1000, 1950, 1500, 2800]  # J002 and J004 have anomalies
        })

        calculator = DiscrepancyCalculator()

        # Full pipeline
        df_for_nb, excluded_indices = calculator.prepare_for_nb_analysis(sample_data)

        logger.info(f"Original records: {len(sample_data)}")
        logger.info(f"Excluded for NB fit: {len(excluded_indices)}")
        logger.info(f"Records for NB analysis: {len(df_for_nb)}")

        if excluded_indices:
            logger.info(f"Excluded indices: {excluded_indices}")

        # Save results (placeholder paths - actual paths from tasks.md)
        output_path = "data/processed/discrepancies_with_flags.csv"
        df_for_nb.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")

        logger.info("Discrepancy calculation and directional anomaly flagging completed successfully")

    except Exception as e:
        logger.error(f"Error in discrepancy calculation: {str(e)}")
        raise


if __name__ == "__main__":
    main()
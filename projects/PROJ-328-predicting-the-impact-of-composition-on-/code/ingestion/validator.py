import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import sys

# Import from project utils to ensure consistent error handling
from utils.error_handlers import DataInsufficientError, DataValidationError
from config import (
    get_config,
    get_data_processed_dir,
    get_composition_sum_threshold,
    get_max_elements
)
from utils.logging_config import get_logger

# Constants for status reporting
STATUS_THRESHOLD_HIGH = 100
STATUS_THRESHOLD_MEDIUM = 50

logger = get_logger(__name__)


class DataValidator:
    """
    Validates cleaned solder hardness data for non-null hardness,
    complete composition, and sufficient sample size.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.composition_threshold = get_composition_sum_threshold()
        self.max_elements = get_max_elements()
        self.processed_dir = get_data_processed_dir()
        
    def validate_hardness_non_null(self, df: pd.DataFrame) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Check for non-null Vickers hardness values.
        
        Returns:
            tuple: (cleaned_df, list_of_failed_records)
        """
        if 'hardness_hv' not in df.columns:
            raise DataValidationError("Input DataFrame missing 'hardness_hv' column")
        
        # Identify null hardness values
        null_mask = df['hardness_hv'].isna()
        failed_records = []
        
        if null_mask.any():
            failed_indices = df[null_mask].index.tolist()
            failed_records = [
                {
                    'index': int(idx),
                    'reason': 'Null hardness value',
                    'row_data': df.loc[idx, :].to_dict()
                }
                for idx in failed_indices
            ]
            
            # Log the failure details
            logger.warning(f"Found {len(failed_records)} records with null hardness values")
            
            # Drop null hardness records
            df_clean = df.dropna(subset=['hardness_hv'])
        else:
            df_clean = df.copy()
            
        return df_clean, failed_records

    def validate_composition_completeness(self, df: pd.DataFrame) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Validate that elemental compositions sum to >= 95% (configurable).
        
        Returns:
            tuple: (cleaned_df, list_of_failed_records)
        """
        if df.empty:
            return df, []
        
        # Identify composition columns (assume they start with 'element_' or are specific element names)
        # A robust approach: find numeric columns that look like elemental percentages
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        # Heuristic: Exclude known non-composition columns
        exclude_cols = ['hardness_hv', 'measurement_temp_c', 'record_id', 'source_id', 'index']
        composition_cols = [c for c in numeric_cols if c not in exclude_cols]
        
        if not composition_cols:
            logger.warning("No composition columns found in DataFrame")
            return df, []
        
        # Calculate sum of compositions for each row
        df['composition_sum'] = df[composition_cols].sum(axis=1)
        
        # Identify invalid records
        invalid_mask = df['composition_sum'] < self.composition_threshold
        failed_records = []
        
        if invalid_mask.any():
            failed_indices = df[invalid_mask].index.tolist()
            failed_records = [
                {
                    'index': int(idx),
                    'reason': f"Composition sum {df.loc[idx, 'composition_sum']:.2f}% < {self.composition_threshold}%",
                    'composition_sum': float(df.loc[idx, 'composition_sum']),
                    'row_data': df.loc[idx, :].to_dict()
                }
                for idx in failed_indices
            ]
            
            logger.warning(f"Found {len(failed_records)} records with composition sum < {self.composition_threshold}%")
            
            # Drop invalid records
            df_clean = df.drop(index=df[invalid_mask].index)
            df_clean = df_clean.drop(columns=['composition_sum'])
        else:
            df_clean = df.drop(columns=['composition_sum'])
            
        return df_clean, failed_records

    def validate_sample_size(self, n: int) -> Dict[str, Any]:
        """
        Check sample size against thresholds and generate status report.
        
        Args:
            n: Number of valid records
            
        Returns:
            Dict with threshold_status, exact_N, and warning_text
        """
        if n >= STATUS_THRESHOLD_HIGH:
            status = 'N>=100'
            warning = None
            logger.info(f"Sample size sufficient: N={n} >= 100")
        elif n >= STATUS_THRESHOLD_MEDIUM:
            status = '50<=N<100'
            warning = f"Power limitation warning: N={n} is between 50 and 100. Statistical power may be limited."
            logger.warning(warning)
        else:
            status = 'N<50'
            warning = f"Severe data insufficiency: N={n} < 50. Results may not be statistically significant."
            logger.error(warning)
            
        return {
            'threshold_status': status,
            'exact_N': n,
            'warning_text': warning
        }

    def run_full_validation(self, input_path: Optional[Path] = None) -> Path:
        """
        Execute the full validation pipeline on cleaned data.
        
        Args:
            input_path: Path to cleaned CSV (defaults to config path)
            
        Returns:
            Path to the status JSON file
        """
        if input_path is None:
            input_path = self.processed_dir / 'solder_hardness_cleaned.csv'
        
        if not input_path.exists():
            raise FileNotFoundError(f"Cleaned data file not found: {input_path}")
        
        logger.info(f"Starting validation on {input_path}")
        
        # Load data
        df = pd.read_csv(input_path)
        initial_n = len(df)
        logger.info(f"Loaded {initial_n} records from {input_path}")
        
        # Step 1: Validate hardness non-null
        df_validated, hardness_failures = self.validate_hardness_non_null(df)
        logger.info(f"After hardness validation: {len(df_validated)} records remain")
        
        # Step 2: Validate composition completeness
        df_validated, comp_failures = self.validate_composition_completeness(df_validated)
        logger.info(f"After composition validation: {len(df_validated)} records remain")
        
        # Save validation logs (optional, for audit)
        if hardness_failures or comp_failures:
            logs_dir = self.processed_dir / 'validation_logs'
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            all_failures = hardness_failures + comp_failures
            if all_failures:
                fail_df = pd.DataFrame(all_failures)
                fail_df.to_csv(logs_dir / 'validation_failures.csv', index=False)
                logger.info(f"Saved {len(all_failures)} validation failures to {logs_dir / 'validation_failures.csv'}")
        
        # Step 3: Check sample size and generate status
        final_n = len(df_validated)
        status_report = self.validate_sample_size(final_n)
        
        # Write status to JSON file
        status_path = self.processed_dir / '.ingestion_status.json'
        with open(status_path, 'w') as f:
            json.dump(status_report, f, indent=2)
        
        logger.info(f"Validation complete. Status written to {status_path}")
        logger.info(f"Final sample size: {final_n} (Status: {status_report['threshold_status']})")
        
        return status_path


def main():
    """Main entry point for validation script."""
    logger.info("Starting DataValidator main()")
    
    try:
        validator = DataValidator()
        status_path = validator.run_full_validation()
        
        # Load and print status for verification
        with open(status_path, 'r') as f:
            status = json.load(f)
            
        print(json.dumps(status, indent=2))
        
        # If N < 50, raise an error to halt the pipeline (optional, based on strictness)
        if status['exact_N'] < STATUS_THRESHOLD_MEDIUM:
            logger.error(f"DataInsufficientError: Sample size {status['exact_N']} is below minimum threshold of 50.")
            # Note: We log the error but do not raise here to allow the pipeline to 
            # continue with a flag, as per task requirements ("do NOT halt" for N<50)
            # However, if strict mode is required, uncomment the next line:
            # raise DataInsufficientError(status['warning_text'])
            
    except Exception as e:
        logger.critical(f"Validation failed with error: {e}")
        raise


if __name__ == '__main__':
    main()
"""
Data validation logic for the solder hardness dataset ingestion pipeline.
Implements T014: Validation reporting logic to check for non-null hardness and complete composition.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import from project utils
from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError, ConfigurationError
from config import (
    get_config,
    get_data_processed_dir,
    get_composition_sum_threshold,
    get_min_n_for_power,
    get_target_n
)

logger = get_logger(__name__)

class DataValidator:
    """
    Validates the cleaned solder hardness dataset against project constraints.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.processed_dir = get_data_processed_dir()
        self.cleaned_file = self.processed_dir / "solder_hardness_cleaned.csv"
        self.filtered_file = self.processed_dir / "validation_logs" / "filtered_records.csv"
        self.status_file = self.processed_dir / ".ingestion_status.json"
        
        # Configuration thresholds
        self.composition_sum_threshold = get_composition_sum_threshold()
        self.min_n_for_power = get_min_n_for_power()
        self.target_n = get_target_n()

    def load_cleaned_data(self) -> pd.DataFrame:
        """Load the cleaned dataset."""
        if not self.cleaned_file.exists():
            raise FileNotFoundError(f"Cleaned data file not found: {self.cleaned_file}")
        
        logger.info(f"Loading cleaned data from {self.cleaned_file}")
        df = pd.read_csv(self.cleaned_file)
        return df

    def load_filtered_records(self) -> pd.DataFrame:
        """Load the filtered records log if it exists."""
        if not self.filtered_file.exists():
            logger.warning(f"Filtered records file not found: {self.filtered_file}. Assuming 0 excluded.")
            return pd.DataFrame()
        
        logger.info(f"Loading filtered records from {self.filtered_file}")
        return pd.read_csv(self.filtered_file)

    def validate_composition_sums(self, df: pd.DataFrame) -> List[str]:
        """
        Validate that all records have composition sums >= threshold.
        Returns a list of indices for any invalid records found.
        """
        # Identify elemental columns (assume they start with 'element_' or are specific known columns)
        # Based on data-model.md, elemental breakdown is stored as columns.
        # We need to identify which columns are elemental percentages.
        # Heuristic: Columns containing 'element' or specific known element names.
        # For robustness, we'll check columns that look like percentages (0.0 to 100.0 or 0.0 to 1.0)
        # but the safer approach is to look for the specific schema.
        # Assuming the CSV has columns like 'Sn_pct', 'Ag_pct', 'Cu_pct', etc. or 'element_Sn', etc.
        # Let's assume the schema from T013: elemental breakdown columns are numeric and sum to ~100 or ~1.0.
        
        # A more robust way: Look for columns that are numeric and not the target or metadata
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        exclude_cols = ['hardness_hv', 'measurement_temp_c', 'source_id', 'record_id'] # Adjust as needed
        element_cols = [c for c in numeric_cols if c not in exclude_cols]
        
        if not element_cols:
            logger.warning("No elemental composition columns found in the dataset. Skipping sum validation.")
            return []

        # Calculate sum for each row
        composition_sums = df[element_cols].sum(axis=1)
        
        # Check against threshold
        invalid_mask = composition_sums < self.composition_sum_threshold
        invalid_indices = df.index[invalid_mask].tolist()
        
        if invalid_indices:
            logger.error(f"Found {len(invalid_indices)} records with composition sum < {self.composition_sum_threshold}")
            logger.error(f"Invalid indices: {invalid_indices}")
            # Log the specific values for debugging
            for idx in invalid_indices[:5]: # Log first 5
                logger.error(f"Record {idx}: sum={composition_sums.iloc[idx]:.4f}, values={df.loc[idx, element_cols].to_dict()}")
        else:
            logger.info(f"All {len(df)} records have composition sum >= {self.composition_sum_threshold}")
        
        return invalid_indices

    def validate_hardness_non_null(self, df: pd.DataFrame) -> int:
        """
        Count records with non-null hardness values.
        """
        non_null_count = df['hardness_hv'].notna().sum()
        null_count = df['hardness_hv'].isna().sum()
        
        logger.info(f"Hardness validation: {non_null_count} non-null, {null_count} null out of {len(df)} total")
        
        if null_count > 0:
            logger.warning(f"Found {null_count} records with missing hardness values. These should have been filtered in T013.")
        
        return int(non_null_count)

    def determine_threshold_status(self, n: int) -> str:
        """Determine the status based on the sample size N."""
        if n >= self.target_n:
            return "N>=100"
        elif n >= self.min_n_for_power:
            return "50<=N<100"
        else:
            return "N<50"

    def run_validation(self) -> Dict[str, Any]:
        """
        Execute the full validation pipeline.
        Returns a dictionary with validation results.
        """
        logger.info("Starting DataValidator.run_validation()")
        
        # 1. Load Data
        try:
            df = self.load_cleaned_data()
            filtered_df = self.load_filtered_records()
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise

        # 2. Validate Composition Sums
        invalid_composition_indices = self.validate_composition_sums(df)
        if invalid_composition_indices:
            # This is a critical failure if T013 was supposed to filter these
            raise DataValidationError(
                f"Found {len(invalid_composition_indices)} records with invalid composition sums in cleaned data. "
                "T013 filtering logic may have failed."
            )

        # 3. Count Non-Null Hardness
        valid_hardness_count = self.validate_hardness_non_null(df)
        
        # 4. Count Excluded Records
        excluded_count = len(filtered_df) if not filtered_df.empty else 0

        # 5. Determine Status
        status = self.determine_threshold_status(valid_hardness_count)
        
        # 6. Check Power Limitation
        power_limitation_warning = None
        if valid_hardness_count < self.min_n_for_power:
            power_limitation_warning = "N < 50"
            logger.warning(f"Severe Warning: Sample size {valid_hardness_count} is below minimum power threshold {self.min_n_for_power}")
        elif valid_hardness_count < self.target_n:
            logger.warning(f"Warning: Sample size {valid_hardness_count} is below target {self.target_n}. Statistical power may be limited.")

        # 7. Prepare Result
        result = {
            "threshold_status": status,
            "exact_N": valid_hardness_count,
            "excluded_count": excluded_count,
            "power_limitation_warning": power_limitation_warning,
            "composition_validation_passed": len(invalid_composition_indices) == 0,
            "timestamp": pd.Timestamp.now().isoformat()
        }

        # 8. Write Status File
        self._write_status_file(result)

        logger.info(f"Validation complete. Status: {status}, N: {valid_hardness_count}")
        return result

    def _write_status_file(self, result: Dict[str, Any]) -> None:
        """Write the validation status to the JSON status file."""
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.status_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Status written to {self.status_file}")

    def verify_against_status(self) -> bool:
        """
        Re-read the status file and verify it matches current data.
        Useful for T014's requirement to 'Calculate Composition Sums ... to confirm'.
        """
        if not self.status_file.exists():
            logger.error("Status file does not exist. Cannot verify.")
            return False

        with open(self.status_file, 'r') as f:
            status_data = json.load(f)

        # Re-load data and re-calculate
        df = self.load_cleaned_data()
        invalid_indices = self.validate_composition_sums(df)
        current_n = self.validate_hardness_non_null(df)
        
        # Check consistency
        if status_data.get("exact_N") != current_n:
            logger.error(f"N mismatch in status file: {status_data.get('exact_N')} vs current {current_n}")
            return False
        
        if not status_data.get("composition_validation_passed") and len(invalid_indices) > 0:
            logger.error("Status file claims validation passed, but invalid records found.")
            return False

        logger.info("Verification against status file passed.")
        return True


def main():
    """Entry point for the validator script."""
    logger.info("Running DataValidator main()")
    
    try:
        validator = DataValidator()
        results = validator.run_validation()
        
        # Perform verification
        if validator.verify_against_status():
            logger.info("Validation and verification successful.")
            return 0
        else:
            logger.error("Verification failed.")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except DataValidationError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

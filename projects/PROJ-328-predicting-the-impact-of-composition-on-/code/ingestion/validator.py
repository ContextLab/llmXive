"""
Validator module for checking data quality and completeness.
Implements strict validation logic for User Story 1 (T014).
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import sys

# Import project utilities
try:
    from utils.logging_config import get_logger
    from utils.error_handlers import DataValidationError, ConfigurationError
    from config import (
        get_data_processed_dir,
        get_min_samples_warning,
        get_composition_sum_threshold,
        get_min_samples_target
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.logging_config import get_logger
    from utils.error_handlers import DataValidationError, ConfigurationError
    from config import (
        get_data_processed_dir,
        get_min_samples_warning,
        get_composition_sum_threshold,
        get_min_samples_target
    )


class DataValidator:
    """
    Validates cleaned data for non-null hardness and complete composition.
    Ensures compliance with T014 requirements.
    """

    def __init__(self):
        self.logger = get_logger("ingestion.validator")
        self.status: Dict[str, Any] = {}
        self.validation_logs: List[Dict[str, Any]] = []

    def validate_hardness(self, df: pd.DataFrame) -> int:
        """Count non-null hardness values."""
        if 'hardness_hv' not in df.columns:
            self.logger.error("Column 'hardness_hv' missing from dataframe.")
            return 0
        
        count = df['hardness_hv'].notna().sum()
        self.logger.info(f"Found {count} non-null hardness values.")
        return int(count)

    def validate_composition_sums(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Explicitly calculate the sum of elemental columns for every record
        to confirm no invalid records remain.
        
        Returns the dataframe with a 'composition_sum' column added.
        """
        # Identify elemental columns (assuming prefix 'element_' based on context)
        # If the schema differs, we look for float columns that are not hardness
        element_cols = [c for c in df.columns if c.startswith('element_')]
        
        if not element_cols:
            # Fallback: try to infer from non-target columns if naming is different
            # But strict adherence to spec suggests 'element_' prefix
            self.logger.warning("No columns starting with 'element_' found. Attempting to infer composition columns.")
            # Exclude known non-composition columns
            exclude_cols = ['hardness_hv', 'alloy_family', 'source_citation', 'measurement_temp_c']
            element_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
            
            if not element_cols:
                self.logger.error("Could not identify any elemental composition columns.")
                return df

        self.logger.info(f"Validating composition sums using columns: {element_cols}")
        
        # Calculate sum
        df = df.copy()
        df['composition_sum'] = df[element_cols].sum(axis=1)
        
        return df

    def check_composition_threshold(self, df: pd.DataFrame, threshold: float) -> bool:
        """
        Enforce threshold: confirm no records have composition sum < threshold.
        """
        invalid_mask = df['composition_sum'] < threshold
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            self.logger.error(f"Found {invalid_count} records with composition sum < {threshold}.")
            # Log specific records for audit
            invalid_records = df[invalid_mask][['composition_sum'] + [c for c in df.columns if c.startswith('element_')]]
            self.validation_logs.append({
                "reason": "COMPOSITION_SUM_LOW",
                "count": int(invalid_count),
                "threshold": threshold,
                "sample": invalid_records.head(5).to_dict(orient='records')
            })
            return False
        
        self.logger.info(f"All {len(df)} records meet the composition sum threshold of {threshold}.")
        return True

    def check_sample_size(self, n: int) -> Dict[str, Any]:
        """
        Check if sample size meets thresholds.
        Logic:
        - If N < 50: Severe warning, proceed with reduced N flag.
        - If 50 <= N < 100: Proceed but flag for power limitation.
        - If N >= 100: Success.
        """
        status = {
            "exact_N": n,
            "threshold_status": "unknown",
            "power_limitation_warning": None
        }

        if n >= 100:
            status["threshold_status"] = "N>=100"
        elif n >= 50:
            status["threshold_status"] = "50<=N<100"
            status["power_limitation_warning"] = "Power limitation: 50 <= N < 100"
        else:
            status["threshold_status"] = "N<50"
            status["power_limitation_warning"] = "N < 50"

        return status

    def run_validation(self, input_path: Path) -> Dict[str, Any]:
        """
        Run full validation pipeline as per T014.
        1. Read cleaned data.
        2. Calculate composition sums.
        3. Enforce threshold.
        4. Count non-null hardness.
        5. Check sample size thresholds.
        6. Write status.
        """
        self.logger.info(f"Starting validation for {input_path}")
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        df = pd.read_csv(input_path)
        
        # 1. & 2. Calculate Composition Sums
        df = self.validate_composition_sums(df)
        
        # 3. Enforce Threshold
        threshold = get_composition_sum_threshold()
        if threshold is None:
            raise ConfigurationError("COMPOSITION_SUM_THRESHOLD is not defined in config.")
        
        if not self.check_composition_threshold(df, threshold):
            # T014 requirement: If invalid records found, we might still proceed if the task 
            # allows, but typically this indicates a failure of the cleaning step (T013).
            # However, T014 is a validation report. We report the failure.
            # The prompt says: "Confirm no records... have composition sum < threshold".
            # If they do, the validation fails.
            raise DataValidationError(
                f"Composition validation failed: {sum(df['composition_sum'] < threshold)} records below threshold {threshold}."
            )

        # 4. Count Non-Null Hardness
        n = self.validate_hardness(df)
        
        # 5. Threshold Check
        status = self.check_sample_size(n)
        
        self.status = status
        self.logger.info(f"Validation complete. Status: {status}")
        
        return status

    def save_status(self, output_path: Path) -> None:
        """Save validation status to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.status, f, indent=2)
        self.logger.info(f"Validation status saved to {output_path}")

    def save_validation_logs(self, log_path: Path) -> None:
        """Save detailed validation logs if any issues were found."""
        if self.validation_logs:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w') as f:
                json.dump(self.validation_logs, f, indent=2)
            self.logger.info(f"Validation logs saved to {log_path}")


def main():
    """
    Entry point for the validator script (T014).
    Reads cleaned data, validates, and writes status to .ingestion_status.json.
    """
    logger = get_logger("ingestion.validator.main")
    logger.info("Running validator main (T014)...")
    
    validator = DataValidator()
    
    # Input: The cleaned file from T013
    input_file = get_data_processed_dir() / "solder_hardness_cleaned.csv"
    # Output: The status file for downstream tasks
    output_file = get_data_processed_dir() / ".ingestion_status.json"
    # Log file for any detailed issues
    log_file = get_data_processed_dir() / "validation_logs.json"
    
    if input_file.exists():
        try:
            status = validator.run_validation(input_file)
            validator.save_status(output_file)
            validator.save_validation_logs(log_file)
            logger.info(f"Validation complete. Status: {status}")
            
            # Exit with code 0 even if N < 50, as per instructions to "proceed with reduced N flag"
            # Only fail if critical config is missing or data is structurally invalid
            return 0
        except (DataValidationError, ConfigurationError) as e:
            logger.error(f"Validation failed: {e}")
            # Write a failure status if applicable, or re-raise
            return 1
    else:
        logger.error(f"Input file {input_file} not found. Cannot run validation.")
        return 1


if __name__ == "__main__":
    exit(main())
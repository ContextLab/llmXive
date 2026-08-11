"""
DataValidator: Validates solder hardness data for completeness and sufficiency.

This module implements the validation logic for T014, including:
- Checking non-null hardness values
- Verifying complete composition
- Enforcing composition sum threshold (>=95%)
- Checking N-count thresholds (>=50 minimum, >=100 target)
- Writing status to .ingestion_status.json
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import sys

from config import get_config, get_data_processed_dir, get_composition_sum_threshold
from utils.error_handlers import DataValidationError
from utils.logging_config import get_logger

class DataInsufficientError(Exception):
    """Raised when data count is below minimum threshold."""
    pass

class DataValidator:
    """
    Validates solder hardness data for completeness and sufficiency.
    
    Implements T014 requirements:
    - Check non-null hardness
    - Verify complete composition
    - Enforce composition sum >= 95%
    - Check N-count thresholds
    - Write status to .ingestion_status.json
    """
    
    def __init__(self):
        """Initialize the DataValidator."""
        self.logger = get_logger("ingestion.validator")
        self.logger.info("Initializing DataValidator")
        
        # Load configuration
        self.config = get_config()
        self.composition_sum_threshold = get_composition_sum_threshold()
        
        # Thresholds
        self.min_samples_warning = self.config.get('MIN_SAMPLES_WARNING', 50)
        self.min_samples_target = self.config.get('MIN_SAMPLES_TARGET', 100)
        
        # Output paths
        self.processed_dir = get_data_processed_dir()
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"DataValidator initialized: min_warning={self.min_samples_warning}, "
                       f"min_target={self.min_samples_target}")
    
    def validate_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the input data.
        
        Args:
            data: DataFrame with solder hardness records
        
        Returns:
            Dictionary with validation results and status
        
        Raises:
            DataInsufficientError: If N < 50
        """
        self.logger.info(f"Starting validation on {len(data)} records")
        
        if data.empty:
            self.logger.error("Input data is empty")
            raise DataInsufficientError("Input data is empty - cannot validate")
        
        # Track validation issues
        issues = []
        valid_count = 0
        
        # Check 1: Non-null hardness
        valid_count = self._check_hardness_not_null(data)
        if valid_count < len(data):
            issues.append(f"{len(data) - valid_count} records with null hardness")
        
        # Check 2: Complete composition (all required elements present)
        valid_count = self._check_complete_composition(data)
        if valid_count < len(data):
            issues.append(f"{len(data) - valid_count} records with incomplete composition")
        
        # Check 3: Composition sum >= 95%
        valid_count = self._check_composition_sum(data)
        if valid_count < len(data):
            issues.append(f"{len(data) - valid_count} records with composition sum < {self.composition_sum_threshold}")
        
        # Final count
        final_count = valid_count
        
        # Determine threshold status
        if final_count >= self.min_samples_target:
            threshold_status = "N>=100"
            warning_text = None
            self.logger.info(f"Validation complete: {final_count} records (Status: {threshold_status})")
        elif final_count >= self.min_samples_warning:
            threshold_status = "50<=N<100"
            warning_text = f"Warning: Only {final_count} records found (minimum 100 recommended for robust analysis)"
            self.logger.warning(f"Validation complete: {final_count} records (Status: {threshold_status})")
        else:
            threshold_status = "N<50"
            warning_text = f"Critical: Only {final_count} records found (minimum 50 required)"
            self.logger.error(f"Validation complete: {final_count} records (Status: {threshold_status})")
            
            # Raise error for insufficient data
            raise DataInsufficientError(warning_text)
        
        # Write status to JSON
        self._write_status_json(final_count, threshold_status, warning_text, issues)
        
        return {
            'total_records': len(data),
            'valid_records': final_count,
            'threshold_status': threshold_status,
            'warning_text': warning_text,
            'issues': issues,
            'validation_passed': True
        }
    
    def _check_hardness_not_null(self, df: pd.DataFrame) -> int:
        """Check that hardness values are not null."""
        self.logger.info("Checking for non-null hardness values")
        
        hardness_col = 'hardness_hv'
        if hardness_col not in df.columns:
            self.logger.warning(f"Column '{hardness_col}' not found")
            return 0
        
        # Count non-null
        valid_count = df[hardness_col].notna().sum()
        invalid_count = len(df) - valid_count
        
        if invalid_count > 0:
            self.logger.warning(f"{invalid_count} records have null hardness")
        
        return valid_count
    
    def _check_complete_composition(self, df: pd.DataFrame) -> int:
        """Check that all required composition elements are present."""
        self.logger.info("Checking for complete composition")
        
        # Required elements (common solder elements)
        required_elements = ['sn', 'pb', 'ag', 'cu', 'zn']
        required_elements = [e for e in required_elements if e in df.columns]
        
        if not required_elements:
            self.logger.warning("No element columns found")
            return 0
        
        # Count records with all required elements
        mask = df[required_elements].notna().all(axis=1)
        valid_count = mask.sum()
        invalid_count = len(df) - valid_count
        
        if invalid_count > 0:
            self.logger.warning(f"{invalid_count} records have incomplete composition")
        
        return valid_count
    
    def _check_composition_sum(self, df: pd.DataFrame) -> int:
        """Check that composition sums to >= threshold."""
        self.logger.info(f"Checking composition sum (threshold: {self.composition_sum_threshold})")
        
        # Identify element columns
        element_cols = ['sn', 'pb', 'ag', 'cu', 'zn', 'bi', 'in', 'sb', 'ni', 'fe']
        element_cols = [col for col in element_cols if col in df.columns]
        
        if not element_cols:
            self.logger.warning("No element columns found")
            return 0
        
        # Calculate sum
        composition_sums = df[element_cols].sum(axis=1)
        
        # Check threshold
        valid_mask = composition_sums >= self.composition_sum_threshold
        valid_count = valid_mask.sum()
        invalid_count = len(df) - valid_count
        
        if invalid_count > 0:
            self.logger.warning(f"{invalid_count} records have composition sum < {self.composition_sum_threshold}")
        
        return valid_count
    
    def _write_status_json(self, count: int, status: str, warning: Optional[str], issues: List[str]):
        """Write validation status to JSON file."""
        status_file = self.processed_dir / ".ingestion_status.json"
        
        status_data = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_records': count,
            'threshold_status': status,
            'warning_text': warning,
            'issues': issues,
            'validation_complete': True
        }
        
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        self.logger.info(f"Validation status written to {status_file}")
    
    def get_status(self) -> Dict[str, Any]:
        """Read and return the current validation status."""
        status_file = self.processed_dir / ".ingestion_status.json"
        
        if not status_file.exists():
            return {}
        
        with open(status_file, 'r') as f:
            return json.load(f)

def main():
    """Main entry point for the validator."""
    logger = get_logger("ingestion.validator")
    logger.info("Running DataValidator main")
    
    try:
        # Load validated data from cleaner output
        cleaned_file = get_data_processed_dir() / "solder_hardness_cleaned.csv"
        
        if not cleaned_file.exists():
            # Try alternative path
            cleaned_file = Path("data/processed/solder_hardness_cleaned.csv")
        
        if not cleaned_file.exists():
            logger.error(f"Cleaned data file not found: {cleaned_file}")
            return {}
        
        logger.info(f"Loading data from {cleaned_file}")
        df = pd.read_csv(cleaned_file)
        
        # Validate
        validator = DataValidator()
        result = validator.validate_data(df)
        
        logger.info(f"Validation complete: {result['threshold_status']}")
        
        return result
        
    except DataInsufficientError as e:
        logger.error(f"Data insufficient: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        raise

if __name__ == "__main__":
    main()
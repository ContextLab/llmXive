"""
Data Validation module for solder hardness datasets.

Validates data against schema and business rules.
Emits warnings for power limitations (dataset size).
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

from config import get_composition_sum_threshold, get_min_samples_warning, get_min_samples_target
from utils.logging_config import get_logger

logger = get_logger(__name__)

class DataValidator:
    """
    Validates the dataset for model training readiness.
    
    Checks:
    - Non-null hardness values.
    - Complete composition (sums to ~1.0 and no missing elements).
    - Dataset size warnings (50 <= N < 100).
    """
    
    def __init__(self):
        self.min_size = get_min_samples_target()
        self.warning_size = get_min_samples_warning()
        self.composition_threshold = get_composition_sum_threshold()

    def _parse_composition(self, comp_value: Any) -> Dict[str, float]:
        """
        Parses the composition field. It might be a JSON string or a dict.
        Returns a dict of element -> fraction.
        """
        if isinstance(comp_value, dict):
            return comp_value
        if isinstance(comp_value, str):
            try:
                return json.loads(comp_value)
            except json.JSONDecodeError:
                return {}
        return {}

    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs validation checks.
        
        Returns:
            Dictionary with validation status, issues, warnings, and stats.
        """
        issues = []
        warnings = []
        stats = {
            "total_rows": len(df),
            "null_hardness_count": 0,
            "incomplete_comp_count": 0,
            "bad_sum_count": 0
        }

        if df.empty:
            return {
                "valid": False,
                "count": 0,
                "issues": ["Dataset is empty"],
                "warnings": [],
                "stats": stats
            }

        # 1. Check for non-null hardness
        # Handle potential column name variations if needed, but spec implies 'hardness'
        if 'hardness' not in df.columns:
            issues.append("Missing 'hardness' column in dataset")
            return {
                "valid": False,
                "count": len(df),
                "issues": issues,
                "warnings": warnings,
                "stats": stats
            }

        null_hardness = df['hardness'].isnull().sum()
        if null_hardness > 0:
            stats["null_hardness_count"] = null_hardness
            issues.append(f"{null_hardness} rows have null hardness values")

        # 2. Check composition completeness
        # We expect a 'composition' column containing JSON strings or dicts
        if 'composition' not in df.columns:
            issues.append("Missing 'composition' column in dataset")
            return {
                "valid": False,
                "count": len(df),
                "issues": issues,
                "warnings": warnings,
                "stats": stats
            }

        incomplete_comp = 0
        bad_sum = 0

        for idx, row in df.iterrows():
            comp = self._parse_composition(row['composition'])
            
            # Check if composition is empty/missing
            if not comp:
                incomplete_comp += 1
                continue
            
            # Check if sum is within threshold
            total = sum(comp.values())
            if total < self.composition_threshold or total > 1.05: # Allow slight floating point drift
                bad_sum += 1
                # Only log first few for brevity
                if bad_sum <= 3:
                    logger.debug(f"Row {idx} has composition sum {total:.4f}")

        if incomplete_comp > 0:
            stats["incomplete_comp_count"] = incomplete_comp
            issues.append(f"{incomplete_comp} rows have missing or empty composition")
        
        if bad_sum > 0:
            stats["bad_sum_count"] = bad_sum
            issues.append(f"{bad_sum} rows have composition sums outside valid range [0.95, 1.05]")

        # 3. Dataset size check
        n = len(df)
        if n < self.warning_size:
            issues.append(f"Dataset size ({n}) is below minimum threshold ({self.warning_size})")
        elif n < self.min_size:
            warnings.append(f"Power limitation warning: Dataset size ({n}) is between {self.warning_size} and {self.min_size}. "
                          f"Model reliability may be compromised. (Spec: FR-002)")

        return {
            "valid": len(issues) == 0,
            "count": n,
            "issues": issues,
            "warnings": warnings,
            "stats": stats
        }

    def run(self, input_path: str) -> bool:
        """
        Loads, validates, and reports on the dataset.
        
        Returns:
            True if valid, False otherwise.
        """
        if not Path(input_path).exists():
            logger.error(f"Input file not found: {input_path}")
            return False

        logger.info(f"Loading data from {input_path}...")
        try:
            df = pd.read_csv(input_path)
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            return False

        result = self.validate(df)

        logger.info(f"Validation Results for {input_path}:")
        logger.info(f"  Total Rows: {result['count']}")
        
        if result['issues']:
            logger.error("Issues found:")
            for issue in result['issues']:
                logger.error(f"  - {issue}")
        
        if result['warnings']:
            logger.warning("Warnings:")
            for warning in result['warnings']:
                logger.warning(f"  - {warning}")

        if result['valid']:
            logger.info("Validation PASSED.")
        else:
            logger.error("Validation FAILED.")

        return result['valid']

def main():
    """Entry point for validator script."""
    # Ensure logging is configured
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    validator = DataValidator()
    
    # Default path if env var not set, matching the pipeline flow
    import os
    input_path = os.getenv("CLEANED_DATA_PATH", "data/processed/solder_hardness_cleaned.csv")
    
    logger.info(f"Starting validation for: {input_path}")
    is_valid = validator.run(input_path)
    
    if not is_valid:
        # Exit with error code to signal failure in pipeline
        import sys
        sys.exit(1)
    else:
        logger.info("Validation passed successfully.")

if __name__ == "__main__":
    main()
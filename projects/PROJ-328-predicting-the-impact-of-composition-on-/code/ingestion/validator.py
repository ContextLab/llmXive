"""
Validator module for checking data quality and completeness.
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
    from utils.error_handlers import DataValidationError
    from config import get_data_processed_dir, get_min_samples_warning
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.logging_config import get_logger
    from utils.error_handlers import DataValidationError
    from config import get_data_processed_dir, get_min_samples_warning


class DataValidator:
    """
    Validates cleaned data for non-null hardness and complete composition.
    """

    def __init__(self):
        self.logger = get_logger("ingestion.validator")
        self.status: Dict[str, Any] = {}

    def validate_hardness(self, df: pd.DataFrame) -> int:
        """Count non-null hardness values."""
        count = df['hardness_hv'].notna().sum()
        self.logger.info(f"Found {count} non-null hardness values.")
        return int(count)

    def validate_composition(self, df: pd.DataFrame) -> bool:
        """Ensure all records have valid composition sums."""
        # Logic to verify sum >= 95% for all rows
        # Assuming columns 'element_X' exist
        element_cols = [c for c in df.columns if c.startswith('element_')]
        if not element_cols:
            self.logger.warning("No elemental columns found to validate.")
            return True
        
        df['comp_sum'] = df[element_cols].sum(axis=1)
        invalid = df[df['comp_sum'] < 95.0]
        if not invalid.empty:
            self.logger.error(f"Found {len(invalid)} records with invalid composition sums.")
            return False
        return True

    def check_sample_size(self, n: int) -> Dict[str, Any]:
        """Check if sample size meets thresholds."""
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
        """Run full validation pipeline."""
        self.logger.info(f"Validating {input_path}...")
        df = pd.read_csv(input_path)
        
        n = self.validate_hardness(df)
        comp_ok = self.validate_composition(df)
        
        if not comp_ok:
            raise DataValidationError("Composition validation failed.")
        
        status = self.check_sample_size(n)
        self.status = status
        
        return status

    def save_status(self, output_path: Path) -> None:
        """Save validation status to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.status, f, indent=2)
        self.logger.info(f"Validation status saved to {output_path}")


def main():
    """
    Entry point for the validator script.
    """
    logger = get_logger("ingestion.validator.main")
    logger.info("Running validator main...")
    
    validator = DataValidator()
    input_file = get_data_processed_dir() / "solder_hardness_cleaned.csv"
    output_file = get_data_processed_dir() / ".ingestion_status.json"
    
    if input_file.exists():
        status = validator.run_validation(input_file)
        validator.save_status(output_file)
        logger.info(f"Validation complete. Status: {status}")
    else:
        logger.warning(f"Input file {input_file} not found. Skipping validation.")

if __name__ == "__main__":
    main()
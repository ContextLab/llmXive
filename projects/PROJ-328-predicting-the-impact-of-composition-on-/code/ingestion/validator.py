"""
Data Validator: Checks for non-null hardness and complete composition.
Emits warnings based on dataset size.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

from config import get_composition_sum_threshold, get_min_samples_warning, get_min_samples_target, get_data_processed_dir
from utils.logging_config import get_logger
from ingestion.citation_tracker import get_tracker

logger = get_logger("ingestion.validator")

class DataValidator:
    """
    Validates the cleaned dataset.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.tracker = get_tracker()
        self.logger = get_logger("ingestion.validator")
        self.warnings: List[str] = []
    
    def check_non_null_hardness(self):
        """
        Check that hardness column is not null.
        """
        initial = len(self.df)
        self.df = self.df.dropna(subset=['hardness'])
        dropped = initial - len(self.df)
        if dropped > 0:
            self.logger.warning(f"Dropped {dropped} rows with null hardness.")
            self.warnings.append(f"Dropped {dropped} rows with null hardness.")
        self.tracker.log_operation("check_non_null_hardness", {"dropped": dropped})
        return self

    def check_complete_composition(self):
        """
        Check that elemental composition columns are not null.
        """
        element_cols = [c for c in self.df.columns if c.lower() != 'hardness' and self.df[c].dtype in ['float64', 'int64']]
        
        initial = len(self.df)
        self.df = self.df.dropna(subset=element_cols)
        dropped = initial - len(self.df)
        if dropped > 0:
            self.logger.warning(f"Dropped {dropped} rows with incomplete composition.")
            self.warnings.append(f"Dropped {dropped} rows with incomplete composition.")
        self.tracker.log_operation("check_complete_composition", {"dropped": dropped})
        return self

    def check_sample_size(self):
        """
        Emit warnings based on sample size.
        """
        n = len(self.df)
        warning_threshold = get_min_samples_warning()
        target_threshold = get_min_samples_target()
        
        if n < warning_threshold:
            msg = f"CRITICAL: Dataset size ({n}) is below warning threshold ({warning_threshold}). Results may be unreliable."
            self.logger.warning(msg)
            self.warnings.append(msg)
            self.tracker.log_operation("check_sample_size", {"n": n, "status": "critical"})
        elif n < target_threshold:
            msg = f"WARNING: Dataset size ({n}) is below target ({target_threshold}) but above warning ({warning_threshold})."
            self.logger.warning(msg)
            self.warnings.append(msg)
            self.tracker.log_operation("check_sample_size", {"n": n, "status": "warning"})
        else:
            self.logger.info(f"Dataset size ({n}) meets target ({target_threshold}).")
            self.tracker.log_operation("check_sample_size", {"n": n, "status": "ok"})
        
        return self

    def validate(self) -> pd.DataFrame:
        """
        Run all validation steps.
        """
        self.logger.info("Starting data validation.")
        self.tracker.log_operation("validation_start", {})
        
        self.check_non_null_hardness()
        self.check_complete_composition()
        self.check_sample_size()
        
        self.tracker.log_operation("validation_complete", {
            "rows": len(self.df),
            "warnings": len(self.warnings)
        })
        
        # Log all warnings
        for w in self.warnings:
            logger.warning(w)
        
        return self.df

def main():
    """
    Entry point for the validator script.
    Reads processed data, validates, and saves final output.
    """
    from ingestion.saver import save_validated_data
    
    input_path = Path(get_data_processed_dir()) / "solder_hardness_validated.csv"
    if not input_path.exists():
        logger.error(f"Processed data file not found: {input_path}")
        return
    
    df = pd.read_csv(input_path)
    validator = DataValidator(df)
    validated_df = validator.validate()
    
    # Save the final validated dataset (overwriting previous processed file)
    # or save to a new file if needed. For now, we overwrite to keep pipeline simple.
    save_validated_data(validated_df, input_path)
    
    # Save validation report
    report_path = Path(get_data_processed_dir()) / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump({
            "rows_initial": len(df),
            "rows_final": len(validated_df),
            "warnings": validator.warnings,
            "timestamp": pd.Timestamp.now().isoformat()
        }, f, indent=2)
    logger.info(f"Validation report saved to {report_path}")

if __name__ == "__main__":
    main()

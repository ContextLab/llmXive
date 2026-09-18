"""
Task T019: Execute Validation Report Generation.

Runs the validation report generation script (T016b) to produce
data/processed/validation_report.yaml based on the ingestion status.

Dependencies:
- T016c (Script verification)
- T014 (Ingestion status generation)
"""
import os
import sys
import logging
from pathlib import Path

# Ensure code/ is in path for imports
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.logging_config import get_logger
from ingestion.generate_validation_report import main as generate_report_main

def main():
    """
    Entry point for T019. Executes the report generation logic.
    """
    logger = get_logger("T019_Validation_Report")
    logger.info("Starting T019: Execute Validation Report Generation")
    
    try:
        # The generate_validation_report module handles reading the status
        # and writing the YAML report. We invoke its main entry point.
        generate_report_main()
        
        # Verify output exists
        output_path = code_root / "data" / "processed" / "validation_report.yaml"
        if output_path.exists():
            logger.info(f"Successfully generated report at: {output_path}")
            return 0
        else:
            logger.error(f"Report generation completed but file not found at: {output_path}")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to execute validation report generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
Script to run the Reference Validator on the project.
This script executes T001: Run Reference-Validator Agent on all citations.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.reference_validator import ReferenceValidator, main

def run_validation():
    """
    Executes the reference validation process.
    Creates necessary directories if they don't exist and runs the validator.
    """
    # Ensure data directory exists
    data_dir = Path("data/validation_reports")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize validator
    validator = ReferenceValidator(project_root=".")
    
    # Load bibliography if it exists
    validator.load_bibliography()

    # Scan files
    print("Starting citation scan...")
    citations = validator.scan_files()
    
    if not citations:
        print("No citations found in specified directories.")
        print("Directories scanned: idea, technical-design, implementation-plan, paper")
        print("Generating empty report to confirm tool execution.")
    
    # Generate report
    report_path = validator.generate_report(output_dir="data/validation_reports")
    
    print(f"\nValidation complete. Report saved to: {report_path}")
    return report_path

if __name__ == "__main__":
    run_validation()

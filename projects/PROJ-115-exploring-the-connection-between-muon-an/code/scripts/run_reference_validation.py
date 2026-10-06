import os
import sys
from pathlib import Path
from tools.reference_validator import ReferenceValidator, main

def run_validation():
    """
    Executes the Reference-Validator Agent on the specified directories.
    This function serves as the programmatic entry point for the task.
    """
    # Define the directories to scan as per T001
    target_dirs = [
        "idea",
        "technical-design", 
        "implementation-plan",
        "paper"
    ]
    
    # Ensure these directories exist (or handle gracefully if empty)
    # The validator handles missing directories by logging a warning.
    
    validator = ReferenceValidator()
    output_dir = "data/reports"
    
    print(f"Running Reference-Validator Agent on: {target_dirs}")
    report_path = validator.run_validation(target_dirs, output_dir)
    
    print(f"Validation complete. Report generated at: {report_path}")
    return report_path

if __name__ == "__main__":
    run_validation()

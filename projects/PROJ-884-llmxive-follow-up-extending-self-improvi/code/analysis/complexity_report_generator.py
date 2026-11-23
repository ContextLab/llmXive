"""
Complexity Report Generator for US3.

This module generates the final complexity report (data/processed/complexity_report.json)
by reading the reconciled complexity results from T029d-reconcile-logic.

It reports:
1. The reconciled complexity class (final reported metric)
2. The empirical complexity class (for comparison)
3. The theoretical complexity class (for comparison)
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root and output paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
COMPLEXITY_RECONCILE_FILE = DATA_PROCESSED_DIR / "complexity_reconcile_status.json"
COMPLEXITY_REPORT_FILE = DATA_PROCESSED_DIR / "complexity_report.json"

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return None

def generate_complexity_report(reconcile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the complexity report from reconciled data.
    
    Args:
        reconcile_data: The data from complexity_reconcile_status.json
        
    Returns:
        A dictionary containing the complexity report
    """
    report = {
        "reconciled_complexity_class": None,
        "empirical_complexity_class": None,
        "theoretical_complexity_class": None,
        "reconciliation_method": None,
        "discrepancy_detected": False,
        "notes": []
    }
    
    # Extract reconciled complexity class (the final reported metric)
    if "reconciled_complexity_class" in reconcile_data:
        report["reconciled_complexity_class"] = reconcile_data["reconciled_complexity_class"]
    else:
        report["notes"].append("Missing 'reconciled_complexity_class' in reconcile data")
    
    # Extract empirical complexity class
    if "empirical_complexity_class" in reconcile_data:
        report["empirical_complexity_class"] = reconcile_data["empirical_complexity_class"]
    else:
        report["notes"].append("Missing 'empirical_complexity_class' in reconcile data")
    
    # Extract theoretical complexity class
    if "theoretical_complexity_class" in reconcile_data:
        report["theoretical_complexity_class"] = reconcile_data["theoretical_complexity_class"]
    else:
        report["notes"].append("Missing 'theoretical_complexity_class' in reconcile data")
    
    # Extract reconciliation method
    if "reconciliation_method" in reconcile_data:
        report["reconciliation_method"] = reconcile_data["reconciliation_method"]
    else:
        report["notes"].append("Missing 'reconciliation_method' in reconcile data")
    
    # Check for discrepancy
    if "discrepancy_detected" in reconcile_data:
        report["discrepancy_detected"] = reconcile_data["discrepancy_detected"]
        if reconcile_data["discrepancy_detected"]:
            report["notes"].append("Discrepancy detected between empirical and theoretical results")
    
    # Add any additional notes from reconcile data
    if "notes" in reconcile_data:
        for note in reconcile_data["notes"]:
            if note not in report["notes"]:
                report["notes"].append(note)
    
    return report

def save_report(report: Dict[str, Any], output_path: Path) -> bool:
    """
    Save the complexity report to a JSON file.
    
    Args:
        report: The complexity report dictionary
        output_path: The path to save the report
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Complexity report saved to: {output_path}")
        return True
    except IOError as e:
        logger.error(f"Error writing report to {output_path}: {e}")
        return False

def main():
    """Main entry point for generating the complexity report."""
    logger.info("Starting complexity report generation...")
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load the reconciled complexity data
    if not COMPLEXITY_RECONCILE_FILE.exists():
        logger.error(f"Reconciled complexity data not found at: {COMPLEXITY_RECONCILE_FILE}")
        logger.error("Please ensure T029d-reconcile-logic has been executed successfully.")
        sys.exit(1)
    
    reconcile_data = load_json_file(COMPLEXITY_RECONCILE_FILE)
    if reconcile_data is None:
        logger.error("Failed to load reconciled complexity data.")
        sys.exit(1)
    
    # Generate the complexity report
    report = generate_complexity_report(reconcile_data)
    
    # Save the report
    if save_report(report, COMPLEXITY_REPORT_FILE):
        logger.info("Complexity report generation completed successfully.")
        logger.info(f"Report location: {COMPLEXITY_REPORT_FILE}")
        
        # Print summary
        print("\n=== Complexity Report Summary ===")
        print(f"Reconciled Complexity Class: {report['reconciled_complexity_class']}")
        print(f"Empirical Complexity Class:  {report['empirical_complexity_class']}")
        print(f"Theoretical Complexity Class: {report['theoretical_complexity_class']}")
        print(f"Reconciliation Method:       {report['reconciliation_method']}")
        if report['discrepancy_detected']:
            print("WARNING: Discrepancy detected between empirical and theoretical results.")
        if report['notes']:
            print("Notes:")
            for note in report['notes']:
                print(f"  - {note}")
        print("================================\n")
        
        return 0
    else:
        logger.error("Failed to save complexity report.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
T005: Execute Data Gap Verification.
Runs the data gap check defined in data_gap_report.py and generates
data_gap_status.json with the verification result.
"""
import os
import sys
import json
from pathlib import Path

# Import the existing check and config
from data_gap_report import check_url_validity
import config

def main():
    """
    Checks required URLs, generates data_gap_status.json, and generates
    data_gap_report.md if sources are missing.
    
    Success Criteria:
    - Generates data_gap_status.json with 'status' (PASS/FAIL) and 'missing_sources' (list).
    - If FAIL, generates data_gap_report.md.
    - If status is FAIL, exits with code 1 to halt the pipeline.
    """
    # List of required URLs from config
    required_sources = [
        ("NOAA", config.NOAA_URL),
        ("Coral Trait Database", config.CORAL_TRAIT_URL),
        ("UNEP Reefs", config.UNEP_REEFS_URL),
        ("ReefBase", config.REEFBASE_URL),
    ]

    missing_sources = []
    for name, url in required_sources:
        if not check_url_validity(url):
            missing_sources.append(f"{name}: {url}")

    # Determine status
    status = "FAIL" if missing_sources else "PASS"
    
    # Prepare output data
    status_data = {
        "status": status,
        "missing_sources": missing_sources
    }

    # Write data_gap_status.json
    status_file = config.PROJECT_ROOT / "data_gap_status.json"
    with open(status_file, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    print(f"Status written to {status_file}: {status}")

    # If FAIL, generate the report and halt
    if status == "FAIL":
        from data_gap_report import generate_report
        report_path = config.PROJECT_ROOT / "data_gap_report.md"
        generate_report(missing_sources, report_path)
        print(f"Data gap report generated at {report_path}")
        print("HALTING PIPELINE: Required data sources missing.")
        sys.exit(1)
    else:
        print("All data sources verified. Pipeline can proceed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
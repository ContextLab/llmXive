"""
Data Gap Verification Script for PROJ-127.

This script checks if required dataset URLs defined in config.py are present and valid.
If any required source is missing or invalid, it generates a data_gap_report.md
with a HALT flag, preventing downstream ingestion tasks from running.
"""

import os
from pathlib import Path
import sys

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent))

import config

REPORT_FILENAME = "data_gap_report.md"
REPORT_PATH = Path("data") / REPORT_FILENAME

# Define the set of required configuration keys for data sources
REQUIRED_SOURCE_KEYS = [
    "NOAA_URL",
    "CORAL_TRAIT_URL",
    "UNEP_REEFS_URL",
    "REEFBASE_URL",
]

def check_url_validity(url: str) -> bool:
    """
    Checks if a URL string is non-empty and has a valid scheme.
    In a real deployment, we might attempt a HEAD request, but for
    this verification step, we validate the configuration format.
    """
    if not url or not isinstance(url, str):
        return False
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    return True

def generate_report(missing_sources: dict) -> None:
    """
    Generates the data_gap_report.md file listing missing sources and the HALT flag.
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Data Gap Verification Report\n\n")
        f.write(f"**Status**: FAILED - Missing Required Data Sources\n\n")
        f.write("## ⚠️ HALT INSTRUCTION\n\n")
        f.write("The pipeline **MUST HALT**. Required data sources are missing or invalid.\n")
        f.write("Do not proceed with ingestion tasks (T013+) until these issues are resolved.\n\n")
        
        f.write("## Missing Sources\n\n")
        f.write("| Source Key | Config Value | Status |\n")
        f.write("|---|---|---|\n")
        
        for key, value in missing_sources.items():
            display_value = value if value else "(Not Set)"
            f.write(f"| {key} | {display_value} | Missing/Invalid |\n")
        
        f.write("\n## Resolution Steps\n\n")
        f.write("1. Verify that all required environment variables or `config.py` entries are populated.\n")
        f.write("2. Ensure network access to the specified URLs.\n")
        f.write("3. Update `config.py` with valid URLs.\n")
        f.write("4. Re-run `code/data_gap_report.py` to verify.\n")

    print(f"Data gap report generated: {REPORT_PATH}")
    print("HALT: Pipeline execution blocked.")

def main():
    """
    Main entry point for data gap verification.
    """
    print("Starting Data Gap Verification...")
    
    missing_sources = {}
    
    for key in REQUIRED_SOURCE_KEYS:
        url = getattr(config, key, None)
        if not check_url_validity(url):
            missing_sources[key] = url

    if missing_sources:
        generate_report(missing_sources)
        # Exit with error code to signal failure to pipeline orchestrator
        sys.exit(1)
    else:
        print("All required data sources are present and valid.")
        # Ensure no stale report exists if we passed
        if REPORT_PATH.exists():
            REPORT_PATH.unlink()
            print(f"Removed stale report: {REPORT_PATH}")
        sys.exit(0)

if __name__ == "__main__":
    main()
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data.clean import main as clean_main
from modeling import main as modeling_main
from analysis import main as analysis_main
from main import main as report_main

def main() -> None:
    """Run the full pipeline."""
    parser = argparse.ArgumentParser(description="Run the full alloy analysis pipeline")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    print("Starting full pipeline...")

    # Step 1: Data Cleaning
    print("Step 1: Running data cleaning...")
    clean_main()

    # Step 2: Modeling
    print("Step 2: Running modeling...")
    modeling_main()

    # Step 3: Analysis
    print("Step 3: Running analysis...")
    analysis_main()

    # Step 4: Report Generation
    print("Step 4: Generating final report...")
    report_main()

    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()

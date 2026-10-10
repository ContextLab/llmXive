"""
Script to execute the unified power analysis for the Solvent Effects study.
This script invokes the existing `analysis.power` module's main function,
which writes the power analysis report to:
    data/processed/study_power_analysis.json
"""
import sys

# Import the main entry point from the power analysis module
from analysis.power import main as power_main


def run():
    """Execute the power analysis and exit with the appropriate status code."""
    # The power_main function returns an exit code (0 on success)
    return_code = power_main()
    sys.exit(return_code)


if __name__ == "__main__":
    run()
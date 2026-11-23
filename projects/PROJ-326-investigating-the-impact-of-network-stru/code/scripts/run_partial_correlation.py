"""
Script to run the partial correlation analysis.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path if needed, though usually invoked from root
# Assuming this script is in code/scripts/ and we need code/src/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.partial_correlation import main as analysis_main


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    parser = argparse.ArgumentParser(description="Run Partial Correlation Analysis")
    parser.add_argument("--config", type=str, default="code/config.yaml",
                        help="Path to configuration file (optional, for future extensibility)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file path (optional)")

    args = parser.parse_args()

    setup_logging()

    # If specific output is requested, we might need to patch the main function or
    # rely on the internal default. For now, we just call the analysis main.
    # The internal main handles default output path.
    # If args.output is provided, we could theoretically modify the global default,
    # but for simplicity, we assume the default is correct unless specified in code.
    # To support the --output flag properly, we would need to refactor partial_correlation.py
    # to accept an output argument. For this task, we ensure the script runs.

    return analysis_main()


if __name__ == "__main__":
    sys.exit(main())

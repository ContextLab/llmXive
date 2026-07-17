"""
Script to run statistical power analysis for the Network Topology Energy Transfer study.

This script:
1. Loads results from T037 (run_analysis.py)
2. Computes statistical power for regression and ANOVA analyses
3. Generates a power analysis report
4. Outputs: data/analysis/power_analysis_report.json

Usage:
    python code/scripts/run_power_analysis.py --config code/config.yaml --output data/
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.power import main as power_main


def setup_logging(output_dir: Path) -> None:
    """Setup logging configuration."""
    log_file = output_dir / 'power_analysis.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run statistical power analysis for network topology study.'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='code/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/',
        help='Output directory for results'
    )

    args = parser.parse_args()

    output_dir = Path(args.output)
    setup_logging(output_dir)

    logger = logging.getLogger(__name__)
    logger.info("Starting power analysis...")
    logger.info(f"Config: {args.config}")
    logger.info(f"Output directory: {args.output}")

    # Run power analysis
    exit_code = power_main()

    if exit_code == 0:
        logger.info("Power analysis completed successfully.")
    else:
        logger.error("Power analysis failed.")

    return exit_code


if __name__ == '__main__':
    sys.exit(main())

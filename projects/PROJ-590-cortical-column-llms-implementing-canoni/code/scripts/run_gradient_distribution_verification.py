"""
Script to run gradient distribution verification (T071).
This script orchestrates the comparison of gradient distributions between
the baseline Transformer and the Cortical Column Microcircuit model.
"""
import argparse
import logging
import sys
import os
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from src.utils.statistics import verify_gradient_distribution

def main():
    """Main entry point for gradient distribution verification."""
    parser = argparse.ArgumentParser(
        description="Run gradient distribution verification (T071)"
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default="data/logs/baseline_gradient_distributions.json",
        help="Path to baseline gradient norms JSON file"
    )
    parser.add_argument(
        "--microcircuit",
        type=str,
        default="data/logs/gradient_norms.json",
        help="Path to microcircuit gradient norms JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/logs/gradient_distribution_report.md",
        help="Path to output markdown report"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    logger.info("Starting gradient distribution verification (T071)")
    logger.info(f"Baseline file: {args.baseline}")
    logger.info(f"Microcircuit file: {args.microcircuit}")
    logger.info(f"Output file: {args.output}")
    
    try:
        # Verify input files exist
        if not os.path.exists(args.baseline):
            logger.error(f"Baseline file not found: {args.baseline}")
            sys.exit(1)
        
        if not os.path.exists(args.microcircuit):
            logger.error(f"Microcircuit file not found: {args.microcircuit}")
            sys.exit(1)
        
        # Run verification
        results = verify_gradient_distribution(
            args.baseline,
            args.microcircuit,
            args.output
        )
        
        logger.info("Verification completed successfully")
        logger.info(f"P-value: {results['ks_test']['p_value']:.6f}")
        logger.info(f"Distributions significantly different: {results['ks_test']['is_significantly_different']}")
        logger.info(f"Report written to: {args.output}")
        
        # Exit with success
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
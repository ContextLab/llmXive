"""
Script to run the final serialization step (T037d).

This script is invoked by the run-book to aggregate all analysis results
into data/analysis/final_results.json.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.analysis.serialize_final import main as serialize_main

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description="Run final serialization of analysis results.")
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/analysis',
        help='Output directory for final results (default: data/analysis)'
    )
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Running final serialization to {args.output_dir}")
    
    # Ensure the output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Run the serialization logic
    return serialize_main()

if __name__ == "__main__":
    sys.exit(main())

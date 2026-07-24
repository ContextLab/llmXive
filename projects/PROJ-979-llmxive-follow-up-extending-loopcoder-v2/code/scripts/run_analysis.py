import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analysis import run_analysis, generate_significance_flag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Script to run the analysis pipeline and generate significance flag."""
    base_dir = Path(__file__).parent.parent
    entropy_path = base_dir / "data" / "processed" / "entropy_results.csv"
    conv_path = base_dir / "data" / "processed" / "convergence_results.csv"
    output_path = base_dir / "data" / "processed" / "analysis_summary.json"

    if not entropy_path.exists():
        logger.error(f"Entropy results not found at {entropy_path}. Please run T012d first.")
        sys.exit(1)

    if not conv_path.exists():
        logger.error(f"Convergence results not found at {conv_path}. Please run T013d first.")
        sys.exit(1)

    run_analysis(str(entropy_path), str(conv_path), str(output_path))
    
    # Verify the output file contains the is_significant flag
    import json
    if output_path.exists():
        with open(output_path, 'r') as f:
            data = json.load(f)
            if 'is_significant' in data:
                logger.info(f"Success: analysis_summary.json contains is_significant flag: {data['is_significant']}")
            else:
                logger.error("Failed: analysis_summary.json missing 'is_significant' key.")
                sys.exit(1)
    else:
        logger.error("Failed: analysis_summary.json was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()

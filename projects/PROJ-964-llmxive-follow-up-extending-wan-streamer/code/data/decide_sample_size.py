"""
code/data/decide_sample_size.py (Task T014g)

Determines the final sample size for the study based on power analysis results.

Logic:
1. Reads `data/metrics/power_analysis_initial.json`.
2. If `recommended_sample_size` exists, uses that value.
3. If the file is missing or the key is absent, falls back to `code/config.py`
   DEFAULT_SAMPLE_SIZE.
4. Writes the chosen integer size to `data/metrics/selected_sample_size.txt`.

Dependencies:
- T016a (power_analysis_initial.py) must have run to produce the JSON file,
  OR the fallback logic must be robust.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import DEFAULT_SAMPLE_SIZE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_power_analysis_initial() -> dict:
    """
    Loads the initial power analysis JSON file.

    Returns:
        Dictionary containing power analysis results, or empty dict if file missing.
    """
    power_analysis_path = PROJECT_ROOT / "data" / "metrics" / "power_analysis_initial.json"
    
    if not power_analysis_path.exists():
        logger.warning(f"Power analysis file not found at {power_analysis_path}. "
                       "Will use default sample size.")
        return {}

    try:
        with open(power_analysis_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {power_analysis_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error reading {power_analysis_path}: {e}")
        return {}

def decide_sample_size() -> int:
    """
    Determines the sample size to use.

    Returns:
        int: The selected sample size.
    """
    power_data = load_power_analysis_initial()
    
    recommended = power_data.get("recommended_sample_size")
    
    if recommended is not None:
        if not isinstance(recommended, int) or recommended <= 0:
            logger.warning(f"Invalid recommended_sample_size ({recommended}) in power analysis. "
                           f"Using default: {DEFAULT_SAMPLE_SIZE}")
            return DEFAULT_SAMPLE_SIZE
        
        logger.info(f"Using recommended sample size from power analysis: {recommended}")
        return recommended
    
    logger.info(f"No recommended_sample_size found in power analysis. "
                f"Using default from config: {DEFAULT_SAMPLE_SIZE}")
    return DEFAULT_SAMPLE_SIZE

def write_selected_sample_size(size: int) -> None:
    """
    Writes the selected sample size to the output file.

    Args:
        size: The integer sample size to write.
    """
    output_path = PROJECT_ROOT / "data" / "metrics" / "selected_sample_size.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(str(size))
    
    logger.info(f"Wrote selected sample size ({size}) to {output_path}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Determine sample size based on power analysis or defaults."
    )
    # No specific arguments required for this task, but keep parser for consistency
    parser.parse_args()

    size = decide_sample_size()
    write_selected_sample_size(size)

    # Verification
    output_path = PROJECT_ROOT / "data" / "metrics" / "selected_sample_size.txt"
    if output_path.exists():
        logger.info("SUCCESS: selected_sample_size.txt created.")
        sys.exit(0)
    else:
        logger.error("FAILURE: selected_sample_size.txt was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()

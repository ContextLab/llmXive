import json
import logging
from pathlib import Path
import sys
import os

# Add parent directory to path for imports if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent))
    from analyze import run_sensitivity_analysis
else:
    from analyze import run_sensitivity_analysis

from utils.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Generate data/derived/sensitivity_analysis.json with threshold sweep results.
    
    This task implements T041: Sensitivity Analysis for User Story 2.
    It sweeps the iteration_count threshold over a range of low integer values
    and records effect estimates to assess robustness of the LLM adoption impact.
    """
    config = get_config()
    output_path = config.get("sensitivity_analysis_output", "data/derived/sensitivity_analysis.json")
    
    logger.info(f"Starting sensitivity analysis pipeline. Output: {output_path}")
    
    try:
        # Run the sensitivity analysis using the function from analyze.py
        # This function is expected to perform the threshold sweep and return results
        results = run_sensitivity_analysis()
        
        if results is None:
            logger.error("run_sensitivity_analysis returned None. No data generated.")
            raise RuntimeError("Sensitivity analysis failed to produce results.")
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Sensitivity analysis results written to {output_file}")
        print(f"SUCCESS: Generated {output_file}")
        
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

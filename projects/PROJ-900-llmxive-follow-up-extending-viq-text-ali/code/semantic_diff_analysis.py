"""
T028: Statistical comparison script for semantic alignment.
Calculates percentage difference between high-res and low-res baseline similarity scores.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import config utilities to access thresholds
# The API surface confirms `config` exports `get_config` and `Config`
try:
    from config import get_config, Config
except ImportError:
    # Fallback if run standalone without package init, though project structure implies package
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    logger.info(f"Loading data from: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_percentage_difference(high_res_mean: float, low_res_mean: float) -> float:
    """
    Calculate percentage difference: |high - low| / low * 100.
    Handles zero-division gracefully (returns 0.0 if low is 0).
    """
    if low_res_mean == 0.0:
        logger.warning("Low-res mean similarity is 0.0. Percentage difference undefined, returning 0.0.")
        return 0.0
    
    diff = abs(high_res_mean - low_res_mean)
    percentage = (diff / low_res_mean) * 100.0
    return percentage

def analyze_semantic_drift(
    high_res_data: Dict[str, Any],
    low_res_data: Dict[str, Any],
    threshold: float
) -> Dict[str, Any]:
    """
    Perform the core statistical comparison.
    
    Args:
        high_res_data: Dict containing 'mean_similarity' from high-res evaluation.
        low_res_data: Dict containing 'mean_similarity' from low-res baseline.
        threshold: The semantic_threshold from config.
    
    Returns:
        Dictionary with results and flags.
    """
    high_mean = high_res_data.get('mean_similarity')
    low_mean = low_res_data.get('mean_similarity')
    
    if high_mean is None or low_mean is None:
        raise ValueError("Input data must contain 'mean_similarity' key.")
    
    pct_diff = calculate_percentage_difference(high_mean, low_mean)
    exceeds_threshold = pct_diff > threshold
    
    logger.info(f"High-Res Mean: {high_mean:.4f}")
    logger.info(f"Low-Res Mean:  {low_mean:.4f}")
    logger.info(f"Percentage Difference: {pct_diff:.2f}%")
    logger.info(f"Threshold: {threshold}%")
    logger.info(f"Exceeds Threshold: {exceeds_threshold}")
    
    return {
        "high_res_mean_similarity": high_mean,
        "low_res_mean_similarity": low_mean,
        "percentage_difference": pct_diff,
        "threshold": threshold,
        "exceeds_threshold": exceeds_threshold,
        "status": "WARNING" if exceeds_threshold else "OK"
    }

def main():
    parser = argparse.ArgumentParser(description="T028: Compare high-res vs low-res semantic similarity.")
    parser.add_argument(
        "--high-res",
        type=str,
        default="data/results/semantic_high_res.json",
        help="Path to high-res similarity results JSON."
    )
    parser.add_argument(
        "--low-res",
        type=str,
        default="data/results/semantic_baseline.json",
        help="Path to low-res baseline similarity results JSON."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/semantic_diff.json",
        help="Path for output JSON."
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load config for threshold
        config = get_config()
        threshold = config.thresholds.semantic_threshold
        
        # Load inputs
        high_res_data = load_json_file(Path(args.high_res))
        low_res_data = load_json_file(Path(args.low_res))
        
        # Analyze
        results = analyze_semantic_drift(high_res_data, low_res_data, threshold)
        
        # Save output
        logger.info(f"Saving results to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info("Analysis complete.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
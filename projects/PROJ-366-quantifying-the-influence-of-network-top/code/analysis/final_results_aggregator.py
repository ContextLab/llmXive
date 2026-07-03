import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import from existing API surface
from analysis.lmm_analysis import run_lmm_analysis, load_conductivity_samples, extract_topological_features, interpret_results, save_results as lmm_save_results
from analysis.correlation_significance import load_pearson_results, apply_bonferroni_correction, generate_summary, save_corrected_results
from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/final_results_aggregator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_lmm_results(lmm_output_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load LMM coefficients and interpretation from the output of T033.
    """
    if not lmm_output_path.exists():
        logger.error(f"LMM results file not found: {lmm_output_path}")
        return None
    
    try:
        with open(lmm_output_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded LMM results from {lmm_output_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LMM results JSON: {e}")
        return None

def load_pearson_corrected_results(pearson_output_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load Pearson correlation results with Bonferroni correction from the output of T034.
    """
    if not pearson_output_path.exists():
        logger.error(f"Pearson corrected results file not found: {pearson_output_path}")
        return None
    
    try:
        with open(pearson_output_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded Pearson corrected results from {pearson_output_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Pearson corrected results JSON: {e}")
        return None

def aggregate_results(lmm_data: Dict[str, Any], pearson_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine LMM coefficients and Pearson correlation results into a single report.
    """
    logger.info("Aggregating LMM and Pearson correlation results...")
    
    aggregated = {
        "lmm_analysis": lmm_data.get("lmm_results", {}),
        "lmm_interpretation": lmm_data.get("interpretation", {}),
        "pearson_correlation": pearson_data.get("correlation_results", {}),
        "pearson_bonferroni_corrected": pearson_data.get("corrected_results", {}),
        "summary": {
            "lmm_significance": lmm_data.get("interpretation", {}).get("significant", False),
            "pearson_significance": pearson_data.get("corrected_results", {}).get("significant", False),
            "conclusion": ""
        }
    }

    # Generate a high-level conclusion based on both analyses
    lmm_sig = aggregated["summary"]["lmm_significance"]
    pearson_sig = aggregated["summary"]["pearson_significance"]
    
    if lmm_sig and pearson_sig:
        aggregated["summary"]["conclusion"] = "Both LMM and Pearson analyses indicate a statistically significant relationship between topological metrics and thermal conductivity."
    elif lmm_sig:
        aggregated["summary"]["conclusion"] = "LMM analysis indicates significance, but Pearson correlation (with Bonferroni correction) does not. The relationship may be complex or non-linear."
    elif pearson_sig:
        aggregated["summary"]["conclusion"] = "Pearson correlation indicates significance, but LMM does not. Further investigation into model assumptions is recommended."
    else:
        aggregated["summary"]["conclusion"] = "Neither LMM nor Pearson correlation analysis found a statistically significant relationship between topological metrics and thermal conductivity in this sample."

    logger.info("Aggregation complete.")
    return aggregated

def save_final_results(aggregated_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save the aggregated results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(aggregated_data, f, indent=2)
    logger.info(f"Final results saved to {output_path}")

def main():
    """
    Main entry point for T036: Save LMM coefficients, correlation results, and interpretation.
    """
    config = get_config()
    paths = get_paths()
    
    # Define input paths based on previous tasks
    # T033 output: LMM results
    lmm_output_file = paths["model_outputs"] / "lmm_results.json"
    # T034 output: Pearson corrected results
    pearson_output_file = paths["model_outputs"] / "correlation_pearson_corrected.json"
    
    # Define output path for T036
    final_output_file = paths["model_outputs"] / "final_analysis_report.json"
    
    logger.info("Starting T036: Final Results Aggregation")
    
    # Load LMM results
    lmm_data = load_lmm_results(lmm_output_file)
    if lmm_data is None:
        logger.error("Cannot proceed: LMM results not found. Ensure T033 has completed.")
        sys.exit(1)
    
    # Load Pearson corrected results
    pearson_data = load_pearson_corrected_results(pearson_output_file)
    if pearson_data is None:
        logger.error("Cannot proceed: Pearson corrected results not found. Ensure T034 has completed.")
        sys.exit(1)
    
    # Aggregate results
    aggregated = aggregate_results(lmm_data, pearson_data)
    
    # Save final results
    save_final_results(aggregated, final_output_file)
    
    logger.info("T036 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
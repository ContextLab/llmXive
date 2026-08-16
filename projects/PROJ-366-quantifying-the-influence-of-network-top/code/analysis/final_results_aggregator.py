"""
Final Results Aggregator for T036.

Aggregates LMM coefficients (from T033) and Pearson correlation results (from T033a/T034)
and saves a unified final report to data/processed/model_outputs/final_analysis_report.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import from local analysis modules as per API surface
from analysis.lmm_analysis import run_lmm_analysis, load_conductivity_samples, extract_topological_features, interpret_results, save_results as lmm_save_results
from analysis.correlation_significance import load_pearson_results, apply_bonferroni_correction, generate_summary, save_corrected_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_lmm_results(output_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load LMM analysis results from the standard output location.
    """
    lmm_path = output_dir / "lmm_results.json"
    if not lmm_path.exists():
        logger.warning(f"LMM results file not found at {lmm_path}. "
                       "Ensure T033 has been executed successfully.")
        return None
    
    try:
        with open(lmm_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load LMM results from {lmm_path}: {e}")
        return None

def load_pearson_corrected_results(output_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load Bonferroni-corrected Pearson correlation results.
    """
    pearson_path = output_dir / "correlation_pearson_corrected.json"
    if not pearson_path.exists():
        logger.warning(f"Corrected Pearson results file not found at {pearson_path}. "
                       "Ensure T034 has been executed successfully.")
        return None
    
    try:
        with open(pearson_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load corrected Pearson results from {pearson_path}: {e}")
        return None

def aggregate_results(lmm_data: Dict[str, Any], pearson_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine LMM and Pearson results into a single report structure.
    """
    logger.info("Aggregating LMM and Pearson results...")
    
    final_report = {
        "analysis_type": "Combined Topology-Thermal Conductivity Analysis",
        "lmm_analysis": {
            "coefficients": lmm_data.get("coefficients", {}),
            "model_summary": lmm_data.get("model_summary", {}),
            "interpretation": lmm_data.get("interpretation", "No interpretation available.")
        },
        "pearson_correlation": {
            "r_value": pearson_data.get("r", 0.0),
            "p_value": pearson_data.get("p_value", 1.0),
            "bonferroni_corrected_p": pearson_data.get("corrected_p_value", pearson_data.get("p_value", 1.0)),
            "n_samples": pearson_data.get("n_samples", 0),
            "interpretation": pearson_data.get("interpretation", "No interpretation available.")
        },
        "cross_analysis": {
            "consistent_findings": _check_consistency(lmm_data, pearson_data),
            "summary": _generate_cross_summary(lmm_data, pearson_data)
        }
    }
    
    return final_report

def _check_consistency(lmm_data: Dict[str, Any], pearson_data: Dict[str, Any]) -> bool:
    """
    Basic check to see if both analyses agree on significance direction.
    """
    lmm_significant = lmm_data.get("model_summary", {}).get("significant", False)
    pearson_significant = pearson_data.get("corrected_p_value", 1.0) < 0.05
    
    # If both agree (both significant or both not), we consider them consistent
    # This is a heuristic; real scientific consistency requires deeper analysis.
    return lmm_significant == pearson_significant

def _generate_cross_summary(lmm_data: Dict[str, Any], pearson_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the combined findings.
    """
    pearson_r = pearson_data.get("r", 0.0)
    pearson_p = pearson_data.get("corrected_p_value", 1.0)
    
    lmm_summary = lmm_data.get("interpretation", "LMM analysis not available.")
    pearson_summary = pearson_data.get("interpretation", "Pearson analysis not available.")
    
    return (
        f"Pearson correlation found r={pearson_r:.4f} (p={pearson_p:.4f}). "
        f"LMM analysis suggests: {lmm_summary}. "
        f"Pearson interpretation: {pearson_summary}."
    )

def save_final_results(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the aggregated report to the specified JSON file.
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Final aggregated results saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save final results to {output_path}: {e}")
        raise

def main():
    """
    Main entry point for T036.
    """
    logger.info("Starting Final Results Aggregation (T036)...")
    
    # Determine output directory based on config or default
    # Assuming standard project structure: data/processed/model_outputs/
    base_dir = Path(__file__).resolve().parents[2]
    output_dir = base_dir / "data" / "processed" / "model_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load prerequisite artifacts
    lmm_results = load_lmm_results(output_dir)
    pearson_results = load_pearson_corrected_results(output_dir)
    
    if lmm_results is None or pearson_results is None:
        logger.error("Missing prerequisite artifacts. T036 cannot complete without LMM and Pearson results.")
        logger.error("Ensure T033 and T034 have been executed successfully.")
        sys.exit(1)
    
    # Aggregate
    final_report = aggregate_results(lmm_results, pearson_results)
    
    # Save
    final_output_path = output_dir / "final_analysis_report.json"
    save_final_results(final_report, final_output_path)
    
    logger.info("T036 completed successfully.")

if __name__ == "__main__":
    main()
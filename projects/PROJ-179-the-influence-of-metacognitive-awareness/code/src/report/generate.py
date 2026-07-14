import json
import logging
import os
import sys
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return None

def write_json_file(data, file_path):
    """Write data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Report written to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write to {file_path}: {e}")
        return False

def load_bootstrap_results(file_path):
    """Load bootstrap results from a JSON file."""
    return load_json_file(file_path)

def load_regression_results(file_path):
    """Load regression results from a JSON file."""
    return load_json_file(file_path)

def load_diagnostics_results(file_path):
    """Load diagnostics results from a JSON file."""
    return load_json_file(file_path)

def determine_correlation_direction(r_value):
    """Determine the direction of correlation based on r value."""
    if r_value > 0:
        return "positive"
    elif r_value < 0:
        return "negative"
    else:
        return "zero"

def calculate_effect_size_magnitude(r_value):
    """Calculate the magnitude of effect size based on Cohen's guidelines for r."""
    abs_r = abs(r_value)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"

def apply_bonferroni_correction(p_values, num_tests):
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of p-values to correct
        num_tests: Number of statistical tests performed (family size)
    
    Returns:
        List of corrected p-values
    """
    if num_tests == 0:
        return p_values
    
    corrected = []
    for p in p_values:
        # Bonferroni: p_corrected = p * k, capped at 1.0
        corrected_p = min(p * num_tests, 1.0)
        corrected.append(corrected_p)
    return corrected

def apply_bh_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg (FDR) correction for multiple comparisons.
    
    Args:
        p_values: List of p-values to correct
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with corrected p-values and significance decisions
    """
    n = len(p_values)
    if n == 0:
        return {"corrected_p_values": [], "significant": []}
    
    # Sort p-values and keep track of original indices
    indexed_p = list(enumerate(p_values))
    sorted_p = sorted(indexed_p, key=lambda x: x[1])
    
    # Calculate BH critical values
    ranks = [i + 1 for i in range(n)]
    critical_values = [(i / n) * alpha for i in ranks]
    
    # Find the largest k such that p(k) <= critical(k)
    significant_indices = []
    for i in range(n - 1, -1, -1):
        if sorted_p[i][1] <= critical_values[i]:
            # All p-values up to this rank are significant
            significant_indices = [j for j in range(i + 1)]
            break
    
    # Calculate adjusted p-values
    adjusted_p = [1.0] * n
    min_adj = 1.0
    for i in range(n - 1, -1, -1):
        orig_idx, p_val = sorted_p[i]
        adj_p = min(min_adj, p_val * n / (i + 1))
        min_adj = adj_p
        adjusted_p[orig_idx] = min(adj_p, 1.0)
    
    # Determine significance
    significant = [p <= alpha for p in adjusted_p]
    
    return {
        "corrected_p_values": adjusted_p,
        "significant": significant
    }

def generate_primary_analysis_report(bootstrap_results):
    """Generate the primary analysis report."""
    if not bootstrap_results:
        logger.error("No bootstrap results provided")
        return None
    
    report = {
        "analysis_type": "primary_correlation",
        "method": "Hold-Out Accuracy (70/30 split)",
        "metric": "Pearson correlation between Type-2 AUC (training) and d' (test)",
        "results": {
            "r": bootstrap_results.get("r", np.nan),
            "p": bootstrap_results.get("p", np.nan),
            "ci_lower": bootstrap_results.get("ci_lower", np.nan),
            "ci_upper": bootstrap_results.get("ci_upper", np.nan),
            "bootstrap_count": bootstrap_results.get("bootstrap_count", 1000)
        },
        "interpretation": {
            "direction": determine_correlation_direction(bootstrap_results.get("r", 0)),
            "magnitude": calculate_effect_size_magnitude(bootstrap_results.get("r", 0))
        }
    }
    return report

def generate_regression_analysis_report(regression_results, diagnostics_results):
    """Generate the regression analysis report."""
    if not regression_results:
        logger.error("No regression results provided")
        return None
    
    report = {
        "analysis_type": "hierarchical_regression",
        "model_1": regression_results.get("model_1", {}),
        "model_2": regression_results.get("model_2", {}),
        "incremental_variance": {
            "delta_r_squared": regression_results.get("delta_r_squared", 0),
            "f_change": regression_results.get("f_change", 0),
            "p_f_change": regression_results.get("p_f_change", 1.0)
        },
        "diagnostics": diagnostics_results if diagnostics_results else {}
    }
    return report

def generate_robustness_analysis_report(visual_results, auditory_results):
    """
    Generate the robustness analysis report with multiple comparison correction.
    
    This function implements T028: applies Bonferroni and Benjamini-Hochberg
    corrections to the p-values from visual and auditory modality-specific
    correlation analyses.
    """
    if not visual_results or not auditory_results:
        logger.error("Missing visual or auditory results for robustness report")
        return None
    
    # Extract p-values from both modalities
    p_visual = visual_results.get("p", np.nan)
    p_auditory = auditory_results.get("p", np.nan)
    
    p_values = [p_visual, p_auditory]
    num_tests = 2  # Two comparisons: visual and auditory
    
    # Apply Bonferroni correction
    bonferroni_corrected = apply_bonferroni_correction(p_values, num_tests)
    
    # Apply Benjamini-Hochberg correction
    bh_results = apply_bh_correction(p_values, alpha=0.05)
    
    # Construct the report
    report = {
        "analysis_type": "modality_specific_robustness",
        "method": "Separate correlation analysis for visual and auditory stimuli",
        "multiple_comparison_correction": {
            "method": ["Bonferroni", "Benjamini-Hochberg (FDR)"],
            "num_tests": num_tests,
            "family_wise_error_rate": 0.05
        },
        "results": {
            "visual": {
                "r": visual_results.get("r", np.nan),
                "p_raw": p_visual,
                "p_bonferroni": bonferroni_corrected[0] if len(bonferroni_corrected) > 0 else np.nan,
                "p_bh": bh_results["corrected_p_values"][0] if len(bh_results["corrected_p_values"]) > 0 else np.nan,
                "ci_lower": visual_results.get("ci_lower", np.nan),
                "ci_upper": visual_results.get("ci_upper", np.nan),
                "significant_bonferroni": bonferroni_corrected[0] < 0.05 if len(bonferroni_corrected) > 0 else False,
                "significant_bh": bh_results["significant"][0] if len(bh_results["significant"]) > 0 else False
            },
            "auditory": {
                "r": auditory_results.get("r", np.nan),
                "p_raw": p_auditory,
                "p_bonferroni": bonferroni_corrected[1] if len(bonferroni_corrected) > 1 else np.nan,
                "p_bh": bh_results["corrected_p_values"][1] if len(bh_results["corrected_p_values"]) > 1 else np.nan,
                "ci_lower": auditory_results.get("ci_lower", np.nan),
                "ci_upper": auditory_results.get("ci_upper", np.nan),
                "significant_bonferroni": bonferroni_corrected[1] < 0.05 if len(bonferroni_corrected) > 1 else False,
                "significant_bh": bh_results["significant"][1] if len(bh_results["significant"]) > 1 else False
            }
        },
        "interpretation": {
            "visual_direction": determine_correlation_direction(visual_results.get("r", 0)),
            "visual_magnitude": calculate_effect_size_magnitude(visual_results.get("r", 0)),
            "auditory_direction": determine_correlation_direction(auditory_results.get("r", 0)),
            "auditory_magnitude": calculate_effect_size_magnitude(auditory_results.get("r", 0))
        }
    }
    
    return report

def write_report(report, output_path):
    """Write a report dictionary to a JSON file."""
    if report is None:
        logger.error("Cannot write None report")
        return False
    return write_json_file(report, output_path)

def main():
    """
    Main entry point for generating the robustness analysis report.
    
    This script:
    1. Loads visual and auditory modality-specific results (from T027)
    2. Applies Bonferroni and BH corrections for multiple comparisons
    3. Writes the corrected results to data/results/robustness_analysis.json
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    results_dir = base_dir / "data" / "results"
    derived_dir = base_dir / "data" / "derived"
    
    # Ensure output directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load input results from T027 (robustness.py)
    # Expected files: data/results/visual_correlation.json and data/results/auditory_correlation.json
    visual_path = derived_dir / "visual_results.json"
    auditory_path = derived_dir / "auditory_results.json"
    
    # Fallback paths if files are in results_dir
    if not visual_path.exists():
        visual_path = results_dir / "visual_correlation.json"
    if not auditory_path.exists():
        auditory_path = results_dir / "auditory_correlation.json"
    
    # Try to load visual results
    visual_results = load_json_file(visual_path)
    if visual_results is None:
        # Try alternative naming
        visual_path = results_dir / "modality_visual.json"
        visual_results = load_json_file(visual_path)
    
    # Try to load auditory results
    auditory_results = load_json_file(auditory_path)
    if auditory_results is None:
        # Try alternative naming
        auditory_path = results_dir / "modality_auditory.json"
        auditory_results = load_json_file(auditory_path)
    
    if visual_results is None or auditory_results is None:
        logger.error("Could not load modality-specific results. Ensure T027 has completed.")
        # Create a placeholder report indicating missing data
        report = {
            "analysis_type": "modality_specific_robustness",
            "status": "failed",
            "reason": "Missing input data from T027 (visual or auditory results not found)",
            "paths_checked": {
                "visual": str(visual_path),
                "auditory": str(auditory_path)
            }
        }
        output_path = results_dir / "robustness_analysis.json"
        write_report(report, output_path)
        return 1
    
    # Generate the robustness report with corrections
    report = generate_robustness_analysis_report(visual_results, auditory_results)
    
    if report is None:
        logger.error("Failed to generate robustness report")
        return 1
    
    # Write the report
    output_path = results_dir / "robustness_analysis.json"
    success = write_report(report, output_path)
    
    if success:
        logger.info(f"Robustness analysis report successfully written to {output_path}")
        return 0
    else:
        logger.error("Failed to write robustness analysis report")
        return 1

if __name__ == "__main__":
    sys.exit(main())
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from scipy import stats

from config import get_config_dict
from metrics import compute_batch_saa

logger = logging.getLogger(__name__)

def load_saa_results(results_path: str) -> List[float]:
    """
    Load SAA scores from the text pipeline results JSON.
    Expects a file containing a list of dicts with 'saa_score' or similar.
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle different potential structures
    if isinstance(data, list):
        # List of result objects
        scores = [item.get('saa_score', item.get('saa', 0.0)) for item in data if 'saa_score' in item or 'saa' in item]
    elif isinstance(data, dict):
        # Maybe a 'results' key
        if 'results' in data and isinstance(data['results'], list):
            scores = [item.get('saa_score', item.get('saa', 0.0)) for item in data['results'] if 'saa_score' in item or 'saa' in item]
        else:
            raise ValueError("Unexpected JSON structure in results file")
    else:
        raise ValueError("Unexpected JSON structure in results file")

    if not scores:
        logger.warning("No SAA scores found in results file.")
        return []
    
    return scores

def load_baseline_saa(baseline_path: str) -> float:
    """
    Load the baseline SAA scalar from the baseline JSON file.
    """
    path = Path(baseline_path)
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {baseline_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Expecting {"baseline_saa": <value>, "source": "..."} or similar
    if 'baseline_saa' in data:
        return float(data['baseline_saa'])
    elif 'value' in data:
        return float(data['value'])
    else:
        raise ValueError("Baseline file does not contain 'baseline_saa' or 'value' key")

def compute_bootstrap_ci(
    scores: List[float], 
    baseline: float, 
    n_bootstrap: int = 10000, 
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Compute bootstrap confidence interval for the mean SAA.
    """
    if len(scores) < 2:
        return {
            "mean_saa": np.mean(scores) if scores else 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "confidence_level": confidence_level,
            "baseline": baseline,
            "baseline_in_ci": False,
            "n_bootstrap": n_bootstrap,
            "n_samples": len(scores),
            "bootstrap_means_sample": [],
            "error": "Insufficient samples for bootstrap (need >= 2)."
        }

    rng = np.random.default_rng(42) # Fixed seed for reproducibility
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        sample = rng.choice(scores, size=len(scores), replace=True)
        bootstrap_means.append(np.mean(sample))
    
    bootstrap_means = np.array(bootstrap_means)
    mean_saa = float(np.mean(bootstrap_means))
    ci_lower = float(np.percentile(bootstrap_means, (1 - confidence_level) / 2 * 100))
    ci_upper = float(np.percentile(bootstrap_means, (1 + confidence_level) / 2 * 100))
    
    baseline_in_ci = ci_lower <= baseline <= ci_upper

    return {
        "mean_saa": mean_saa,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "confidence_level": confidence_level,
        "baseline": baseline,
        "baseline_in_ci": baseline_in_ci,
        "n_bootstrap": n_bootstrap,
        "n_samples": len(scores),
        "bootstrap_means_sample": bootstrap_means[:100].tolist() # Store sample for debugging
    }

def run_t_test(scores: List[float], baseline: float) -> Dict[str, Any]:
    """
    Perform a one-sample t-test comparing mean SAA against the baseline.
    H0: mean(scores) == baseline
    H1: mean(scores) != baseline
    """
    if len(scores) < 2:
        return {
            "error": f"Insufficient samples for t-test (need >= 2, got {len(scores)}).",
            "t_statistic": None,
            "p_value": None,
            "significant": False
        }
    
    t_stat, p_value = stats.ttest_1samp(scores, baseline)
    significant = p_value < 0.05

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "significant": significant
    }

def main():
    config = get_config_dict()
    results_path = Path(config.get('paths', {}).get('results', 'data/results/text_pipeline_results.json'))
    baseline_path = Path(config.get('paths', {}).get('baseline_saa', 'data/baseline_saa_raw.json'))
    output_path = Path(config.get('paths', {}).get('statistical_test', 'data/results/statistical_test.json'))

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        scores = load_saa_results(str(results_path))
        if not scores:
            logger.error("No SAA scores loaded. Cannot perform statistical test.")
            # Write error state
            result = {
                "bootstrap_ci": {"error": "No scores loaded"},
                "t_test": {"error": "No scores loaded"},
                "analysis_timestamp": None,
                "n_samples": 0,
                "baseline_value": None
            }
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            return

        baseline = load_baseline_saa(str(baseline_path))
        logger.info(f"Loaded {len(scores)} SAA scores. Baseline: {baseline}")

        bootstrap_ci = compute_bootstrap_ci(scores, baseline)
        t_test_result = run_t_test(scores, baseline)

        result = {
            "bootstrap_ci": bootstrap_ci,
            "t_test": t_test_result,
            "analysis_timestamp": None, # Can be filled with datetime if needed
            "n_samples": len(scores),
            "baseline_value": baseline
        }

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Statistical analysis complete. Results saved to {output_path}")
        logger.info(f"T-test: t={t_test_result.get('t_statistic')}, p={t_test_result.get('p_value')}, significant={t_test_result.get('significant')}")

    except Exception as e:
        logger.error(f"Error during statistical analysis: {e}", exc_info=True)
        result = {
            "bootstrap_ci": {"error": str(e)},
            "t_test": {"error": str(e)},
            "analysis_timestamp": None,
            "n_samples": 0,
            "baseline_value": None
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

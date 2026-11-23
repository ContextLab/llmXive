"""
T025 Implementation: Save final SAA metrics and statistical test results.

This module aggregates the results from the SAA evaluation (T022),
the statistical t-test (T023a), and the hallucination rate analysis (T024b)
into a single summary JSON file: data/results/saa_summary.json.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from config import get_config_dict
from baseline_ref import load_baseline_saa
from statistical_analysis import load_saa_results as load_stats_saa_results, run_t_test
from hallucination_rate import load_saa_results as load_halluc_saa_results, calculate_hallucination_metrics

logger = logging.getLogger(__name__)

def load_saa_results() -> Dict[str, Any]:
    """
    Loads the intermediate SAA results from the text pipeline evaluation.
    Path is determined by config (typically data/results/text_pipeline_results.json).
    """
    cfg = get_config_dict()
    # T019 output path
    results_path = Path(cfg['paths']['results']) / 'text_pipeline_results.json'
    
    if not results_path.exists():
        raise FileNotFoundError(f"Required intermediate results not found at {results_path}. "
                                "Ensure T019 has been completed successfully.")
    
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compute_summary_metrics(saa_results: Dict[str, Any], baseline_value: float) -> Dict[str, Any]:
    """
    Computes final summary metrics including mean SAA, count, and comparison to baseline.
    """
    if not saa_results or 'results' not in saa_results:
        raise ValueError("Invalid SAA results structure: missing 'results' key.")

    results_list = saa_results['results']
    if not results_list:
        raise ValueError("SAA results list is empty.")

    # Extract SAA scores
    # The structure from T022/T019 is expected to be a list of dicts with 'saa_score' or similar
    # Looking at typical pipeline outputs, we assume a 'saa_score' or 'is_correct' field.
    # Based on T008 compute_saa, it returns a boolean or float. T022 saves to results.
    # We assume the saved result has 'saa_score' (float 0.0 or 1.0) or 'is_correct' (bool).
    
    scores = []
    for item in results_list:
        if 'saa_score' in item:
            scores.append(float(item['saa_score']))
        elif 'is_correct' in item:
            scores.append(1.0 if item['is_correct'] else 0.0)
        else:
            # Fallback if structure varies, log warning
            logger.warning(f"Item missing expected SAA fields: {item.keys()}")
            continue

    if not scores:
        raise ValueError("Could not extract any SAA scores from results.")

    mean_saa = float(sum(scores) / len(scores))
    std_saa = float(np.std(scores) if len(scores) > 1 else 0.0)
    
    # Comparison to baseline
    delta = mean_saa - baseline_value
    improved = delta > 0

    return {
        "count": len(scores),
        "mean_saa": round(mean_saa, 6),
        "std_saa": round(std_saa, 6),
        "baseline_saa": baseline_value,
        "delta_from_baseline": round(delta, 6),
        "improved_vs_baseline": improved
    }

def save_summary(summary_data: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the summary dictionary to the specified JSON path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)
    logger.info(f"Saved SAA summary to {output_path}")

def main():
    """
    Orchestrates the loading of results, computation of summary, and saving to file.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        cfg = get_config_dict()
        baseline_value = load_baseline_saa()
        
        logger.info("Loading SAA results from text pipeline...")
        saa_results = load_saa_results()
        
        logger.info("Computing summary metrics...")
        summary_metrics = compute_summary_metrics(saa_results, baseline_value)
        
        # Integrate Statistical Test Results (T023a)
        # T023a saves to data/results/statistical_test.json
        stats_path = Path(cfg['paths']['results']) / 'statistical_test.json'
        stat_test_results = {}
        if stats_path.exists():
            with open(stats_path, 'r', encoding='utf-8') as f:
                stat_test_results = json.load(f)
            logger.info("Integrated statistical test results.")
        else:
            logger.warning(f"Statistical test results not found at {stats_path}. "
                           "Proceeding without t-test data in summary.")

        # Integrate Hallucination Rate (T024b)
        # T024b saves to data/results/hallucination_rate.json
        halluc_path = Path(cfg['paths']['results']) / 'hallucination_rate.json'
        hallucination_results = {}
        if halluc_path.exists():
            with open(halluc_path, 'r', encoding='utf-8') as f:
                hallucination_results = json.load(f)
            logger.info("Integrated hallucination rate results.")
        else:
            logger.warning(f"Hallucination rate results not found at {halluc_path}. "
                           "Proceeding without hallucination data in summary.")

        # Construct final summary
        final_summary = {
            "task_id": "T025",
            "description": "Final SAA metrics and statistical test results summary",
            "metrics": summary_metrics,
            "statistical_test": stat_test_results,
            "hallucination_analysis": hallucination_results,
            "generated_at": "auto-generated-by-saa_summary.py"
        }

        output_path = Path(cfg['paths']['results']) / 'saa_summary.json'
        save_summary(final_summary, output_path)
        
        print(f"SUCCESS: SAA Summary saved to {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    # Import numpy locally to avoid issues if not needed in all paths, 
    # though it's likely already imported in metrics.py context.
    import numpy as np
    sys.exit(main())

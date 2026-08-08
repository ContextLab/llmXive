import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
from config import get_config_dict

# Import from existing project modules
from statistical_analysis import load_saa_results, load_baseline_saa, run_t_test
from metrics import compute_batch_saa

logger = logging.getLogger(__name__)

def load_saa_results(results_path: str) -> Dict[str, Any]:
    """
    Load the SAA evaluation results from the text pipeline.
    Expected file: data/results/text_pipeline_results.json
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found at {results_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def load_baseline_saa(baseline_path: str) -> float:
    """
    Load the baseline SAA scalar from the verified baseline file.
    Expected file: data/baseline_saa_raw.json or data/baseline_saa.json
    """
    path = Path(baseline_path)
    if not path.exists():
        # Fallback to common locations if exact path not provided
        fallback_paths = [
            Path("data/baseline_saa.json"),
            Path("data/baseline_saa_raw.json")
        ]
        for fp in fallback_paths:
            if fp.exists():
                path = fp
                break
        else:
            raise FileNotFoundError("Baseline SAA file not found in expected locations.")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both potential key names based on T007 spec
    if 'baseline_saa' in data:
        return float(data['baseline_saa'])
    elif 'value' in data:
        return float(data['value'])
    else:
        raise KeyError("Baseline file does not contain 'baseline_saa' or 'value' key.")

def compute_summary_metrics(
    results: Dict[str, Any], 
    baseline_saa: float, 
    t_test_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate final SAA metrics, statistical test results, and failure mode counts
    into a single summary dictionary.
    """
    # Extract individual SAA scores if available in results
    # The structure of results from T019/T022 is expected to be a list of query results
    query_results = results.get('results', [])
    
    if not query_results:
        logger.warning("No query results found in input data.")
        return {
            "mean_saa": 0.0,
            "baseline_saa": baseline_saa,
            "improvement": 0.0,
            "statistical_test": t_test_results,
            "sample_size": 0
        }

    # Calculate mean SAA from the results list
    # Assuming each result has a 'saa' or 'strict_attributed_accuracy' key
    saa_scores = []
    for item in query_results:
        if 'saa' in item:
            saa_scores.append(item['saa'])
        elif 'strict_attributed_accuracy' in item:
            saa_scores.append(item['strict_attributed_accuracy'])
    
    if not saa_scores:
        logger.warning("Could not extract SAA scores from results.")
        mean_saa = 0.0
    else:
        mean_saa = float(sum(saa_scores) / len(saa_scores))

    improvement = mean_saa - baseline_saa

    summary = {
        "mean_saa": round(mean_saa, 4),
        "baseline_saa": round(baseline_saa, 4),
        "improvement": round(improvement, 4),
        "sample_size": len(saa_scores),
        "statistical_test": t_test_results,
        "timestamp": results.get('timestamp', 'unknown'),
        "metadata": {
            "model": results.get('metadata', {}).get('model', 'unknown'),
            "retriever": results.get('metadata', {}).get('retriever', 'unknown')
        }
    }

    # Include hallucination rate if available (from T024b)
    if 'hallucination_rate' in results:
        summary['hallucination_rate'] = results['hallucination_rate']
    
    return summary

def save_summary(summary_data: Dict[str, Any], output_path: str) -> None:
    """
    Save the final summary dictionary to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Summary saved to {output_path}")

def main():
    """
    Main entry point to generate the final SAA summary.
    Loads results from T019/T022, statistical tests from T023a, and combines them.
    """
    config = get_config_dict()
    
    # Paths based on project conventions
    results_path = config.get('paths', {}).get('text_results', 'data/results/text_pipeline_results.json')
    baseline_path = config.get('paths', {}).get('baseline_saa', 'data/baseline_saa.json')
    t_test_path = config.get('paths', {}).get('statistical_test', 'data/results/statistical_test.json')
    output_path = config.get('paths', {}).get('saa_summary', 'data/results/saa_summary.json')

    # Ensure paths exist
    if not Path(results_path).exists():
        raise FileNotFoundError(f"Required results file missing: {results_path}")
    if not Path(baseline_path).exists():
        raise FileNotFoundError(f"Required baseline file missing: {baseline_path}")
    if not Path(t_test_path).exists():
        raise FileNotFoundError(f"Required statistical test file missing: {t_test_path}")

    # Load data
    logger.info(f"Loading results from {results_path}")
    results_data = load_saa_results(results_path)
    
    logger.info(f"Loading baseline from {baseline_path}")
    baseline_saa = load_baseline_saa(baseline_path)
    
    logger.info(f"Loading statistical test results from {t_test_path}")
    with open(t_test_path, 'r', encoding='utf-8') as f:
        t_test_results = json.load(f)

    # Compute summary
    logger.info("Computing summary metrics...")
    summary = compute_summary_metrics(results_data, baseline_saa, t_test_results)

    # Save summary
    logger.info(f"Saving summary to {output_path}")
    save_summary(summary, output_path)

    print(f"Final SAA Summary generated successfully at {output_path}")
    print(f"Mean SAA: {summary['mean_saa']} (Baseline: {summary['baseline_saa']}, Improvement: {summary['improvement']})")
    
    return summary

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
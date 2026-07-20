"""
Result Aggregator for US2 Benchmarking.

Aggregates results from heuristic runs and the Dense Attention baseline
into a single benchmark report (results/benchmark_report.json).

Computes:
  - F1 Score
  - Perplexity (PPL)
  - Delta vs Dense Attention baseline for each heuristic
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from eval.metrics import calculate_metrics, calculate_perplexity
from utils.logger import get_logger_for_task

logger = get_logger_for_task(__name__)

def load_experiment_results(results_dir: Path) -> Dict[str, Any]:
    """
    Load all result JSON files from the experiment directory.
    Expects files named like: <heuristic_name>_results.json or baseline_results.json
    """
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    results = {}
    for file_path in results_dir.glob("*.json"):
        if file_path.name == "benchmark_report.json":
            continue  # Skip the report itself if it exists

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Determine key: usually the heuristic name or 'baseline'
            key = file_path.stem.replace("_results", "")
            results[key] = data
            logger.info(f"Loaded results for '{key}' from {file_path.name}")

    return results

def aggregate_benchmark_report(
    results: Dict[str, Any], 
    baseline_key: str = "baseline"
) -> Dict[str, Any]:
    """
    Aggregate metrics and calculate deltas against the baseline.
    
    Args:
        results: Dictionary of heuristic/baseline results keyed by name.
        baseline_key: The key in 'results' that corresponds to the Dense Attention baseline.
    
    Returns:
        A dictionary structure suitable for writing to benchmark_report.json.
    """
    if baseline_key not in results:
        raise ValueError(f"Baseline '{baseline_key}' not found in results. Available keys: {list(results.keys())}")
    
    baseline_data = results[baseline_key]
    
    # Extract baseline metrics (expecting specific keys from the runner)
    # The baseline runner typically outputs: f1_score, perplexity, total_samples, correct_samples
    baseline_f1 = baseline_data.get("f1_score")
    baseline_ppl = baseline_data.get("perplexity")
    
    if baseline_f1 is None or baseline_ppl is None:
        logger.warning(f"Baseline metrics missing. Baseline data: {baseline_data}")
        # If missing, we might need to calculate them if raw data exists, 
        # but for this aggregator we assume the runner already computed them.
        # If not, we return an error state.
        raise ValueError("Baseline F1 or Perplexity is missing. Cannot calculate delta.")

    report = {
        "baseline": {
            "f1_score": baseline_f1,
            "perplexity": baseline_ppl,
            "source": "Dense Attention (Full Context)"
        },
        "heuristics": {},
        "metadata": {
            "aggregated_at": None, # Set dynamically if needed, or left to caller
            "baseline_key": baseline_key
        }
    }

    for name, data in results.items():
        if name == baseline_key:
            continue

        # Calculate metrics if not present in the data (fallback)
        # Usually the heuristic runner also outputs these, but we ensure consistency.
        current_f1 = data.get("f1_score")
        current_ppl = data.get("perplexity")

        # If the runner didn't compute them, we try to compute from raw lists if available
        if current_f1 is None and "predictions" in data and "references" in data:
            current_f1 = calculate_metrics(data["predictions"], data["references"])["f1"]
        if current_ppl is None and "log_probs" in data:
            current_ppl = calculate_perplexity(data["log_probs"])

        if current_f1 is None or current_ppl is None:
            logger.warning(f"Skipping heuristic '{name}' due to missing metrics.")
            continue

        # Calculate Delta
        delta_f1 = current_f1 - baseline_f1
        delta_ppl = current_ppl - baseline_ppl

        report["heuristics"][name] = {
            "f1_score": current_f1,
            "perplexity": current_ppl,
            "delta_f1_vs_baseline": delta_f1,
            "delta_ppl_vs_baseline": delta_ppl,
            "samples_processed": data.get("total_samples", 0),
            "details": data.get("details", {})
        }
        
        logger.info(f"Aggregated '{name}': F1={current_f1:.4f} (delta={delta_f1:.4f}), PPL={current_ppl:.2f} (delta={delta_ppl:.2f})")

    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the aggregated report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Benchmark report saved to {output_path}")

def run_aggregation(
    results_dir: str = "data/processed/experiments", 
    output_file: str = "results/benchmark_report.json",
    baseline_key: str = "baseline"
) -> Dict[str, Any]:
    """
    Main entry point to run the aggregation pipeline.
    Loads results, aggregates, and saves the report.
    """
    results_path = Path(results_dir)
    output_path = Path(output_file)

    logger.info(f"Starting aggregation. Reading from {results_path}, writing to {output_path}")

    try:
        results = load_experiment_results(results_path)
        if not results:
            raise ValueError("No experiment results found in the directory.")
        
        report = aggregate_benchmark_report(results, baseline_key)
        save_report(report, output_path)
        
        return report
    
    except Exception as e:
        logger.error(f"Aggregation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Default execution for manual testing or script invocation
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate benchmark results into a report.")
    parser.add_argument("--results-dir", type=str, default="data/processed/experiments", help="Directory containing individual experiment JSON files.")
    parser.add_argument("--output", type=str, default="results/benchmark_report.json", help="Output path for the benchmark report.")
    parser.add_argument("--baseline", type=str, default="baseline", help="Key name for the baseline results in the directory.")
    
    args = parser.parse_args()
    
    run_aggregation(
        results_dir=args.results_dir,
        output_file=args.output,
        baseline_key=args.baseline
    )
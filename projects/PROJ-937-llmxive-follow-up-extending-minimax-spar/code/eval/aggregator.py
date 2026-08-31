import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from eval.metrics import calculate_metrics, calculate_perplexity
from utils.logger import get_logger_for_task

# Configure logger
logger = get_logger_for_task("T024")

def load_experiment_results(experiment_dir: Path, experiment_name: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load results from a specific experiment run.
    Expects a file like: experiment_dir/experiment_name/results.json
    """
    result_file = experiment_dir / experiment_name / "results.json"
    if not result_file.exists():
        logger.warning(f"Result file not found: {result_file}")
        return None

    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure it's a list of records
            if isinstance(data, dict):
                return [data]
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {result_file}: {e}")
        return None

def load_baseline_metrics(experiment_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load the dense attention baseline metrics.
    Expected file: experiment_dir/baseline/results.json
    """
    return load_experiment_results(experiment_dir, "baseline")

def aggregate_benchmark_report(
    baseline_results: List[Dict[str, Any]],
    heuristic_results: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Aggregate results into a benchmark report comparing heuristics against the baseline.
    Calculates F1, PPL, and delta vs Dense Attention baseline.
    """
    report = {
        "baseline": {},
        "heuristics": {}
    }

    # 1. Aggregate Baseline
    if baseline_results:
        # Assume baseline results are a list of per-sample metrics or a single aggregated dict
        # We will compute averages if multiple samples exist
        total_f1 = 0.0
        total_ppl = 0.0
        count = 0
        
        for res in baseline_results:
            # Handle both flat metrics and nested 'metrics' keys if necessary
            f1 = res.get('f1_score', res.get('metrics', {}).get('f1', 0.0))
            ppl = res.get('perplexity', res.get('metrics', {}).get('perplexity', 0.0))
            
            # If metrics are not pre-calculated, calculate them from raw predictions
            # This block assumes the runner already calculated f1_score and perplexity
            # If not, we would need to call calculate_metrics here, but typically
            # the runner (T022c) outputs these.
            
            total_f1 += float(f1)
            total_ppl += float(ppl)
            count += 1

        avg_f1 = total_f1 / count if count > 0 else 0.0
        avg_ppl = total_ppl / count if count > 0 else 0.0

        report["baseline"] = {
            "f1_score": round(avg_f1, 4),
            "perplexity": round(avg_ppl, 4),
            "samples_processed": count
        }
    else:
        logger.warning("No baseline results found. Cannot compute deltas.")
        report["baseline"] = {
            "f1_score": None,
            "perplexity": None,
            "samples_processed": 0,
            "error": "Baseline results missing"
        }

    baseline_f1 = report["baseline"].get("f1_score")
    baseline_ppl = report["baseline"].get("perplexity")

    # 2. Aggregate Heuristics
    for heuristic_name, results in heuristic_results.items():
        if not results:
            report["heuristics"][heuristic_name] = {
                "f1_score": None,
                "perplexity": None,
                "delta_f1": None,
                "delta_ppl": None,
                "samples_processed": 0,
                "status": "no_data"
            }
            continue

        total_f1 = 0.0
        total_ppl = 0.0
        count = 0

        for res in results:
            f1 = res.get('f1_score', res.get('metrics', {}).get('f1', 0.0))
            ppl = res.get('perplexity', res.get('metrics', {}).get('perplexity', 0.0))
            
            total_f1 += float(f1)
            total_ppl += float(ppl)
            count += 1

        avg_f1 = total_f1 / count if count > 0 else 0.0
        avg_ppl = total_ppl / count if count > 0 else 0.0

        delta_f1 = None
        delta_ppl = None

        if baseline_f1 is not None:
            delta_f1 = round(avg_f1 - baseline_f1, 4)
        if baseline_ppl is not None:
            delta_ppl = round(avg_ppl - baseline_ppl, 4)

        report["heuristics"][heuristic_name] = {
            "f1_score": round(avg_f1, 4),
            "perplexity": round(avg_ppl, 4),
            "delta_f1": delta_f1,
            "delta_ppl": delta_ppl,
            "samples_processed": count,
            "status": "ok"
        }

    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the benchmark report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Benchmark report saved to {output_path}")

def run_aggregation(
    experiment_dir: Path,
    baseline_name: str = "baseline",
    heuristic_names: Optional[List[str]] = None,
    output_file: str = "results/benchmark_report.json"
) -> Dict[str, Any]:
    """
    Main entry point for T024: Aggregates results and writes benchmark_report.json.
    """
    logger.info(f"Starting aggregation for experiment directory: {experiment_dir}")

    # Load Baseline
    baseline_data = load_experiment_results(experiment_dir, baseline_name)
    if baseline_data is None:
        baseline_data = [] # Treat as empty if not found

    # Load Heuristics
    if heuristic_names is None:
        # Discover heuristic result directories if names not provided
        # Assuming standard naming: code/heuristics/entropy.py -> "entropy"
        heuristic_names = ["entropy", "gradient", "recency"]
    
    heuristic_data = {}
    for name in heuristic_names:
        data = load_experiment_results(experiment_dir, name)
        if data:
            heuristic_data[name] = data
        else:
            heuristic_data[name] = []

    # Aggregate
    report = aggregate_benchmark_report(baseline_data, heuristic_data)

    # Save
    output_path = Path(output_file)
    save_report(report, output_path)

    return report

def main():
    """
    CLI entry point for T024.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Aggregate benchmark results (T024)")
    parser.add_argument("--experiment-dir", type=str, default="data/processed/experiments",
                        help="Directory containing experiment subfolders (baseline, entropy, etc.)")
    parser.add_argument("--output", type=str, default="results/benchmark_report.json",
                        help="Output path for the JSON report")
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    if not exp_dir.exists():
        logger.error(f"Experiment directory not found: {exp_dir}")
        sys.exit(1)

    try:
        run_aggregation(exp_dir, output_file=args.output)
        logger.info("Aggregation completed successfully.")
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise

if __name__ == "__main__":
    main()
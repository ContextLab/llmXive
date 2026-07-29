import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from eval.metrics import calculate_metrics, calculate_perplexity

logger = logging.getLogger(__name__)

def load_experiment_results(results_dir: Path) -> Dict[str, Any]:
    """
    Load experiment results from the results directory.
    Expects files like 'heuristic_entropy_results.json', 'heuristic_gradient_results.json', etc.
    """
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    results = {}
    for file_path in results_dir.glob("heuristic_*_results.json"):
        heuristic_name = file_path.stem.replace("heuristic_", "").replace("_results", "")
        with open(file_path, 'r') as f:
            results[heuristic_name] = json.load(f)
    
    # Also load baseline results if they exist
    baseline_path = results_dir / "baseline_dense_attention_results.json"
    if baseline_path.exists():
        with open(baseline_path, 'r') as f:
            results['baseline'] = json.load(f)
    else:
        logger.warning(f"Baseline results file not found: {baseline_path}")
    
    return results

def aggregate_benchmark_report(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate benchmark report with F1, PPL, and delta vs Dense Attention baseline.
    
    Args:
        results: Dictionary containing results for each heuristic and baseline
    
    Returns:
        Dictionary with aggregated benchmark report
    """
    if 'baseline' not in results:
        raise ValueError("Baseline results required for aggregation")
    
    baseline_metrics = results['baseline'].get('metrics', {})
    baseline_f1 = baseline_metrics.get('f1_score', 0.0)
    baseline_ppl = baseline_metrics.get('perplexity', float('inf'))
    
    report = {
        'baseline': {
            'f1_score': baseline_f1,
            'perplexity': baseline_ppl
        },
        'heuristics': {}
    }
    
    for heuristic_name, heuristic_data in results.items():
        if heuristic_name == 'baseline':
            continue
        
        metrics = heuristic_data.get('metrics', {})
        f1_score = metrics.get('f1_score', 0.0)
        ppl = metrics.get('perplexity', float('inf'))
        
        # Calculate delta vs baseline
        f1_delta = f1_score - baseline_f1
        ppl_delta = ppl - baseline_ppl if baseline_ppl != float('inf') else float('inf')
        
        report['heuristics'][heuristic_name] = {
            'f1_score': f1_score,
            'perplexity': ppl,
            'f1_delta_vs_baseline': f1_delta,
            'perplexity_delta_vs_baseline': ppl_delta,
            'samples_evaluated': heuristic_data.get('samples_evaluated', 0)
        }
    
    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the benchmark report to a JSON file.
    
    Args:
        report: The benchmark report dictionary
        output_path: Path to save the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Benchmark report saved to {output_path}")

def run_aggregation(results_dir: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main function to run the full aggregation pipeline.
    
    Args:
        results_dir: Directory containing experiment results (default: results/)
        output_path: Path to save the benchmark report (default: results/benchmark_report.json)
    
    Returns:
        The aggregated benchmark report
    """
    if results_dir is None:
        results_dir = Path("results")
    
    if output_path is None:
        output_path = Path("results/benchmark_report.json")
    
    logger.info(f"Loading experiment results from {results_dir}")
    results = load_experiment_results(results_dir)
    
    logger.info("Aggregating benchmark report")
    report = aggregate_benchmark_report(results)
    
    logger.info(f"Saving benchmark report to {output_path}")
    save_report(report, output_path)
    
    return report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate benchmark results")
    parser.add_argument("--results-dir", type=str, default="results",
                      help="Directory containing experiment results")
    parser.add_argument("--output-path", type=str, default="results/benchmark_report.json",
                      help="Path to save the benchmark report")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    report = run_aggregation(
        results_dir=Path(args.results_dir),
        output_path=Path(args.output_path)
    )
    
    print(json.dumps(report, indent=2))
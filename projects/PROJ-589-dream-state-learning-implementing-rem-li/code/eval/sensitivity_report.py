import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

def load_temperature_sweep_results(results_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads the results from the temperature sweep experiments.
    Expects JSON files named 'seed_{seed}_temp_{temp}.json' or a single aggregated file.
    """
    config = Config()
    if results_dir is None:
        results_dir = str(config.results_dir / "sensitivity")
    
    results_path = Path(results_dir)
    if not results_path.exists():
        logger.error(f"Results directory not found: {results_path}")
        return []

    all_results = []
    
    # Try to find a single aggregated report first
    aggregated_file = results_path / "sweep_results.json"
    if aggregated_file.exists():
        with open(aggregated_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_results = data
            else:
                all_results = [data]
        logger.info(f"Loaded aggregated results from {aggregated_file}")
        return all_results

    # Otherwise, scan for individual seed results
    for file_path in results_path.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Normalize structure if needed
                if 'temperature' not in data and 'final_accuracy' not in data:
                    logger.warning(f"Skipping file {file_path} due to missing expected keys")
                    continue
                all_results.append(data)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON in {file_path}")
    
    logger.info(f"Loaded {len(all_results)} individual results from {results_path}")
    return all_results

def compute_variance_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes variance and other statistical metrics for final accuracy across temperatures.
    """
    if not results:
        return {"error": "No results to analyze"}

    # Group by temperature
    temp_accuracies: Dict[float, List[float]] = {}
    
    for res in results:
        temp = float(res.get('temperature', 0.0))
        acc = float(res.get('final_accuracy', 0.0))
        
        if temp not in temp_accuracies:
            temp_accuracies[temp] = []
        temp_accuracies[temp].append(acc)

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(results),
        "temperatures_analyzed": sorted(temp_accuracies.keys()),
        "per_temperature_stats": {}
    }

    for temp, accuracies in temp_accuracies.items():
        if len(accuracies) < 2:
            variance = 0.0
            std_dev = 0.0
            logger.warning(f"Only {len(accuracies)} run(s) for temp={temp}, variance set to 0.0")
        else:
            variance = float(np.var(accuracies, ddof=1)) # Sample variance
            std_dev = float(np.std(accuracies, ddof=1))
        
        mean_acc = float(np.mean(accuracies))
        min_acc = float(np.min(accuracies))
        max_acc = float(np.max(accuracies))

        metrics["per_temperature_stats"][str(temp)] = {
            "mean_accuracy": mean_acc,
            "variance": variance,
            "std_dev": std_dev,
            "min_accuracy": min_acc,
            "max_accuracy": max_acc,
            "n_runs": len(accuracies),
            "raw_accuracies": accuracies
        }

    # Overall variance across all runs (global variance)
    all_accuracies = [float(r.get('final_accuracy', 0.0)) for r in results]
    metrics["global_variance"] = float(np.var(all_accuracies, ddof=1)) if len(all_accuracies) > 1 else 0.0
    metrics["global_std_dev"] = float(np.std(all_accuracies, ddof=1)) if len(all_accuracies) > 1 else 0.0
    metrics["global_mean_accuracy"] = float(np.mean(all_accuracies))

    return metrics

def generate_sensitivity_report(metrics: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generates a JSON report containing the variance analysis.
    """
    config = Config()
    if output_path is None:
        output_path = str(config.results_dir / "sensitivity" / "variance_report.json")
    
    report = {
        "report_type": "temperature_sensitivity_variance",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "global_variance": metrics.get("global_variance", 0.0),
            "global_std_dev": metrics.get("global_std_dev", 0.0),
            "temperatures_tested": metrics.get("temperatures_analyzed", []),
            "total_experiments": metrics.get("total_runs", 0)
        },
        "detailed_stats": metrics.get("per_temperature_stats", {})
    }

    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Sensitivity variance report saved to {report_path}")
    
    # Print summary to stdout
    print(f"\n--- Sensitivity Analysis Report ---")
    print(f"Temperatures tested: {report['summary']['temperatures_tested']}")
    print(f"Global Variance: {report['summary']['global_variance']:.6f}")
    print(f"Global Std Dev: {report['summary']['global_std_dev']:.6f}")
    print(f"Total Experiments: {report['summary']['total_experiments']}")
    print("-----------------------------------\n")

    return output_path

def main():
    """
    Entry point for running the sensitivity report generation.
    """
    logger.info("Starting sensitivity variance report generation...")
    
    results = load_temperature_sweep_results()
    if not results:
        logger.error("No results found to generate report. Ensure temperature sweep has been run.")
        sys.exit(1)

    metrics = compute_variance_metrics(results)
    output_file = generate_sensitivity_report(metrics)
    
    logger.info(f"Report generation complete: {output_file}")
    return output_file

if __name__ == "__main__":
    main()
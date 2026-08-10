import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.gatekeeper.pipeline import run_gatekeeper_pipeline, run_baseline
from code.gatekeeper.metrics import calculate_access_control_score, run_access_control_evaluation
from code.utils.data_loader import fetch_gatemem, validate_episode, load_schema
from code.utils.profiling import start_profiling, stop_profiling, get_peak_memory_mb
from code.logging_config import setup_logging, pin_random_seed

logger = setup_logging()

def parse_args():
    parser = argparse.ArgumentParser(description="Run GateMem Benchmark Evaluation")
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        help="Comma-separated list of domains to evaluate (e.g., medical,office)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save results"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    return parser.parse_args()

def load_domain_data(domains: List[str]) -> List[Dict[str, Any]]:
    """
    Fetches GateMem dataset and filters by the specified domains.
    """
    logger.info(f"Loading data for domains: {domains}")
    
    # Fetch the full dataset (assuming real source availability)
    # The data loader will raise an error if the real source is unreachable
    dataset = fetch_gatemem()
    
    filtered_episodes = []
    for episode in dataset:
        if episode.get("domains") in domains:
            # Validate the episode against the schema
            schema_path = "contracts/dataset.schema.yaml"
            if os.path.exists(schema_path):
                try:
                    validate_episode(episode, schema_path)
                except ValueError as e:
                    logger.warning(f"Skipping invalid episode: {e}")
                    continue
            filtered_episodes.append(episode)
    
    logger.info(f"Loaded {len(filtered_episodes)} episodes for domains {domains}")
    return filtered_episodes

def run_gatekeeper_pipeline(episodes: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Executes the Gatekeeper pipeline on the provided episodes.
    """
    logger.info("Starting Gatekeeper pipeline execution...")
    start_profiling()
    pin_random_seed(42)
    
    # Run the pipeline using the existing implementation
    results = run_gatekeeper_pipeline(episodes)
    
    peak_ram = get_peak_memory_mb()
    stop_profiling()
    
    # Save raw pipeline results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Gatekeeper pipeline complete. Results saved to {output_path}")
    return results

def run_baseline_pipeline(episodes: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Executes the Baseline pipeline on the provided episodes.
    """
    logger.info("Starting Baseline pipeline execution...")
    start_profiling()
    pin_random_seed(42)
    
    # Run the baseline using the existing implementation
    results = run_baseline(episodes)
    
    peak_ram = get_peak_memory_mb()
    stop_profiling()
    
    # Save raw baseline results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Baseline pipeline complete. Results saved to {output_path}")
    return results

def calculate_reduction(gk_score: float, base_score: float) -> float:
    """
    Calculates the percentage reduction (or improvement) of Gatekeeper vs Baseline.
    For Access Control, a lower unauthorized rate is better.
    """
    if base_score == 0:
        return 0.0
    return ((base_score - gk_score) / base_score) * 100

def aggregate_profiling_data(gk_results: Dict, base_results: Dict) -> Dict[str, Any]:
    """
    Aggregates profiling data from both runs.
    """
    return {
        "gatekeeper": {
            "peak_ram_mb": gk_results.get("metrics", {}).get("peak_ram_mb", 0),
            "latency_ms": gk_results.get("metrics", {}).get("latency_ms", 0)
        },
        "baseline": {
            "peak_ram_mb": base_results.get("metrics", {}).get("peak_ram_mb", 0),
            "latency_ms": base_results.get("metrics", {}).get("latency_ms", 0)
        }
    }

def generate_comparison_table(gk_score: float, base_score: float, domains: List[str]) -> str:
    """
    Generates a text-based comparison table for the results.
    """
    reduction = calculate_reduction(gk_score, base_score)
    lines = [
        "Access Control Evaluation Results",
        "=" * 40,
        f"Domains: {', '.join(domains)}",
        "-" * 40,
        f"Gatekeeper Unauthorized Rate: {gk_score:.4f}",
        f"Baseline Unauthorized Rate:   {base_score:.4f}",
        f"Improvement (Reduction):      {reduction:.2f}%",
        "-" * 40
    ]
    return "\n".join(lines)

def save_results(results: Dict[str, Any], output_dir: Path):
    """
    Saves the final aggregated results to a JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "access_control_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Final results saved to {output_file}")

def main():
    args = parse_args()
    
    # Parse domains
    domains = [d.strip() for d in args.domain.split(",")]
    if not domains:
        logger.error("No domains specified.")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    episodes = load_domain_data(domains)
    if not episodes:
        logger.error(f"No valid episodes found for domains: {domains}")
        sys.exit(1)
    
    # Define output paths
    gk_output_path = output_dir / "gatekeeper_raw.json"
    base_output_path = output_dir / "baseline_raw.json"
    
    # Run Pipelines
    gk_results = run_gatekeeper_pipeline(episodes, gk_output_path)
    base_results = run_baseline_pipeline(episodes, base_output_path)
    
    # Calculate Metrics
    # We expect the pipeline results to contain the necessary data for metrics calculation
    # or we calculate them directly from the loaded episodes and predictions.
    # Using the metrics module's function to calculate the score.
    
    # Assuming run_gatekeeper_pipeline returns a structure with 'predictions' and 'ground_truth'
    # or we pass the episodes and results to the metric calculator.
    # Based on T018, we have calculate_access_control_score.
    
    gk_score = calculate_access_control_score(gk_results)
    base_score = calculate_access_control_score(base_results)
    
    # Aggregate Profiling
    profiling_data = aggregate_profiling_data(gk_results, base_results)
    
    # Generate Report
    report_text = generate_comparison_table(gk_score, base_score, domains)
    print(report_text)
    
    # Final Output Structure
    final_results = {
        "domains": domains,
        "access_control": {
            "gatekeeper_score": gk_score,
            "baseline_score": base_score,
            "improvement_percent": calculate_reduction(gk_score, base_score)
        },
        "profiling": profiling_data,
        "episode_count": len(episodes)
    }
    
    save_results(final_results, output_dir)
    
    logger.info("Evaluation complete.")

if __name__ == "__main__":
    main()
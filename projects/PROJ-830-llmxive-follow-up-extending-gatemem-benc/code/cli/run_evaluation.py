import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project modules based on API surface
from code.logging_config import setup_logging, pin_random_seed
from code.gatekeeper.pipeline import (
    run_gatekeeper_pipeline,
    run_baseline_pipeline,
    save_results as save_gatekeeper_results,
)
from code.gatekeeper.metrics import calculate_access_control_score
from code.data.loader import fetch_gatemem
from code.utils.profiling import profile_execution, save_results_to_file

# Configure logging
logger = setup_logging()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run GateMem benchmark evaluation pipeline.")
    parser.add_argument(
        "--domains",
        type=str,
        default="medical,office",
        help="Comma-separated list of domains to evaluate (e.g., medical,office)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save results."
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Run only baseline evaluations (Gatekeeper skipped)."
    )
    parser.add_argument(
        "--gatekeeper-only",
        action="store_true",
        help="Run only Gatekeeper evaluation (Baselines skipped)."
    )
    return parser.parse_args()

def load_domain_data(domains: List[str]) -> List[Dict[str, Any]]:
    """
    Load dataset episodes for specified domains.
    Uses the data loader to fetch and validate real data.
    """
    logger.info(f"Loading data for domains: {domains}")

    # Stream the dataset; the loader returns a streaming dataset object.
    dataset = fetch_gatemem(split="test", streaming=True)

    episodes = [ep for ep in dataset if ep.get("domain") in domains]

    if not episodes:
        raise ValueError(f"No valid episodes found for domains: {domains}")

    logger.info(f"Loaded {len(episodes)} episodes.")
    return episodes

def run_gatekeeper_pipeline_wrapper(episodes: List[Dict[str, Any]], output_dir: str) -> List[Dict[str, Any]]:
    """
    Wrapper to run the Gatekeeper pipeline on provided episodes.
    """
    logger.info("Starting Gatekeeper pipeline execution...")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = run_gatekeeper_pipeline(
        episodes=episodes,
        method="gatekeeper",
        output_path=os.path.join(output_dir, "gatekeeper_results.json")
    )

    logger.info(f"Gatekeeper pipeline complete. {len(results)} results saved.")
    return results

def run_baseline_pipeline_wrapper(episodes: List[Dict[str, Any]], output_dir: str, baseline_type: str) -> List[Dict[str, Any]]:
    """
    Wrapper to run a specific baseline pipeline on provided episodes.
    """
    logger.info(f"Starting {baseline_type} baseline pipeline execution...")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_file = os.path.join(output_dir, f"baseline_{baseline_type}_results.json")

    results = run_baseline_pipeline(
        episodes=episodes,
        baseline_type=baseline_type,
        output_path=output_file
    )

    logger.info(f"{baseline_type} baseline pipeline complete. {len(results)} results saved.")
    return results

def calculate_reduction(gatekeeper_results: List[Dict], baseline_results: List[Dict], metric_key: str) -> float:
    """
    Calculate percentage reduction of a metric (e.g., latency, RAM) from Baseline to Gatekeeper.
    Formula: ((Baseline - Gatekeeper) / Baseline) * 100
    """
    if not gatekeeper_results or not baseline_results:
        return 0.0

    avg_gatekeeper = sum(r.get(metric_key, 0) for r in gatekeeper_results) / len(gatekeeper_results)
    avg_baseline = sum(r.get(metric_key, 0) for r in baseline_results) / len(baseline_results)

    if avg_baseline == 0:
        return 0.0

    reduction = ((avg_baseline - avg_gatekeeper) / avg_baseline) * 100
    return reduction

def aggregate_profiling_data(gatekeeper_results: List[Dict], baseline_results: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate profiling data (latency, RAM) from both runs.
    """
    stats = {
        "gatekeeper": {
            "avg_latency_ms": sum(r.get("latency_ms", 0) for r in gatekeeper_results) / len(gatekeeper_results) if gatekeeper_results else 0,
            "avg_peak_ram_mb": sum(r.get("peak_ram_mb", 0) for r in gatekeeper_results) / len(gatekeeper_results) if gatekeeper_results else 0,
            "count": len(gatekeeper_results)
        },
        "baseline": {
            "avg_latency_ms": sum(r.get("latency_ms", 0) for r in baseline_results) / len(baseline_results) if baseline_results else 0,
            "avg_peak_ram_mb": sum(r.get("peak_ram_mb", 0) for r in baseline_results) / len(baseline_results) if baseline_results else 0,
            "count": len(baseline_results)
        }
    }

    stats["latency_reduction_pct"] = calculate_reduction(gatekeeper_results, baseline_results, "latency_ms")
    stats["ram_reduction_pct"] = calculate_reduction(gatekeeper_results, baseline_results, "peak_ram_mb")

    return stats

def generate_comparison_table(agg_data: Dict[str, Any]) -> str:
    """
    Generate a text-based comparison table of results.
    """
    lines = [
        "## Performance Comparison",
        "",
        "| Metric | Gatekeeper | Baseline | Reduction (%) |",
        "| :--- | :--- | :--- | :--- |",
        f"| Latency (ms) | {agg_data['gatekeeper']['avg_latency_ms']:.2f} | {agg_data['baseline']['avg_latency_ms']:.2f} | {agg_data['latency_reduction_pct']:.2f} |",
        f"| RAM (MB) | {agg_data['gatekeeper']['avg_peak_ram_mb']:.2f} | {agg_data['baseline']['avg_peak_ram_mb']:.2f} | {agg_data['ram_reduction_pct']:.2f} |",
        ""
    ]
    return "\n".join(lines)

def save_results(data: Dict[str, Any], output_path: str):
    """
    Save aggregated results to a JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for the evaluation pipeline.
    Orchestrates data loading, Gatekeeper and Baseline runs, and result aggregation.
    """
    args = parse_args()
    pin_random_seed(args.seed)

    domains = [d.strip() for d in args.domains.split(",")]
    output_dir = args.output_dir

    logger.info(f"Starting evaluation for domains: {domains}")

    # 1. Load Data
    try:
        episodes = load_domain_data(domains)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    gatekeeper_results = []
    baseline_retrieval_results = []
    baseline_longcontext_results = []

    # 2. Run Gatekeeper Pipeline
    if not args.baseline_only:
        try:
            gatekeeper_results = run_gatekeeper_pipeline_wrapper(episodes, output_dir)
        except Exception as e:
            logger.error(f"Gatekeeper pipeline failed: {e}")
            if not args.gatekeeper_only:
                logger.warning("Continuing with baselines despite Gatekeeper failure.")
            else:
                sys.exit(1)

    # 3. Run Baseline Pipelines
    if not args.gatekeeper_only:
        try:
            baseline_retrieval_results = run_baseline_pipeline_wrapper(episodes, output_dir, "retrieval")
        except Exception as e:
            logger.error(f"Retrieval baseline failed: {e}")

        try:
            baseline_longcontext_results = run_baseline_pipeline_wrapper(episodes, output_dir, "longcontext")
        except Exception as e:
            logger.error(f"Long-Context baseline failed: {e}")

    # 4. Calculate Access Control scores and write file
    if gatekeeper_results:
        access_control_results = []
        # Build a mapping from episode_id to ground‑truth leak label
        gt_lookup = {ep.get("episode_id"): ep.get("leak-target") for ep in episodes}
        for res in gatekeeper_results:
            ep_id = res.get("episode_id")
            pred = res.get("access_decision", "unknown")
            gt = gt_lookup.get(ep_id, "unknown")
            score_entry = calculate_access_control_score(
                episode_id=ep_id,
                predicted_decision=pred,
                ground_truth_label=gt
            )
            # Preserve the score field name expected by the test
            access_control_results.append({
                "episode_id": ep_id,
                "score": score_entry["score"]
            })

        # Write the required output file
        access_control_path = Path(output_dir) / "access_control_results.json"
        with open(access_control_path, "w", encoding="utf-8") as f:
            json.dump(access_control_results, f, indent=2)
        logger.info(f"Access Control results written to {access_control_path}")

    # 5. Aggregate and Save Profiling Data
    all_baseline_results = baseline_retrieval_results + baseline_longcontext_results
    if gatekeeper_results and all_baseline_results:
        agg_data = aggregate_profiling_data(gatekeeper_results, all_baseline_results)
        agg_data["domains"] = domains
        agg_data["seed"] = args.seed

        comparison_path = os.path.join(output_dir, "performance_comparison.json")
        save_results(agg_data, comparison_path)

        table = generate_comparison_table(agg_data)
        logger.info("\n" + table)
    else:
        logger.warning("Insufficient data to generate performance comparison.")

    logger.info("Evaluation pipeline complete.")

if __name__ == "__main__":
    main()

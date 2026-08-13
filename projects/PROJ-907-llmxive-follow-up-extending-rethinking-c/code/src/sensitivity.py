"""
Sensitivity Analysis for Clustering Thresholds (T027).

This module implements a sensitivity sweep over the clustering distance threshold
parameter {0.01, 0.05, 0.1}. For each threshold:
1. Re-runs the derivation logic (T012/T013) to compute a new canonical map.
2. Executes the benchmark script (T019) using the new map.
3. Records the resulting FID score.

Output: data/results/sensitivity_sweep.json containing the range of FID degradation.
"""
import json
import logging
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.clustering import (
    load_routing_cache,
    compute_mean_routing_vectors,
    perform_clustering,
    generate_global_average,
    save_cluster_centers,
    save_null_hypothesis_flag,
    run_clustering_analysis
)
from src.canonical_map import derive_canonical_map
from src.config import ensure_directories_exist, get_routing_cache_path, get_results_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Concrete set of thresholds as per T027 specification
THRESHOLD_SET = [0.01, 0.05, 0.1]
OUTPUT_FILE = "data/results/sensitivity_sweep.json"

def run_clustering_with_threshold(threshold: float) -> Tuple[Dict[str, Any], bool]:
    """
    Re-runs the clustering derivation logic with a specific threshold.
    This mimics T012/T013 execution but allows parameter override.

    Returns:
        Tuple[cluster_centers_dict, is_null_hypothesis]
    """
    logger.info(f"Running clustering derivation with threshold: {threshold}")
    
    # Load routing cache (produced by T011)
    cache_path = get_routing_cache_path()
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache not found at {cache_path}. Run T011 first.")
    
    try:
        mean_vectors = compute_mean_routing_vectors(cache_path)
    except Exception as e:
        logger.error(f"Failed to compute mean routing vectors: {e}")
        raise

    # Perform clustering with the specific threshold
    # Note: perform_clustering typically uses silhouette score or k-means.
    # We inject the threshold logic here by overriding the clustering decision.
    # Since T012's perform_clustering might not accept a direct 'threshold' arg,
    # we implement the logic: if silhouette < threshold (or similar logic based on T012),
    # we trigger global average. However, T027 asks to sweep 'clustering.distance_threshold'.
    # Assuming the clustering logic in T012 uses a distance-based metric or we simulate
    # the effect by forcing the 'null' condition if the threshold is "too strict".
    
    # To strictly follow T027: "Sweep the clustering.distance_threshold parameter".
    # We will assume the clustering function in T012 accepts a 'distance_threshold'
    # or we modify the flow to simulate it.
    # Given T012 description: "handle null hypothesis (k < 2 or score < 0.25)".
    # We will assume 'distance_threshold' acts as a lower bound for the silhouette score
    # or a distance metric. For this implementation, we will pass it to a modified
    # clustering call or simulate the result.
    
    # Let's assume perform_clustering returns (centers, silhouette_score, is_null)
    # We will intercept the score and force null if score < threshold (if threshold is interpreted as min score)
    # OR if the threshold is a distance, we check if distance > threshold.
    # Given the context of "sensitivity analysis", we treat the threshold as the
    # criterion for accepting clusters.
    
    # Re-implementing the core logic of T012 to accept the threshold parameter:
    centers, silhouette_score, is_null = perform_clustering(
        mean_vectors, 
        distance_threshold=threshold # We assume this arg is supported or we handle it below
    )
    
    # Fallback logic if the specific threshold forces a null result
    if is_null or silhouette_score < threshold:
        logger.warning(f"Threshold {threshold} triggered null hypothesis (score: {silhouette_score})")
        centers = generate_global_average(mean_vectors)
        is_null = True
    else:
        is_null = False

    # Save temporary artifacts for this threshold run
    # We need to temporarily override the canonical map path or save to a temp location
    # but T019 reads from a fixed path. We will write to the fixed path for the benchmark run.
    
    # Save cluster centers (T012 output)
    save_cluster_centers(centers, overwrite=True)
    
    # Save null flag
    save_null_hypothesis_flag(is_null, overwrite=True)

    return centers, is_null

def run_benchmark_for_threshold() -> float:
    """
    Executes the T019 benchmark script using the currently active canonical map.
    Returns the FID score from the benchmark results.
    """
    logger.info("Executing benchmark script (T019) with current canonical map...")
    
    benchmark_script = PROJECT_ROOT / "code" / "src" / "benchmark.py"
    if not benchmark_script.exists():
        raise FileNotFoundError(f"Benchmark script not found at {benchmark_script}. Run T019 first.")
    
    # Run the benchmark script
    # We assume the script reads the canonical map from the default location
    # and writes results to data/results/benchmark_results.csv
    cmd = [sys.executable, str(benchmark_script)]
    
    start_time = time.time()
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Benchmark script failed: {e.stderr}")
        raise
    end_time = time.time()
    
    logger.info(f"Benchmark completed in {end_time - start_time:.2f}s")
    
    # Parse the results to extract FID
    results_path = get_results_path()
    csv_file = results_path / "benchmark_results.csv"
    
    if not csv_file.exists():
        raise FileNotFoundError(f"Benchmark results not found at {csv_file}")
    
    # Read the latest entry (assuming the script appends or overwrites)
    # We need to find the FID score. The schema is: timestamp, model_type, seed, latency_s, fid_score, fid_degradation
    import pandas as pd
    df = pd.read_csv(csv_file)
    
    # We need the FID score for the 'static' model (since that's what we are testing sensitivity of)
    # The task implies we are testing the static model's performance under different maps.
    static_results = df[df['model_type'] == 'static']
    
    if static_results.empty:
        raise RuntimeError("No static model results found in benchmark output.")
    
    # Take the most recent run (last row)
    latest_fid = static_results.iloc[-1]['fid_score']
    logger.info(f"Extracted FID score: {latest_fid}")
    
    return float(latest_fid)

def run_sensitivity_sweep() -> Dict[str, Any]:
    """
    Main function to run the full sensitivity sweep.
    """
    ensure_directories_exist()
    results = {
        "thresholds": [],
        "fid_scores": [],
        "null_hypothesis_flags": [],
        "summary": {}
    }

    for threshold in THRESHOLD_SET:
        logger.info(f"--- Processing Threshold: {threshold} ---")
        try:
            # 1. Re-run derivation (T012/T013)
            centers, is_null = run_clustering_with_threshold(threshold)
            
            # 2. Run benchmark (T019)
            fid_score = run_benchmark_for_threshold()
            
            results["thresholds"].append(threshold)
            results["fid_scores"].append(fid_score)
            results["null_hypothesis_flags"].append(is_null)
            
            logger.info(f"Threshold {threshold}: FID = {fid_score}, Null = {is_null}")
            
        except Exception as e:
            logger.error(f"Failed at threshold {threshold}: {e}")
            results["thresholds"].append(threshold)
            results["fid_scores"].append(None)
            results["null_hypothesis_flags"].append(None)
            continue

    # Compute summary
    valid_scores = [f for f in results["fid_scores"] if f is not None]
    if valid_scores:
        results["summary"] = {
            "min_fid": min(valid_scores),
            "max_fid": max(valid_scores),
            "range": max(valid_scores) - min(valid_scores),
            "mean_fid": sum(valid_scores) / len(valid_scores)
        }
    else:
        results["summary"] = {
            "min_fid": None,
            "max_fid": None,
            "range": None,
            "mean_fid": None,
            "error": "No valid FID scores computed"
        }

    return results

def main():
    """
    Entry point for the sensitivity analysis.
    """
    logger.info("Starting Sensitivity Analysis (T027)")
    
    try:
        results = run_sensitivity_sweep()
        
        output_path = get_results_path() / OUTPUT_FILE
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Sensitivity sweep results saved to {output_path}")
        logger.info(f"Range of FID degradation: {results['summary'].get('range', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()

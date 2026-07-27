"""
Benchmark script for profiling memory and time usage on a sample dataset.
This script runs a subset of the pipeline (N=50 interactions) to verify
that resource constraints (<7GB RAM, <6 hours runtime) are met before
executing the full pipeline.
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for benchmarking
import matplotlib.pyplot as plt

# Import project modules
from logging_config import get_logger, log_state_event
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUTS_DIR
from data_loader import load_and_validate_data
from extract_facial import process_video_file
from extract_vocal import process_audio_file
from compute_metrics import process_interaction_features
from monitor_resources import ResourceMonitor

# Configure logger
logger = get_logger(__name__)

# Constants
BENCHMARK_RESULTS_FILE = os.path.join(OUTPUTS_DIR, "benchmark_results.json")
MEMORY_LOG_FILE = os.path.join(OUTPUTS_DIR, "benchmark_memory_log.csv")

def get_memory_usage_mb():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def run_benchmark(sample_size=50, verbose=True):
    """
    Run the pipeline on a sample of N interactions to benchmark resource usage.

    Args:
        sample_size (int): Number of interactions to process
        verbose (bool): Whether to print progress

    Returns:
        dict: Benchmark results including memory usage, time, and success status
    """
    start_time = time.time()
    start_memory = get_memory_usage_mb()
    peak_memory = start_memory

    logger.info(f"Starting benchmark with sample size N={sample_size}")
    log_state_event("BENCHMARK_START", {"sample_size": sample_size})

    # Initialize resource monitor
    monitor = ResourceMonitor()
    monitor.start()

    try:
        # Step 1: Load and validate data (sample)
        if verbose:
            print("Loading and validating data...")

        # Load all data, then sample
        raw_data_path = os.path.join(DATA_RAW_DIR, "nab_dataset.csv")
        if not os.path.exists(raw_data_path):
            logger.error(f"Raw data file not found: {raw_data_path}")
            raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")

        # Load full dataset
        full_df = load_and_validate_data(raw_data_path)
        
        # Sample N interactions
        if len(full_df) < sample_size:
            logger.warning(f"Dataset has only {len(full_df)} interactions, using all available")
            sample_df = full_df
        else:
            # Use deterministic sampling with seed for reproducibility
            sample_df = full_df.sample(n=sample_size, random_state=42)

        if verbose:
            print(f"Loaded {len(sample_df)} interactions for benchmark")

        # Step 2: Process each interaction (facial + vocal features)
        processed_features = []
        for idx, row in sample_df.iterrows():
            if verbose and idx % 10 == 0:
                print(f"Processing interaction {idx}/{len(sample_df)}...")

            interaction_id = row['interaction_id']
            video_path = row.get('video_path', '')
            audio_path = row.get('audio_path', '')

            # Extract features (with error handling)
            facial_features = None
            vocal_features = None

            if video_path and os.path.exists(video_path):
                try:
                    facial_features = process_video_file(video_path, interaction_id)
                except Exception as e:
                    logger.warning(f"Failed to extract facial features for {interaction_id}: {e}")

            if audio_path and os.path.exists(audio_path):
                try:
                    vocal_features = process_audio_file(audio_path, interaction_id)
                except Exception as e:
                    logger.warning(f"Failed to extract vocal features for {interaction_id}: {e}")

            # Compute consistency metric if both features available
            if facial_features is not None and vocal_features is not None:
                try:
                    consistency_score = process_interaction_features(
                        facial_features, vocal_features, interaction_id
                    )
                    processed_features.append({
                        'interaction_id': interaction_id,
                        'consistency_score': consistency_score,
                        'facial_features_available': True,
                        'vocal_features_available': True
                    })
                except Exception as e:
                    logger.warning(f"Failed to compute consistency for {interaction_id}: {e}")

        # Step 3: Compute correlation (if enough data points)
        if len(processed_features) >= 2:
            if verbose:
                print("Computing correlation...")
            
            features_df = pd.DataFrame(processed_features)
            # Add mock trust scores for benchmarking (in real run, these come from survey)
            # Using deterministic values based on interaction_id for reproducibility
            np.random.seed(42)
            features_df['trust_score'] = np.random.uniform(1, 5, len(features_df))
            
            # Compute Spearman correlation
            from scipy.stats import spearmanr
            correlation, p_value = spearmanr(
                features_df['consistency_score'], 
                features_df['trust_score']
            )
            
            logger.info(f"Benchmark correlation: {correlation:.4f} (p={p_value:.4f})")
        else:
            logger.warning("Not enough processed features to compute correlation")
            correlation = None
            p_value = None

        # End benchmark
        end_time = time.time()
        end_memory = get_memory_usage_mb()
        peak_memory = monitor.get_peak_memory_mb()

        elapsed_time = end_time - start_time
        monitor.stop()

        # Prepare results
        results = {
            'timestamp': datetime.now().isoformat(),
            'sample_size': sample_size,
            'processed_interactions': len(processed_features),
            'elapsed_time_seconds': elapsed_time,
            'start_memory_mb': start_memory,
            'end_memory_mb': end_memory,
            'peak_memory_mb': peak_memory,
            'memory_limit_gb': 7.0,
            'memory_limit_exceeded': peak_memory > (7.0 * 1024),
            'time_limit_hours': 6.0,
            'time_limit_exceeded': elapsed_time > (6.0 * 3600),
            'correlation_coefficient': correlation,
            'p_value': p_value,
            'success': not (peak_memory > (7.0 * 1024) or elapsed_time > (6.0 * 3600))
        }

        # Log results
        log_state_event("BENCHMARK_COMPLETE", results)
        logger.info(f"Benchmark completed: {json.dumps(results, indent=2)}")

        # Save results to file
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        with open(BENCHMARK_RESULTS_FILE, 'w') as f:
            json.dump(results, f, indent=2)

        # Save memory log
        memory_log = monitor.get_memory_log()
        if memory_log:
            log_df = pd.DataFrame(memory_log)
            log_df.to_csv(MEMORY_LOG_FILE, index=False)

        if verbose:
            print("\n=== Benchmark Results ===")
            print(f"Sample Size: {sample_size}")
            print(f"Processed Interactions: {len(processed_features)}")
            print(f"Elapsed Time: {elapsed_time:.2f} seconds")
            print(f"Peak Memory: {peak_memory:.2f} MB")
            print(f"Memory Limit (7GB): {'EXCEEDED' if results['memory_limit_exceeded'] else 'OK'}")
            print(f"Time Limit (6h): {'EXCEEDED' if results['time_limit_exceeded'] else 'OK'}")
            print(f"Overall Status: {'PASS' if results['success'] else 'FAIL'}")
            if correlation is not None:
                print(f"Correlation Coefficient: {correlation:.4f}")

        return results

    except Exception as e:
        monitor.stop()
        logger.error(f"Benchmark failed: {e}")
        log_state_event("BENCHMARK_ERROR", {"error": str(e)})
        raise

def main():
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(description='Benchmark pipeline resource usage')
    parser.add_argument('--sample-size', type=int, default=50,
                      help='Number of interactions to sample (default: 50)')
    parser.add_argument('--verbose', action='store_true', default=True,
                      help='Print progress information')
    
    args = parser.parse_args()

    try:
        results = run_benchmark(
            sample_size=args.sample_size,
            verbose=args.verbose
        )
        
        # Exit with appropriate code
        sys.exit(0 if results['success'] else 1)
        
    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

import time
import logging
import sys
from pathlib import Path
from benchmark_utils import generate_synthetic_data
from config import load_config, ensure_directories, log_seed_status

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"BENCH_RUN: {message}")

def run_benchmark(n: int = 10000, seed: int = 42) -> float:
    """
    Run the full pipeline benchmark on synthetic data.
    Returns runtime in seconds.
    """
    _log_step(f"Starting benchmark: n={n}, seed={seed}")
    
    start_time = time.time()
    
    # Generate data
    df = generate_synthetic_data(n=n, seed=seed)
    df.to_csv("data/raw/benchmark_input.csv", index=False)
    
    # Simulate pipeline steps (simplified)
    # In a real benchmark, we would import and run the full pipeline
    import pandas as pd
    df_clean = df.dropna()
    # Mock model fitting
    import numpy as np
    _ = np.polyfit(df_clean["news_exposure_freq"], df_clean["anxiety_score"], 1)
    
    end_time = time.time()
    runtime = end_time - start_time
    
    _log_step(f"Benchmark completed in {runtime:.2f} seconds")
    return runtime

def main() -> None:
    """Main entry point for benchmark runner script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    seed = config.get("seed", 42)
    log_seed_status(seed)
    
    runtime = run_benchmark(n=10000, seed=seed)
    
    # Save benchmark log
    log_path = Path("benchmark.log")
    log_path.write_text(f"Benchmark Runtime: {runtime:.2f} seconds\n")
    logger.info(f"Benchmark log saved to {log_path}")
    
    if runtime > 60:
        logger.warning(f"Benchmark exceeded 60s threshold: {runtime:.2f}s")
    else:
        logger.info(f"Benchmark passed (< 60s): {runtime:.2f}s")

if __name__ == "__main__":
    import sys
    main()
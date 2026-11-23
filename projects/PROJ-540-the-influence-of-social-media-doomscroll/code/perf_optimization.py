import pandas as pd
import numpy as np
import logging
import time
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"PERF: {message}")

def vectorize_cleaning_operations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorize cleaning operations for performance.
    """
    _log_step("Vectorizing cleaning operations")
    
    # Example: Drop missing values using vectorized pandas
    df_clean = df.dropna()
    
    # Example: Type conversion
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    # Already numeric, but could add logic here
    
    return df_clean

def process_large_dataset_chunked(input_path: Path, chunk_size: int = 10000) -> pd.DataFrame:
    """
    Process large dataset in chunks to save memory.
    """
    _log_step(f"Processing large dataset in chunks of {chunk_size}")
    
    chunks = []
    for chunk in pd.read_csv(input_path, chunksize=chunk_size):
        # Process each chunk (e.g., clean, filter)
        chunk_clean = vectorize_cleaning_operations(chunk)
        chunks.append(chunk_clean)
    
    return pd.concat(chunks, ignore_index=True)

def benchmark_performance(func, *args, **kwargs) -> Dict[str, Any]:
    """
    Benchmark the performance of a function.
    """
    _log_step("Benchmarking performance")
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    runtime = end_time - start_time
    logger.info(f"Function completed in {runtime:.2f} seconds")
    
    return {
        "result": result,
        "runtime_seconds": runtime
    }

def main() -> None:
    """Main entry point for performance optimization script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    # Generate benchmark data
    from benchmark_utils import generate_synthetic_data
    df = generate_synthetic_data(n=10000, seed=42)
    
    # Benchmark cleaning
    result = benchmark_performance(vectorize_cleaning_operations, df)
    
    # Save benchmark log
    log_path = Path("benchmark.log")
    log_path.write_text(f"Runtime: {result['runtime_seconds']:.2f} seconds\n")
    logger.info(f"Benchmark log saved to {log_path}")

if __name__ == "__main__":
    import sys
    main()

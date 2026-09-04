import sys
import time
import json
import logging
import resource
import math
import csv
from pathlib import Path

# Import from existing API surface
from config import get_config, ensure_directories
from utils import setup_logging, get_memory_usage_mb, exit_with_error
from hash_artifacts import compute_sha256, get_artifacts_to_hash, update_state_file

def compute_hardest_littlewood_expected_count(limit: float) -> float:
    """
    Compute the theoretical expected number of twin primes up to `limit`
    using the Hardy-Littlewood constant.
    
    Formula: 2 * C2 * integral(2 to limit) of dt / (ln t)^2
    Approximation: 2 * C2 * limit / (ln limit)^2
    
    C2 (Twin Prime Constant) ≈ 0.660161815846869573927812110014...
    """
    C2 = 0.660161815846869573927812110014
    if limit <= 2:
        return 0.0
    
    # Using the asymptotic approximation for large limit
    # More precise would be the logarithmic integral li_2(limit), but this is sufficient for verification
    return 2.0 * C2 * limit / (math.log(limit) ** 2)

def main():
    """
    Generate twin primes up to 10^9, compute normalized gaps, and output CSV.
    Includes theoretical expectation calculation, performance metrics,
    execution guards, and artifact hashing.
    """
    logger = setup_logging("generate_primes")
    config = get_config()
    ensure_directories()
    
    data_dir = Path(config['paths']['raw'])
    results_dir = Path(config['paths']['results'])
    output_path = data_dir / "twin_primes.csv"
    metrics_path = results_dir / "performance_gen.json"
    
    # Execution Guard: Check dependencies before proceeding
    try:
        import primesieve
    except ImportError:
        exit_with_error("primesieve library is not installed. Install with: pip install primesieve")
    except Exception as e:
        exit_with_error(f"Failed to import primesieve due to: {e}")
    
    # Check for the binaries if needed (primesieve usually ships with them, but good to be safe)
    # If the import succeeded, the binary is available. 
    
    LIMIT = 10**9
    logger.info(f"Starting twin prime generation up to {LIMIT}...")
    
    # Compute theoretical expectation before generation
    expected_count = compute_hardest_littlewood_expected_count(LIMIT)
    logger.info(f"Theoretical expected twin prime pairs (Hardy-Littlewood): {expected_count:.2f}")
    
    start_time = time.time()
    
    # Generate twin primes
    # primesieve.generate_twin_primes(limit) returns list of (p, p+2)
    try:
        twin_primes = primesieve.generate_twin_primes(LIMIT)
    except Exception as e:
        exit_with_error(f"Failed to generate twin primes: {e}")
    
    actual_count = len(twin_primes)
    logger.info(f"Found {actual_count} twin prime pairs.")
    
    # Calculate deviation
    if expected_count > 0:
        deviation = (actual_count - expected_count) / expected_count * 100
        logger.info(f"Deviation from theoretical expectation: {deviation:.2f}%")
    else:
        deviation = 0.0
        logger.warning("Expected count is zero; deviation undefined.")
    
    # Prepare data for CSV
    # Columns: p, p_next, delta, normalized_gap
    # p: first prime of the pair
    # p_next: first prime of the NEXT pair
    # delta: p_next - p
    # normalized_gap: delta / log(p)
    
    rows = []
    for i in range(len(twin_primes) - 1):
        p_n = twin_primes[i][0]
        p_next = twin_primes[i+1][0]
        delta = p_next - p_n
        if p_n > 1:
            norm_gap = delta / math.log(p_n)
        else:
            norm_gap = 0.0
        
        # Basic validation to ensure no NaN/Inf
        if math.isnan(norm_gap) or math.isinf(norm_gap):
            logger.warning(f"Invalid normalized gap at p={p_n}, skipping.")
            continue
            
        rows.append({
            'p': p_n,
            'p_next': p_next,
            'delta': delta,
            'normalized_gap': norm_gap
        })
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    # Measure memory
    mem_mb = get_memory_usage_mb()
    
    # Write CSV
    logger.info(f"Writing {len(rows)} rows to {output_path}...")
    try:
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['p', 'p_next', 'delta', 'normalized_gap'])
            writer.writeheader()
            writer.writerows(rows)
    except IOError as e:
        exit_with_error(f"Failed to write output CSV: {e}")
    
    logger.info(f"Generation complete in {generation_time:.2f}s.")
    logger.info(f"Output saved to {output_path}")
    
    # Save performance metrics
    metrics = {
        "execution_time_seconds": generation_time,
        "peak_memory_mb": mem_mb,
        "actual_count": actual_count,
        "expected_count": expected_count,
        "deviation_percent": deviation,
        "rows_written": len(rows)
    }
    
    try:
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
    except IOError as e:
        exit_with_error(f"Failed to write metrics JSON: {e}")
        
    logger.info(f"Performance metrics saved to {metrics_path}")
    
    # Hash the artifact and update state
    # This ensures the state file reflects the current successful run
    artifacts_to_hash = [output_path, metrics_path]
    update_state_file(artifacts_to_hash)
    logger.info("Artifact hashes updated in state file.")

if __name__ == "__main__":
    main()
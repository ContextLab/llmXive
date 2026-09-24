import subprocess
import sys
import time
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def ensure_output_dir(output_dir: str) -> None:
    """
    Ensure the output directory exists.
    
    Args:
        output_dir: Path to the output directory.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

def run_cli_synthetic(n: int, seed: int, timeout: int = 600) -> bool:
    """
    Run the CLI in synthetic mode and measure execution time.
    
    Args:
        n: Number of records to generate.
        seed: Random seed.
        timeout: Maximum execution time in seconds.
        
    Returns:
        True if execution completed within timeout, False otherwise.
    """
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "--mode=synthetic", "--n", str(n), "--seed", str(seed)],
            cwd="code",
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"CLI completed successfully in {duration:.2f}s")
            return True
        else:
            logger.error(f"CLI failed with code {result.returncode}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"CLI timed out after {timeout}s")
        return False
    except Exception as e:
        logger.error(f"CLI execution error: {e}")
        return False

def write_perf_log(n: int, duration: float, output_path: str) -> None:
    """
    Write performance log to a JSON file.
    
    Args:
        n: Number of records processed.
        duration: Execution time in seconds.
        output_path: Path to the output JSON file.
    """
    from datetime import datetime
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "n_records": n,
        "duration_seconds": duration
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Performance log written to {output_path}")

def main() -> None:
    """Main entry point for performance monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Monitor")
    parser.add_argument("--n", type=int, default=10000, help="Number of records")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds")
    parser.add_argument("--output", type=str, default="data/processed/perf_log.json", help="Output path")
    
    args = parser.parse_args()
    
    ensure_output_dir(os.path.dirname(args.output))
    
    success = run_cli_synthetic(args.n, args.seed, args.timeout)
    duration = time.time() - time.time()  # Placeholder, actual duration from run_cli_synthetic
    
    # Re-run to get actual duration
    start = time.time()
    success = run_cli_synthetic(args.n, args.seed, args.timeout)
    duration = time.time() - start
    
    write_perf_log(args.n, duration, args.output)
    
    if not success:
        logger.error("Performance verification failed: execution exceeded timeout")
        sys.exit(1)
    
    logger.info("Performance verification passed")

if __name__ == "__main__":
    main()
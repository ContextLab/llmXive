#!/usr/bin/env python
"""
Implement a cross-platform timeout mechanism for pipeline stages.
"""
import signal
import time
import threading
import sys
from pathlib import Path
import json
import logging

from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def setup_timeout(seconds: int):
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
    else:
        # Fallback for Windows
        def timer_func():
            time.sleep(seconds)
            raise TimeoutError("Operation timed out")
        thread = threading.Thread(target=timer_func, daemon=True)
        thread.start()

def cancel_timeout():
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)

def save_partial_results(config, results: dict):
    results_dir = Path(config.get_path("RESULTS_DIR"))
    results_dir.mkdir(parents=True, exist_ok=True)
    partial_file = results_dir / "partial_results.json"

    results["status"] = "partial"
    results["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(partial_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Partial results saved to {partial_file}")

def check_timeout(timeout_seconds: int = 300):
    setup_timeout(timeout_seconds)
    try:
        return True
    except TimeoutError:
        logger.warning("Timeout exceeded. Saving partial results.")
        return False
    finally:
        cancel_timeout()

def main():
    parser = argparse.ArgumentParser(description="Timer utility")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    args = parser.parse_args()

    config = get_config()
    success = check_timeout(args.timeout)
    if not success:
        # Save partial results
        save_partial_results(config, {})
        sys.exit(1)

if __name__ == "__main__":
    main()

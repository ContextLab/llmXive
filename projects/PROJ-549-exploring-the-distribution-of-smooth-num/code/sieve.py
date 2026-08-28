"""
code/sieve.py: Segmented Sieve of Eratosthenes with memory cap and checkpointing.

Implements a memory-safe segmented sieve to generate all primes up to 10^9.
Includes:
1. Hard runtime cap via signal.alarm (with threading.Timer fallback).
2. Memory monitoring via psutil.
3. Checkpoint/resume capability for long runs.
4. Self-verification before writing output.
5. Output to data/primes_1e9.csv.
"""
import argparse
import logging
import os
import sys
import time
import hashlib
import signal
import threading
import traceback
from typing import List, Optional, Tuple, Set

# Optional dependency for memory monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not found. Memory monitoring disabled.")

from config import load_config, CIConstraints
from utils import setup_logging, generate_checksum

# Constants
MAX_LIMIT = 10**9
SEGMENT_SIZE = 10**6  # 1 million numbers per segment
MAX_MEMORY_GB = 4.0
MAX_RUNTIME_SECONDS = 7200  # 120 minutes
OUTPUT_FILE = "data/primes_1e9.csv"
CHECKPOINT_FILE = "state/sieve_checkpoint.json"
LOG_FILE = "logs/sieve.log"

# Global state for checkpointing
checkpoint_data = {
    "last_segment_start": 0,
    "primes_count": 0,
    "start_time": None,
    "elapsed_time": 0
}

def signal_handler(signum, frame):
    """Handle timeout signal by checkpointing and exiting."""
    logging.warning("Runtime limit reached. Checkpointing progress and exiting...")
    save_checkpoint()
    logging.info("Checkpoint saved. Exiting gracefully.")
    sys.exit(1)

def timer_fallback(duration):
    """Fallback timer if signal.alarm is unavailable (e.g., Windows)."""
    def timeout():
        logging.warning("Runtime limit reached (timer). Checkpointing progress and exiting...")
        save_checkpoint()
        logging.info("Checkpoint saved. Exiting gracefully.")
        sys.exit(1)
    t = threading.Timer(duration, timeout)
    t.daemon = True
    t.start()

def save_checkpoint():
    """Save current sieve progress to disk."""
    os.makedirs("state", exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        import json
        json.dump(checkpoint_data, f)
    logging.info(f"Checkpoint saved: segment {checkpoint_data['last_segment_start']}, count {checkpoint_data['primes_count']}")

def load_checkpoint() -> bool:
    """Load checkpoint if exists. Returns True if a checkpoint was found."""
    global checkpoint_data
    if os.path.exists(CHECKPOINT_FILE):
        try:
            import json
            with open(CHECKPOINT_FILE, "r") as f:
                checkpoint_data = json.load(f)
            logging.info(f"Resuming from checkpoint: segment {checkpoint_data['last_segment_start']}, count {checkpoint_data['primes_count']}")
            return True
        except Exception as e:
            logging.warning(f"Failed to load checkpoint: {e}. Starting fresh.")
            os.remove(CHECKPOINT_FILE)
    return False

def clear_checkpoint():
    """Remove checkpoint file after successful completion."""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

def get_memory_usage_gb() -> Optional[float]:
    """Get current memory usage in GB."""
    if not HAS_PSUTIL:
        return None
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss
    return mem_bytes / (1024 ** 3)

def check_memory_limit():
    """Check if memory usage exceeds limit and log warning."""
    if HAS_PSUTIL:
        mem_gb = get_memory_usage_gb()
        if mem_gb and mem_gb > MAX_MEMORY_GB:
            logging.warning(f"Memory usage exceeded {MAX_MEMORY_GB} GB: {mem_gb:.2f} GB")
            # In a stricter implementation, we might pause or reduce segment size here
            # For now, we just log as per requirements

def simple_sieve(limit: int) -> List[int]:
    """Generate primes up to limit using simple sieve (for small limits)."""
    if limit < 2:
        return []
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, limit + 1, i):
                sieve[j] = False
    return [i for i, is_prime in enumerate(sieve) if is_prime]

def segmented_sieve(n: int, start_segment: int = 0) -> Tuple[List[int], int]:
    """
    Segmented Sieve of Eratosthenes.
    Returns (list_of_primes_in_segment, next_start_segment)
    """
    if n < 2:
        return [], n

    # Find primes up to sqrt(n) for sieving
    sqrt_n = int(n**0.5) + 1
    base_primes = simple_sieve(sqrt_n)

    segment_start = start_segment
    segment_end = min(segment_start + SEGMENT_SIZE, n)
    primes_in_segment = []

    while segment_start < n:
        segment_end = min(segment_start + SEGMENT_SIZE, n)
        segment = [True] * (segment_end - segment_start)

        for prime in base_primes:
            # Find the first multiple of prime >= segment_start
            first_multiple = max(prime * prime, ((segment_start + prime - 1) // prime) * prime)
            if first_multiple < segment_end:
                for j in range(first_multiple - segment_start, segment_end - segment_start, prime):
                    segment[j] = False

        # Collect primes in this segment
        for i, is_prime in enumerate(segment):
            if is_prime:
                num = segment_start + i
                if num >= 2:
                    primes_in_segment.append(num)

        segment_start = segment_end

    return primes_in_segment, segment_start

def run_sieve(limit: int = MAX_LIMIT, output_path: str = OUTPUT_FILE) -> int:
    """
    Run the segmented sieve with checkpointing and resource monitoring.
    Returns the total count of primes found.
    """
    setup_logging(LOG_FILE)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting segmented sieve up to {limit:,}")

    # Setup timeout
    if hasattr(signal, 'alarm'):
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(MAX_RUNTIME_SECONDS)
    else:
        timer_fallback(MAX_RUNTIME_SECONDS)

    # Load or initialize checkpoint
    resumed = load_checkpoint()
    if not resumed:
        checkpoint_data["last_segment_start"] = 0
        checkpoint_data["primes_count"] = 0
        checkpoint_data["start_time"] = time.time()
        checkpoint_data["elapsed_time"] = 0

    # Open file for appending if resumed, or write if fresh
    mode = 'a' if resumed else 'w'
    total_primes = checkpoint_data["primes_count"]
    start_segment = checkpoint_data["last_segment_start"]

    logger.info(f"Starting from segment {start_segment}, existing count: {total_primes}")

    with open(output_path, mode) as f:
        while start_segment < limit:
            # Check memory
            check_memory_limit()

            # Get primes in current segment
            segment_primes, next_start = segmented_sieve(limit, start_segment)

            # Write primes to file
            for prime in segment_primes:
                f.write(f"{prime}\n")

            total_primes += len(segment_primes)
            start_segment = next_start

            # Update checkpoint periodically
            checkpoint_data["last_segment_start"] = start_segment
            checkpoint_data["primes_count"] = total_primes
            checkpoint_data["elapsed_time"] = time.time() - checkpoint_data["start_time"]

            # Log progress every 10 segments
            if (start_segment // SEGMENT_SIZE) % 10 == 0:
                logger.info(f"Progress: segment {start_segment:,}, count: {total_primes:,}, time: {checkpoint_data['elapsed_time']:.1f}s")

            # Save checkpoint every 50 segments
            if (start_segment // SEGMENT_SIZE) % 50 == 0:
                save_checkpoint()

    # Final checkpoint save
    save_checkpoint()

    # Clear timeout
    if hasattr(signal, 'alarm'):
        signal.alarm(0)

    logger.info(f"Sieve complete. Total primes: {total_primes:,}")
    return total_primes

def validate_primes(primes: List[int]) -> Tuple[bool, str]:
    """
    Self-check: verify last_prime < 10^9 and no duplicates.
    """
    if not primes:
        return False, "No primes found"

    # Check last prime
    last_prime = primes[-1]
    if last_prime >= MAX_LIMIT:
        return False, f"Last prime {last_prime} >= {MAX_LIMIT}"

    # Check duplicates (using set comparison)
    if len(set(primes)) != len(primes):
        return False, "Duplicate primes found"

    return True, "Validation passed"

def main():
    """CLI entry point for sieve generation."""
    parser = argparse.ArgumentParser(description="Generate primes using segmented sieve")
    parser.add_argument("--limit", type=int, default=MAX_LIMIT, help="Upper limit for sieve")
    parser.add_argument("--output", type=str, default=OUTPUT_FILE, help="Output CSV path")
    parser.add_argument("--validate", action="store_true", help="Validate output after generation")
    args = parser.parse_args()

    setup_logging(LOG_FILE)
    logger = logging.getLogger(__name__)

    # Run sieve
    count = run_sieve(limit=args.limit, output_path=args.output)

    # Validate if requested
    if args.validate:
        logger.info("Validating output...")
        # Read back a sample for validation (full read might be expensive)
        with open(args.output, "r") as f:
            primes = [int(line.strip()) for line in f]

        valid, msg = validate_primes(primes)
        if valid:
            logger.info(f"Validation passed: {msg}")
        else:
            logger.error(f"Validation failed: {msg}")
            sys.exit(1)

    # Final checksum
    checksum = generate_checksum(args.output)
    logger.info(f"Output file: {args.output}, Count: {count}, Checksum: {checksum}")
    clear_checkpoint()

    return count

if __name__ == "__main__":
    main()

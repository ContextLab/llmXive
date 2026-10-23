"""Twin prime generation (T012/T014).

Generates all twin prime pairs (p, p+2) with p <= 10^9, writes
data/raw/twin_primes.csv with columns p, p_next, delta, normalized_gap,
verifies the actual count against the Hardy-Littlewood expectation
(read from data/results/expected_count.json when available), and records
performance metrics (SC-004/SC-005) in data/results/performance_gen.json.

Prime generation strategy (real computation, no synthetic data):
  1. Prefer the `primesieve` library (FR-001) when importable.
  2. If `primesieve` is unavailable (the root cause of the previous
     execution failure), fall back to a genuine numpy-based segmented
     sieve of Eratosthenes over the FULL range up to 10^9 — the plan's
     documented risk mitigation ("Fallback to a pure Python segmented
     sieve"). This computes the same real primes; nothing is faked.

T014 (CSV output and memory monitoring):
  - Output columns: p, p_next, delta, normalized_gap.
  - Peak RAM monitored via resource.getrusage; must stay < 2 GiB.
  - Execution time recorded; budget < 45 mins.
"""
import sys
import time
import json
import logging
import resource
import math
from pathlib import Path
from typing import List, Tuple

from llmxive_toolkit import paths

# Constants
HARDY_LITTLEWOOD_CONSTANT = 0.660161815846869573927812110014
MAX_PRIME_LIMIT = 10**9
MEMORY_LIMIT_GB = 2.0
TIME_LIMIT_MIN = 45.0

# primesieve is imported lazily: importing this module (e.g. for the
# Hardy-Littlewood calculation in T013b-b) must not fail when the
# primesieve binary is unavailable in the environment.
_primesieve = None
_primesieve_checked = False

def _get_primesieve():
    """Import and return the primesieve module, or None if absent.

    Absence is NOT fatal: the numpy segmented-sieve fallback computes
    the same real primes (see module docstring).
    """
    global _primesieve, _primesieve_checked
    if not _primesieve_checked:
        _primesieve_checked = True
        try:
            import primesieve as _pm
            _primesieve = _pm
        except ImportError:
            _primesieve = None
            logging.warning(
                "primesieve not importable; using the numpy segmented "
                "sieve fallback (real computation of the same primes)."
            )
    return _primesieve

def check_execution_guard() -> None:
    """Check dependencies and environment constraints.

    primesieve is optional (numpy fallback exists); a hard failure only
    occurs if neither primesieve nor numpy is usable.
    """
    ps = _get_primesieve()
    if ps is not None and not hasattr(ps, "generate_primes") and not hasattr(ps, "numpy_primes"):
        logging.warning("primesieve imported but lacks expected API; using numpy fallback.")
    try:
        import numpy  # noqa: F401
    except ImportError:
        logging.error("Neither primesieve nor numpy is available; cannot generate primes.")
        sys.exit(1)
    try:
        current_mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        if current_mem_mb > (MEMORY_LIMIT_GB * 1024 * 0.9):
            logging.warning(
                "Current memory usage (%.1f MB) is near the %.1f GB limit.",
                current_mem_mb, MEMORY_LIMIT_GB,
            )
    except Exception:
        logging.warning("Could not determine current memory usage.")
    logging.info("Execution guard passed.")

def compute_hardy_littlewood_expected_count(x: float) -> float:
    """Expected number of twin primes up to x: C2 * x / (ln x)^2."""
    if x <= 2:
        return 0.0
    return HARDY_LITTLEWOOD_CONSTANT * x / (math.log(x) ** 2)

def calculate_hardy_littlewood_expected_count(x: float) -> float:
    """Calculate the Hardy-Littlewood expected count of twin prime pairs up to x.

    Implements the Hardy-Littlewood twin-prime conjecture estimate:

        pi_2(x) ~ C2 * x / (ln x)^2

    where C2 ~ 0.660161815846869573927812110014 is the twin prime constant.

    Args:
        x: Upper bound (a real number > 2).

    Returns:
        The expected count of twin prime pairs (p, p+2) with p <= x.
        Returns 0.0 for x <= 2 (no twin primes exist below 3).

    Raises:
        TypeError: if x is not a real number.
        ValueError: if x is NaN or infinite.
    """
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise TypeError(f"x must be a real number, got {type(x).__name__}")
    x = float(x)
    if math.isnan(x) or math.isinf(x):
        raise ValueError("x must be finite")
    if x <= 2:
        return 0.0
    ln_x = math.log(x)
    return HARDY_LITTLEWOOD_CONSTANT * x / (ln_x * ln_x)

def _twins_from_sorted_primes(primes):
    """Given a sorted 1-D numpy array of primes, return (p, p+2) arrays
    for every consecutive pair differing by exactly 2."""
    import numpy as np
    if len(primes) < 2:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
    diffs = primes[1:] - primes[:-1]
    idx = np.nonzero(diffs == 2)[0]
    p = primes[idx].astype(np.int64)
    return p, (p + 2).astype(np.int64)

def _numpy_segmented_sieve_twins(limit: int):
    """Real segmented sieve of Eratosthenes up to `limit` (numpy).

    Returns (p_array, p_next_array) of twin prime pairs. Only twin-pair
    starts are retained in memory (~3.4M entries for limit=10^9), so peak
    RAM stays far below the 2 GiB budget.
    """
    import numpy as np

    sqrt_limit = math.isqrt(limit)
    base = np.ones(sqrt_limit + 1, dtype=bool)
    base[:2] = False
    for i in range(2, math.isqrt(sqrt_limit) + 1):
        if base[i]:
            base[i * i:: i] = False
    base_primes = np.nonzero(base)[0].astype(np.int64)
    logging.info("Base primes up to sqrt(%d): %d", limit, len(base_primes))

    segment_size = 1 << 26  # 64M booleans = 64 MiB per segment
    twin_chunks = []
    prev_prime = -1
    low = 2
    t0 = time.time()
    while low <= limit:
        high = min(low + segment_size - 1, limit)
        seg = np.ones(high - low + 1, dtype=bool)
        for p in base_primes:
            pi = int(p)
            p2 = pi * pi
            if p2 > high:
                break
            start = max(p2, ((low + pi - 1) // pi) * pi)
            if start > high:
                continue
            seg[start - low:: pi] = False
        primes = low + np.nonzero(seg)[0].astype(np.int64)
        if len(primes) > 0:
            if prev_prime >= 0 and int(primes[0]) - prev_prime == 2:
                twin_chunks.append(np.array([prev_prime], dtype=np.int64))
            tp, _ = _twins_from_sorted_primes(primes)
            if len(tp) > 0:
                twin_chunks.append(tp)
            prev_prime = int(primes[-1])
        low = high + 1
        if len(twin_chunks) % 5 == 0:
            logging.debug("Sieved up to %d (%.1fs elapsed)", high, time.time() - t0)
    if twin_chunks:
        p = np.concatenate(twin_chunks)
    else:
        p = np.empty(0, dtype=np.int64)
    logging.info("Segmented sieve complete in %.1f s; %d twin pairs.", time.time() - t0, len(p))
    return p, p + 2

def generate_twin_primes(limit: int = MAX_PRIME_LIMIT) -> Tuple[List[int], List[int]]:
    """Generate twin primes up to `limit`.

    Uses primesieve when available (FR-001); otherwise computes the same
    real primes with a numpy segmented sieve. Returns two arrays
    (p_list, p_next_list) where each row is a twin pair (p, p+2).
    """
    ps = _get_primesieve()
    if ps is not None and (hasattr(ps, "numpy_primes") or hasattr(ps, "generate_primes")):
        logging.info("Generating all primes up to %d with primesieve...", limit)
        start_time = time.time()
        try:
            if hasattr(ps, "numpy_primes"):
                primes = ps.numpy_primes(limit)
            else:
                import numpy as np
                primes = np.asarray(ps.generate_primes(limit), dtype=np.int64)
        except Exception as e:
            logging.error("primesieve failed (%s); falling back to numpy segmented sieve.", e)
            primes = None
        if primes is not None:
            elapsed = time.time() - start_time
            logging.info("Generated %d primes in %.2f seconds.", len(primes), elapsed)
            return _twins_from_sorted_primes(primes)
    # Fallback: real numpy segmented sieve over the full range.
    logging.info("Generating all primes up to %d with numpy segmented sieve...", limit)
    return _numpy_segmented_sieve_twins(limit)

def normalized_gap(p: int, p_next: int) -> float:
    """
    Compute the normalized twin‑prime gap for a pair (p, p_next).

    The gap ``delta`` is ``p_next - p`` (always 2 for twin primes).
    The normalized gap is ``delta / log(p)``.
    """
    delta = p_next - p
    if p <= 1:
        raise ValueError("p must be greater than 1 for logarithm.")
    return delta / math.log(p)

def write_csv_output(p_list, p_next_list, output_path: Path) -> None:
    """Write twin prime data to CSV with columns p, p_next, delta, normalized_gap.

    delta = p_next - p (the within-pair gap, always 2 for twin primes,
    matching the T010 unit test: (5-3)/log(3)); normalized_gap = delta/log(p).
    Fails loudly if any normalized_gap is non-finite or non-positive.
    """
    import numpy as np

    logging.info("Writing CSV to %s", output_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    p = np.asarray(p_list, dtype=np.int64)
    pn = np.asarray(p_next_list, dtype=np.int64)
    delta = (pn - p).astype(np.int64)
    if len(p) > 0:
        norm = delta.astype(np.float64) / np.log(p.astype(np.float64))
    else:
        norm = np.empty(0, dtype=np.float64)

    if len(p) > 0:
        if not np.all(np.isfinite(norm)):
            raise ValueError("NaN/inf values found in normalized_gap; refusing to write.")
        if not np.all(norm > 0):
            raise ValueError("Non-positive normalized_gap values found; refusing to write.")

    rows = np.column_stack([p, pn, delta, norm]) if len(p) > 0 else np.empty((0, 4))
    with open(output_path, "w", newline="") as f:
        f.write("p,p_next,delta,normalized_gap\n")
        if len(p) > 0:
            np.savetxt(f, rows, fmt="%d,%d,%d,%.12f")
    logging.info("CSV writing complete (%d rows). File: %s", len(p), output_path)

def _load_expected_count(limit: int) -> float:
    """Read expected_count from data/results/expected_count.json (T013b-b)
    if present; otherwise compute the same Hardy-Littlewood estimate
    in-process (2*C2*x/(ln x)^2, matching compute_expected_count.py)."""
    expected_path = paths.data("results", "expected_count.json")
    if expected_path.exists():
        try:
            with open(expected_path, "r") as f:
                data = json.load(f)
            val = float(data["expected_count"])
            if val > 0:
                return val
        except Exception as e:
            logging.warning("Could not read %s (%s); computing expectation in-process.", expected_path, e)
    ln_x = math.log(limit)
    return 2.0 * HARDY_LITTLEWOOD_CONSTANT * limit / (ln_x * ln_x)

def _get_limit() -> int:
    """Read the range limit from the project config when possible."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from config import get_config
        cfg = get_config()
        limit = int(cfg.get("limits", {}).get("max_prime", MAX_PRIME_LIMIT))
        return limit
    except Exception as e:
        logging.warning("Could not read config (%s); using default limit 10^9.", e)
        return MAX_PRIME_LIMIT

def main():
    """Main entry point: generate twin primes, verify count, write CSV
    and performance metrics (T014: CSV output + memory monitoring)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    limit = _get_limit()
    output_path = paths.data("raw", "twin_primes.csv")
    perf_path = paths.data("results", "performance_gen.json")

    # 1. Execution guard
    check_execution_guard()

    # 2. Generate twin primes (timed for SC-004)
    start_gen = time.time()
    p_list, p_next_list = generate_twin_primes(limit)
    gen_time = time.time() - start_gen
    actual_count = len(p_list)

    # 3. Verify count against the Hardy-Littlewood expectation
    expected_count = _load_expected_count(limit)
    ratio = actual_count / expected_count if expected_count > 0 else 0.0
    logging.info("Expected count (Hardy-Littlewood, 2*C2): %.2f", expected_count)
    logging.info("Actual count: %d", actual_count)
    logging.info("Ratio (Actual/Expected): %.4f", ratio)
    if not (0.95 <= ratio <= 1.05):
        logging.warning(
            "Actual count is outside +/-5%% of expected count. Ratio: %.4f "
            "(recorded as a warning; the dataset is still written).", ratio
        )

    # 4. Write CSV output (validates no NaN / non-positive gaps)
    write_csv_output(p_list, p_next_list, output_path)

    # 5. Record performance metrics (SC-004/SC-005: time + peak memory)
    peak_mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    performance = {
        "execution_time_seconds": round(gen_time, 3),
        "peak_memory_mb": round(peak_mem_mb, 2),
        "total_pairs": int(actual_count),
        "gaps_calculated": int(actual_count),
        "expected_count": expected_count,
        "actual_over_expected_ratio": round(ratio, 6),
        "within_5_percent_of_expected": bool(0.95 <= ratio <= 1.05),
        "memory_limit_mb": MEMORY_LIMIT_GB * 1024,
        "within_memory_limit": bool(peak_mem_mb <= MEMORY_LIMIT_GB * 1024),
        "time_limit_minutes": TIME_LIMIT_MIN,
        "within_time_limit": bool(gen_time <= TIME_LIMIT_MIN * 60),
    }
    with open(perf_path, "w") as f:
        json.dump(performance, f, indent=2)
    logging.info("Performance metrics written to %s", perf_path)

    # 6. Final memory check (fail loudly if the 2 GiB budget is exceeded)
    if peak_mem_mb > MEMORY_LIMIT_GB * 1024:
        logging.error("Final memory usage exceeded limit: %.2f MB", peak_mem_mb)
        raise MemoryError(
            f"Peak memory {peak_mem_mb:.2f} MB exceeded the "
            f"{MEMORY_LIMIT_GB} GiB budget (SC-004)."
        )
    logging.info("Peak memory usage: %.2f MB (limit %.0f MB)", peak_mem_mb, MEMORY_LIMIT_GB * 1024)
    if gen_time > TIME_LIMIT_MIN * 60:
        logging.error("Execution time exceeded limit: %.2f s", gen_time)
        raise RuntimeError(
            f"Execution time {gen_time:.2f} s exceeded the "
            f"{TIME_LIMIT_MIN} minute budget (SC-005)."
        )
    logging.info("Execution time %.2f s within the %.0f minute budget.", gen_time, TIME_LIMIT_MIN)

    logging.info("Twin prime generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

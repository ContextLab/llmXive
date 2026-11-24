"""T014b [US1] [SC-004] [SC-005]: Measure and record execution time and
peak memory usage of the twin-prime generation pipeline.

Runs sequentially immediately after T014 (code/generate_primes.py)
completes its file writes. Behavior:

1. If data/raw/twin_primes.csv and data/results/performance_gen.json
   already exist from the T014 run and the recorded pair count matches
   the actual CSV row count, those REAL measured metrics are used
   (the generation is not redundantly repeated).
2. Otherwise the generation script is re-executed as a subprocess and
   real wall-clock time and peak child memory (resource.getrusage,
   RUSAGE_CHILDREN) are measured.

In both cases the metrics are validated (non-null, positive, populated)
and written to data/results/performance_gen.json, plus a durable copy
at results/performance_gen.json outside the gitignored raw-data cache.
"""
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from llmxive_toolkit import paths

MEMORY_LIMIT_MB = 2048.0
TIME_LIMIT_MIN = 45.0
GENERATION_SCRIPT = Path(__file__).resolve().parent / "generate_primes.py"
CSV_PATH = paths.data("raw", "twin_primes.csv")
PERF_PATH = paths.data("results", "performance_gen.json")


def get_peak_memory_mb() -> float:
    """Returns the peak memory usage of the current process in MB."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def count_csv_rows(path: Path) -> int:
    """Count data rows (excluding header) of the twin primes CSV."""
    with open(path, "rb") as f:
        return max(sum(1 for _ in f) - 1, 0)


def run_generation_pipeline() -> Dict[str, Any]:
    """Runs the generation script and captures timing and memory metrics.

    Returns a dictionary with execution time (wall clock, seconds) and
    peak memory (MB, measured over all child processes via
    resource.getrusage(RUSAGE_CHILDREN)). Fails loudly if the
    generation script exits non-zero.
    """
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    t0 = time.time()
    proc = subprocess.run([sys.executable, str(GENERATION_SCRIPT)])
    elapsed = time.time() - t0
    if proc.returncode != 0:
        raise RuntimeError(
            f"Generation script {GENERATION_SCRIPT} failed with exit "
            f"code {proc.returncode}; cannot record performance metrics."
      )
    after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak_mb = max(after, before) / 1024.0
    return {
        "execution_time_seconds": round(elapsed, 3),
        "peak_memory_mb": round(peak_mb, 2),
    }


def _load_existing_metrics() -> Optional[Dict[str, Any]]:
    """Load the performance JSON written by the T014 run, if valid."""
    if not PERF_PATH.exists():
        return None
    try:
        data = json.loads(PERF_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def main() -> int:
    """Main entry point for measuring generation performance.

    Saves metrics to data/results/performance_gen.json (and a durable
    copy at results/performance_gen.json).
    """
    metrics: Optional[Dict[str, Any]] = None

    # Fast path: reuse the real T014 measurement when it is consistent
    # with the CSV that T014 just wrote.
    if PERF_PATH.exists() and CSV_PATH.exists():
        existing = _load_existing_metrics()
        if existing is not None:
            rows = count_csv_rows(CSV_PATH)
            recorded = existing.get("total_pairs")
            if (
                rows > 0
                and isinstance(recorded, (int, float))
                and int(recorded) == rows
                and isinstance(existing.get("execution_time_seconds"), (int, float))
                and existing["execution_time_seconds"] > 0
                and isinstance(existing.get("peak_memory_mb"), (int, float))
                and existing["peak_memory_mb"] > 0
            ):
                metrics = dict(existing)
                metrics["gaps_calculated"] = rows
                print(
                    f"Reusing T014 measurement: {rows} pairs, "
                    f"{metrics['execution_time_seconds']} s, "
                    f"{metrics['peak_memory_mb']} MB peak."
                )

    # Slow path: re-run the real generation pipeline and measure it.
    if metrics is None:
        if not GENERATION_SCRIPT.exists():
            raise FileNotFoundError(
                f"Generation script not found: {GENERATION_SCRIPT}"
            )
        print("Re-running generation pipeline to measure performance...")
        measured = run_generation_pipeline()
        rows = count_csv_rows(CSV_PATH)
        existing = _load_existing_metrics() or {}
        metrics = {**existing, **measured}
        metrics["total_pairs"] = rows
        metrics["gaps_calculated"] = rows

    # Enforce and record the SC-004/SC-005 budget checks.
    metrics["memory_limit_mb"] = MEMORY_LIMIT_MB
    metrics["within_memory_limit"] = bool(
        metrics["peak_memory_mb"] <= MEMORY_LIMIT_MB
    )
    metrics["time_limit_minutes"] = TIME_LIMIT_MIN
    metrics["within_time_limit"] = bool(
        metrics["execution_time_seconds"] <= TIME_LIMIT_MIN * 60
    )

    # Validate: no hollow / null measurements are ever written.
    for key in ("execution_time_seconds", "peak_memory_mb", "total_pairs"):
        value = metrics.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(
                f"Performance metric '{key}' is missing or invalid "
                f"({value!r}); refusing to write a hollow result."
            )
    if not isinstance(metrics.get("gaps_calculated"), int) or metrics["gaps_calculated"] <= 0:
        raise ValueError("Metric 'gaps_calculated' is missing or invalid.")

    PERF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PERF_PATH.write_text(json.dumps(metrics, indent=2) + "\n")

    # Durable copy outside the gitignored raw-data cache.
    durable = paths.results("performance_gen.json")
    durable.write_text(json.dumps(metrics, indent=2) + "\n")

    print(f"Performance metrics written to {PERF_PATH}")
    print(f"Durable copy written to {durable}")
    print(
        f"execution_time_seconds={metrics['execution_time_seconds']} "
        f"peak_memory_mb={metrics['peak_memory_mb']} "
        f"total_pairs={metrics['total_pairs']} "
        f"within_memory_limit={metrics['within_memory_limit']} "
        f"within_time_limit={metrics['within_time_limit']}"
    )

    if not metrics["within_memory_limit"]:
        raise MemoryError(
            f"Peak memory {metrics['peak_memory_mb']} MB exceeded the "
            f"{MEMORY_LIMIT_MB} MB budget (SC-004)."
        )
    if not metrics["within_time_limit"]:
        raise RuntimeError(
            f"Execution time {metrics['execution_time_seconds']} s exceeded "
            f"the {TIME_LIMIT_MIN} minute budget (SC-005)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

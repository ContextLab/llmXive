"""
timing.py
----------
Provides a context manager `phase_timer` for measuring wall‑clock time and peak RSS
memory usage of a pipeline phase. The measurements are appended as a row to
`data/results/runtime_summary.csv` with columns: `phase`, `wall_clock_s`,
`peak_rss_mb`.
"""
import time
import psutil
from pathlib import Path
from contextlib import contextmanager
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

@contextmanager
def phase_timer(phase_name: str):
    """
    Context manager that records the elapsed wall‑clock time (using
    ``time.perf_counter``) and the peak resident set size (RSS) in megabytes
    for the wrapped code block.

    Parameters
    ----------
    phase_name: str
        Human‑readable name of the phase, written to the CSV.

    The CSV file ``runtime_summary.csv`` is created under ``data/results/`` if it
    does not already exist. Each invocation appends a new row.
    """
    start_time = time.perf_counter()
    process = psutil.Process()
    # Initial memory usage
    mem_before = process.memory_info().rss
    peak_rss = mem_before

    try:
        yield
    finally:
        # Capture after‑execution memory and compute peak.
        mem_after = process.memory_info().rss
        # Simple peak estimate: max of before and after.
        peak_rss = max(mem_before, mem_after)

        elapsed = time.perf_counter() - start_time
        elapsed = round(elapsed, 4)

        # Convert bytes to megabytes
        peak_mb = round(peak_rss / (1024 * 1024), 4)

        # Prepare output path and ensure parent directory exists
        out_path: Path = paths.results("runtime_summary.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Write header if file is new
        write_header = not out_path.is_file()
        with out_path.open("a", encoding="utf-8", newline="") as f:
            if write_header:
                f.write("phase,wall_clock_s,peak_rss_mb\n")
            f.write(f"{phase_name},{elapsed},{peak_mb}\n")

        log.info(
            "Phase %s completed: wall_clock_s=%.4f, peak_rss_mb=%.4f",
            phase_name,
            elapsed,
            peak_mb,
        )

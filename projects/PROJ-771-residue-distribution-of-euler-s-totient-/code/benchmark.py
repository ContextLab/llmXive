"""
Benchmark instrumentation module.

Provides a context manager ``benchmark(name)`` that records wall-clock time
and peak memory usage during the wrapped block of code. The results are
written as a JSON file ``results/reports/benchmark_{name}.json``.
"""

import time
import json
import psutil
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

class _BenchmarkContext:
    """
    Internal helper implementing the context manager protocol.
    """

    def __init__(self, name: str):
        self.name = name
        self.start_time: float = 0.0
        self.peak_memory_mb: float = 0.0
        self._process = psutil.Process()

    def __enter__(self):
        self.start_time = time.time()
        # Record initial memory usage as a starting point for peak tracking
        self.peak_memory_mb = self._process.memory_info().rss / (1024 * 1024)
        log.debug(f"Benchmark '{self.name}' started – initial memory {self.peak_memory_mb:.2f} MiB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        # Capture final memory usage and keep the maximum observed
        final_mem = self._process.memory_info().rss / (1024 * 1024)
        self.peak_memory_mb = max(self.peak_memory_mb, final_mem)

        result = {
            "name": self.name,
            "wall_time_sec": elapsed,
            "peak_memory_mb": self.peak_memory_mb,
        }

        out_path = paths.results("reports", f"benchmark_{self.name}.json")
        try:
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            log.info(
                f"Benchmark '{self.name}' completed – wall time {elapsed:.3f}s, "
                f"peak memory {self.peak_memory_mb:.2f} MiB (written to {out_path})"
            )
        except Exception as e:
            log.error(f"Failed to write benchmark report for '{self.name}': {e}")
            raise

        # Do not suppress any exception that occurred inside the block
        return False

def benchmark(name: str):
    """
    Context manager for simple benchmark instrumentation.

    Example
    -------
    >>> from benchmark import benchmark
    >>> with benchmark("my_stage"):
    ...     # code to be timed and memory‑profiled
    ...     do_heavy_work()
    """
    return _BenchmarkContext(name)

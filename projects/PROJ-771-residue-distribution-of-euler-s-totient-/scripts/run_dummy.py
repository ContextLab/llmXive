"""
Dummy benchmark script.

This script invokes the ``benchmark`` context manager with the name
``dummy`` and performs a trivial loop.  Upon exiting the context,
``benchmark`` writes ``results/reports/benchmark_dummy.json`` containing
the wall‑clock time and peak memory usage.
"""

from benchmark import benchmark

def main() -> None:
    # A tiny workload – the loop itself does nothing substantial.
    with benchmark("dummy"):
        for _ in range(10_000):
            pass

if __name__ == "__main__":
    main()
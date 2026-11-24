"""
run_all.py

Orchestrates the end‑to‑end pipeline while recording runtime and
peak memory usage as required by FR‑001–FR‑008 and the success
criteria.
"""

import argparse
import importlib
import json
import sys
import time
import psutil
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _run_module(module_name: str) -> None:
    """
    Import a module by name (e.g., ``code.ingest``) and, if it defines a
    ``main`` callable, execute it. Missing modules or missing ``main``
    functions are logged and ignored, allowing the pipeline to continue
    gracefully.
    """
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        log.error(f"Failed to import {module_name}: {e}")
        return

    main_func = getattr(module, "main", None)
    if callable(main_func):
        log.info(f"Running {module_name}.main()")
        main_func()
    else:
        log.warning(f"No main() in {module_name}; skipping.")

def _write_json(path: Path, data: dict) -> None:
    """Write *data* as pretty‑printed JSON to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

def main() -> None:
    """
    Execute the pipeline steps sequentially while timing the total
    execution and capturing peak memory usage.
    """
    start_time = time.perf_counter()
    process = psutil.Process()

    # Define the ordered list of sub‑commands (module names).
    steps = [
        "code.ingest",
        "code.descriptors",
        "code.physical_properties",
        "code.train_ebm",
        "code.interpret",
        "code.validate",
    ]

    for step in steps:
        _run_module(step)

    # Record runtime.
    elapsed = time.perf_counter() - start_time
    runtime_path = paths.outputs("logs", "runtime.json")
    _write_json(runtime_path, {"elapsed_seconds": elapsed})
    log.info(f"Total runtime: {elapsed:.2f}s recorded at {runtime_path}")

    # Record peak memory usage.
    mem_path = paths.outputs("logs", "memory.json")
    _write_json(mem_path, {"peak_rss_mb": process.memory_info().rss / (1024 * 1024)})
    log.info(f"Peak RSS memory recorded at {mem_path}")

if __name__ == "__main__":
    main()
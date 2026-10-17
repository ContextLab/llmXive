"""
run_all.py
-------------
Orchestrates the full analysis pipeline, records total runtime, and captures
peak RSS memory usage during the execution. The script follows the existing
project conventions: it uses ``_run_module`` to execute sub‑modules that
expose a ``main`` callable, writes timing information to
``outputs/logs/runtime.json`` and memory usage to
``outputs/logs/memory.json``.
"""

import importlib
import json
import time
import psutil

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _run_module(module_name: str) -> None:
    """
    Import a module by name and, if it defines a ``main`` callable,
    execute it. Any exception raised by the module propagates so that
    pipeline failures are visible; missing modules are logged and ignored.
    """
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        log.warning(f"Module {module_name} not found; skipping.")
        return

    if hasattr(module, "main"):
        log.info(f"Running {module_name}.main()")
        module.main()
    else:
        log.info(f"Module {module_name} has no main(); skipping.")


def main() -> None:
    """
    Execute the pipeline steps sequentially, timing the whole run and
    persisting the elapsed seconds to ``outputs/logs/runtime.json``.
    After the pipeline finishes, capture the process' peak RSS memory
    (in megabytes) and write it to ``outputs/logs/memory.json``.

    The list of sub‑modules mirrors the quick‑start DAG; modules that are
    not present are simply logged and ignored.
    """
    logger = log
    start_time = time.perf_counter()

    # List of pipeline modules in execution order.
    pipeline_modules = [
        "code.ingest",
        "code.descriptors",
        "code.physical_properties",
        "code.train_ebm",
        "code.interpret",
        "code.validate",
    ]

    # Run each module, updating the peak memory after each step.
    peak_rss_bytes = 0
    process = psutil.Process()

    for mod_name in pipeline_modules:
        _run_module(mod_name)
        # Update peak RSS after the step.
        try:
            current_rss = process.memory_info().rss
            if current_rss > peak_rss_bytes:
                peak_rss_bytes = current_rss
        except Exception as exc:
            logger.warning(f"Failed to read memory usage after {mod_name}: {exc}")

    elapsed = time.perf_counter() - start_time
    runtime_path = paths.outputs("logs", "runtime.json")
    runtime_path.write_text(json.dumps({"elapsed_seconds": elapsed}, indent=2))
    logger.info(f"Runtime written to {runtime_path}")

    # Record peak RSS memory (convert bytes to megabytes, round to 2 decimals)
    peak_rss_mb = round(peak_rss_bytes / (1024 * 1024), 2)
    memory_path = paths.outputs("logs", "memory.json")
    memory_path.write_text(json.dumps({"peak_rss_mb": peak_rss_mb}, indent=2))
    logger.info(f"Peak RSS memory ({peak_rss_mb} MB) written to {memory_path}")


if __name__ == "__main__":
    # Allow the script to be executed directly via ``python -m code.run_all``.
    main()

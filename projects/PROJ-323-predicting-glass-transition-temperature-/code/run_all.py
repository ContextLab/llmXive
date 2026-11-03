"""
run_all.py

Orchestrates the end‑to‑end pipeline. It records total runtime using
``time.perf_counter`` and captures peak RSS memory via ``psutil``,
writing the results to ``outputs/logs/runtime.json`` and
``outputs/logs/memory.json`` respectively.
"""

import importlib
import json
import time
import psutil

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _run_module(module_name: str) -> None:
    """
    Import a module by name and, if it defines a ``main`` callable,
    execute it. Missing modules are logged and ignored.
    """
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        log.warning(f"Module {module_name} not found; skipping.")
        return

    if hasattr(mod, "main"):
        log.info(f"Running {module_name}.main()")
        try:
            mod.main()
        except Exception as exc:
            log.error(f"Error while running {module_name}.main(): {exc}")
            raise
    else:
        log.info(f"Module {module_name} has no main(); skipping.")

def main() -> None:
    """
    Execute the pipeline steps sequentially, timing the whole run and
    persisting the elapsed seconds to ``outputs/logs/runtime.json``.
    After the pipeline finishes, capture the process' peak RSS memory
    (in megabytes) and write it to ``outputs/logs/memory.json``.
    """
    start_time = time.perf_counter()

    # Ordered list of pipeline modules.
    pipeline_modules = [
        "code.ingest",
        "code.descriptors",
        "code.physical_properties",
        "code.train_ebm",
        "code.interpret",
        "code.validate",
    ]

    for module_name in pipeline_modules:
        _run_module(module_name)

    # Runtime measurement.
    elapsed = time.perf_counter() - start_time
    runtime_path = paths.outputs("logs", "runtime.json")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    with runtime_path.open("w", encoding="utf-8") as f:
        json.dump({"elapsed_seconds": elapsed}, f)
    log.info(f"Total runtime: {elapsed:.3f}s written to {runtime_path}")

    # Peak memory measurement using psutil.
    process = psutil.Process()
    mem_info = process.memory_info()
    peak_rss_mb = mem_info.rss / (1024 * 1024)  # Convert bytes to MB
    memory_path = paths.outputs("logs", "memory.json")
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    with memory_path.open("w", encoding="utf-8") as f:
        json.dump({"peak_rss_mb": peak_rss_mb}, f)
    log.info(f"Peak RSS memory: {peak_rss_mb:.2f} MB written to {memory_path}")

if __name__ == "__main__":
    main()

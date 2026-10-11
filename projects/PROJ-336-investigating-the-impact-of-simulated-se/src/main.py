"""
src/main.py
Entry point for the research pipeline.

This module provides a thin wrapper around the actual implementation
located in ``code/main.py``. It adds support for the ``--dry-run``
flag required by the quickstart verification. When ``--dry-run`` is
supplied the script prints the ordered pipeline stages and exits
with status 0 without invoking any heavy computation.
"""
import argparse
import sys
import importlib.util
from pathlib import Path
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper to dynamically load the implementation module located at
# ``code/main.py``. This mirrors the original behaviour of the wrapper.
# ----------------------------------------------------------------------
def _load_code_main():
    """
    Dynamically load ``code/main.py`` and return the loaded module.

    Returns
    -------
    module
        The loaded ``code.main`` module.
    """
    code_main_path = Path(__file__).parents[1] / "code" / "main.py"
    spec = importlib.util.spec_from_file_location("code_main", code_main_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find code/main.py at {code_main_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# ----------------------------------------------------------------------
# Public entry point expected by the test suite and by ``python -m src.main``.
# ----------------------------------------------------------------------
def main():
    """
    Parse command‑line arguments and either perform a dry‑run or
    delegate to the full pipeline implementation in ``code/main.py``.
    """
    parser = argparse.ArgumentParser(description="Sensory deprivation pipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the pipeline stages without executing them."
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Process only the first N subjects (used for quick sanity checks)."
    )
    # Allow unknown arguments to be passed through to the real implementation
    args, unknown = parser.parse_known_args()

    if args.dry_run:
        # The ordered stages are defined in the project specification.
        stages = [
            "download",
            "quality_check",
            "preprocess",
            "connectivity",
            "metrics",
            "stats",
            "viz"
        ]
        print("Pipeline stages (dry‑run):")
        for stage in stages:
            print(f" - {stage}")
        sys.exit(0)

    # If not a dry‑run, load the full implementation and forward the arguments.
    code_main = _load_code_main()
    # The implementation module is expected to expose a ``main`` function
    # that accepts the original argv list (including the script name).
    # We reconstruct a minimal argv that mimics ``python -m src.main``.
    # ``unknown`` contains any extra flags passed by the caller.
    argv = [sys.argv[0]] + unknown
    # ``code_main.main`` may be a function or a callable object.
    if hasattr(code_main, "main"):
        return code_main.main()
    else:
        raise AttributeError("The loaded code/main.py does not define a 'main' function.")

if __name__ == "__main__":
    sys.exit(main())

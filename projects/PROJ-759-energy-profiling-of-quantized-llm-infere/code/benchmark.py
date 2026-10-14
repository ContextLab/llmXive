"""
Benchmark entry point for energy profiling of quantized LLM inference.

This module provides a minimal CLI that supports a ``--dry-run`` flag used
by the quickstart guide to verify that the ``pyRAPL`` library can be
imported and initialized on the current runner.

The full benchmarking functionality (model loading, inference, energy
measurement, result aggregation) will be implemented in later tasks.
For the purpose of T001 we only need to:
  * Parse ``--config`` (required for future extensions).
  * If ``--dry-run`` is supplied, attempt to import ``pyRAPL`` and call
    ``pyRAPL.setup()``.
  * Print a clear confirmation string ``pyRAPL available`` on success.
Any exception during the import/initialisation causes the script to exit
with a non‑zero status so that the test suite can detect failure.
"""

import argparse
import sys

def _check_pyrapl() -> None:
    """Import and initialise pyRAPL, raising on failure."""
    try:
        import pyRAPL
    except Exception as exc:
        raise RuntimeError("Failed to import pyRAPL") from exc

    try:
        pyRAPL.setup()
    except Exception as exc:
        raise RuntimeError("Failed to initialise pyRAPL") from exc

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Energy profiling benchmark (dry‑run mode)."
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to a configuration JSON file (future use).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only verify that pyRAPL can be loaded and initialised.",
    )
    args = parser.parse_args(argv)

    if args.dry_run:
        _check_pyrapl()
        print("pyRAPL available")
        return 0

    # Placeholder for the full benchmark implementation.
    parser.error(
        "Full benchmark functionality not yet implemented; use --dry-run."
    )
    return 1  # Unreachable

if __name__ == "__main__":
    sys.exit(main())

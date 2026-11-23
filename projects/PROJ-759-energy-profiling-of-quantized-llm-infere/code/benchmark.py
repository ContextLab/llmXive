"""
Benchmark entry point for the energy profiling project.

This script provides a minimal CLI that supports a dry‑run mode used by the
contract test ``test_pyrapl_load``. In dry‑run mode the script attempts to
import the ``pyRAPL`` library and prints exactly the string required by the
test:

    pyRAPL available

If the import fails the exception is propagated so the test fails loudly.

The full benchmarking functionality (energy measurement, inference loops,
result aggregation) will be implemented in later tasks. For now we only
provide argument parsing and the dry‑run behaviour required to satisfy
T001.
"""

import argparse
import json
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

__all__ = ["_check_pyrapl", "_load_config", "_build_parser", "main"]

def _check_pyrapl() -> None:
    """
    Verify that the ``pyRAPL`` library can be imported and initialized.

    The function imports ``pyRAPL``; if successful it prints the exact
    confirmation string required by the contract test. Any import error is
    allowed to propagate so that the caller (or pytest) sees a failure.
    """
    try:
        import pyRAPL  # noqa: F401
    except Exception as exc:
        log.error("Failed to import pyRAPL: %s", exc)
        raise
    # If import succeeded, print the required message.
    print("pyRAPL available")

def _load_config(config_path: Path) -> dict:
    """
    Load a JSON configuration file.

    Parameters
    ----------
    config_path: Path
        Path to the JSON configuration file.

    Returns
    -------
    dict
        Parsed configuration dictionary.
    """
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg

def _build_parser() -> argparse.ArgumentParser:
    """
    Construct the argument parser used by the script.

    The parser mirrors the command documented in ``code/quickstart.md``.
    ``--config`` is required for normal operation; ``--dry-run`` triggers
    the pyRAPL availability check. All other arguments are optional so
    that the quickstart command does not raise parsing errors.
    """
    parser = argparse.ArgumentParser(
        description="Energy profiling benchmark (dry‑run supported)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON configuration file describing the model.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only check that pyRAPL can be imported; do not run the benchmark.",
    )
    parser.add_argument(
        "--prompt-length",
        type=int,
        default=500,
        help="Length of the prompt in tokens (placeholder).",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=5,
        help="Number of repetitions per configuration (placeholder).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=paths.results(),
        help="Directory where result files will be written (placeholder).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=paths.logs(),
        help="Directory for log files (placeholder).",
    )
    return parser

def main(argv: list[str] | None = None) -> int:
    """
    Entry point for ``python -m code.benchmark``.

    The function parses CLI arguments, performs a dry‑run check when
    requested, and otherwise loads the provided configuration. Full
    benchmark execution will be added in later tasks.

    Returns
    -------
    int
        Exit status (0 for success, non‑zero for failure).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        _check_pyrapl()
        return 0

    # Normal (non‑dry‑run) execution path – placeholder for now.
    try:
        config = _load_config(args.config)
    except Exception as exc:
        log.error("Failed to load configuration: %s", exc)
        return 1

    # Placeholder: just log that we would run the benchmark.
    log.info(
        "Benchmark would run with config %s, prompt length %s, repetitions %s",
        args.config,
        args.prompt_length,
        args.repetitions,
    )
    # Future implementation will write results to args.output_dir etc.
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""
Benchmark script for energy profiling of quantized LLM inference.

This script supports a dry‑run mode that verifies the availability of the
``pyRAPL`` library (or its fallback) and prints a confirmation message.
It also parses the full set of CLI arguments used by the quickstart
documentation so that the command line does not drift from the run‑book.
The actual inference and energy‑measurement logic is out of scope for
task T001; the script therefore exits gracefully after argument parsing
when not in dry‑run mode.
"""

import argparse
import json
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _check_pyrapl() -> None:
    """
    Verify that the ``pyRAPL`` library can be imported and initialized.

    The function attempts to import ``pyRAPL`` and, if successful, prints a
    short confirmation string required by the contract test
    ``test_pyrapl_load``.  If the import fails, the exception is re‑raised so
    that the caller can handle it (the test will fail, signalling that the
    environment is not ready).
    """
    try:
        import pyRAPL
    except Exception as exc:
        log.error("pyRAPL import failed: %s", exc)
        raise

    # ``pyRAPL`` provides a ``setup`` function that must be called before
    # measurements.  We call it here to ensure the library is functional.
    try:
        pyRAPL.setup()
    except Exception as exc:
        log.error("pyRAPL setup failed: %s", exc)
        raise

    # The contract test expects exactly this output on stdout.
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
    try:
        with config_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        log.debug("Loaded config from %s", config_path)
        return cfg
    except Exception as exc:
        log.error("Failed to load config %s: %s", config_path, exc)
        raise

def _build_parser() -> argparse.ArgumentParser:
    """
    Construct the argument parser used by the script.

    The parser mirrors the command line documented in ``code/quickstart.md``.
    """
    parser = argparse.ArgumentParser(
        description="Run energy‑aware LLM inference benchmarks."
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a JSON configuration file describing the model checkpoint.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only verify that pyRAPL can be imported and initialized.",
    )
    parser.add_argument(
        "--prompt-length",
        type=int,
        default=500,
        help="Length of the tokenised prompt (default: 500).",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=5,
        help="Number of independent inference repetitions (default: 5).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=paths.data("results"),
        help="Directory where run artefacts will be stored.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=paths.path("logs"),
        help="Directory for log files.",
    )
    return parser

def main(argv: list[str] | None = None) -> int:
    """
    Entry point for ``python -m code.benchmark``.

    The function parses CLI arguments, performs a dry‑run check when requested,
    and otherwise loads the provided configuration.  Full benchmark execution
    is deferred to later tasks; this script simply validates that the
    environment is correctly set up.

    Returns
    -------
    int
        Exit status (0 for success).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Ensure output and log directories exist.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.log_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        try:
            _check_pyrapl()
        except Exception:
            # Propagate the error so the test fails if pyRAPL is unavailable.
            return 1
        return 0

    # Load configuration (the JSON schema validation happens in later tasks).
    try:
        config = _load_config(args.config)
    except Exception:
        return 1

    # Placeholder for the real benchmarking logic.
    log.info(
        "Benchmark would run here with prompt_length=%s, repetitions=%s",
        args.prompt_length,
        args.repetitions,
    )
    log.debug("Configuration: %s", config)

    # For now we simply exit successfully.
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""
CI Runtime Check Script

This script is intended to be used as a CI step. It runs the full pipeline
(via the existing ``benchmark_runtime`` module), records the total runtime
in ``results/benchmark_report.txt`` and optionally fails the CI job if the
runtime exceeds a configured limit.

Configuration is read from ``src/config/parameters.yaml``. The relevant
keys are:

* ``runtime_limit_seconds`` (optional) – The maximum allowed runtime in
  seconds.  If omitted, no limit is applied.
* ``enforce_runtime_limit`` (optional, default ``false``) – When set to
  ``true`` the step will exit with a non‑zero status if the measured
  runtime exceeds ``runtime_limit_seconds``.  When ``false`` the step only
  emits a warning but always succeeds.

The script writes a human‑readable report to
``results/benchmark_report.txt`` containing the elapsed time.  The report
format is compatible with the later ``T046`` task that expects this file.
"""

import sys
import pathlib
import yaml

# The benchmark_runtime module provides the core functionality for
# executing the pipeline and writing the report.
from benchmark_runtime import run_make_all, write_report

CONFIG_PATH = pathlib.Path("src/config/parameters.yaml")
REPORT_PATH = pathlib.Path("results/benchmark_report.txt")


def load_configuration() -> dict:
    """
    Load the runtime configuration from ``src/config/parameters.yaml``.
    If the file does not exist or cannot be parsed, a ``FileNotFoundError``
    or ``yaml.YAMLError`` will be raised, causing the CI step to fail
    loudly – this is intentional to avoid silent fall‑backs.
    """
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def main() -> int:
    """
    Execute the CI runtime check.

    Returns:
        int: Exit code (0 for success, 1 for failure when the limit is
             enforced and exceeded).
    """
    # Load configuration – any problem here should abort the CI step.
    config = load_configuration()
    runtime_limit = config.get("runtime_limit_seconds")
    enforce_limit = bool(config.get("enforce_runtime_limit", False))

    # Run the full pipeline and measure elapsed time.
    # ``run_make_all`` returns the elapsed time in seconds.
    elapsed_seconds = run_make_all()

    # Ensure the results directory exists before writing the report.
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write a concise report – the helper handles formatting.
    write_report(elapsed_seconds, REPORT_PATH)

    # Produce a friendly console output for CI logs.
    elapsed_minutes = elapsed_seconds / 60.0
    print(f"[CI] Pipeline runtime: {elapsed_seconds:.2f} seconds "
          f"({elapsed_minutes:.2f} minutes)")

    # Evaluate the limit, if configured.
    if runtime_limit is not None:
        if elapsed_seconds > runtime_limit:
            message = (f"[CI] Runtime limit exceeded: {elapsed_seconds:.2f}s "
                       f"> {runtime_limit:.2f}s")
            if enforce_limit:
                print(message + " – failing CI job.")
                return 1
            else:
                print(message + " – warning only (limit not enforced).")
        else:
            print(f"[CI] Runtime within configured limit ({runtime_limit:.2f}s).")
    else:
        print("[CI] No runtime limit configured; only recording runtime.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
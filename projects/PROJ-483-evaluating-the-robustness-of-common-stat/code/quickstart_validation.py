"""
Quickstart Validation Script
----------------------------

This script runs the reproducibility verification step defined in
``quickstart.md`` by invoking the project's main entry point with the
``--action verify`` flag. If the verification succeeds, a JSON report is
written to ``results/quickstart_validation_report.json`` containing the
captured standard output, standard error and a success flag.

The script is deliberately lightweight: it does **not** re‑run the full
simulation pipeline (which would be far too expensive for the CI
environment). Instead it relies on the existing verification logic
implemented in ``code/main.py`` which checks artifact hashes recorded in
``state.yaml`` and other reproducibility artefacts.

The script can be executed directly:

    python code/quickstart_validation.py

It will raise an exception if the verification step fails.
"""

import sys
import json
import subprocess
from llmxive_toolkit import paths, get_logger

def _run_verify_action() -> subprocess.CompletedProcess:
    """
    Execute the project's main script with the ``--action verify`` argument.

    Returns:
        subprocess.CompletedProcess: The completed process object.

    Raises:
        RuntimeError: If the subprocess exits with a non‑zero return code.
    """
    logger = get_logger(__name__)
    cmd = [
        sys.executable,
        str(paths.code("main.py")),
        "--action",
        "verify",
    ]
    logger.info("Running quickstart verification command: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(
            "Verification command failed (exit %s). Stderr: %s",
            result.returncode,
            result.stderr,
        )
        raise RuntimeError(
            f"Quickstart verification failed with exit code {result.returncode}"
        )
    logger.info("Verification command succeeded.")
    return result

def _write_report(proc: subprocess.CompletedProcess) -> None:
    """
    Write a JSON report summarising the verification outcome.

    The report is stored at ``results/quickstart_validation_report.json``.
    """
    report_path = paths.results("quickstart_validation_report.json")
    report = {
        "success": True,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    report_path.write_text(json.dumps(report, indent=2))
    get_logger(__name__).info(
        "Quickstart validation report written to %s", report_path
    )

def main() -> None:
    """
    Entry point for the validation script.
    """
    logger = get_logger(__name__)
    logger.info("Starting quickstart reproducibility validation.")
    proc = _run_verify_action()
    _write_report(proc)
    logger.info("Quickstart reproducibility validation completed successfully.")

if __name__ == "__main__":
    main()

"""
verify_logging.py
-----------------
This script verifies that the pipeline log file exists and contains at least one
entry for each expected pipeline stage.  The log file is written by the
project's logging utilities (`code/utils/logging.py`) as JSON‑lines.  Each
line must contain a ``stage`` field indicating the pipeline stage that
generated the entry.

Expected stages (derived from the quickstart pipeline):
  - download
  - validate
  - preprocess
  - split
  - train
  - evaluate
  - interpret

If any expected stage is missing, the script raises ``RuntimeError`` and
exits with a non‑zero status code.  When all stages are present the script
exits silently with status 0, satisfying the verification criterion for
task **T003a**.
"""

import json
import sys
from pathlib import Path
from typing import List, Set

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
EXPECTED_STAGES: List[str] = [
    "download",
    "validate",
    "preprocess",
    "split",
    "train",
    "evaluate",
    "interpret",
]

LOG_PATH: Path = paths.data("logs", "pipeline.log")


def _load_log_stages(log_path: Path) -> Set[str]:
    """
    Read the JSON‑lines log file and collect all distinct ``stage`` values.

    Parameters
    ----------
    log_path: Path
        Path to the pipeline log file.

    Returns
    -------
    Set[str]
        The set of stage names observed in the log.

    Raises
    ------
    RuntimeError
        If the file cannot be read or a line is not valid JSON.
    """
    if not log_path.is_file():
        raise RuntimeError(f"Pipeline log file not found at {log_path}")

    observed: Set[str] = set()
    with log_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue  # skip empty lines
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON on line {line_number} of {log_path}: {exc}"
                ) from exc

            stage = entry.get("stage")
            if stage:
                observed.add(str(stage))
    return observed


def verify_log(
    log_path: Path = LOG_PATH,
    expected_stages: List[str] = EXPECTED_STAGES,
) -> None:
    """
    Verify that the log file contains at least one entry for each expected
    pipeline stage.

    Parameters
    ----------
    log_path: Path
        Path to the pipeline log file.
    expected_stages: List[str]
        List of stage identifiers that must appear in the log.

    Raises
    ------
    RuntimeError
        If the log file is missing, empty, or any expected stage is absent.
    """
    observed = _load_log_stages(log_path)

    if not observed:
        raise RuntimeError(f"The pipeline log at {log_path} is empty.")

    missing = [s for s in expected_stages if s not in observed]
    if missing:
        raise RuntimeError(
            f"The pipeline log at {log_path} is missing entries for stage(s): "
            f"{', '.join(missing)}. Observed stages: {', '.join(sorted(observed))}"
        )

    # All good – print a short confirmation (optional)
    print(
        f"Verification passed: all {len(expected_stages)} expected stages are present "
        f"in {log_path}."
    )


def main() -> None:
    """
    Entry‑point for ``python -m code.utils.verify_logging``.
    """
    try:
        verify_log()
    except RuntimeError as err:
        # Propagate the error message to stderr and exit with a non‑zero code.
        print(str(err), file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

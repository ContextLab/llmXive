"""Integration of the tie‑breaking validator into the reproducibility workflow.

This module executes the ``tie_breaking_validator`` script and records its
success status in ``docs/reproducibility/validation_status.md``. It is intended
to be invoked as a pre‑processing step in the main pipeline.
"""

import subprocess
from pathlib import Path


def run_and_record() -> None:
    """Run the validator and append the result to the validation status file.

    The validator is executed as a module; a zero exit code denotes success.
    """
    result = subprocess.run(
        ["python", "-m", "code.reproducibility.tie_breaking_validator"],
        capture_output=True,
        text=True,
    )
    success = result.returncode == 0

    # Path to the validation status markdown file
    status_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "reproducibility"
        / "validation_status.md"
    )
    with open(status_path, "a", encoding="utf-8") as f:
        f.write(f"Tie‑breaking validator success: {success}\n")


if __name__ == "__main__":
    run_and_record()


"""
Unit test for verifying that the CI workflow file exists and contains a
``validate`` job.

The CI workflow is expected to be located at ``.github/workflows/ci.yml``.
The test asserts:
  1. The file exists.
  2. The file contains a top‑level job named ``validate`` (checked via a
     simple regular‑expression search).
"""

import re
from pathlib import Path

def test_ci_workflow_contains_validate_job() -> None:
    """
    Ensure the GitHub Actions CI workflow file is present and defines a
    ``validate`` job.
    """
    ci_path = Path(".github/workflows/ci.yml")
    # 1. File must exist
    assert ci_path.is_file(), f"CI workflow file not found at {ci_path}"

    content = ci_path.read_text(encoding="utf-8")

    # 2. Look for a job named ``validate`` at the top level under ``jobs:``
    #    A simple robust check is to ensure a line starts with ``validate:``
    #    possibly preceded by whitespace.
    job_pattern = re.compile(r"^\s*validate\s*:", re.MULTILINE)
    assert job_pattern.search(content), (
        "The CI workflow does not define a job named 'validate'. "
        "Expected a line like 'validate:' under the top‑level 'jobs' key."
    )
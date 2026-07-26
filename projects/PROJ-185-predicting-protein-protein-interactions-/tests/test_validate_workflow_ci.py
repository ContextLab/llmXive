"""Tests for the CI workflow validator (src/ci/validate_workflow.py)."""

import pathlib
import subprocess
import sys
import textwrap

import pytest

# Import the validator's main function for direct testing.
from src.ci.validate_workflow import main as validator_main


@pytest.fixture
def temp_workflow_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a minimal but valid GitHub Actions workflow file."""
    content = textwrap.dedent(
        """
        name: CI

        on:
          push:
            branches: [ main ]

        jobs:
          validate:
            runs-on: ubuntu-latest
            steps:
              - name: Run validation
                run: make validate
        """
    )
    wf_path = tmp_path / "ci.yml"
    wf_path.write_text(content, encoding="utf-8")
    return wf_path


def test_validator_exits_successfully_with_valid_workflow(temp_workflow_file: pathlib.Path):
    """The validator should exit with code 0 when the workflow is valid."""
    # Invoke the validator via its CLI entry point.
    # We capture stdout to avoid cluttering test output.
    result = subprocess.run(
        [sys.executable, "-c", "from src.ci.validate_workflow import main; main()", str(temp_workflow_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Expected success, got {result.stderr}"
    assert "✅ Workflow structure is valid." in result.stdout


def test_validator_fails_when_validate_job_missing(temp_workflow_file: pathlib.Path):
    """If the `validate` job is missing, the validator must fail."""
    # Rewrite the workflow without the validate job.
    invalid_content = textwrap.dedent(
        """
        name: CI

        on:
          push:
            branches: [ main ]

        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - name: Dummy step
                run: echo "Hello"
        """
    )
    temp_workflow_file.write_text(invalid_content, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-c", "from src.ci.validate_workflow import main; main()", str(temp_workflow_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "No `validate` job defined" in result.stderr


def test_validator_fails_when_make_validate_step_missing(temp_workflow_file: pathlib.Path):
    """The validator must fail if the `validate` job lacks a `make validate` step."""
    # Rewrite the workflow with a validate job that does not run `make validate`.
    invalid_content = textwrap.dedent(
        """
        name: CI

        on:
          push:
            branches: [ main ]

        jobs:
          validate:
            runs-on: ubuntu-latest
            steps:
              - name: Some other command
                run: echo "nothing"
        """
    )
    temp_workflow_file.write_text(invalid_content, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-c", "from src.ci.validate_workflow import main; main()", str(temp_workflow_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "does not contain a step that runs `make validate`" in result.stderr


def test_validator_direct_import_success():
    """Calling the validator's main() function directly should succeed with a valid file."""
    # Create a temporary valid workflow file.
    wf_path = pathlib.Path("tmp_valid_ci.yml")
    wf_path.write_text(
        """
        jobs:
          validate:
            steps:
              - run: make validate
        """,
        encoding="utf-8",
    )
    try:
        # The function reads the path from sys.argv if provided;
        # we pass the path explicitly.
        validator_main([str(wf_path)])
    finally:
        wf_path.unlink()

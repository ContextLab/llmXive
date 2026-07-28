"""
CI workflow validation script.

This script is used as a CI step to ensure that the GitHub Actions workflow
file ``.github/workflows/ci.yml`` contains the required job definitions.
Specifically it checks for:
  * the presence of a top‑level ``jobs`` mapping,
  * a job named ``validate``,
  * a job whose name includes the word ``skeleton`` (e.g. ``skeleton-ci``).

If any of these checks fail the script exits with a non‑zero status code
and prints a helpful error message to ``stderr``; otherwise it exits with
status ``0`` and prints a success message.
"""

import sys
from pathlib import Path

import yaml


def get_workflow_path() -> Path:
    """
    Return the absolute path to the CI workflow file.

    The repository layout is expected to have the workflow at
    ``.github/workflows/ci.yml`` relative to the project root.
    """
    return Path(".github") / "workflows" / "ci.yml"


def load_workflow(path: Path) -> dict:
    """
    Load and parse a YAML workflow file.

    Parameters
    ----------
    path: Path
        Path to the YAML file.

    Returns
    -------
    dict
        The parsed YAML content.

    Raises
    ------
    yaml.YAMLError
        If the file cannot be parsed as valid YAML.
    """
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_workflow_structure(workflow: dict) -> list[str]:
    """
    Validate the essential structure of the CI workflow.

    The function returns a list of error messages; an empty list means the
    workflow satisfies all required checks.

    Checks performed
    ----------------
    1. The workflow must be a mapping (dictionary).
    2. A top‑level ``jobs`` key must exist and be a mapping.
    3. A job called ``validate`` must be present.
    4. At least one job whose name contains the substring ``skeleton``
       (case‑insensitive) must be present (e.g. ``skeleton-ci``).

    Parameters
    ----------
    workflow: dict
        Parsed CI workflow content.

    Returns
    -------
    list[str]
        List of validation error messages.
    """
    errors: list[str] = []

    if not isinstance(workflow, dict):
        errors.append("Workflow file does not contain a YAML mapping at the top level.")
        return errors

    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        errors.append("Missing or invalid top‑level 'jobs' mapping.")
        return errors

    # 3. ``validate`` job
    if "validate" not in jobs:
        errors.append("Required job 'validate' is missing from the workflow.")

    # 4. skeleton‑ci job (any job containing the word 'skeleton')
    skeleton_job_found = any("skeleton" in name.lower() for name in jobs.keys())
    if not skeleton_job_found:
        errors.append(
            "Missing skeleton CI job (expected a job with 'skeleton' in its name)."
        )

    return errors


def main() -> None:
    """
    Entry point for the CI validation step.

    The function performs the following steps:
    1. Locate the workflow file.
    2. Parse the YAML content.
    3. Run structural validation.
    4. Exit with status 0 on success or 1 on failure, printing messages
       to ``stderr`` for any problems.
    """
    workflow_path = get_workflow_path()

    if not workflow_path.is_file():
        print(
            f"CI workflow file not found at expected location: {workflow_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        workflow = load_workflow(workflow_path)
    except Exception as exc:  # pragma: no cover – YAML parsing errors are rare
        print(f"Failed to parse CI workflow YAML: {exc}", file=sys.stderr)
        sys.exit(1)

    validation_errors = validate_workflow_structure(workflow)

    if validation_errors:
        for err in validation_errors:
            print(f"CI workflow validation error: {err}", file=sys.stderr)
        sys.exit(1)

    # All checks passed
    print("CI workflow structure validated successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
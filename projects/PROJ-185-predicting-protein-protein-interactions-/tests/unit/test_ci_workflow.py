import yaml
from pathlib import Path

def test_ci_workflow_contains_validate_job():
    """
    Verify that the CI workflow file exists and defines a job named ``validate``.
    """
    # Repository root is two levels up from this test file (tests/unit -> tests -> repo root)
    repo_root = Path(__file__).resolve().parents[2]
    workflow_path = repo_root / ".github" / "workflows" / "ci.yml"

    # The workflow file must exist
    assert workflow_path.is_file(), f"CI workflow file not found at {workflow_path}"

    # Load the YAML content
    content = yaml.safe_load(workflow_path.read_text())
    assert isinstance(content, dict), "CI workflow YAML should be a mapping"

    # Ensure a 'jobs' mapping is present
    jobs = content.get("jobs")
    assert isinstance(jobs, dict), "CI workflow must contain a top‑level 'jobs' mapping"

    # Verify that a job named 'validate' is defined
    assert "validate" in jobs, "CI workflow must contain a 'validate' job"

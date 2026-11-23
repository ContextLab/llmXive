"""
Additional unit tests to validate the CI workflow configuration.
"""
import os
import yaml
import pytest
from pathlib import Path

CI_WORKFLOW_PATH = Path(".github/workflows/ci.yml")

@pytest.fixture
def ci_config():
    if not CI_WORKFLOW_PATH.exists():
        pytest.skip("CI workflow file not found")
    with open(CI_WORKFLOW_PATH, "r") as f:
        return yaml.safe_load(f)

def test_ci_workflow_syntax(ci_config):
    """Verify the CI workflow file has valid YAML syntax."""
    assert ci_config is not None
    assert isinstance(ci_config, dict)

def test_ci_workflow_has_jobs(ci_config):
    """Verify the CI workflow has at least one job defined."""
    assert "jobs" in ci_config
    assert len(ci_config["jobs"]) > 0

def test_ci_workflow_job_has_steps(ci_config):
    """Verify each job has steps defined."""
    for job_name, job_config in ci_config["jobs"].items():
        assert "steps" in job_config, f"Job {job_name} has no steps"
        assert len(job_config["steps"]) > 0, f"Job {job_name} has no steps defined"

def test_ci_workflow_uses_actions(ci_config):
    """Verify the CI workflow uses standard GitHub Actions."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    uses_actions = [s for s in steps if "uses" in s]
    assert len(uses_actions) > 0, "CI workflow should use GitHub Actions"

def test_ci_workflow_python_version(ci_config):
    """Verify the CI workflow sets a Python version."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    python_setup = next((s for s in steps if "Set up Python" in s.get("name", "")), None)
    assert python_setup is not None, "CI workflow must set up Python"
    assert "with" in python_setup
    assert "python-version" in python_setup["with"], "CI workflow must specify Python version"
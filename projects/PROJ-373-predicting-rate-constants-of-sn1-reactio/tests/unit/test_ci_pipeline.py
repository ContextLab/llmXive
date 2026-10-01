"""
Unit tests for the CI/CD pipeline logic.
These tests ensure that the pipeline configuration is valid and that
the expected stages (unit, integration, contract tests) are defined.
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

def test_ci_workflow_exists(ci_config):
    """Verify the CI workflow file exists and is valid YAML."""
    assert ci_config is not None
    assert "name" in ci_config
    assert ci_config["name"] == "CI/CD Pipeline"

def test_ci_triggers(ci_config):
    """Verify the CI workflow triggers on push and pull_request."""
    assert "on" in ci_config
    triggers = ci_config["on"]
    assert "push" in triggers
    assert "pull_request" in triggers

def test_ci_job_structure(ci_config):
    """Verify the CI job structure."""
    assert "jobs" in ci_config
    assert "build-and-test" in ci_config["jobs"]
    job = ci_config["jobs"]["build-and-test"]
    assert "runs-on" in job
    assert job["runs-on"] == "ubuntu-latest"
    assert "steps" in job

def test_ci_steps_exist(ci_config):
    """Verify the CI pipeline includes all required steps."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    step_names = [s.get("name", "") for s in steps]

    required_steps = [
        "Checkout code",
        "Set up Python",
        "Install dependencies",
        "Run Unit Tests",
        "Run Integration Tests",
        "Run Contract Tests"
    ]

    for req in required_steps:
        assert any(req in name for name in step_names), f"Missing step: {req}"

def test_ci_test_commands(ci_config):
    """Verify the test commands are correctly specified."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]

    # Find the test steps
    unit_test_step = next((s for s in steps if "Run Unit Tests" in s.get("name", "")), None)
    integration_test_step = next((s for s in steps if "Run Integration Tests" in s.get("name", "")), None)
    contract_test_step = next((s for s in steps if "Run Contract Tests" in s.get("name", "")), None)

    assert unit_test_step is not None
    assert "run" in unit_test_step
    assert "pytest tests/unit/" in unit_test_step["run"]

    assert integration_test_step is not None
    assert "run" in integration_test_step
    assert "pytest tests/integration/" in integration_test_step["run"]

    assert contract_test_step is not None
    assert "run" in contract_test_step
    assert "pytest tests/contract/" in contract_test_step["run"]

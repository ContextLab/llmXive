"""
Contract tests for the CI/CD pipeline.
These tests verify that the CI pipeline adheres to the project's
quality gates and testing requirements.
"""
import os
import yaml
import pytest
from pathlib import Path

CI_WORKFLOW_PATH = Path(".github/workflows/ci.yml")
REQUIREMENTS_PATH = Path("requirements.txt")

@pytest.fixture
def ci_config():
    if not CI_WORKFLOW_PATH.exists():
        pytest.skip("CI workflow file not found")
    with open(CI_WORKFLOW_PATH, "r") as f:
        return yaml.safe_load(f)

def test_ci_requires_unit_tests(ci_config):
    """Verify the CI pipeline requires unit tests."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    has_unit_tests = any("Run Unit Tests" in s.get("name", "") for s in steps)
    assert has_unit_tests, "CI pipeline must include unit tests"

def test_ci_requires_integration_tests(ci_config):
    """Verify the CI pipeline requires integration tests."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    has_integration_tests = any("Run Integration Tests" in s.get("name", "") for s in steps)
    assert has_integration_tests, "CI pipeline must include integration tests"

def test_ci_requires_contract_tests(ci_config):
    """Verify the CI pipeline requires contract tests."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    has_contract_tests = any("Run Contract Tests" in s.get("name", "") for s in steps)
    assert has_contract_tests, "CI pipeline must include contract tests"

def test_ci_uses_pytest(ci_config):
    """Verify the CI pipeline uses pytest for running tests."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    for step in steps:
        if "run" in step:
            assert "pytest" in step["run"], "CI pipeline must use pytest"

def test_ci_installs_dependencies(ci_config):
    """Verify the CI pipeline installs dependencies."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    has_install = any("Install dependencies" in s.get("name", "") for s in steps)
    assert has_install, "CI pipeline must install dependencies"
    # Check that it references requirements.txt
    install_step = next((s for s in steps if "Install dependencies" in s.get("name", "")), None)
    if install_step and "run" in install_step:
        assert "requirements.txt" in install_step["run"], "CI pipeline must install from requirements.txt"

def test_ci_uploads_test_results(ci_config):
    """Verify the CI pipeline uploads test results."""
    job = ci_config["jobs"]["build-and-test"]
    steps = job["steps"]
    has_upload = any("Upload test results" in s.get("name", "") for s in steps)
    assert has_upload, "CI pipeline must upload test results"

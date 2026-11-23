"""
Unit tests to verify CI/CD workflow configuration and logic.
These tests ensure that the pipeline logic (if extracted to Python helpers)
works correctly, and that the workflow file exists and is valid YAML.
"""
import os
import yaml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

def test_ci_workflow_file_exists():
    """Verify that the CI workflow file exists."""
    assert WORKFLOW_PATH.exists(), f"CI workflow file not found at {WORKFLOW_PATH}"

def test_ci_workflow_is_valid_yaml():
    """Verify that the CI workflow file is valid YAML."""
    try:
        with open(WORKFLOW_PATH, 'r') as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"CI workflow file is not valid YAML: {e}")

def test_ci_workflow_has_required_jobs():
    """Verify that the CI workflow contains the required jobs."""
    with open(WORKFLOW_PATH, 'r') as f:
        workflow = yaml.safe_load(f)

    assert 'jobs' in workflow, "CI workflow missing 'jobs' key"
    jobs = workflow['jobs']

    required_jobs = ['setup-and-test']
    for job in required_jobs:
        assert job in jobs, f"Required job '{job}' not found in CI workflow"

def test_ci_workflow_runs_unit_tests():
    """Verify that the CI workflow includes a step to run unit tests."""
    with open(WORKFLOW_PATH, 'r') as f:
        workflow = yaml.safe_load(f)

    steps = workflow['jobs']['setup-and-test']['steps']
    unit_test_step_found = False
    for step in steps:
        if 'Run Unit Tests' in step.get('name', ''):
            unit_test_step_found = True
            break

    assert unit_test_step_found, "CI workflow does not include a 'Run Unit Tests' step"

def test_ci_workflow_runs_integration_tests():
    """Verify that the CI workflow includes a step to run integration tests."""
    with open(WORKFLOW_PATH, 'r') as f:
        workflow = yaml.safe_load(f)

    steps = workflow['jobs']['setup-and-test']['steps']
    integration_test_step_found = False
    for step in steps:
        if 'Run Integration Tests' in step.get('name', ''):
            integration_test_step_found = True
            break

    assert integration_test_step_found, "CI workflow does not include a 'Run Integration Tests' step"

def test_ci_workflow_runs_contract_tests():
    """Verify that the CI workflow includes a step to run contract tests."""
    with open(WORKFLOW_PATH, 'r') as f:
        workflow = yaml.safe_load(f)

    steps = workflow['jobs']['setup-and-test']['steps']
    contract_test_step_found = False
    for step in steps:
        if 'Run Contract Tests' in step.get('name', ''):
            contract_test_step_found = True
            break

    assert contract_test_step_found, "CI workflow does not include a 'Run Contract Tests' step"

def test_ci_workflow_uploads_artifacts():
    """Verify that the CI workflow includes a step to upload artifacts."""
    with open(WORKFLOW_PATH, 'r') as f:
        workflow = yaml.safe_load(f)

    steps = workflow['jobs']['setup-and-test']['steps']
    upload_step_found = False
    for step in steps:
        if 'Upload Test Results' in step.get('name', '') or 'Upload Coverage' in step.get('name', ''):
            upload_step_found = True
            break

    assert upload_step_found, "CI workflow does not include an artifact upload step"

def test_required_test_directories_exist():
    """Verify that the test directories referenced in CI exist."""
    unit_dir = PROJECT_ROOT / "tests" / "unit"
    integration_dir = PROJECT_ROOT / "tests" / "integration"
    contract_dir = PROJECT_ROOT / "tests" / "contract"

    assert unit_dir.exists(), f"Unit test directory not found: {unit_dir}"
    assert integration_dir.exists(), f"Integration test directory not found: {integration_dir}"
    assert contract_dir.exists(), f"Contract test directory not found: {contract_dir}"

def test_pytest_command_exists_in_workflow():
    """Verify that 'pytest' is used in the workflow steps."""
    with open(WORKFLOW_PATH, 'r') as f:
        content = f.read()

    assert 'pytest' in content, "CI workflow does not use 'pytest' command"

def test_workflow_has_timeout():
    """Verify that the CI workflow has a timeout configured."""
    with open(WORKFLOW_PATH, 'r') as f:
        workflow = yaml.safe_load(f)

    job_config = workflow['jobs']['setup-and-test']
    assert 'timeout-minutes' in job_config, "CI workflow job missing 'timeout-minutes' configuration"
    assert job_config['timeout-minutes'] > 0, "CI workflow timeout must be greater than 0"
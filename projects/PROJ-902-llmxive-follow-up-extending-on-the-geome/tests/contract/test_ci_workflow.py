"""
Contract test for CI workflow schema validation.

This test validates that the GitHub Actions workflow file (.github/workflows/ci.yml)
adheres to the expected schema defined in the project specifications.
It checks for the presence of required jobs, steps, and configuration options
such as caching, timeouts, and resource monitoring artifacts.
"""

import os
import yaml
import pytest
from pathlib import Path

# Path to the CI workflow file
CI_WORKFLOW_PATH = Path(".github/workflows/ci.yml")

# Expected schema constraints based on project requirements
REQUIRED_JOBS = ["build", "test"]
REQUIRED_STEPS_IN_BUILD = [
    "Checkout",
    "Set up Python",
    "Install dependencies",
    "Run linters",
    "Run tests"
]
REQUIRED_STEPS_IN_TEST = [
    "Checkout",
    "Set up Python",
    "Install dependencies",
    "Run resource monitor",
    "Upload artifacts"
]

REQUIRED_CACHE_KEYS = ["datasets"]
REQUIRED_TIMEOUT_MINUTES = 360  # 6 hours as per spec
REQUIRED_ARTIFACT_NAME = "ci_metrics.json"


def load_workflow():
    """Load and parse the GitHub Actions workflow YAML file."""
    if not CI_WORKFLOW_PATH.exists():
        raise FileNotFoundError(f"CI workflow file not found at {CI_WORKFLOW_PATH}")

    with open(CI_WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_workflow_file_exists():
    """Assert that the CI workflow file exists."""
    assert CI_WORKFLOW_PATH.exists(), f"File {CI_WORKFLOW_PATH} must exist"


def test_workflow_valid_yaml():
    """Assert that the workflow file is valid YAML."""
    try:
        workflow = load_workflow()
        assert workflow is not None, "Workflow content cannot be empty"
    except yaml.YAMLError as e:
        pytest.fail(f"Workflow file contains invalid YAML: {e}")


def test_workflow_has_required_jobs():
    """Assert that the workflow contains all required jobs."""
    workflow = load_workflow()
    jobs = workflow.get("jobs", {})
    
    for job_name in REQUIRED_JOBS:
        assert job_name in jobs, f"Required job '{job_name}' is missing from the workflow"


def test_workflow_build_job_has_required_steps():
    """Assert that the 'build' job contains required steps."""
    workflow = load_workflow()
    build_job = workflow.get("jobs", {}).get("build", {})
    steps = build_job.get("steps", [])
    
    step_names = [step.get("name", "") for step in steps]
    
    for required_step in REQUIRED_STEPS_IN_BUILD:
        found = any(required_step.lower() in name.lower() for name in step_names)
        assert found, f"Required step '{required_step}' is missing from the 'build' job"


def test_workflow_test_job_has_required_steps():
    """Assert that the 'test' job contains required steps."""
    workflow = load_workflow()
    test_job = workflow.get("jobs", {}).get("test", {})
    steps = test_job.get("steps", [])
    
    step_names = [step.get("name", "") for step in steps]
    
    for required_step in REQUIRED_STEPS_IN_TEST:
        found = any(required_step.lower() in name.lower() for name in step_names)
        assert found, f"Required step '{required_step}' is missing from the 'test' job"


def test_workflow_has_timeout():
    """Assert that the workflow or jobs have a timeout configuration."""
    workflow = load_workflow()
    
    # Check top-level timeout if present, otherwise check jobs
    timeout = workflow.get("defaults", {}).get("run", {}).get("timeout-minutes")
    if not timeout:
        jobs = workflow.get("jobs", {})
        # Check if any job has a timeout, preferably the test job
        test_job = jobs.get("test", {})
        timeout = test_job.get("timeout-minutes")
    
    assert timeout is not None, "Workflow must define a timeout configuration"
    assert timeout <= REQUIRED_TIMEOUT_MINUTES, f"Timeout ({timeout} min) must not exceed {REQUIRED_TIMEOUT_MINUTES} min"


def test_workflow_has_cache_configuration():
    """Assert that the workflow includes caching for datasets."""
    workflow = load_workflow()
    jobs = workflow.get("jobs", {})
    
    # Check both build and test jobs for cache steps
    found_cache = False
    for job_name in REQUIRED_JOBS:
        job = jobs.get(job_name, {})
        steps = job.get("steps", [])
        for step in steps:
            if step.get("uses", "").startswith("actions/cache"):
                with_key = step.get("with", {})
                key = with_key.get("key", "")
                if any(cache_key.lower() in key.lower() for cache_key in REQUIRED_CACHE_KEYS):
                    found_cache = True
                    break
        if found_cache:
            break
    
    assert found_cache, f"Workflow must include a cache step for keys containing: {REQUIRED_CACHE_KEYS}"


def test_workflow_uploads_ci_metrics_artifact():
    """Assert that the workflow uploads the ci_metrics.json artifact."""
    workflow = load_workflow()
    jobs = workflow.get("jobs", {})
    
    found_artifact = False
    for job_name in REQUIRED_JOBS:
        job = jobs.get(job_name, {})
        steps = job.get("steps", [])
        for step in steps:
            if step.get("uses", "").startswith("actions/upload-artifact"):
                with_key = step.get("with", {})
                name = with_key.get("name", "")
                if REQUIRED_ARTIFACT_NAME in name:
                    found_artifact = True
                    break
        if found_artifact:
            break
    
    assert found_artifact, f"Workflow must upload an artifact named '{REQUIRED_ARTIFACT_NAME}'"


def test_workflow_has_resource_monitor_step():
    """Assert that the workflow explicitly runs the resource monitor."""
    workflow = load_workflow()
    jobs = workflow.get("jobs", {})
    test_job = jobs.get("test", {})
    steps = test_job.get("steps", [])
    
    found_monitor = False
    for step in steps:
        step_name = step.get("name", "")
        step_run = step.get("run", "")
        if "resource_monitor" in step_name.lower() or "resource_monitor" in step_run.lower():
            found_monitor = True
            break
    
    assert found_monitor, "Workflow must include a step that runs the resource monitor"
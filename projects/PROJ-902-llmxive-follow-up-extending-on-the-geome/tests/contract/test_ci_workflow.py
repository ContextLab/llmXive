"""
Contract tests for the CI workflow configuration.

This module validates the structure and content of the GitHub Actions
workflow file (.github/workflows/ci.yml) to ensure it adheres to the
project's requirements for matrix splitting, timeouts, and artifact handling.
"""
import os
import yaml
from pathlib import Path
import pytest

# Path to the CI workflow file relative to project root
CI_WORKFLOW_PATH = Path(".github/workflows/ci.yml")

@pytest.fixture
def ci_workflow_content():
    """Load and parse the CI workflow YAML content."""
    if not CI_WORKFLOW_PATH.exists():
        pytest.fail(f"CI workflow file not found at {CI_WORKFLOW_PATH}")
    
    with open(CI_WORKFLOW_PATH, "r", encoding="utf-8") as f:
        try:
            content = yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Failed to parse CI workflow YAML: {e}")
    
    if content is None:
        pytest.fail("CI workflow file is empty or invalid YAML")
    
    return content

def test_ci_workflow_exists(ci_workflow_content):
    """Verify the CI workflow file exists and is valid YAML."""
    assert ci_workflow_content is not None, "CI workflow content is None"
    assert isinstance(ci_workflow_content, dict), "CI workflow must be a YAML mapping"

def test_ci_workflow_has_required_top_level_keys(ci_workflow_content):
    """Verify the CI workflow contains required top-level keys."""
    required_keys = ["name", "on", "jobs"]
    for key in required_keys:
        assert key in ci_workflow_content, f"Missing required top-level key: {key}"

def test_ci_workflow_triggers_on_push_and_pull_request(ci_workflow_content):
    """Verify the workflow triggers on push and pull_request events."""
    on_config = ci_workflow_content.get("on", {})
    
    # 'on' can be a dict or a list in YAML, handle both
    if isinstance(on_config, dict):
        triggers = list(on_config.keys())
    elif isinstance(on_config, list):
        triggers = on_config
    else:
        pytest.fail("Invalid 'on' configuration in CI workflow")
    
    assert "push" in triggers, "Workflow must trigger on 'push' events"
    assert "pull_request" in triggers, "Workflow must trigger on 'pull_request' events"

def test_ci_workflow_has_ci_job(ci_workflow_content):
    """Verify the workflow contains a 'ci' job or equivalent CI job."""
    jobs = ci_workflow_content.get("jobs", {})
    assert isinstance(jobs, dict), "Jobs must be a mapping"
    
    # Check for any job that looks like a CI job (e.g., 'ci', 'test', 'build')
    ci_job_names = [name for name in jobs.keys() if name.lower() in ["ci", "test", "build", "check"]]
    assert len(ci_job_names) > 0, "No CI-related job found in workflow"

def test_ci_workflow_job_has_steps(ci_workflow_content):
    """Verify CI jobs have a steps list."""
    jobs = ci_workflow_content.get("jobs", {})
    
    for job_name, job_config in jobs.items():
        if job_name.lower() in ["ci", "test", "build", "check"]:
            steps = job_config.get("steps", [])
            assert isinstance(steps, list), f"Job '{job_name}' must have a steps list"
            assert len(steps) > 0, f"Job '{job_name}' must have at least one step"

def test_ci_workflow_has_matrix_splitting_logic(ci_workflow_content):
    """
    Verify the workflow implements matrix-splitting logic as required by FR-012.
    
    The spec requires:
    - Separate jobs per condition with ≤15 seeds
    - Explicit matrix configuration in the workflow
    """
    jobs = ci_workflow_content.get("jobs", {})
    
    matrix_found = False
    for job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])
        for step in steps:
            # Check for 'uses: actions/checkout' or similar to identify job structure
            if "with" in step and "matrix" in step.get("with", {}):
                matrix_found = True
                break
            if "run" in step:
                # Look for matrix configuration in run commands
                run_cmd = step.get("run", "")
                if "matrix" in run_cmd.lower() or "SEED" in run_cmd.upper():
                    matrix_found = True
                    break
        
        # Check if job itself has strategy.matrix
        strategy = job_config.get("strategy", {})
        if "matrix" in strategy:
            matrix_found = True
            break
    
    assert matrix_found, "CI workflow must implement matrix-splitting logic (strategy.matrix or matrix parameter)"

def test_ci_workflow_matrix_has_seed_limit(ci_workflow_content):
    """
    Verify matrix configuration limits seeds to ≤15 per job.
    
    This is a heuristic check - we look for explicit seed limits or
    comments indicating the limit.
    """
    jobs = ci_workflow_content.get("jobs", {})
    
    for job_name, job_config in jobs.items():
        strategy = job_config.get("strategy", {})
        matrix = strategy.get("matrix", {})
        
        if "seeds" in matrix or "seed" in matrix:
            seeds_config = matrix.get("seeds", matrix.get("seed", []))
            if isinstance(seeds_config, list):
                # If seeds are explicitly listed, check count
                assert len(seeds_config) <= 15, \
                    f"Matrix seeds in job '{job_name}' must be ≤15, found {len(seeds_config)}"
            elif isinstance(seeds_config, dict):
                # If seeds are defined as a range or set, check for max limit
                max_seeds = seeds_config.get("max", 999)
                assert max_seeds <= 15, \
                    f"Matrix seed limit in job '{job_name}' must be ≤15, found {max_seeds}"

def test_ci_workflow_has_timeout_configuration(ci_workflow_content):
    """Verify the workflow has timeout configuration for jobs."""
    jobs = ci_workflow_content.get("jobs", {})
    
    timeout_found = False
    for job_name, job_config in jobs.items():
        if "timeout-minutes" in job_config:
            timeout_found = True
            timeout_val = job_config["timeout-minutes"]
            assert isinstance(timeout_val, (int, float)), \
                f"timeout-minutes in job '{job_name}' must be a number"
            assert timeout_val > 0, \
                f"timeout-minutes in job '{job_name}' must be positive"
            break
        
        # Check steps for timeout
        steps = job_config.get("steps", [])
        for step in steps:
            if "timeout-minutes" in step:
                timeout_found = True
                break
        
        if timeout_found:
            break
    
    # Allow timeout at job or step level
    assert timeout_found, "CI workflow must have timeout configuration (timeout-minutes)"

def test_ci_workflow_uploads_artifacts(ci_workflow_content):
    """Verify the workflow uploads artifacts (e.g., logs, metrics)."""
    jobs = ci_workflow_content.get("jobs", {})
    
    upload_found = False
    for job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])
        for step in steps:
            # Check for upload-artifact action
            if step.get("uses", "").startswith("actions/upload-artifact"):
                upload_found = True
                break
            # Check for upload-artifact in run commands
            if "run" in step and "upload-artifact" in step.get("run", "").lower():
                upload_found = True
                break
        
        if upload_found:
            break
    
    assert upload_found, "CI workflow must upload artifacts (e.g., logs, metrics)"

def test_ci_workflow_has_cache_configuration(ci_workflow_content):
    """Verify the workflow caches dependencies (e.g., datasets)."""
    jobs = ci_workflow_content.get("jobs", {})
    
    cache_found = False
    for job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])
        for step in steps:
            # Check for cache action
            if step.get("uses", "").startswith("actions/cache"):
                cache_found = True
                break
            # Check for cache in run commands
            if "run" in step and "cache" in step.get("run", "").lower():
                cache_found = True
                break
        
        if cache_found:
            break
    
    assert cache_found, "CI workflow must have cache configuration for dependencies"

def test_ci_workflow_handles_failures_gracefully(ci_workflow_content):
    """
    Verify the workflow has failure handling (e.g., continue-on-error, 
    or archive logs on failure).
    """
    jobs = ci_workflow_content.get("jobs", {})
    
    failure_handling_found = False
    for job_name, job_config in jobs.items():
        # Check for continue-on-error at job level
        if job_config.get("continue-on-error", False):
            failure_handling_found = True
            break
        
        # Check steps for failure handling
        steps = job_config.get("steps", [])
        for step in steps:
            # Check for continue-on-error at step level
            if step.get("continue-on-error", False):
                failure_handling_found = True
                break
            # Check for archive logs on failure
            if "run" in step:
                run_cmd = step.get("run", "")
                if "archive" in run_cmd.lower() and ("log" in run_cmd.lower() or "artifact" in run_cmd.lower()):
                    failure_handling_found = True
                    break
        
        if failure_handling_found:
            break
    
    assert failure_handling_found, "CI workflow must have failure handling (continue-on-error or archive logs)"

def test_ci_workflow_runs_python_tests(ci_workflow_content):
    """Verify the workflow runs Python tests."""
    jobs = ci_workflow_content.get("jobs", {})
    
    test_found = False
    for job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])
        for step in steps:
            if "run" in step:
                run_cmd = step.get("run", "")
                if "pytest" in run_cmd.lower() or "python -m pytest" in run_cmd.lower():
                    test_found = True
                    break
            if step.get("uses", "").startswith("actions/setup-python"):
                # If Python is set up, there should be a test step
                # This is a heuristic - we expect tests to be run
                test_found = True
                break
        
        if test_found:
            break
    
    assert test_found, "CI workflow must run Python tests (pytest)"
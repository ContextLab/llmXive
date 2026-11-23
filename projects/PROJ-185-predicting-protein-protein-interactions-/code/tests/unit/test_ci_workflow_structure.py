import pytest
import yaml
from pathlib import Path

@pytest.fixture
def workflow_path():
    return Path(__file__).resolve().parent.parent.parent / ".github" / "workflows" / "ci.yml"

def test_workflow_exists(workflow_path):
    assert workflow_path.exists(), "CI workflow file missing"

def test_workflow_has_validate_job(workflow_path):
    with open(workflow_path, "r") as f:
        data = yaml.safe_load(f)
    
    assert "jobs" in data, "No jobs section in workflow"
    assert "validate" in data["jobs"], "Missing 'validate' job"

def test_workflow_has_skeleton_ci_job(workflow_path):
    with open(workflow_path, "r") as f:
        data = yaml.safe_load(f)
    
    assert "skeleton-ci" in data["jobs"], "Missing 'skeleton-ci' job"

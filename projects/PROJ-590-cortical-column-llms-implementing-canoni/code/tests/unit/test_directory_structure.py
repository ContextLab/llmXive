import os
import pytest
import sys
from pathlib import Path

# Add the project root to the path to allow imports if needed,
# though this test primarily checks file system state.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

REQUIRED_DIRS = [
    "src/models",
    "src/data",
    "src/training",
    "src/experiments",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "scripts",
    "data/results",
    "data/logs",
    "data/configs",
    "state"
]

def test_project_directories_exist():
    """
    Verifies that all required directories from plan.md exist.
    This test satisfies the requirement for T001a to provide concrete evidence
    of the directory tree.
    """
    missing = []
    for d in REQUIRED_DIRS:
        path = project_root / d
        if not path.exists() or not path.is_dir():
            missing.append(d)
    
    assert not missing, f"Missing required directories: {missing}"

def test_project_root_is_valid():
    """
    Verifies that the project root contains the expected top-level structure
    and specifically that the 'state' directory contains the required template.
    """
    state_dir = project_root / "state"
    assert state_dir.exists(), "State directory missing"
    
    template_file = state_dir / "project_state.yaml"
    assert template_file.exists(), "State template file (project_state.yaml) missing in state/"
    
    # Verify content of the template
    import yaml
    with open(template_file, 'r') as f:
        content = yaml.safe_load(f)
    
    required_keys = {"hashes", "artifacts", "updated_at"}
    assert set(content.keys()) == required_keys, \
        f"State template missing required keys. Found: {set(content.keys())}, Expected: {required_keys}"
    
    # Verify types
    assert isinstance(content["hashes"], dict), "hashes must be a dict"
    assert isinstance(content["artifacts"], list), "artifacts must be a list"
    assert isinstance(content["updated_at"], str), "updated_at must be a string"
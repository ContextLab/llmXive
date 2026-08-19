"""
Unit tests for T001: Verify directory structure creation.
"""
import os
import pytest
import sys
from pathlib import Path

# Add parent to path for imports if running directly
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.setup_directories import ensure_directory_structure, create_state_template

def test_project_directories_exist(tmp_path):
    """
    Test that ensure_directory_structure creates all required folders.
    """
    required_dirs = [
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
        "state",
    ]

    ensure_directory_structure(tmp_path)

    for d in required_dirs:
        full_path = tmp_path / d
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} exists but is not a directory"

def test_state_template_exists(tmp_path):
    """
    Test that create_state_template creates state/template.yaml.
    """
    ensure_directory_structure(tmp_path)
    create_state_template(tmp_path)
    
    template_path = tmp_path / "state" / "template.yaml"
    assert template_path.exists(), "state/template.yaml was not created"
    assert template_path.is_file(), "state/template.yaml is not a file"
    
    # Verify it's valid YAML
    import yaml
    with open(template_path, "r") as f:
        content = yaml.safe_load(f)
    
    assert "project" in content
    assert content["project"] == "PROJ-590-cortical-column-llms-implementing-canoni"

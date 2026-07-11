"""
Unit tests for configuration and project structure.
"""
import pytest
import os
from pathlib import Path

def test_project_structure_exists():
    """Verify that the required project directories exist."""
    base = Path(__file__).parent.parent
    assert (base / "code").exists(), "code/ directory missing"
    assert (base / "tests").exists(), "tests/ directory missing"
    assert (base / "data").exists(), "data/ directory missing"
    
    # Verify subdirectories
    assert (base / "code" / "utils").exists(), "code/utils/ missing"
    assert (base / "code" / "embeddings").exists(), "code/embeddings/ missing"
    assert (base / "code" / "models").exists(), "code/models/ missing"
    assert (base / "code" / "pipelines").exists(), "code/pipelines/ missing"
    assert (base / "code" / "analysis").exists(), "code/analysis/ missing"

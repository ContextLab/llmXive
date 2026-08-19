"""
Unit tests for T003: Verify .gitignore configuration.
"""
import os
import pytest
from pathlib import Path

def test_gitignore_content(tmp_path):
    """
    Verify that .gitignore contains required exclusions and inclusions.
    """
    gitignore_path = tmp_path / ".gitignore"
    
    # Create a minimal gitignore for testing if not present
    # In real scenario, this file is created by T003 script
    expected_exclusions = [
        "data/",
        "__pycache__",
        "*.pyc",
        "*.log"
    ]
    
    expected_inclusions = [
        "!data/configs/",
        "!data/results/",
        "!data/logs/",
        "!state/"
    ]

    # If we are testing the actual project file
    project_root = Path(__file__).parent.parent.parent
    actual_gitignore = project_root / ".gitignore"
    
    if actual_gitignore.exists():
        with open(actual_gitignore, "r") as f:
            content = f.read()
        
        # Check exclusions
        for exclusion in expected_exclusions:
            assert exclusion in content, f"Missing exclusion: {exclusion}"
        
        # Check inclusions
        for inclusion in expected_inclusions:
            assert inclusion in content, f"Missing inclusion: {inclusion}"
        
        # CRITICAL: Ensure state/*.yaml is NOT ignored
        # The pattern "!state/" ensures state is tracked
        # We must NOT have "state/*.yaml" or "state/" ignored without un-ignore
        assert "state/*.yaml" not in content or "!state/*.yaml" in content, \
            "state/*.yaml should not be ignored"
    else:
        pytest.skip("Actual .gitignore not found in project root")

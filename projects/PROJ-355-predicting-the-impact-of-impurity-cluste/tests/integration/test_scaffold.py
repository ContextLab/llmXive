"""
Basic scaffold verification for integration tests.

This test ensures the integration test directory structure is correctly initialized
and that the test runner can discover tests in this package.
"""

def test_integration_directory_exists():
    """Verify that the integration test directory is present."""
    import os
    from pathlib import Path
    
    # Verify the current directory is the integration test directory
    current_dir = Path(__file__).parent
    assert current_dir.name == "integration", "This test must reside in the 'integration' directory"
    assert current_dir.is_dir(), "Integration test directory must exist"
    
    # Verify the parent directory (tests) exists
    assert current_dir.parent.name == "tests", "Parent directory must be 'tests'"
    assert current_dir.parent.is_dir(), "Tests directory must exist"

def test_project_structure_accessible():
    """Verify that the project structure is accessible from integration tests."""
    from pathlib import Path
    
    # Check that we can reach the project root via standard paths
    project_root = Path(__file__).parent.parent.parent
    assert project_root.exists(), "Project root must be accessible"
    
    # Verify key directories exist relative to project root
    required_dirs = ["code", "data", "results", "tests"]
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Required directory {dir_name} must exist at project root"
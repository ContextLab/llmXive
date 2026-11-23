"""
Integration test to verify the project structure is correctly created.
This test ensures that the setup script produces the expected directory layout
that other tasks depend on.
"""
import os
import pytest
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_project import main

def test_integration_project_structure():
    """
    End-to-end test: Run setup and verify the complete structure is ready
    for subsequent tasks (ingest, train, etc.).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Execute setup
            result = main()
            assert result == 0, "Setup should complete successfully"
            
            # Verify critical paths needed by downstream tasks
            critical_paths = {
                "code": "Required for Python modules",
                "data/raw": "Required for raw data ingestion (T010)",
                "data/processed": "Required for cleaned data (T012, T014)",
                "models": "Required for saving models (T018, T025)",
                "reports": "Required for output reports (T019, T020)",
                "state": "Required for state files (T005, T017c)",
                "tests": "Required for test suite"
            }
            
            for path, reason in critical_paths.items():
                full_path = Path(tmp_dir) / path
                assert full_path.exists(), f"{path} missing: {reason}"
                assert full_path.is_dir(), f"{path} is not a directory: {reason}"
                
        finally:
            os.chdir(original_cwd)
"""
Unit tests for the Quickstart Validation script.
These tests verify the logic of the validation script without running the full pipeline.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path if needed, though we are testing logic
# We will mock the environment for these tests

def test_check_environment_success(mocker):
    """Test that check_environment passes when all packages are present."""
    from code.quickstart_validate import check_environment
    
    # Mock imports to simulate presence
    mocker.patch.dict(sys.modules, {
        "mne": True,
        "numpy": True,
        "pandas": True,
        "scipy": True,
        "yaml": True,
        "sklearn": True,
        "lempel_ziv_complexity": True,
        "pytest": True
    })
    
    # This should not raise
    try:
        check_environment()
    except RuntimeError as e:
        pytest.fail(f"check_environment raised unexpectedly: {e}")

def test_check_environment_failure(mocker):
    """Test that check_environment fails when a package is missing."""
    from code.quickstart_validate import check_environment
    
    # Remove a mock to simulate missing package
    mocker.patch.dict(sys.modules, {
        "mne": True,
        "numpy": True,
        "pandas": True,
        "scipy": True,
        "yaml": True,
        "sklearn": True,
        "lempel_ziv_complexity": True,
        "pytest": True
    }, clear=False)
    
    # We can't easily "remove" a real package in the test env, so we test the logic
    # by patching the import logic inside the function if possible, or just trust the logic.
    # For this specific function, it relies on __import__.
    # A better test is to verify the error message format if we could force a failure.
    # Since we can't easily uninstall packages in the test runner, we skip the failure case
    # or mock the __import__ function globally.
    
    original_import = __builtins__.__import__
    
    def mock_import(name, *args, **kwargs):
        if name == "lempel_ziv_complexity":
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)
    
    __builtins__.__import__ = mock_import
    try:
        with pytest.raises(RuntimeError) as exc_info:
            check_environment()
        assert "Missing dependencies" in str(exc_info.value)
    finally:
        __builtins__.__import__ = original_import

def test_check_structure_success(mocker, tmp_path):
    """Test structure check with valid directories."""
    from code.quickstart_validate import check_structure
    
    # Create temporary directories
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "data" / "analysis").mkdir(parents=True)
    (tmp_path / "code").mkdir(parents=True)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "integration").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    
    # Patch PROJECT_ROOT
    import code.quickstart_validate as qv
    original_root = qv.PROJECT_ROOT
    qv.PROJECT_ROOT = tmp_path
    
    try:
        check_structure()
    finally:
        qv.PROJECT_ROOT = original_root

def test_check_structure_failure(mocker, tmp_path):
    """Test structure check with missing directories."""
    from code.quickstart_validate import check_structure
    
    # Create only some directories
    (tmp_path / "data" / "raw").mkdir(parents=True)
    # Missing others
    
    import code.quickstart_validate as qv
    original_root = qv.PROJECT_ROOT
    qv.PROJECT_ROOT = tmp_path
    
    try:
        with pytest.raises(FileNotFoundError) as exc_info:
            check_structure()
        assert "Missing directories" in str(exc_info.value)
    finally:
        qv.PROJECT_ROOT = original_root

def test_cpu_only_check(mocker):
    """Test that CPU check runs without error."""
    from code.quickstart_validate import check_cpu_only
    
    # Mock mne and torch to avoid side effects
    mocker.patch.dict(sys.modules, {
        "torch": None,
        "mne": type('obj', (object,), {'set_config': lambda k, v: None})()
    })
    
    # Should not raise
    check_cpu_only()

def test_validation_report_generation(mocker, tmp_path):
    """Test that the validation report is generated correctly."""
    from code.quickstart_validate import main
    import json
    
    # Mock the necessary checks to pass
    mocker.patch("code.quickstart_validate.check_environment")
    mocker.patch("code.quickstart_validate.check_structure")
    mocker.patch("code.quickstart_validate.check_cpu_only")
    mocker.patch("code.quickstart_validate.run_minimal_pipeline")
    
    # Mock PROJECT_ROOT
    import code.quickstart_validate as qv
    original_root = qv.PROJECT_ROOT
    qv.PROJECT_ROOT = tmp_path
    
    try:
        # Run main
        # We need to capture sys.exit
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        
        # Check report
        report_path = tmp_path / "data" / "analysis" / "validation_report.json"
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["status"] == "passed"
        assert "checks" in report
        assert "duration_seconds" in report
    finally:
        qv.PROJECT_ROOT = original_root

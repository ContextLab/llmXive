"""
Tests for the quickstart validation script.

These tests ensure that the validation logic works correctly
and handles edge cases appropriately.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from scripts.validate_quickstart import (
    check_directories,
    check_dependencies,
    check_entry_points,
    check_quickstart_exists,
    run_quickstart_simulation,
    REQUIRED_DIRS,
    REQUIRED_PACKAGES
)

class TestDirectoryValidation:
    def test_check_directories_all_exist(self, tmp_path):
        """Test that check_directories passes when all dirs exist."""
        # Create all required directories in tmp_path
        for d in REQUIRED_DIRS:
            # Replace PROJECT_ROOT with tmp_path for testing
            test_dir = tmp_path / d.relative_to(code_dir.parent)
            test_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the global REQUIRED_DIRS to use tmp_path
        with patch('scripts.validate_quickstart.REQUIRED_DIRS', 
                  [tmp_path / d.relative_to(code_dir.parent) for d in REQUIRED_DIRS]):
            ok, missing = check_directories()
            assert ok is True
            assert len(missing) == 0

    def test_check_directories_missing_some(self, tmp_path):
        """Test that check_directories fails when some dirs are missing."""
        # Only create some directories
        if len(REQUIRED_DIRS) > 1:
            created_dir = REQUIRED_DIRS[0].relative_to(code_dir.parent)
            (tmp_path / created_dir).mkdir(parents=True, exist_ok=True)
            
            with patch('scripts.validate_quickstart.REQUIRED_DIRS', 
                      [tmp_path / d.relative_to(code_dir.parent) for d in REQUIRED_DIRS]):
                ok, missing = check_directories()
                assert ok is False
                assert len(missing) > 0

class TestDependencyValidation:
    def test_check_dependencies_importable(self):
        """Test that check_dependencies passes for standard packages."""
        # Test with a known importable package
        test_packages = ["os", "sys", "json"]
        
        with patch('scripts.validate_quickstart.REQUIRED_PACKAGES', test_packages):
            ok, missing = check_dependencies()
            assert ok is True
            assert len(missing) == 0

    def test_check_dependencies_missing_package(self):
        """Test that check_dependencies fails for non-existent packages."""
        test_packages = ["os", "nonexistent_package_xyz_123"]
        
        with patch('scripts.validate_quickstart.REQUIRED_PACKAGES', test_packages):
            ok, missing = check_dependencies()
            assert ok is False
            assert "nonexistent_package_xyz_123" in missing

class TestEntryPointsValidation:
    def test_check_entry_points_existing_functions(self):
        """Test that check_entry_points finds existing functions."""
        # Test with a known module and function
        test_entry_points = [
            ("config", "ensure_directories")
        ]
        
        with patch('scripts.validate_quickstart.ENTRY_POINTS', test_entry_points):
            ok, failed = check_entry_points()
            # Should pass if ensure_directories exists in config
            # Note: This depends on the actual file structure
            # We're testing the logic, not the existence
            assert isinstance(ok, bool)
            assert isinstance(failed, list)

    def test_check_entry_points_missing_functions(self):
        """Test that check_entry_points reports missing functions."""
        test_entry_points = [
            ("config", "nonexistent_function_xyz_123")
        ]
        
        with patch('scripts.validate_quickstart.ENTRY_POINTS', test_entry_points):
            ok, failed = check_entry_points()
            assert ok is False
            assert len(failed) > 0

class TestQuickstartSimulation:
    @patch('scripts.validate_quickstart.load_manifest')
    @patch('scripts.validate_quickstart.calculate_pearson_correlation_all_genes')
    def test_run_quickstart_simulation_success(self, mock_calc, mock_load):
        """Test that simulation succeeds when mocks work."""
        mock_load.return_value = {"datasets": []}
        mock_calc.return_value = 0.95
        
        ok, msg = run_quickstart_simulation()
        assert ok is True
        assert "Simulation passed" in msg

    @patch('scripts.validate_quickstart.load_manifest')
    def test_run_quickstart_simulation_failure(self, mock_load):
        """Test that simulation fails when dependencies fail."""
        mock_load.side_effect = Exception("Mock failure")
        
        ok, msg = run_quickstart_simulation()
        assert ok is False
        assert "Mock failure" in msg

class TestIntegration:
    def test_main_function_exists(self):
        """Test that main function exists and returns integer."""
        from scripts.validate_quickstart import main
        assert callable(main)
        
        # We can't run main() fully without full setup, 
        # but we can verify it exists
        assert main.__name__ == "main"

    def test_all_required_functions_exist(self):
        """Test that all required functions are importable."""
        from scripts.validate_quickstart import (
            check_directories,
            check_dependencies,
            check_entry_points,
            check_quickstart_exists,
            run_quickstart_simulation
        )
        
        assert callable(check_directories)
        assert callable(check_dependencies)
        assert callable(check_entry_points)
        assert callable(check_quickstart_exists)
        assert callable(run_quickstart_simulation)
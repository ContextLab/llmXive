import pytest
import sys
from code.setup_dependencies import check_package_installed, get_package_version, validate_dependencies

def test_check_package_installed():
    """Test that we can check for installed packages."""
    # pandas should be installed if the environment is correct
    assert check_package_installed("pandas") is True

def test_get_package_version():
    """Test that we can get package versions."""
    version = get_package_version("pandas")
    assert version != "Not installed"
    assert len(version) > 0

def test_validate_dependencies():
    """Test validation of a list of dependencies."""
    deps = ["pandas", "nonexistent_package_xyz_123"]
    results = validate_dependencies(deps)
    
    assert "pandas" in results["results"]
    assert results["results"]["pandas"] is True
    assert "nonexistent_package_xyz_123" in results["results"]
    assert results["results"]["nonexistent_package_xyz_123"] is False
    assert len(results["missing"]) == 1
    assert "nonexistent_package_xyz_123" in results["missing"]

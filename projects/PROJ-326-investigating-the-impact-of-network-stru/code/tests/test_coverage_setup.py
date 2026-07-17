"""
Test to verify that the coverage setup is working correctly.
This test ensures that pytest-cov is properly configured and can measure coverage.
"""
import pytest
import sys
import os
from pathlib import Path

def test_coverage_module_imports():
    """Test that all source modules can be imported for coverage analysis."""
    modules_to_test = [
        "code.src.generators.base",
        "code.src.generators.er",
        "code.src.generators.sw",
        "code.src.generators.sf",
        "code.src.generators.metrics",
        "code.src.generators.metadata",
        "code.src.simulation.dynamics",
        "code.src.simulation.metrics",
        "code.src.simulation.stability",
        "code.src.simulation.diffusion",
        "code.src.analysis.regression",
        "code.src.analysis.anova",
        "code.src.analysis.sensitivity",
        "code.src.analysis.plotting",
        "code.src.analysis.power",
        "code.src.utils.config",
        "code.src.utils.logging",
        "code.src.utils.io",
        "code.src.utils.reproducibility",
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")

def test_pytest_cov_available():
    """Test that pytest-cov plugin is available."""
    try:
        import pytest_cov
    except ImportError:
        pytest.fail("pytest-cov is not installed. Please install it with: pip install pytest-cov")

def test_coverage_report_generation():
    """
    Test that coverage can be collected on a simple function.
    This verifies the coverage mechanism is working.
    """
    import coverage
    
    # Create a simple coverage instance
    cov = coverage.Coverage()
    cov.start()
    
    # Run a simple operation
    x = 1 + 1
    assert x == 2
    
    cov.stop()
    cov.save()
    
    # Verify coverage data was collected
    data = cov.get_data()
    assert data is not None
    
    # Clean up
    cov.erase()

def test_pytest_config_exists():
    """Test that pytest configuration file exists."""
    project_root = Path(__file__).parent.parent
    config_file = project_root / "pytest.ini"
    
    assert config_file.exists(), "pytest.ini configuration file not found"
    
    content = config_file.read_text()
    assert "[pytest]" in content, "pytest section not found in pytest.ini"
    assert "testpaths" in content, "testpaths not configured in pytest.ini"
    assert "--cov" in content, "coverage options not configured in pytest.ini"
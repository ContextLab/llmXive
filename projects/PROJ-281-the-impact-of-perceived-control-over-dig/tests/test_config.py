"""
Basic sanity test to ensure the project configuration and imports work.
This serves as a smoke test for the pytest setup.
"""
import pytest
from pathlib import Path

def test_project_structure(project_root_path):
    """Verify that the expected project directories exist."""
    assert (project_root_path / "code").exists(), "code/ directory missing"
    assert (project_root_path / "tests").exists(), "tests/ directory missing"
    assert (project_root_path / "data").exists(), "data/ directory missing"
    
    # Check subdirectories if they should exist
    # Note: T008 ensures these exist, but we check for robustness
    # If T008 failed, this might fail, which is expected behavior for a failing setup
    if (project_root_path / "data" / "raw").exists():
        assert (project_root_path / "data" / "raw").is_dir()
    if (project_root_path / "data" / "processed").exists():
        assert (project_root_path / "data" / "processed").is_dir()

def test_config_imports():
    """Verify that the config module can be imported."""
    try:
        import config
        assert hasattr(config, 'CONFIG'), "CONFIG not found in config module"
    except ImportError as e:
        pytest.fail(f"Failed to import config module: {e}")

def test_services_imports():
    """Verify that core services can be imported."""
    try:
        from services.data_ingestion import run_data_ingestion_pipeline
        from services.anxiety_scoring import run_full_scoring_pipeline
        from services.proxy_extractor import run_proxy_extraction_pipeline
    except ImportError as e:
        pytest.fail(f"Failed to import services: {e}")

def test_analysis_imports():
    """Verify that analysis modules can be imported."""
    try:
        from analysis.statistical_test import run_statistical_analysis_pipeline
    except ImportError as e:
        pytest.fail(f"Failed to import analysis modules: {e}")

def test_viz_imports():
    """Verify that visualization modules can be imported."""
    try:
        from viz.plot_results import run_visualization_pipeline
    except ImportError as e:
        pytest.fail(f"Failed to import viz modules: {e}")

"""
Test suite to ensure all project modules are importable without errors.
"""
import pytest

def test_module_imports():
    """Verify that all core sub-packages can be imported."""
    try:
        import code.src.data
        import code.src.analysis
        import code.src.stats
        import code.src.reporting
        import code.src.utils
        import code.src.pipeline
        import code.src.run_pipeline
    except ImportError as e:
        pytest.fail(f"Module import failed: {e}")

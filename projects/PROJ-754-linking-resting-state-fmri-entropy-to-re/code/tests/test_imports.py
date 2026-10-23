"""
Tests that all core modules are importable without syntax or dependency errors.
"""
import pytest

def test_core_imports():
    """Verify that all required pipeline modules can be imported."""
    try:
        import code.src.pipeline
        import code.src.run_pipeline
        import code.src.data.download_hcp
        import code.src.data.qc
        import code.src.analysis.entropy
        import code.src.compute_entropy
        import code.src.data.download_data
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

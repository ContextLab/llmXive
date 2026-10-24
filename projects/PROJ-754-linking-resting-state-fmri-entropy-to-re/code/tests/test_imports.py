"""
Test that all core project modules can be imported without error.
"""
import pytest

def test_module_imports():
    """Verify that all key modules are importable."""
    try:
        import code.src.run_pipeline
        import code.src.pipeline
        import code.src.download_data
        import code.src.data.download_hcp
        import code.src.data.qc
        import code.src.analysis.entropy
        import code.src.compute_entropy
    except ImportError as e:
        pytest.fail(f"Module import failed: {e}")

def test_toolkit_import():
    """Verify llmxive_toolkit is available."""
    try:
        from llmxive_toolkit import paths, get_logger
    except ImportError as e:
        pytest.fail(f"llmxive_toolkit import failed: {e}")

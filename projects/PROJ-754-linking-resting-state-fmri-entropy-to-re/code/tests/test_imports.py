import pytest
import logging

# Configure logging to avoid noise during import tests
logging.basicConfig(level=logging.ERROR)

def test_core_imports():
    """Verify that all primary project modules are importable without syntax or dependency errors."""
    try:
        import code.src.pipeline
        import code.src.run_pipeline
        import code.src.download_data
        import code.src.data.download_hcp
        import code.src.data.qc
        import code.src.analysis.entropy
        import code.src.compute_entropy
        # Check sub-packages
        import code.src.stats
        import code.src.reporting
        import code.src.utils
    except ImportError as e:
        pytest.fail(f"Module import failed: {e}")

def test_toolkit_imports():
    """Verify that the llmxive_toolkit is available."""
    try:
        from llmxive_toolkit import paths, get_logger
    except ImportError as e:
        pytest.fail(f"llmxive_toolkit import failed: {e}")

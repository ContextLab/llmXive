"""
Test that all major modules in the project can be imported without errors.
This catches package structure issues and dependency conflicts.
"""
import pytest

def test_import_pipeline():
    import code.src.pipeline
    import code.src.run_pipeline
    import code.src.download_data
    import code.src.data.download_hcp
    import code.src.data.qc
    import code.src.compute_entropy
    import code.src.analysis.entropy

def test_import_config():
    import code.config.env_manager
    import code.config.logging_config
    import code.config.lint_format

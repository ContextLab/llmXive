"""
Tests to verify that API documentation generation is valid.
This test ensures that the Sphinx configuration can successfully parse
the target modules without import errors.
"""
import subprocess
import os
import sys
import pytest
from pathlib import Path

@pytest.mark.skipif(
    os.environ.get('CI') == 'true' and sys.platform == 'win32',
    reason="Skip docs test on Windows CI"
)
def test_sphinx_config_imports_modules():
    """
    Verify that the Sphinx configuration can import the target modules
    without raising ImportError.
    """
    # Add code directory to path
    code_dir = Path(__file__).parent.parent.parent / 'code'
    sys.path.insert(0, str(code_dir))

    # Try importing the target modules
    try:
        from code import __init__ as code_init  # noqa: F401
    except ImportError:
        pass  # code package might not be a package

    # Import 01_data_acquisition
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "01_data_acquisition",
            code_dir / "01_data_acquisition.py"
        )
        if spec and spec.loader:
            module_01 = importlib.util.module_from_spec(spec)
            sys.modules['01_data_acquisition'] = module_01
            spec.loader.exec_module(module_01)
    except Exception as e:
        pytest.fail(f"Failed to import 01_data_acquisition: {e}")

    # Import 02_pattern_mapping
    try:
        spec = importlib.util.spec_from_file_location(
            "02_pattern_mapping",
            code_dir / "02_pattern_mapping.py"
        )
        if spec and spec.loader:
            module_02 = importlib.util.module_from_spec(spec)
            sys.modules['02_pattern_mapping'] = module_02
            spec.loader.exec_module(module_02)
    except Exception as e:
        pytest.fail(f"Failed to import 02_pattern_mapping: {e}")

    # Import 05_statistical_analysis
    try:
        spec = importlib.util.spec_from_file_location(
            "05_statistical_analysis",
            code_dir / "05_statistical_analysis.py"
        )
        if spec and spec.loader:
            module_05 = importlib.util.module_from_spec(spec)
            sys.modules['05_statistical_analysis'] = module_05
            spec.loader.exec_module(module_05)
    except Exception as e:
        pytest.fail(f"Failed to import 05_statistical_analysis: {e}")

def test_docs_directory_structure_exists():
    """Verify that the docs directory and required files exist."""
    docs_dir = Path(__file__).parent.parent.parent / 'docs'
    assert docs_dir.exists(), "docs/ directory must exist"
    
    required_files = [
        'conf.py',
        'index.rst',
        'modules.rst',
        'Makefile'
    ]
    
    for filename in required_files:
        filepath = docs_dir / filename
        assert filepath.exists(), f"Required docs file missing: {filename}"
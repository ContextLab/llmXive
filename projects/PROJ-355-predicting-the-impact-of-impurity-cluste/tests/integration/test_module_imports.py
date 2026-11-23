"""
Integration test to verify all modules can be imported correctly.
"""
import pytest
import sys
from pathlib import Path

# Add code directory to path
project_root = Path(__file__).parent.parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

def test_all_modules_importable():
    """Verify that all expected modules can be imported without errors."""
    modules_to_test = [
        "config",
        "validators",
        "data.download",
        "data.gb_builder",
        "data.descriptors",
        "data.simulate_energy",
        "data.descriptor_filter",
        "data.preprocessing",
        "modeling.train",
        "modeling.evaluate_per_system",
        "modeling.confidence_intervals",
        "main",
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {str(e)}")

def test_main_module_exports():
    """Verify that main.py exports the expected functions."""
    from main import run_pipeline
    
    assert callable(run_pipeline)
    assert run_pipeline.__name__ == "run_pipeline"

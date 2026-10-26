"""
tests/unit/test_main_execution.py

Simple integration test to verify that the ``src.main`` entry point
executes without raising an exception and produces the expected
``data_availability.json`` report.
"""

import pytest
from llmxive_toolkit import paths

def test_main_runs_successfully():
    # Import and run the main function.
    from src.main import main
    # The function should complete without raising.
    main()
    # Verify that the expected output file exists.
    out_path = paths.results("data_availability.json")
    assert out_path.is_file(), "data_availability.json was not created by src.main"
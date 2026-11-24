"""
Unit test for the create_code_dirs script (task T001b).
Verifies that the script creates the expected directories.
"""

import importlib
import os
from pathlib import Path

# Import the script to be tested
from code import create_code_dirs

def test_create_code_directories():
    """
    Run the create_code_dirs script and assert that the three directories exist.
    """
    # Execute the main function which should create the directories
    create_code_dirs.main()

    # Use the llmxive_toolkit path helpers to locate the directories
    from llmxive_toolkit import paths

    assert paths.code().exists(), "code/ directory should exist"
    assert paths.code('models').exists(), "code/models/ directory should exist"
    assert paths.code('utils').exists(), "code/utils/ directory should exist"
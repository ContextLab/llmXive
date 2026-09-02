import os
import shutil
import tempfile
from pathlib import Path

import pytest

# We need to mock the project root for testing without affecting the real project
# Since setup_directories imports from config, we will test the logic by
# ensuring the function can be imported and the paths are constructed correctly.
# However, to avoid side effects on the real project, we will verify the
# directory creation logic by inspecting the paths it attempts to create.

from setup_directories import create_directories
from config import get_project_root


def test_create_directories_structure_exists(tmp_path):
    """
    Test that create_directories creates the expected directory structure.

    We temporarily override the project root to use a temporary directory
    to avoid modifying the actual project structure during tests.
    """
    # This is a structural test. Since we cannot easily mock get_project_root
    # without patching the module in setup_directories, we will verify
    # that the function runs without error and creates the directories
    # in the actual project if run in the correct context, or we verify
    # the logic by checking the expected paths.

    # For this specific test, we will assert that the expected directories
    # are defined in the function.
    expected_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/derivatives",
        "data/processed",
        "state",
    ]

    # Verify the function exists and is callable
    assert callable(create_directories)

    # Since we are in a test environment, we can't easily run the script
    # against a fake root without patching. Instead, we verify the
    # configuration of the function by checking the source or by
    # running it in a controlled environment if possible.
    # Given the constraints, we will assume the implementation is correct
    # if it runs without error in the actual project root.
    # However, to be rigorous, we will check if the directories exist
    # in the current project root after running the function.
    # But since this test might run before the directories exist, we will
    # create them in a temp dir and verify.

    # We will patch the get_project_root function temporarily
    import setup_directories as sd_module
    import config as config_module

    original_get_project_root = config_module.get_project_root

    def mock_get_project_root():
        return tmp_path

    config_module.get_project_root = mock_get_project_root
    sd_module.get_project_root = mock_get_project_root

    try:
        create_directories()

        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"
    finally:
        # Restore original function
        config_module.get_project_root = original_get_project_root
        sd_module.get_project_root = original_get_project_root
"""
Unit test for the `create_data_dirs` script.

The test imports the script, runs its `main()` function, and then checks that
the expected directories exist using the project's `paths` helper.
"""
from llmxive_toolkit import paths
import importlib

# Import the script as a module
create_data_dirs = importlib.import_module("code.create_data_dirs")

def test_data_directories_created():
    # Run the script's main function to create the directories
    create_data_dirs.main()

    # Verify each required directory exists
    assert paths.data("raw").is_dir(), "data/raw/ directory was not created"
    assert paths.data("processed").is_dir(), "data/processed/ directory was not created"
    assert paths.data("interior").is_dir(), "data/interior/ directory was not created"
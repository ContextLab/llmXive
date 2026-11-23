"""
Unit test for the data directory creation script (T001c).

The test simply verifies that the required directories exist after the
setup script has been executed. The `setup_data_dirs.py` script is executed
as part of the task, so the directories should be present in the filesystem.
"""

from llmxive_toolkit import paths

def test_raw_and_processed_directories_exist():
    """
    Ensure that `data/raw/` and `data/processed/` directories exist.
    """
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")

    assert raw_dir.is_dir(), f"Raw data directory missing: {raw_dir}"
    assert processed_dir.is_dir(), f"Processed data directory missing: {processed_dir}"
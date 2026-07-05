import os
import sys
import pytest
import tempfile
import shutil

# Add the project root to the path to allow importing from src.utils
# Assuming the project structure places tests at root and code in 'code' (based on constraints)
# But the API surface shows files like code/setup_data_dirs.py.
# The task requires testing src/utils/config.py.
# We need to ensure src is importable.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
code_dir = os.path.join(project_root, "code")
src_dir = os.path.join(project_root, "src")

if code_dir not in sys.path:
    sys.path.insert(0, code_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from utils.config import get_project_root, SEED, RANDOM_SEED, CONFIG_PATH
except ImportError as e:
    # Fallback if structure is slightly different or we are running in a specific context
    # Try relative to where the test file is
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    from utils.config import get_project_root, SEED, RANDOM_SEED, CONFIG_PATH

class TestConfigUtils:
    def test_seed_is_integer(self):
        """Verify SEED is an integer."""
        assert isinstance(SEED, int), "SEED must be an integer"

    def test_random_seed_is_integer(self):
        """Verify RANDOM_SEED is an integer."""
        assert isinstance(RANDOM_SEED, int), "RANDOM_SEED must be an integer"

    def test_config_path_exists_or_is_string(self):
        """Verify CONFIG_PATH is a string."""
        assert isinstance(CONFIG_PATH, str), "CONFIG_PATH must be a string"

    def test_get_project_root_returns_string(self):
        """Verify get_project_root returns a string path."""
        root = get_project_root()
        assert isinstance(root, str), "get_project_root must return a string"
        assert len(root) > 0, "get_project_root must return a non-empty string"

    def test_get_project_root_is_absolute(self):
        """Verify get_project_root returns an absolute path."""
        root = get_project_root()
        assert os.path.isabs(root), "get_project_root must return an absolute path"

    def test_get_project_root_matches_current_dir(self):
        """Verify get_project_root matches the directory of the config file."""
        # We infer the project root by going up from the config module location
        # Assuming utils.config is at src/utils/config.py
        config_file_dir = os.path.dirname(__file__) # This is tests/unit
        # Navigate up to project root (tests -> src -> project_root? No, usually tests is at root)
        # Based on constraints: "All artifact paths are relative to the project root and MUST live under code/, data/, tests/, or specs/"
        # So tests/ is at root.
        # get_project_root() should return the directory containing 'tests', 'code', 'data', 'src'.
        root = get_project_root()
        # Check if 'tests' directory exists in root
        assert os.path.isdir(os.path.join(root, "tests")), "Project root should contain 'tests' directory"
        assert os.path.isdir(os.path.join(root, "code")), "Project root should contain 'code' directory"

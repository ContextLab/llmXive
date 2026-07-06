import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We need to import the function. Since the task is about creating a directory,
# we will mock the environment to test the creation logic without affecting the real repo.
# However, the task requires a real directory creation artifact.
# The test verifies that the setup script correctly targets the path.

def test_metadata_directory_path_construction():
    """Verify the setup script targets the correct relative path."""
    from code.setup_data_metadata import main
    # We cannot easily run main() in a test without side effects on the real FS
    # unless we change CWD. Instead, we verify the logic by inspecting the module
    # or running it in a temp directory.
    # Here we run the actual logic in a temp directory to ensure it works.
    
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Re-import to ensure it picks up the new CWD if the module cached paths
            # (It doesn't cache, but good practice in tests)
            import importlib
            import code.setup_data_metadata
            importlib.reload(code.setup_data_metadata)
            
            code.setup_data_metadata.main()
            
            metadata_path = Path(tmpdir) / "data" / "metadata"
            assert metadata_path.exists(), "The data/metadata directory was not created."
            assert metadata_path.is_dir(), "The created path is not a directory."
        finally:
            os.chdir(original_cwd)

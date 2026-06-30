import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_project_structure


def test_full_project_structure_creation():
    """
    Integration test: Verify the full project structure is created correctly
    when running the setup script from a fresh directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Execute the setup
            created, skipped = create_project_structure()
            
            # Assert success
            assert skipped == 0, "Some directories failed to create"
            assert created > 0, "No directories were created"
            
            # Verify the hierarchy exists (e.g., code/data exists and is a directory)
            code_data_dir = Path(tmpdir) / "code" / "data"
            assert code_data_dir.exists() and code_data_dir.is_dir()
            
            # Verify tests hierarchy
            tests_unit_dir = Path(tmpdir) / "tests" / "unit"
            assert tests_unit_dir.exists() and tests_unit_dir.is_dir()
            
            # Verify data hierarchy
            data_stimuli_dir = Path(tmpdir) / "data" / "stimuli"
            assert data_stimuli_dir.exists() and data_stimuli_dir.is_dir()
            
        finally:
            os.chdir(original_dir)
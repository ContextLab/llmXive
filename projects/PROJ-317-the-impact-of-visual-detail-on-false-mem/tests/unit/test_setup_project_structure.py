import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_project_structure


def test_create_project_structure():
    """Test that create_project_structure creates the required directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run the function
            created_count, skipped_count = create_project_structure()
            
            # Verify no errors occurred
            assert skipped_count == 0, f"Failed to create some directories: {skipped_count}"
            
            # Verify specific directories exist
            required_dirs = [
                "data/stimuli",
                "data/stimuli_metadata",
                "data/responses",
                "data/processed",
                "data/ethics",
                "code/data",
                "code/stimuli",
                "code/participants",
                "code/analysis",
                "tests/unit",
                "tests/integration",
                "tests/contract",
                "docs/ethics",
            ]
            
            for rel_path in required_dirs:
                target_path = Path(tmpdir) / rel_path
                assert target_path.exists(), f"Directory not created: {rel_path}"
                assert target_path.is_dir(), f"Path is not a directory: {rel_path}"
            
            assert created_count == len(required_dirs), f"Expected {len(required_dirs)} directories, created {created_count}"
            
        finally:
            os.chdir(original_dir)

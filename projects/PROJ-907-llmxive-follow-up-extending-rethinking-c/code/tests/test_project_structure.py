import os
import pytest
from pathlib import Path
import sys

# Ensure we can import the setup script
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestProjectStructure:
    """
    Test suite to verify T001: Project structure creation.
    """
    
    def test_directories_exist(self):
        """Verify that all required directories from T001 exist."""
        base_path = Path(__file__).parent.parent
        project_root = base_path / "PROJ-907-llmxive-follow-up-extending-rethinking-c"
        code_dir = project_root / "code"

        required_dirs = [
            "src",
            "tests",
            "data/imagenet_trace",
            "data/imagenet_benchmark",
            "data/routing_cache",
            "data/results",
            "docs"
        ]

        missing_dirs = []
        for rel_dir in required_dirs:
            full_path = code_dir / rel_dir
            if not full_path.exists():
                missing_dirs.append(rel_dir)
            elif not full_path.is_dir():
                missing_dirs.append(f"{rel_dir} (not a directory)")

        assert not missing_dirs, f"Missing directories: {missing_dirs}"

    def test_code_root_exists(self):
        """Verify the code root directory exists."""
        base_path = Path(__file__).parent.parent
        code_dir = base_path / "PROJ-907-llmxive-follow-up-extending-rethinking-c" / "code"
        assert code_dir.exists(), "Code root directory does not exist"
        assert code_dir.is_dir(), "Code root is not a directory"
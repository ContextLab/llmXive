import os
import sys
from pathlib import Path

import pytest

# Ensure we can import project modules if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestDirectoryStructure:
    """Tests to verify the existence of required project directories."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.required_dirs = [
            "data/raw",
            "data/interim",
            "data/processed",
            "code",
            "tests",
            "tests/unit",
            "tests/integration",
            "reports",
        ]

    def test_required_directories_exist(self):
        """Verify that all required project directories exist."""
        missing_dirs = []
        for dir_path in self.required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
            elif not full_path.is_dir():
                missing_dirs.append(dir_path)

        if missing_dirs:
            pytest.fail(f"Missing or invalid directories: {', '.join(missing_dirs)}")

    def tests_unit_integration_exist(self):
        """Specific check for tests/unit and tests/integration as per T001d."""
        unit_path = self.project_root / "tests" / "unit"
        integration_path = self.project_root / "tests" / "integration"

        assert unit_path.exists(), "tests/unit directory does not exist"
        assert unit_path.is_dir(), "tests/unit is not a directory"

        assert integration_path.exists(), "tests/integration directory does not exist"
        assert integration_path.is_dir(), "tests/integration is not a directory"

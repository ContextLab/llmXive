import os
import pytest
from pathlib import Path
from typing import List, Dict, Any

class TestDirectoryStructureContract:
    """
    Contract test to verify the project directory structure exists as defined in T001a.
    """

    @pytest.fixture
    def root_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent

    def test_src_directory_exists(self, root_dir: Path):
        """Verify 'src' directory exists per T001a."""
        src_dir = root_dir / "src"
        assert src_dir.exists(), f"Directory 'src' does not exist at {src_dir}"
        assert src_dir.is_dir(), f"'src' at {src_dir} is not a directory"

    def tests_directory_exists(self, root_dir: Path):
        """Verify 'tests' directory exists per T001a."""
        tests_dir = root_dir / "tests"
        assert tests_dir.exists(), f"Directory 'tests' does not exist at {tests_dir}"
        assert tests_dir.is_dir(), f"'tests' at {tests_dir} is not a directory"

    def test_config_directory_exists(self, root_dir: Path):
        """Verify 'config' directory exists per T001a."""
        config_dir = root_dir / "config"
        assert config_dir.exists(), f"Directory 'config' does not exist at {config_dir}"
        assert config_dir.is_dir(), f"'config' at {config_dir} is not a directory"

    def test_data_directory_exists(self, root_dir: Path):
        """Verify 'data' directory exists per T001a."""
        data_dir = root_dir / "data"
        assert data_dir.exists(), f"Directory 'data' does not exist at {data_dir}"
        assert data_dir.is_dir(), f"'data' at {data_dir} is not a directory"

    def test_results_directory_exists(self, root_dir: Path):
        """Verify 'results' directory exists per T001a."""
        results_dir = root_dir / "results"
        assert results_dir.exists(), f"Directory 'results' does not exist at {results_dir}"
        assert results_dir.is_dir(), f"'results' at {results_dir} is not a directory"

    def test_docs_directory_exists(self, root_dir: Path):
        """Verify 'docs' directory exists per T001a."""
        docs_dir = root_dir / "docs"
        assert docs_dir.exists(), f"Directory 'docs' does not exist at {docs_dir}"
        assert docs_dir.is_dir(), f"'docs' at {docs_dir} is not a directory"

    def test_test_subdirectories_exist(self, root_dir: Path):
        """Verify test subdirectories (unit, integration, contract) exist per T001c."""
        tests_dir = root_dir / "tests"
        subdirs = ["unit", "integration", "contract"]
        for subdir in subdirs:
            sub_path = tests_dir / subdir
            assert sub_path.exists(), f"Directory 'tests/{subdir}' does not exist at {sub_path}"
            assert sub_path.is_dir(), f"'tests/{subdir}' at {sub_path} is not a directory"

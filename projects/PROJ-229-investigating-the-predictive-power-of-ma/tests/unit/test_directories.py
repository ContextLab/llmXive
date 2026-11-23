import os
import pytest
from pathlib import Path

class TestDirectoryStructure:
    """Tests to verify the project directory structure exists."""

    @pytest.fixture
    def project_root(self):
        # Assuming tests are in tests/unit, root is two levels up
        return Path(__file__).parent.parent.parent

    def test_data_raw_exists(self, project_root):
        assert (project_root / "data" / "raw").exists()

    def test_data_processed_exists(self, project_root):
        assert (project_root / "data" / "processed").exists()

    def test_data_results_exists(self, project_root):
        assert (project_root / "data" / "results").exists()

    def test_data_external_exists(self, project_root):
        assert (project_root / "data" / "external").exists()

    def test_code_data_exists(self, project_root):
        assert (project_root / "code" / "data").exists()

    def test_code_models_exists(self, project_root):
        assert (project_root / "code" / "models").exists()

    def test_code_utils_exists(self, project_root):
        assert (project_root / "code" / "utils").exists()

    def test_code_validate_exists(self, project_root):
        assert (project_root / "code" / "validate").exists()

    def test_tests_unit_exists(self, project_root):
        assert (project_root / "tests" / "unit").exists()

    def test_tests_integration_exists(self, project_root):
        assert (project_root / "tests" / "integration").exists()

    def test_tests_contract_exists(self, project_root):
        assert (project_root / "tests" / "contract").exists()

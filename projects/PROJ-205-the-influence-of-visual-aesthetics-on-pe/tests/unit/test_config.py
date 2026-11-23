import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We need to ensure the path is set up correctly for imports
sys_path_backup = list(__import__('sys').path)
try:
    # Add the project root to path so we can import utils
    # Assuming this test runs from the project root or we adjust accordingly
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in __import__('sys').path:
        __import__('sys').path.insert(0, str(project_root))
    
    from utils.config import (
        get_project_root,
        get_consent_file_path,
        load_consent_text,
        get_irb_protocol_id,
        ENV_VAR_NAME,
        DEFAULT_CONSENT_PATH
    )
finally:
    __import__('sys').path[:] = sys_path_backup


class TestConfig:
    """Tests for the configuration module."""

    def test_get_project_root_structure(self):
        """Test that get_project_root returns a path with 'code' and 'data' directories."""
        root = get_project_root()
        assert (root / "code").exists() or (root / "data").exists(), \
            "Project root should contain 'code' or 'data' directories"

    def test_get_consent_file_path_default(self, tmp_path):
        """Test default consent file path resolution."""
        # Create a mock project structure in tmp_path
        mock_code = tmp_path / "code"
        mock_data = tmp_path / "data"
        mock_consent_dir = mock_data / "consent"
        mock_consent_dir.mkdir(parents=True)
        
        # Create the default consent file
        mock_consent_file = mock_consent_dir / "irb_approved.txt"
        mock_consent_file.write_text("Mock Consent Text")

        with patch('utils.config.get_project_root', return_value=tmp_path):
            path = get_consent_file_path()
            assert path == mock_consent_file
            assert path.exists()

    def test_get_consent_file_path_env_var(self, tmp_path):
        """Test consent file path resolution via environment variable."""
        mock_code = tmp_path / "code"
        mock_data = tmp_path / "data"
        mock_consent_dir = mock_data / "consent"
        mock_consent_dir.mkdir(parents=True)
        
        # Create a custom consent file
        custom_consent_file = mock_consent_dir / "custom_consent.txt"
        custom_consent_file.write_text("Custom Consent Text")

        with patch('utils.config.get_project_root', return_value=tmp_path):
            with patch.dict(os.environ, {ENV_VAR_NAME: "data/consent/custom_consent.txt"}):
                path = get_consent_file_path()
                assert path == custom_consent_file
                assert path.exists()

    def test_get_consent_file_path_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised when consent file is missing."""
        mock_code = tmp_path / "code"
        mock_data = tmp_path / "data"
        mock_consent_dir = mock_data / "consent"
        mock_consent_dir.mkdir(parents=True)
        
        # Do NOT create the file

        with patch('utils.config.get_project_root', return_value=tmp_path):
            with pytest.raises(FileNotFoundError):
                get_consent_file_path()

    def test_load_consent_text(self, tmp_path):
        """Test loading consent text from file."""
        mock_code = tmp_path / "code"
        mock_data = tmp_path / "data"
        mock_consent_dir = mock_data / "consent"
        mock_consent_dir.mkdir(parents=True)
        
        expected_text = "This is the IRB approved consent text."
        mock_consent_file = mock_consent_dir / "irb_approved.txt"
        mock_consent_file.write_text(expected_text)

        with patch('utils.config.get_project_root', return_value=tmp_path):
            text = load_consent_text()
            assert text == expected_text

    def test_get_irb_protocol_id(self, tmp_path):
        """Test extracting IRB Protocol ID from consent text."""
        mock_code = tmp_path / "code"
        mock_data = tmp_path / "data"
        mock_consent_dir = mock_data / "consent"
        mock_consent_dir.mkdir(parents=True)
        
        consent_text = """
        INFORMED CONSENT FORM
        IRB Protocol ID: IRB-TEST-123
        """
        mock_consent_file = mock_consent_dir / "irb_approved.txt"
        mock_consent_file.write_text(consent_text)

        with patch('utils.config.get_project_root', return_value=tmp_path):
            protocol_id = get_irb_protocol_id()
            assert protocol_id == "IRB-TEST-123"

    def test_get_irb_protocol_id_not_found(self, tmp_path):
        """Test ValueError when IRB Protocol ID is missing."""
        mock_code = tmp_path / "code"
        mock_data = tmp_path / "data"
        mock_consent_dir = mock_data / "consent"
        mock_consent_dir.mkdir(parents=True)
        
        consent_text = """
        INFORMED CONSENT FORM
        No protocol ID here.
        """
        mock_consent_file = mock_consent_dir / "irb_approved.txt"
        mock_consent_file.write_text(consent_text)

        with patch('utils.config.get_project_root', return_value=tmp_path):
            with pytest.raises(ValueError):
                get_irb_protocol_id()

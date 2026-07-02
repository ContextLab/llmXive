import os
import tempfile
from pathlib import Path
import pytest

# Mock the config module to allow testing without full project setup
import sys
from unittest.mock import patch, MagicMock

from stimuli.check_irb_env import verify_irb_content

@pytest.fixture
def mock_env_var():
    with patch.dict(os.environ, {"IRB_PROTOCOL_ID": "PROTOCOL-12345-TEST"}):
        yield "PROTOCOL-12345-TEST"

@pytest.fixture
def temp_consent_file_with_id():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("This is the IRB approved consent text.\n")
        f.write("Protocol ID: PROTOCOL-12345-TEST\n")
        f.write("Participant signature required below.\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_consent_file_without_id():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("This is the IRB approved consent text.\n")
        f.write("Protocol ID: WRONG-PROTOCOL-ID\n")
        f.write("Participant signature required below.\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_empty_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def mock_get_consent_file_path(temp_consent_file_with_id):
    with patch('stimuli.check_irb_env.get_consent_file_path') as mock_func:
        mock_func.return_value = Path(temp_consent_file_with_id)
        yield mock_func

def test_irb_verification_success(mock_env_var, temp_consent_file_with_id, mock_get_consent_file_path):
    """Test that verification passes when ID is present."""
    is_valid, message = verify_irb_content()
    assert is_valid is True
    assert "successful" in message.lower()

def test_irb_verification_missing_env_var():
    """Test that verification fails when env var is missing."""
    # Remove the env var if it exists in the test environment
    original = os.environ.get('IRB_PROTOCOL_ID')
    if 'IRB_PROTOCOL_ID' in os.environ:
        del os.environ['IRB_PROTOCOL_ID']
    
    try:
        is_valid, message = verify_irb_content()
        assert is_valid is False
        assert "not set" in message
    finally:
        # Restore original if it existed
        if original:
            os.environ['IRB_PROTOCOL_ID'] = original

def test_irb_verification_file_not_found(mock_env_var):
    """Test that verification fails when file does not exist."""
    with patch('stimuli.check_irb_env.get_consent_file_path') as mock_func:
        mock_func.return_value = Path("/nonexistent/path/file.txt")
        is_valid, message = verify_irb_content()
        assert is_valid is False
        assert "not found" in message.lower()

def test_irb_verification_id_not_in_content(mock_env_var, temp_consent_file_without_id):
    """Test that verification fails when ID is not in content."""
    with patch('stimuli.check_irb_env.get_consent_file_path') as mock_func:
        mock_func.return_value = Path(temp_consent_file_without_id)
        is_valid, message = verify_irb_content()
        assert is_valid is False
        assert "not found in the consent file content" in message

def test_irb_verification_empty_file(mock_env_var, temp_empty_file):
    """Test that verification fails for empty file."""
    with patch('stimuli.check_irb_env.get_consent_file_path') as mock_func:
        mock_func.return_value = Path(temp_empty_file)
        is_valid, message = verify_irb_content()
        assert is_valid is False
        assert "empty" in message.lower()
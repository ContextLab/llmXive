"""
Unit tests for the consent modal implementation (T012).
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import get_irb_protocol_id, load_consent_text, get_consent_file_path

def test_irb_protocol_id_retrieval():
    """Test that IRB Protocol ID is correctly retrieved from environment."""
    with patch.dict(os.environ, {"IRB_PROTOCOL_ID": "TEST-123"}):
        assert get_irb_protocol_id() == "TEST-123"

def test_irb_protocol_id_missing_fails_loudly():
    """Test that missing IRB ID raises ValueError."""
    with patch.dict(os.environ, {}, clear=True):
        try:
            get_irb_protocol_id()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "IRB_PROTOCOL_ID" in str(e)

def test_consent_text_loading():
    """Test that consent text is loaded correctly."""
    # Create a temporary file with mock consent text
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Mock Consent Text")
        temp_path = f.name

    try:
        with patch('utils.config.get_consent_file_path', return_value=Path(temp_path)):
            text = load_consent_text()
            assert text == "Mock Consent Text"
    finally:
        os.unlink(temp_path)

def test_consent_file_missing_fails_loudly():
    """Test that missing consent file raises FileNotFoundError."""
    with patch('utils.config.get_consent_file_path', return_value=Path("/nonexistent/path.txt")):
        try:
            load_consent_text()
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError as e:
            assert "IRB consent file not found" in str(e)

def test_consent_modal_header_includes_protocol_id():
    """
    Verify that the consent modal (in app.py) includes the IRB Protocol ID.
    This is a static analysis check on the code structure.
    """
    app_path = Path(__file__).parent.parent.parent / "code" / "survey" / "app.py"
    assert app_path.exists(), "app.py not found"
    
    content = app_path.read_text()
    
    # Check that get_irb_protocol_id is imported or used
    assert "get_irb_protocol_id" in content, "get_irb_protocol_id not found in app.py"
    
    # Check that the ID is displayed in the UI (markdown or header)
    # Look for a pattern like st.markdown(f"**IRB Protocol ID:**")
    assert "IRB Protocol ID" in content, "IRB Protocol ID not displayed in UI"
    
    # Verify the flow: load ID -> display in header
    lines = content.split('\n')
    found_id_load = False
    found_display = False
    
    for line in lines:
        if "irb_protocol_id = get_irb_protocol_id()" in line:
            found_id_load = True
        if "IRB Protocol ID" in line and found_id_load:
            found_display = True
            break
    
    assert found_id_load, "IRB Protocol ID not loaded in show_consent_form"
    assert found_display, "IRB Protocol ID not displayed after loading"
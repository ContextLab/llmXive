"""
Unit tests for code/validators.py validation functions.
"""
import pytest
from pathlib import Path
import sys
import tempfile
import yaml

# Ensure code is importable
project_root = Path(__file__).parent.parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from validators import validate_citations, validate_schema

def test_validate_citations_with_whitelisted_url():
    """Test validation with a whitelisted URL that exists."""
    # Create a temporary metadata file with a whitelisted URL
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            "sources": [
                {"url": "https://materialsproject.org", "name": "Test Source"}
            ]
        }, f)
        temp_path = f.name

    try:
        # This should return True for a whitelisted URL
        result = validate_citations("https://materialsproject.org", temp_path)
        assert result is True
    finally:
        Path(temp_path).unlink()

def test_validate_citations_with_non_whitelisted_url():
    """Test validation with a non-whitelisted URL raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            "sources": [
                {"url": "https://unknown-site.com", "name": "Unknown"}
            ]
        }, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            validate_citations("https://unknown-site.com", temp_path)
        assert "DATA_UNAVAILABLE" in str(exc_info.value)
    finally:
        Path(temp_path).unlink()

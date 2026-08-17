"""
Unit tests for the verify_constitution script.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.verify_constitution import verify_constitution, REQUIRED_KEYWORDS, CONSTITUTION_PATH

def test_verify_constitution_file_not_found():
    """Test that verification fails when constitution.md is missing."""
    with patch('utils.verify_constitution.CONSTITUTION_PATH') as mock_path:
        mock_path.exists.return_value = False
        result = verify_constitution()
        assert result is False

def test_verify_constitution_missing_principle_vi():
    """Test that verification fails if Principle VI is missing."""
    content = """
    # Constitution
    ## Principle I
    Some text...
    """
    with patch('utils.verify_constitution.CONSTITUTION_PATH') as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = content
        result = verify_constitution()
        assert result is False

def test_verify_constitution_missing_keywords():
    """Test that verification fails if required keywords are missing."""
    content = """
    # Constitution
    ## Principle VI
    FFT-based methods are okay.
    """
    with patch('utils.verify_constitution.CONSTITUTION_PATH') as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = content
        result = verify_constitution()
        assert result is False

def test_verify_constitution_success():
    """Test that verification passes with a correctly amended constitution."""
    content = """
    # Constitution
    ## Principle VI
    This project explicitly permits the use of **FFT-based numerical homogenization** 
    as the primary ground-truth method.
    """
    with patch('utils.verify_constitution.CONSTITUTION_PATH') as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = content
        result = verify_constitution()
        assert result is True

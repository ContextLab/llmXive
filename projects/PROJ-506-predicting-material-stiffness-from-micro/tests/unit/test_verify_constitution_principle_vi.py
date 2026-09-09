"""
Unit tests for Constitution Principle VI verification.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.verify_constitution_principle_vi import verify_constitution_principle_vi


class TestVerifyConstitutionPrincipleVI:
    """Test cases for verify_constitution_principle_vi function."""

    def test_principle_vi_passes_with_fft(self):
        """Test that verification passes when 'FFT' is present."""
        mock_content = """
        # Constitution
        
        ## Principle VI: Numerical Methods
        
        FFT-based numerical homogenization is permitted for computing effective properties.
        """
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('pathlib.Path.exists', return_value=True):
                result = verify_constitution_principle_vi()
                assert result is True

    def test_principle_vi_passes_with_numerical(self):
        """Test that verification passes when 'numerical' is present (case insensitive)."""
        mock_content = """
        # Constitution
        
        ## Principle VI: Numerical Methods
        
        Numerical homogenization methods are permitted for computing effective properties.
        """
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('pathlib.Path.exists', return_value=True):
                result = verify_constitution_principle_vi()
                assert result is True

    def test_principle_vi_fails_without_permission(self):
        """Test that verification fails when neither FFT nor numerical is mentioned."""
        mock_content = """
        # Constitution
        
        ## Principle VI: Analytical Methods
        
        Only analytical methods are permitted.
        """
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('pathlib.Path.exists', return_value=True):
                with pytest.raises(AssertionError) as exc_info:
                    verify_constitution_principle_vi()
                
                assert "Principle VI missing permission" in str(exc_info.value)

    def test_constitution_file_not_found(self):
        """Test that FileNotFoundError is raised when constitution is missing."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                verify_constitution_principle_vi()

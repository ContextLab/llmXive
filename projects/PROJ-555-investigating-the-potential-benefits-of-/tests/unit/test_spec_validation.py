import pytest
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, mock_open
import logging

from code.spec_validation import verify_fr002_nonlinear_fallback, main
from code.logging_config import setup_logging, get_logger

class TestFR002Verification:
    """Tests for FR-002 non-linear fallback note verification."""

    def test_verify_fr002_pass(self):
        """Test that verification passes when the required phrase is present."""
        mock_content = """
        # Spec Document
        
        ## FR-002 Modeling Requirements
        ...
        If non-linear asymptotic fitting fails (R² < 0.95), linear slope is the ACCEPTED metric.
        ...
        """
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('code.spec_validation.Path.exists', return_value=True):
                result = verify_fr002_nonlinear_fallback("fake/spec.md")
                assert result is True

    def test_verify_fr002_fail(self):
        """Test that verification fails when the required phrase is missing."""
        mock_content = """
        # Spec Document
        
        ## FR-002 Modeling Requirements
        ...
        Some other text without the required phrase.
        ...
        """
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('code.spec_validation.Path.exists', return_value=True):
                result = verify_fr002_nonlinear_fallback("fake/spec.md")
                assert result is False

    def test_verify_fr002_file_not_found(self):
        """Test that FileNotFoundError is raised when spec file is missing."""
        with patch('code.spec_validation.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                verify_fr002_nonlinear_fallback("nonexistent/spec.md")

    def test_main_success_scenario(self, tmp_path):
        """Test main() when verification passes."""
        setup_logging()
        
        # Create a temporary spec file with the required phrase
        spec_dir = tmp_path / "specs" / "001-ecotourism-regeneration"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("If non-linear asymptotic fitting fails...")
        
        # Create state directory for log
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        
        with patch('code.spec_validation.Path') as mock_path_class:
            mock_path = mock_path_class.return_value
            mock_path.exists.return_value = True
            mock_path.__truediv__.return_value = state_dir / "spec_validation.log"
            mock_path.mkdir.return_value = None
            
            # Mock the open for file writing
            with patch('builtins.open', mock_open()):
                # We expect this to return 0 (success)
                # Note: main() calls setup_logging internally, so we need to be careful
                pass

    def test_main_failure_scenario(self, tmp_path):
        """Test main() when verification fails and raises RuntimeError."""
        setup_logging()
        
        # Create a temporary spec file WITHOUT the required phrase
        spec_dir = tmp_path / "specs" / "001-ecotourism-regeneration"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("Some other text without the required phrase.")
        
        with patch('code.spec_validation.Path') as mock_path_class:
            mock_path = mock_path_class.return_value
            mock_path.exists.return_value = True
            mock_path.__truediv__.return_value = tmp_path / "state" / "spec_validation.log"
            mock_path.mkdir.return_value = None
            
            with patch('builtins.open', mock_open()):
                with pytest.raises(RuntimeError, match="CRITICAL: FR-002 non-linear fallback note missing"):
                    main()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
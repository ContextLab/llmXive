"""
Unit tests for the Static Analysis Check logic.

Verifies that the check correctly identifies restricted imports
and allows valid ones.
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import the check function from the analysis script
# We need to adjust the import path for testing
import sys
from code.pipeline.static_analysis_check import check_file_integrity

class TestStaticAnalysis:
    
    def test_allows_valid_imports(self, tmp_path):
        """Test that a file with valid imports passes."""
        valid_code = """
        import os
        import numpy as np
        import pandas as pd
        from utils.config import get_env_config
        from utils.io import log_operation
        from models.dreamx_base import create_dreamx_base_model
        
        def my_func():
            pass
        """
        file_path = tmp_path / "valid.py"
        file_path.write_text(valid_code)
        
        assert check_file_integrity(str(file_path)) is True
        
    def test_blocks_dit_attention_import(self, tmp_path):
        """Test that importing dit_attention fails."""
        invalid_code = """
        from models.dreamx_base import dit_attention
        
        def my_func():
            pass
        """
        file_path = tmp_path / "invalid1.py"
        file_path.write_text(invalid_code)
        
        assert check_file_integrity(str(file_path)) is False
        
    def test_blocks_latent_space_import(self, tmp_path):
        """Test that importing latent_space fails."""
        invalid_code = """
        from models.dreamx_lite import latent_space
        
        def my_func():
            pass
        """
        file_path = tmp_path / "invalid2.py"
        file_path.write_text(invalid_code)
        
        assert check_file_integrity(str(file_path)) is False
        
    def test_blocks_direct_module_import(self, tmp_path):
        """Test that importing a restricted module name fails."""
        invalid_code = """
        import dit_attention
        
        def my_func():
            pass
        """
        file_path = tmp_path / "invalid3.py"
        file_path.write_text(invalid_code)
        
        assert check_file_integrity(str(file_path)) is False
        
    def test_blocks_backbone_import(self, tmp_path):
        """Test that importing backbone fails."""
        invalid_code = """
        from models import backbone
        
        def my_func():
            pass
        """
        file_path = tmp_path / "invalid4.py"
        file_path.write_text(invalid_code)
        
        assert check_file_integrity(str(file_path)) is False
        
    def test_syntax_error_handling(self, tmp_path):
        """Test that syntax errors are handled gracefully."""
        invalid_syntax = """
        def broken(
            pass
        """
        file_path = tmp_path / "syntax_error.py"
        file_path.write_text(invalid_syntax)
        
        assert check_file_integrity(str(file_path)) is False
        
    def test_nonexistent_file(self, tmp_path):
        """Test that missing files are handled."""
        assert check_file_integrity(str(tmp_path / "nonexistent.py")) is False
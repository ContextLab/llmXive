"""
Unit tests for the quickstart.md validation logic.
"""
import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add code/scripts to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "scripts"))

from validate_quickstart import validate_quickstart

class TestQuickstartValidation:
    def test_missing_file_fails(self, tmp_path):
        """Test that validation fails if quickstart.md is missing."""
        # Create a temp docs dir without quickstart.md
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        
        # Temporarily change working directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = validate_quickstart()
            assert result is False, "Validation should fail if file is missing"
        finally:
            os.chdir(original_cwd)

    def test_forbidden_pattern_static_only(self, tmp_path):
        """Test that validation fails if 'static-only shortcut' is present."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        quickstart = docs_dir / "quickstart.md"
        
        content = """
        # Quickstart
        This is a static-only shortcut guide.
        Skip the heavy execution.
        """
        quickstart.write_text(content)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = validate_quickstart()
            assert result is False, "Validation should fail on forbidden pattern"
        finally:
            os.chdir(original_cwd)

    def test_forbidden_pattern_skip_dynamic(self, tmp_path):
        """Test that validation fails if 'skip dynamic execution' is present."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        quickstart = docs_dir / "quickstart.md"
        
        content = """
        # Quickstart
        You can skip dynamic execution for faster results.
        """
        quickstart.write_text(content)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = validate_quickstart()
            assert result is False, "Validation should fail on skip dynamic pattern"
        finally:
            os.chdir(original_cwd)

    def test_compliant_file_passes(self, tmp_path):
        """Test that a compliant file passes validation."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        quickstart = docs_dir / "quickstart.md"
        
        content = """
        # Quickstart Guide
        
        ## Environment Setup
        This guide enforces the full-environment re-execution baseline.
        Do not use static-only modes.
        
        ## Data Download
        1. Download the dataset from HuggingFace.
        
        ## Setup
        1. Install dependencies.
        2. Configure environment variables.
        
        ## Execution
        1. Run the baseline tests.
        2. Execute dynamic analysis.
        3. Train the model.
        """
        quickstart.write_text(content)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = validate_quickstart()
            assert result is True, "Validation should pass for compliant file"
        finally:
            os.chdir(original_cwd)

    def test_missing_required_step_fails(self, tmp_path):
        """Test that missing required steps causes failure."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        quickstart = docs_dir / "quickstart.md"
        
        # Has re-execution but no download or execution steps
        content = """
        # Quickstart
        This guide mentions full-environment re-execution.
        But it lacks download or run steps.
        """
        quickstart.write_text(content)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = validate_quickstart()
            assert result is False, "Validation should fail if steps are missing"
        finally:
            os.chdir(original_cwd)
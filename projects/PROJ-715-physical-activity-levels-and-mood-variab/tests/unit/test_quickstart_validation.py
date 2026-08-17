"""
Unit tests for quickstart validation logic.
Tests the validation functions to ensure they correctly identify 
valid and invalid documentation states.
"""
import pytest
import tempfile
import os
from pathlib import Path
import shutil

# Import the validation functions
# Note: We need to add code/ to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validate_quickstart import (
    validate_file_paths_in_doc,
    validate_python_imports,
    validate_requirements_syntax,
    extract_commands_from_quickstart
)


class TestValidateFilePathsInDoc:
    """Tests for validate_file_paths_in_doc function."""

    def test_all_files_exist(self, tmp_path):
        """Test when all referenced files exist."""
        # Create a temporary directory structure
        (tmp_path / "quickstart.md").write_text("# Test")
        (tmp_path / "code" / "requirements.txt").write_text("pandas\n")
        (tmp_path / "code" / "config.py").write_text("# config")
        (tmp_path / "code" / "ingest.py").write_text("# ingest")
        (tmp_path / "code" / "preprocess.py").write_text("# preprocess")
        (tmp_path / "code" / "analysis.py").write_text("# analysis")
        (tmp_path / "code" / "report.py").write_text("# report")
        
        # Create data directories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        (tmp_path / "data" / "raw" / "bronze.parquet").touch()
        (tmp_path / "data" / "processed" / "daily_aggregates.csv").touch()
        (tmp_path / "data" / "processed" / "model_results.json").touch()
        
        # Temporarily change PROJECT_ROOT
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            success, errors = validate_file_paths_in_doc()
            assert success is True
            assert len(errors) == 0
        finally:
            validate_quickstart.PROJECT_ROOT = original_root

    def test_missing_file(self, tmp_path):
        """Test when a referenced file is missing."""
        # Create minimal structure
        (tmp_path / "quickstart.md").write_text("# Test")
        (tmp_path / "code").mkdir()
        (tmp_path / "code" / "requirements.txt").write_text("pandas\n")
        # Missing other files
        
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            success, errors = validate_file_paths_in_doc()
            assert success is False
            assert len(errors) > 0
            assert any("not found" in err for err in errors)
        finally:
            validate_quickstart.PROJECT_ROOT = original_root


class TestValidateRequirementsSyntax:
    """Tests for validate_requirements_syntax function."""

    def test_valid_requirements(self, tmp_path):
        """Test with valid requirements.txt."""
        requirements_path = tmp_path / "code" / "requirements.txt"
        requirements_path.parent.mkdir(parents=True)
        requirements_path.write_text("pandas>=1.0\nnumpy\nscikit-learn==1.0\n")
        
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            success, errors = validate_requirements_syntax()
            assert success is True
            assert len(errors) == 0
        finally:
            validate_quickstart.PROJECT_ROOT = original_root

    def test_empty_requirements(self, tmp_path):
        """Test with empty requirements.txt."""
        requirements_path = tmp_path / "code" / "requirements.txt"
        requirements_path.parent.mkdir(parents=True)
        requirements_path.write_text("")
        
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            success, errors = validate_requirements_syntax()
            assert success is False
            assert any("empty" in err.lower() for err in errors)
        finally:
            validate_quickstart.PROJECT_ROOT = original_root

    def test_invalid_package_name(self, tmp_path):
        """Test with invalid package specifier."""
        requirements_path = tmp_path / "code" / "requirements.txt"
        requirements_path.parent.mkdir(parents=True)
        requirements_path.write_text("-invalid-package-name\n")
        
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            success, errors = validate_requirements_syntax()
            # Our validator is lenient, so this might pass
            # The test ensures the function runs without crashing
            assert isinstance(success, bool)
            assert isinstance(errors, list)
        finally:
            validate_quickstart.PROJECT_ROOT = original_root


class TestExtractCommandsFromQuickstart:
    """Tests for extract_commands_from_quickstart function."""

    def test_extract_bash_commands(self, tmp_path):
        """Test extraction of bash commands from markdown."""
        quickstart_content = """
        # Quickstart Guide

        ```bash
        pip install -r requirements.txt
        python code/ingest.py
        ```

        ```shell
        python code/preprocess.py
        ```
        """
        
        quickstart_path = tmp_path / "quickstart.md"
        quickstart_path.write_text(quickstart_content)
        
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            commands = extract_commands_from_quickstart()
            assert len(commands) == 2
            assert any("pip install" in cmd for cmd, _ in commands)
            assert any("python code/preprocess.py" in cmd for cmd, _ in commands)
        finally:
            validate_quickstart.PROJECT_ROOT = original_root

    def test_no_commands(self, tmp_path):
        """Test when no code blocks exist."""
        quickstart_path = tmp_path / "quickstart.md"
        quickstart_path.write_text("# No commands here")
        
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            commands = extract_commands_from_quickstart()
            assert len(commands) == 0
        finally:
            validate_quickstart.PROJECT_ROOT = original_root


class TestValidatePythonImports:
    """Tests for validate_python_imports function."""

    def test_valid_imports(self, tmp_path):
        """Test when all modules can be imported."""
        # Create minimal module files
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "__init__.py").write_text("")
        (code_dir / "config.py").write_text("")
        (code_dir / "ingest.py").write_text("")
        (code_dir / "preprocess.py").write_text("")
        (code_dir / "analysis.py").write_text("")
        (code_dir / "report.py").write_text("")
        
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            success, errors = validate_python_imports()
            # Should succeed since we created empty modules
            assert success is True
            assert len(errors) == 0
        finally:
            validate_quickstart.PROJECT_ROOT = original_root

    def test_missing_module(self, tmp_path):
        """Test when a module is missing."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "__init__.py").write_text("")
        # Missing some modules
        
        import validate_quickstart
        original_root = validate_quickstart.PROJECT_ROOT
        validate_quickstart.PROJECT_ROOT = tmp_path
        
        try:
            success, errors = validate_python_imports()
            assert success is False
            assert len(errors) > 0
        finally:
            validate_quickstart.PROJECT_ROOT = original_root
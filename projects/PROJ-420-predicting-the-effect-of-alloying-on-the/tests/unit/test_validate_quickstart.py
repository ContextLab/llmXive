"""
Unit tests for the QuickstartValidator.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

# Mock the config and logging for testing
import sys
from unittest.mock import MagicMock, patch

# Create a mock config
class MockConfig:
    def __init__(self, root_path):
        self.root = Path(root_path)
        self.data_dir = self.root / "data"
        self.code_dir = self.root / "code"
        self.docs_dir = self.root / "docs"

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create expected directory structure
    (project_root / "code").mkdir()
    (project_root / "data").mkdir()
    (project_root / "docs").mkdir()
    (project_root / "models").mkdir()
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def validator_with_config(temp_project_dir):
    """Create a validator with a mock config."""
    from validate_quickstart import QuickstartValidator
    
    config = MockConfig(temp_project_dir)
    validator = QuickstartValidator(config=config)
    return validator

def test_read_quickstart_missing_file(validator_with_config):
    """Test reading a missing quickstart.md file."""
    result = validator_with_config.read_quickstart()
    assert result == ""
    assert len(validator_with_config.errors) == 1
    assert "not found" in validator_with_config.errors[0]

def test_read_quickstart_existing_file(validator_with_config, temp_project_dir):
    """Test reading an existing quickstart.md file."""
    quickstart_path = temp_project_dir / "docs" / "quickstart.md"
    quickstart_path.write_text("# Quickstart\n\nSome content")
    
    result = validator_with_config.read_quickstart()
    assert result == "# Quickstart\n\nSome content"
    assert len(validator_with_config.errors) == 0

def test_extract_code_blocks(validator_with_config):
    """Test extracting code blocks from markdown."""
    content = """
    # Example

    ```bash
    python code/main.py
    ```

    ```python
    import pandas as pd
    ```
    """
    
    blocks = validator_with_config.extract_code_blocks(content)
    assert len(blocks) == 2
    assert "python code/main.py" in blocks[0]
    assert "import pandas as pd" in blocks[1]

def test_extract_file_references(validator_with_config):
    """Test extracting file references from content."""
    content = """
    Run `python code/main.py` to start.
    Data is saved to `data/processed/filtered_alloys.csv`.
    See `docs/quickstart.md` for details.
    """
    
    refs = validator_with_config.extract_file_references(content)
    assert "code/main.py" in refs
    assert "data/processed/filtered_alloys.csv" in refs
    assert "docs/quickstart.md" in refs

def test_validate_script_existence_missing(validator_with_config, temp_project_dir):
    """Test validation when referenced script is missing."""
    file_refs = {"code/main.py"}
    validator_with_config.validate_script_existence(file_refs)
    
    assert len(validator_with_config.errors) == 1
    assert "not found" in validator_with_config.errors[0]

def test_validate_script_existence_exists(validator_with_config, temp_project_dir):
    """Test validation when referenced script exists."""
    script_path = temp_project_dir / "code" / "main.py"
    script_path.write_text("# Mock script")
    
    file_refs = {"code/main.py"}
    validator_with_config.validate_script_existence(file_refs)
    
    assert len(validator_with_config.errors) == 0

def test_validate_commands_invalid_python(validator_with_config):
    """Test validation of invalid Python commands."""
    content = """
    ```bash
    python
    ```
    """
    
    validator_with_config.validate_commands(content)
    assert len(validator_with_config.errors) >= 1

def test_validate_commands_valid_python(validator_with_config, temp_project_dir):
    """Test validation of valid Python commands."""
    script_path = temp_project_dir / "code" / "main.py"
    script_path.write_text("# Mock script")
    
    content = """
    ```bash
    python code/main.py
    ```
    """
    
    validator_with_config.validate_commands(content)
    # Should not have errors for valid command
    script_errors = [e for e in validator_with_config.errors if "Python script not found" in e]
    assert len(script_errors) == 0

def test_extract_requirements(validator_with_config):
    """Test extracting package requirements."""
    content = """
    Run `pip install pandas numpy scikit-learn`.
    Also need `pandas>=1.0`.
    """
    
    packages = validator_with_config.extract_requirements(content)
    assert "pandas" in packages
    assert "numpy" in packages
    assert "scikit-learn" in packages

def test_run_validation_success(validator_with_config, temp_project_dir):
    """Test a successful validation run."""
    # Create all necessary files
    (temp_project_dir / "docs" / "quickstart.md").write_text("""
    # Quickstart

    ## Installation
    pip install pandas numpy

    ## Data Extraction
    python code/data_extraction.py

    ## Results
    See data/processed/filtered_alloys.csv
    """)
    
    (temp_project_dir / "code" / "data_extraction.py").write_text("# Mock")
    
    # Create requirements.txt
    (temp_project_dir / "code" / "requirements.txt").write_text("pandas\nnumpy\n")
    
    is_valid = validator_with_config.run_validation()
    
    # Should pass if all files exist and references are correct
    assert is_valid or len(validator_with_config.errors) == 0

def test_run_validation_failure(validator_with_config, temp_project_dir):
    """Test a failed validation run."""
    # Create quickstart with missing script reference
    (temp_project_dir / "docs" / "quickstart.md").write_text("""
    # Quickstart

    Run `python code/nonexistent.py`
    """)
    
    is_valid = validator_with_config.run_validation()
    
    assert not is_valid
    assert len(validator_with_config.errors) > 0

def test_generate_report(validator_with_config, temp_project_dir):
    """Test report generation."""
    (temp_project_dir / "docs" / "quickstart.md").write_text("""
    # Quickstart

    Run `python code/missing.py`
    """)
    
    validator_with_config.run_validation()
    report = validator_with_config.generate_report()
    
    assert "quickstart_path" in report
    assert "valid" in report
    assert "error_count" in report
    assert "errors" in report
    assert report["error_count"] > 0
    assert report["valid"] is False
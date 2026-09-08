"""
Unit tests for T039: verify_research.py
"""
import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from verify_research import validate_research_md, FORBIDDEN_PATTERNS

class TestResearchValidation:
    def setup_method(self):
        """Setup temporary directory and file for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = Path(self.temp_dir.name) / "research.md"

    def teardown_method(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def write_test_file(self, content: str):
        """Helper to write content to test file."""
        self.test_file_path.write_text(content)
        # Temporarily patch the global variable in the module
        import verify_research
        original_path = verify_research.RESEARCH_FILE
        verify_research.RESEARCH_FILE = self.test_file_path
        return original_path

    def restore_path(self, original_path):
        """Restore original path."""
        import verify_research
        verify_research.RESEARCH_FILE = original_path

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised if research.md is missing."""
        import verify_research
        original_path = verify_research.RESEARCH_FILE
        verify_research.RESEARCH_FILE = Path("/nonexistent/path/research.md")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            validate_research_md()
        
        assert "not found" in str(exc_info.value)
        
        verify_research.RESEARCH_FILE = original_path

    def test_dynamic_search_logic_detected(self):
        """Test that dynamic search patterns trigger ValueError."""
        content = """
        # Research
        We will search for datasets on OpenML.
        """
        original_path = self.write_test_file(content)
        
        with pytest.raises(ValueError) as exc_info:
            validate_research_md()
        
        assert "dynamic search logic" in str(exc_info.value).lower()
        
        self.restore_path(original_path)

    def test_placeholder_detected(self):
        """Test that placeholders trigger ValueError."""
        content = """
        # Research
        URL: TODO_insert_url_here
        """
        original_path = self.write_test_file(content)
        
        with pytest.raises(ValueError) as exc_info:
            validate_research_md()
        
        assert "placeholder" in str(exc_info.value).lower()
        
        self.restore_path(original_path)

    def test_valid_static_urls(self):
        """Test that valid static URLs pass validation."""
        content = """
        # Research Data Sources
        1. OpenML Dataset: https://openml.org/s/dataset/12345
        2. HuggingFace: https://huggingface.co/datasets/lst-wear-data
        3. GitHub: https://github.com/research/lst-wear/tree/main/data
        """
        original_path = self.write_test_file(content)
        
        # Should not raise
        result = validate_research_md()
        assert result is True
        
        self.restore_path(original_path)

    def test_valid_static_ids(self):
        """Test that valid static IDs pass validation."""
        content = """
        # Research Data Sources
        - openml_id: 45678
        - hf_dataset: research/lst-wear
        """
        original_path = self.write_test_file(content)
        
        result = validate_research_md()
        assert result is True
        
        self.restore_path(original_path)

    def test_no_sources_detected(self):
        """Test that file with no sources triggers ValueError."""
        content = """
        # Research Plan
        We need to find data.
        """
        original_path = self.write_test_file(content)
        
        with pytest.raises(ValueError) as exc_info:
            validate_research_md()
        
        assert "no static URLs or dataset IDs" in str(exc_info.value).lower()
        
        self.restore_path(original_path)

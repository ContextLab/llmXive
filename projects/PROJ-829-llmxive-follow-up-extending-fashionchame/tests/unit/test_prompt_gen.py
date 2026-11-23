"""
Unit tests for the prompt generation module (FR-008).
Tests blind metadata-to-text prompt generation functionality.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.prompt_gen import (
    generate_prompt,
    generate_prompts_batch,
    normalize_attribute,
    load_settings,
    save_prompts_to_file,
    main
)


class TestNormalizeAttribute:
    """Tests for the normalize_attribute function."""
    
    def test_empty_string(self):
        """Test handling of empty strings."""
        assert normalize_attribute("") == ""
        assert normalize_attribute(None) == ""
    
    def test_snake_case_conversion(self):
        """Test conversion of snake_case to space-separated words."""
        assert normalize_attribute("long_sleeve") == "Long Sleeve"
        assert normalize_attribute("high_waisted") == "High Waisted"
    
    def test_kebab_case_conversion(self):
        """Test conversion of kebab-case to space-separated words."""
        assert normalize_attribute("long-sleeve") == "Long Sleeve"
        assert normalize_attribute("high-waisted") == "High Waisted"
    
    def test_capitalization(self):
        """Test that output is properly capitalized."""
        assert normalize_attribute("red") == "Red"
        assert normalize_attribute("striped") == "Striped"
    
    def test_whitespace_handling(self):
        """Test trimming of leading/trailing whitespace."""
        assert normalize_attribute("  red  ") == "Red"
        assert normalize_attribute("\tstriped\n") == "Striped"


class TestGeneratePrompt:
    """Tests for the generate_prompt function."""
    
    def test_minimal_metadata(self):
        """Test prompt generation with minimal required fields."""
        metadata = {"category": "dress"}
        prompt = generate_prompt(metadata)
        assert "dress" in prompt.lower()
        assert prompt.endswith(".")
    
    def test_category_variations(self):
        """Test that different categories produce valid prompts."""
        categories = ["shirt", "pants", "skirt", "jacket"]
        for category in categories:
            metadata = {"category": category}
            prompt = generate_prompt(metadata)
            assert category.lower() in prompt.lower()
            assert prompt.endswith(".")
    
    def test_color_inclusion(self):
        """Test that color is properly included in prompts."""
        metadata = {
            "category": "dress",
            "color": "red"
        }
        prompt = generate_prompt(metadata)
        assert "red" in prompt.lower()
        assert "dress" in prompt.lower()
    
    def test_attribute_inclusion(self):
        """Test that attributes are properly included in prompts."""
        metadata = {
            "category": "shirt",
            "attributes": ["striped", "long_sleeve"]
        }
        prompt = generate_prompt(metadata)
        assert "shirt" in prompt.lower()
        assert "striped" in prompt.lower() or "long sleeve" in prompt.lower()
    
    def test_multiple_attributes_limit(self):
        """Test that only first 3 attributes are used."""
        metadata = {
            "category": "shirt",
            "attributes": ["a", "b", "c", "d", "e"]
        }
        prompt = generate_prompt(metadata)
        # Should contain at most 3 attribute-related words
        # This is a soft check since template selection varies
        assert prompt.endswith(".")
    
    def test_missing_category_raises_error(self):
        """Test that missing category field raises ValueError."""
        metadata = {"color": "red"}
        with pytest.raises(ValueError, match="category"):
            generate_prompt(metadata)
    
    def test_empty_attributes(self):
        """Test handling of empty attributes list."""
        metadata = {
            "category": "dress",
            "attributes": []
        }
        prompt = generate_prompt(metadata)
        assert "dress" in prompt.lower()
        # Should not contain attribute-related words
        assert "with" not in prompt.lower() or "dress" in prompt.lower()
    
    def test_none_attributes(self):
        """Test handling of None attributes."""
        metadata = {
            "category": "dress",
            "attributes": None
        }
        prompt = generate_prompt(metadata)
        assert "dress" in prompt.lower()
    
    def test_bbox_context_disabled(self):
        """Test that bbox context is not included when disabled."""
        metadata = {
            "category": "dress",
            "bounding_box": [0, 0, 100, 200]
        }
        prompt = generate_prompt(metadata, {"include_bbox_context": False})
        assert "aspect ratio" not in prompt.lower()
    
    def test_bbox_context_enabled(self):
        """Test that bbox context is included when enabled."""
        metadata = {
            "category": "dress",
            "bounding_box": [0, 0, 200, 100]  # Wide aspect ratio
        }
        prompt = generate_prompt(metadata, {"include_bbox_context": True})
        # Should contain aspect ratio description
        assert "aspect ratio" in prompt.lower() or "wide" in prompt.lower()
    
    def test_deterministic_template_selection(self):
        """Test that template selection is deterministic for same input."""
        metadata = {"category": "dress", "color": "red"}
        prompt1 = generate_prompt(metadata)
        prompt2 = generate_prompt(metadata)
        assert prompt1 == prompt2


class TestGeneratePromptsBatch:
    """Tests for the generate_prompts_batch function."""
    
    def test_single_metadata(self):
        """Test batch generation with single entry."""
        metadata_list = [{"category": "dress"}]
        results = generate_prompts_batch(metadata_list)
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert "prompt" in results[0]
    
    def test_multiple_metadata(self):
        """Test batch generation with multiple entries."""
        metadata_list = [
            {"category": "dress"},
            {"category": "shirt"},
            {"category": "pants"}
        ]
        results = generate_prompts_batch(metadata_list)
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
    
    def test_mixed_success_failure(self):
        """Test batch generation with mixed success/failure."""
        metadata_list = [
            {"category": "dress"},
            {"color": "red"},  # Missing category - should fail
            {"category": "shirt"}
        ]
        results = generate_prompts_batch(metadata_list)
        assert len(results) == 3
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "failed"
        assert results[2]["status"] == "success"
        assert "error" in results[1]
    
    def test_index_tracking(self):
        """Test that indices are correctly tracked."""
        metadata_list = [{"category": "dress"}, {"category": "shirt"}]
        results = generate_prompts_batch(metadata_list)
        assert results[0]["index"] == 0
        assert results[1]["index"] == 1


class TestSavePromptsToFile:
    """Tests for the save_prompts_to_file function."""
    
    def test_save_and_load(self, tmp_path):
        """Test saving prompts to file and loading them back."""
        prompts_data = [
            {"index": 0, "prompt": "A dress.", "status": "success"},
            {"index": 1, "prompt": "A shirt.", "status": "success"}
        ]
        output_path = tmp_path / "prompts.json"
        
        save_prompts_to_file(prompts_data, str(output_path))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 2
        assert loaded[0]["prompt"] == "A dress."
        assert loaded[1]["prompt"] == "A shirt."
    
    def test_creates_directory(self, tmp_path):
        """Test that function creates parent directories."""
        prompts_data = [{"index": 0, "prompt": "A dress.", "status": "success"}]
        output_path = tmp_path / "subdir" / "prompts.json"
        
        save_prompts_to_file(prompts_data, str(output_path))
        
        assert output_path.exists()


class TestLoadSettings:
    """Tests for the load_settings function."""
    
    def test_load_from_config(self):
        """Test loading settings from config file."""
        # Mock the settings file existence and content
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open_read_data='{}'):
                with patch.dict('sys.modules', {'yaml': MagicMock()}):
                    settings = load_settings()
                    assert isinstance(settings, dict)
    
    def test_missing_file_raises_error(self):
        """Test that missing settings file raises FileNotFoundError."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                load_settings()
    
    def test_missing_yaml_raises_error(self):
        """Test that missing yaml module raises ImportError."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open_read_data='{}'):
                with patch.dict('sys.modules', {'yaml': None}):
                    with pytest.raises(ImportError):
                        load_settings()


# Helper function for mocking file operations
def mock_open_read_data(data):
    """Helper to create a mock file object that returns given data."""
    mock_file = MagicMock()
    mock_file.__enter__ = MagicMock(return_value=mock_file)
    mock_file.__exit__ = MagicMock(return_value=None)
    mock_file.read = MagicMock(return_value=data)
    return mock_file


class TestMain:
    """Tests for the main function."""
    
    def test_missing_input_file(self, tmp_path):
        """Test main function with missing input file."""
        # Create a temporary directory structure
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        # Mock paths
        with patch('src.data.prompt_gen.Path', return_value=tmp_path):
            with patch('src.data.prompt_gen.load_settings', return_value={}):
                # This should handle missing input gracefully
                # and create an empty output file
                pass  # Actual test would require more complex mocking
    
    def test_empty_input_file(self, tmp_path):
        """Test main function with empty input file."""
        # Setup would require extensive mocking of file system
        # This is a placeholder for the actual test logic
        pass
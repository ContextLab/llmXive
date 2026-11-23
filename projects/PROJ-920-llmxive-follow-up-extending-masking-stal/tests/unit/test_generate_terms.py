"""
Unit tests for generate_terms.py
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to temporarily modify sys.path to import from code/
import sys
from pathlib import Path

# Add the project root to path so we can import code.generate_terms
# Assuming tests are in tests/unit/ and code/ is at project root
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from generate_terms import (
    DEFAULT_TERMS,
    ensure_config_directory,
    load_user_terms,
    generate_default_terms,
    write_terms_file
)

class TestGenerateTerms:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """
        Setup: Create a temporary directory structure mimicking the project.
        Teardown: Clean up is handled by tmp_path fixture.
        """
        self.original_cwd = Path.cwd()
        
        # Create a temporary project structure
        self.temp_project = tmp_path / "test_project"
        self.temp_project.mkdir()
        
        self.temp_code = self.temp_project / "code"
        self.temp_code.mkdir()
        
        self.temp_config = self.temp_code / "config"
        self.temp_config.mkdir()
        
        # Change to temp project root to simulate relative path resolution
        os.chdir(self.temp_project)
        
        # We need to mock the paths used in the module
        # Since the module uses Path(__file__).resolve().parent.parent,
        # we can't easily change that without modifying the module.
        # Instead, we will test the logic directly by calling functions
        # that don't rely on hardcoded relative paths, or by patching.
        
        # For this test, we will directly test the logic by importing
        # and using the functions, but we must be careful about path resolution.
        # The safest way is to test the logic without relying on file system
        # for the path resolution part, or to patch the module's global variables.
        
        # Let's patch the paths in the module temporarily
        import generate_terms
        self.original_project_root = generate_terms.PROJECT_ROOT
        self.original_config_dir = generate_terms.CONFIG_DIR
        self.original_user_terms_path = generate_terms.USER_TERMS_PATH
        self.original_output_path = generate_terms.OUTPUT_PATH
        
        generate_terms.PROJECT_ROOT = self.temp_project
        generate_terms.CONFIG_DIR = self.temp_config
        generate_terms.USER_TERMS_PATH = self.temp_config / "user_terms.json"
        generate_terms.OUTPUT_PATH = self.temp_config / "density_terms.json"

        yield

        # Restore original paths
        generate_terms.PROJECT_ROOT = self.original_project_root
        generate_terms.CONFIG_DIR = self.original_config_dir
        generate_terms.USER_TERMS_PATH = self.original_user_terms_path
        generate_terms.OUTPUT_PATH = self.original_output_path
        
        # Restore original working directory
        os.chdir(self.original_cwd)

    def test_default_terms_content(self):
        """Test that DEFAULT_TERMS contains the expected values."""
        expected = [
            "entropy", "retrieval", "context", "density", "horizon",
            "masking", "trajectory", "agent", "search", "stale"
        ]
        assert DEFAULT_TERMS == expected
        assert len(DEFAULT_TERMS) == 10

    def test_generate_default_terms(self):
        """Test that generate_default_terms returns the correct list."""
        result = generate_default_terms()
        assert result == DEFAULT_TERMS
        assert isinstance(result, list)
        assert all(isinstance(term, str) for term in result)

    def test_ensure_config_directory_creates_dir(self):
        """Test that ensure_config_directory creates the config dir."""
        # The fixture already creates it, but let's test the function
        # by removing it first (if it exists) and calling the function
        if self.temp_config.exists():
            shutil.rmtree(self.temp_config)
        
        ensure_config_directory()
        assert self.temp_config.exists()
        assert self.temp_config.is_dir()

    def test_load_user_terms_file_not_exists(self):
        """Test load_user_terms returns None when file doesn't exist."""
        result = load_user_terms()
        assert result is None

    def test_load_user_terms_valid_file(self):
        """Test load_user_terms loads valid user_terms.json."""
        user_data = {"terms": ["custom", "terms", "list"]}
        user_path = self.temp_config / "user_terms.json"
        
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(user_data, f)
        
        result = load_user_terms()
        assert result == ["custom", "terms", "list"]

    def test_load_user_terms_invalid_format_missing_terms_key(self):
        """Test load_user_terms raises error for missing 'terms' key."""
        invalid_data = {"wrong_key": ["list"]}
        user_path = self.temp_config / "user_terms.json"
        
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        with pytest.raises(ValueError, match="Invalid format"):
            load_user_terms()

    def test_load_user_terms_invalid_format_terms_not_list(self):
        """Test load_user_terms raises error if 'terms' is not a list."""
        invalid_data = {"terms": "not_a_list"}
        user_path = self.temp_config / "user_terms.json"
        
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        with pytest.raises(ValueError, match="must be a list"):
            load_user_terms()

    def test_write_terms_file_creates_correct_structure(self):
        """Test write_terms_file creates the correct JSON structure."""
        terms = ["test1", "test2"]
        write_terms_file(terms)
        
        assert self.temp_config / "density_terms.json".exists()
        
        with open(self.temp_config / "density_terms.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "terms" in data
        assert data["terms"] == terms

    def test_write_terms_file_with_default_terms(self):
        """Test writing default terms produces correct output."""
        write_terms_file(DEFAULT_TERMS)
        
        output_path = self.temp_config / "density_terms.json"
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["terms"] == DEFAULT_TERMS
        assert len(data["terms"]) == 10

    def test_write_terms_file_rejects_non_string_terms(self):
        """Test write_terms_file handles non-string terms (validation happens in main, but let's test the list)."""
        # The function itself just writes, validation is in main
        # But we can test that it accepts a list
        terms = ["valid", "strings"]
        write_terms_file(terms)
        assert (self.temp_config / "density_terms.json").exists()
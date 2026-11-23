"""
Unit tests for research file validation (T039a).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_research import (
    parse_research_md,
    check_static_urls,
    validate_research_file,
    DYNAMIC_SEARCH_PATTERNS,
    STATIC_URL_PATTERNS
)

class TestParseResearchMd:
    """Tests for parse_research_md function."""
    
    def test_parse_existing_file(self, tmp_path):
        """Test parsing a valid research.md file."""
        # Create test file
        test_content = """
        ### Data Sources
        OpenML: https://www.openml.org/d/123
        HuggingFace: dataset_id = 'face-shape-rule-set'
        
        ### Literature
        Paper 1: https://doi.org/10.1234/test
        """
        test_file = tmp_path / "research.md"
        test_file.write_text(test_content)
        
        # Parse and verify
        result = parse_research_md(test_file)
        
        assert result['file_path'] == str(test_file)
        assert result['file_size'] == len(test_content)
        assert 'Data Sources' in result['sections']
        assert 'Literature' in result['sections']
        assert 'raw_content' in result
    
    def test_parse_missing_file(self, tmp_path):
        """Test parsing a missing file raises error."""
        missing_file = tmp_path / "nonexistent.md"
        
        with pytest.raises(FileNotFoundError):
            parse_research_md(missing_file)

class TestCheckStaticUrls:
    """Tests for check_static_urls function."""
    
    def test_detect_static_urls(self):
        """Test detection of static URLs."""
        content = """
        OpenML: https://www.openml.org/d/123
        HuggingFace: dataset_id = 'face-shape-rule-set'
        Paper: https://doi.org/10.1234/test
        """
        
        is_valid, static_urls, dynamic_patterns = check_static_urls(content)
        
        assert is_valid is True
        assert len(static_urls) == 3
        assert len(dynamic_patterns) == 0
    
    def test_detect_dynamic_search(self):
        """Test detection of dynamic search logic."""
        content = """
        # Dynamic search
        results = api.search(query="laser texturing")
        data = engine.find(pattern="wear_*")
        """
        
        is_valid, static_urls, dynamic_patterns = check_static_urls(content)
        
        assert is_valid is False
        assert len(static_urls) == 0
        assert len(dynamic_patterns) > 0
    
    def test_mixed_content(self):
        """Test content with both static and dynamic elements."""
        content = """
        Static: https://www.openml.org/d/123
        Dynamic: results = api.search(query="test")
        Static: dataset_id = 'face-shape-rule-set'
        """
        
        is_valid, static_urls, dynamic_patterns = check_static_urls(content)
        
        assert is_valid is False  # Dynamic logic present
        assert len(static_urls) == 2
        assert len(dynamic_patterns) == 1

class TestValidateResearchFile:
    """Tests for validate_research_file function."""
    
    def test_validate_valid_file(self, tmp_path):
        """Test validation of a compliant research.md file."""
        # Create valid research.md
        valid_content = """
        # Research Data Sources
        
        ### OpenML
        Dataset ID: 12345
        URL: https://www.openml.org/d/12345
        
        ### HuggingFace
        dataset_id = 'face-shape-rule-set'
        URL: https://huggingface.co/datasets/face-shape-rule-set
        
        ### Literature
        Paper 1: https://doi.org/10.1234/test-paper
        """
        
        research_file = tmp_path / "research.md"
        research_file.write_text(valid_content)
        
        # Validate
        results = validate_research_file(research_file)
        
        assert results['validation_passed'] is True
        assert results['static_urls_count'] > 0
        assert results['dynamic_patterns_found'] == 0
        assert results['validation_details']['meets_constitution_ii'] is True
    
    def test_validate_invalid_file(self, tmp_path):
        """Test validation of a non-compliant research.md file."""
        # Create invalid research.md with dynamic search
        invalid_content = """
        # Research Data Sources
        
        ### Dynamic Search
        results = api.search(query="laser wear")
        data = browse_database("wear_data")
        """
        
        research_file = tmp_path / "research.md"
        research_file.write_text(invalid_content)
        
        # Validate
        results = validate_research_file(research_file)
        
        assert results['validation_passed'] is False
        assert results['dynamic_patterns_found'] > 0
        assert results['validation_details']['meets_constitution_ii'] is False

class TestIntegration:
    """Integration tests for the validation pipeline."""
    
    def test_full_validation_flow(self, tmp_path, tmp_path_factory):
        """Test the complete validation flow including output file generation."""
        # Create valid research.md
        valid_content = """
        # Research Data Sources
        
        ### OpenML
        Dataset ID: 12345
        URL: https://www.openml.org/d/12345
        
        ### HuggingFace
        dataset_id = 'face-shape-rule-set'
        """
        
        # Set up directories
        specs_dir = tmp_path / "specs" / "001-predict-lst-wear"
        specs_dir.mkdir(parents=True)
        research_file = specs_dir / "research.md"
        research_file.write_text(valid_content)
        
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        output_file = state_dir / "research_validation.json"
        
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run validation
            from verify_research import validate_research_file, save_validation_results
            
            results = validate_research_file(research_file)
            save_validation_results(results, output_file)
            
            # Verify output file exists and is valid JSON
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                saved_results = json.load(f)
            
            assert saved_results['validation_passed'] is True
            assert saved_results['static_urls_count'] > 0
            assert saved_results['dynamic_patterns_found'] == 0
            
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

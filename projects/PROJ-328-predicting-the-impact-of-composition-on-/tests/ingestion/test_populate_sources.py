"""
Tests for T009c: Populate sources.yaml functionality.
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.ingestion.populate_sources import parse_verified_sources, save_sources_yaml

class TestPopulateSources:
    """Test cases for populate_sources module."""

    def test_parse_verified_sources_empty_file(self, tmp_path):
        """Test parsing an empty verified sources file."""
        verified_file = tmp_path / "research_verified.md"
        verified_file.write_text("")
        
        result = parse_verified_sources(verified_file)
        assert result == []

    def test_parse_verified_sources_no_verified(self, tmp_path):
        """Test parsing a file with no verified sources."""
        verified_file = tmp_path / "research_verified.md"
        content = """# Verified Sources
        - [http://example.com] (pending) Citation: Example
        - [http://example2.com] (rejected) Citation: Example 2
        """
        verified_file.write_text(content)
        
        result = parse_verified_sources(verified_file)
        assert result == []

    def test_parse_verified_sources_single_verified(self, tmp_path):
        """Test parsing a file with one verified source."""
        verified_file = tmp_path / "research_verified.md"
        content = """# Verified Sources
        - [http://example.com] (verified) Citation: Example Source
        """
        verified_file.write_text(content)
        
        result = parse_verified_sources(verified_file)
        assert len(result) == 1
        assert result[0]['url'] == 'http://example.com'
        assert result[0]['status'] == 'verified'
        assert result[0]['citation'] == 'Example Source'

    def test_parse_verified_sources_multiple_verified(self, tmp_path):
        """Test parsing a file with multiple verified sources."""
        verified_file = tmp_path / "research_verified.md"
        content = """# Verified Sources
        - [http://example1.com] (verified) Citation: Source 1
        - [http://example2.com] (verified) Citation: Source 2
        - [http://example3.com] (pending) Citation: Source 3
        - [http://example4.com] (verified) Citation: Source 4
        """
        verified_file.write_text(content)
        
        result = parse_verified_sources(verified_file)
        assert len(result) == 3
        urls = [s['url'] for s in result]
        assert 'http://example1.com' in urls
        assert 'http://example2.com' in urls
        assert 'http://example4.com' in urls
        assert 'http://example3.com' not in urls

    def test_parse_verified_sources_alt_pattern(self, tmp_path):
        """Test parsing with alternative pattern (URL Citation: ...)."""
        verified_file = tmp_path / "research_verified.md"
        content = """# Verified Sources
        - https://example.com Citation: Alternative Format
        - https://example2.com Citation: Another Format
        """
        verified_file.write_text(content)
        
        result = parse_verified_sources(verified_file)
        assert len(result) == 2
        assert result[0]['url'] == 'https://example.com'
        assert result[0]['citation'] == 'Alternative Format'

    def test_save_sources_yaml_creates_file(self, tmp_path):
        """Test that save_sources_yaml creates the output file."""
        sources = [
            {'url': 'http://example.com', 'status': 'verified', 'citation': 'Test'}
        ]
        output_file = tmp_path / "sources.yaml"
        
        save_sources_yaml(sources, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['_verification_status'] == 'verified'
        assert data['_verified_count'] == 1

    def test_save_sources_yaml_categorizes_sources(self, tmp_path):
        """Test that sources are correctly categorized as API or PDF."""
        sources = [
            {'url': 'https://api.materialsproject.org', 'status': 'verified', 'citation': 'MP'},
            {'url': 'https://example.com/paper.pdf', 'status': 'verified', 'citation': 'PDF Paper'}
        ]
        output_file = tmp_path / "sources.yaml"
        
        save_sources_yaml(sources, output_file)
        
        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert 'api_sources' in data
        assert 'literature_pdfs' in data
        assert len(data['api_sources']) == 1
        assert len(data['literature_pdfs']) == 1

    def test_save_sources_yaml_preserves_existing(self, tmp_path):
        """Test that save_sources_yaml preserves existing data when updating."""
        # Create existing file
        output_file = tmp_path / "sources.yaml"
        existing_data = {
            '_existing_key': 'existing_value',
            'other_section': {'item': 'value'}
        }
        with open(output_file, 'w') as f:
            yaml.dump(existing_data, f)
        
        sources = [
            {'url': 'http://example.com', 'status': 'verified', 'citation': 'Test'}
        ]
        
        save_sources_yaml(sources, output_file)
        
        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['_existing_key'] == 'existing_value'
        assert data['other_section']['item'] == 'value'
        assert data['_verification_status'] == 'verified'
        
    def test_parse_url_only_pattern(self, tmp_path):
        """Test parsing lines with just a URL."""
        verified_file = tmp_path / "research_verified.md"
        content = """# Verified Sources
        - https://example.com
        - https://api.example.org
        """
        verified_file.write_text(content)
        
        result = parse_verified_sources(verified_file)
        assert len(result) == 2
        assert result[0]['url'] == 'https://example.com'
        assert result[0]['status'] == 'verified'
        assert result[1]['source_type'] == 'api'  # Should detect API from domain
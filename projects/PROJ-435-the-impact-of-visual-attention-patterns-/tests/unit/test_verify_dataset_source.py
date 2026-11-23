import os
import sys
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.verify_dataset_source import parse_research_md_for_verified_source, compare_sources

class TestParseResearchMd:
    def test_parse_research_md_for_verified_source(self, tmp_path):
        research_md = tmp_path / "research.md"
        content = """
        # Research
        ### VERIFIED REAL DATA SOURCE
        - Package: datasets
        - Id: dundee/eye_tracking
        - Recipe: load_dataset("dundee/eye_tracking")
        """
        research_md.write_text(content)
        
        result = parse_research_md_for_verified_source(str(research_md))
        
        assert result['package'] == 'datasets'
        assert result['id'] == 'dundee/eye_tracking'
        assert 'load_dataset("dundee/eye_tracking")' in result['recipe']

    def test_parse_research_md_no_source(self, tmp_path):
        research_md = tmp_path / "research.md"
        content = "# Research\nNo source here"
        research_md.write_text(content)
        
        result = parse_research_md_for_verified_source(str(research_md))
        
        assert result is None

class TestCompareSources:
    def test_compare_sources_match(self):
        source1 = {'id': 'dundee/eye_tracking', 'recipe': 'load_dataset("dundee/eye_tracking")'}
        source2 = {'id': 'dundee/eye_tracking', 'recipe': 'load_dataset("dundee/eye_tracking")'}
        
        assert compare_sources(source1, source2) is True

    def test_compare_sources_mismatch_id(self):
        source1 = {'id': 'dundee/eye_tracking', 'recipe': '...'}
        source2 = {'id': 'boston/eye_tracking', 'recipe': '...'}
        
        assert compare_sources(source1, source2) is False

    def test_compare_sources_mismatch_recipe(self):
        source1 = {'id': 'dundee/eye_tracking', 'recipe': 'load_dataset("dundee/eye_tracking")'}
        source2 = {'id': 'dundee/eye_tracking', 'recipe': 'load_dataset("other")'}
        
        assert compare_sources(source1, source2) is False
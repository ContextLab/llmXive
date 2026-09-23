"""
Tests for T009c: populate_sources.py
"""
import os
import sys
import json
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.populate_sources import parse_verified_sources, save_sources_yaml

class TestPopulateSources:
    """Test suite for populate_sources module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "data" / "config"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.test_specs_dir = Path(self.temp_dir) / "specs" / "001-predict-solder-hardness"
        self.test_specs_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_parse_json_candidate_sources(self):
        """Test parsing candidate_sources.txt in JSON format."""
        candidate_file = Path(self.temp_dir) / "candidate_sources.txt"
        test_data = [
            {
                "url": "https://api.materialsproject.org",
                "source_type": "api",
                "citation": "Materials Project API"
            },
            {
                "url": "https://archive.ics.uci.edu/ml/datasets.php",
                "source_type": "api",
                "citation": "NIST/UCI Repository"
            },
            {
                "url": "https://openalloy.org/api/v1",
                "source_type": "api",
                "citation": "OpenAlloy API"
            },
            {
                "url": "https://doi.org/10.1016/j.jallcom.2023.123456",
                "source_type": "pdf",
                "citation": "Solder Hardness Review 2023"
            }
        ]
        candidate_file.write_text(json.dumps(test_data), encoding='utf-8')

        sources = parse_verified_sources(candidate_file)

        assert sources['_verification_status'] == 'verified'
        assert sources['_verified_count'] == 4
        assert 'materials_project' in sources
        assert sources['materials_project']['verified'] is True
        assert 'nist_uci' in sources
        assert 'openalloy' in sources
        assert len(sources['literature_pdfs']) == 1
        assert sources['literature_pdfs'][0]['verified'] is True

    def test_parse_markdown_verified_sources(self):
        """Test parsing research_verified.md in Markdown format."""
        md_file = self.test_specs_dir / "research_verified.md"
        md_content = """
        # Verified Research Sources

        ## API Sources
        - Materials Project: https://api.materialsproject.org
        - NIST/UCI: https://archive.ics.uci.edu/ml/datasets.php
        - OpenAlloy: https://openalloy.org/api/v1

        ## PDF Sources
        - Solder Hardness Review 2023: https://doi.org/10.1016/j.jallcom.2023.123456
        """
        md_file.write_text(md_content, encoding='utf-8')

        sources = parse_verified_sources(md_file)

        assert sources['_verification_status'] == 'verified'
        assert sources['_verified_count'] >= 3
        assert 'materials_project' in sources
        assert 'nist_uci' in sources
        assert 'openalloy' in sources

    def test_save_sources_yaml(self):
        """Test saving sources to YAML file."""
        sources = {
            'materials_project': {'name': 'Materials Project', 'verified': True},
            'nist_uci': {'name': 'NIST/UCI', 'verified': True},
            'literature_pdfs': [],
            '_verification_status': 'verified',
            '_verified_count': 2
        }
        output_file = Path(self.temp_dir) / "sources.yaml"

        save_sources_yaml(sources, output_file)

        assert output_file.exists()
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_sources = yaml.safe_load(f)

        assert loaded_sources['materials_project']['name'] == 'Materials Project'
        assert loaded_sources['_verification_status'] == 'verified'

    def test_missing_source_file(self):
        """Test handling of missing source file."""
        missing_file = Path(self.temp_dir) / "nonexistent.txt"
        sources = parse_verified_sources(missing_file)

        assert sources['_verification_status'] == 'provisional'
        assert sources['_verified_count'] == 0

    def test_empty_json_list(self):
        """Test parsing empty JSON list."""
        candidate_file = Path(self.temp_dir) / "empty_candidates.txt"
        candidate_file.write_text("[]", encoding='utf-8')

        sources = parse_verified_sources(candidate_file)

        assert sources['_verification_status'] == 'provisional'
        assert sources['_verified_count'] == 0
        assert len(sources['literature_pdfs']) == 0

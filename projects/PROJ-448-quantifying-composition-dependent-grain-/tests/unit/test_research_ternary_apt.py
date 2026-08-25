import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.scripts.research_ternary_apt import search_zenodo, verify_zenodo_accession, write_data_sources_md

class TestSearchZenodo:
    def test_search_zenodo_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hits": {
                "hits": [
                    {
                        "id": 12345,
                        "doi": "10.5281/zenodo.12345",
                        "metadata": {
                            "title": "Atom Probe Tomography of Fe-Cr-Mo",
                            "description": "Ternary APT data",
                            "keywords": ["atom probe", "ternary"]
                        }
                    }
                ]
            }
        }
        
        with patch('code.scripts.research_ternary_apt.requests.get', return_value=mock_response):
            results = search_zenodo("Fe-Cr-Mo atom probe")
            assert len(results) == 1
            assert results[0]["id"] == 12345

    def test_search_zenodo_failure(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Network error")
        
        with patch('code.scripts.research_ternary_apt.requests.get', return_value=mock_response):
            results = search_zenodo("Fe-Cr-Mo atom probe")
            assert results == []

class TestVerifyZenodoAccession:
    def test_valid_apt_ternary(self):
        record = {
            "metadata": {
                "title": "Fe-Cr-Mo Atom Probe Study",
                "description": "Detailed analysis of ternary alloy",
                "keywords": ["apt", "ternary"]
            }
        }
        assert verify_zenodo_accession(record) is True

    def test_missing_apt_keyword(self):
        record = {
            "metadata": {
                "title": "Fe-Cr-Mo Diffusion Study",
                "description": "Diffusion in ternary alloy",
                "keywords": ["diffusion"]
            }
        }
        assert verify_zenodo_accession(record) is False

    def test_apt_only(self):
        record = {
            "metadata": {
                "title": "Atom Probe Tomography of Pure Iron",
                "description": "APT study",
                "keywords": ["apt"]
            }
        }
        # Should return True if APT is present, even if ternary is not explicit in keywords
        # The logic in verify_zenodo_accession returns True if has_apt is True
        assert verify_zenodo_accession(record) is True

class TestWriteDataSourcesMd:
    def test_write_empty_list(self, tmp_path):
        output_path = tmp_path / "data_sources.md"
        write_data_sources_md([], output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "[]" in content
        assert "Ternary APT Data Sources" in content

    def test_write_with_results(self, tmp_path):
        results = [
            {
                "id": 1,
                "doi": "10.5281/zenodo.1",
                "metadata": {
                    "title": "Test",
                    "description": "Test desc"
                }
            }
        ]
        output_path = tmp_path / "data_sources.md"
        write_data_sources_md(results, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "10.5281/zenodo.1" in content
        assert "Test" in content
        assert "```json" in content

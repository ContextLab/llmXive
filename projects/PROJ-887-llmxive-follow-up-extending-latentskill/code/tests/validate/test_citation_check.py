import pytest
import yaml
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.validate.citation_check import (
    load_data_sources,
    check_url_reachability,
    check_hf_dataset_files,
    verify_sources
)

class TestLoadDataSources:
    def test_load_valid_yaml(self, tmp_path):
        """Test loading a valid YAML configuration."""
        config_file = tmp_path / "data_sources.yaml"
        config_content = {
            "sources": {
                "test_source": {
                    "type": "url",
                    "url": "https://example.com"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        result = load_data_sources(str(config_file))
        assert "sources" in result
        assert "test_source" in result["sources"]
        assert result["sources"]["test_source"]["type"] == "url"

    def test_load_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_data_sources("nonexistent.yaml")

    def test_load_invalid_format(self, tmp_path):
        """Test that invalid YAML format raises ValueError."""
        config_file = tmp_path / "data_sources.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: without: proper: structure")
        
        # This might raise yaml.YAMLError or ValueError depending on content
        with pytest.raises((yaml.YAMLError, ValueError)):
            load_data_sources(str(config_file))

class TestCheckUrlReachability:
    @patch('src.validate.citation_check.requests.get')
    def test_reachable_url(self, mock_get):
        """Test a reachable URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        reachable, msg = check_url_reachability("https://example.com")
        assert reachable is True
        assert "200" in msg

    @patch('src.validate.citation_check.requests.get')
    def test_unreachable_url(self, mock_get):
        """Test an unreachable URL."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        reachable, msg = check_url_reachability("https://example.com/404")
        assert reachable is False
        assert "404" in msg

    @patch('src.validate.citation_check.requests.get')
    def test_connection_error(self, mock_get):
        """Test connection error handling."""
        mock_get.side_effect = Exception("Connection failed")
        
        reachable, msg = check_url_reachability("https://invalid.url")
        assert reachable is False
        assert "failed" in msg.lower()

class TestVerifySources:
    def test_verify_url_source(self):
        """Test verification of a URL source."""
        data = {
            "sources": {
                "test_url": {
                    "type": "url",
                    "url": "https://example.com"
                }
            }
        }
        
        with patch('src.validate.citation_check.check_url_reachability') as mock_check:
            mock_check.return_value = (True, "Reachable (HTTP 200)")
            
            report = verify_sources(data)
            
            assert report["summary"]["total"] == 1
            assert report["summary"]["passed"] == 1
            assert report["details"][0]["status"] == "passed"
            assert report["details"][0]["source"] == "test_url"

    def test_verify_hf_source(self):
        """Test verification of a HuggingFace source."""
        data = {
            "sources": {
                "test_hf": {
                    "type": "huggingface",
                    "dataset_id": "test/dataset"
                }
            }
        }
        
        with patch('src.validate.citation_check.check_hf_dataset_files') as mock_check:
            mock_check.return_value = (True, "Dataset exists", ["file1.txt"])
            
            report = verify_sources(data)
            
            assert report["summary"]["total"] == 1
            assert report["summary"]["passed"] == 1
            assert report["details"][0]["status"] == "passed"
            assert report["details"][0]["source"] == "test_hf"
            assert "test/dataset" in report["details"][0]["details"]["dataset_id"]

    def test_verify_with_fallback(self):
        """Test verification with fallback URL."""
        data = {
            "sources": {
                "test_hf_fallback": {
                    "type": "huggingface",
                    "dataset_id": "invalid/dataset",
                    "fallback": {
                        "type": "url",
                        "url": "https://example.com/fallback"
                    }
                }
            }
        }
        
        with patch('src.validate.citation_check.check_hf_dataset_files') as mock_hf, \
             patch('src.validate.citation_check.check_url_reachability') as mock_url:
            
            mock_hf.return_value = (False, "Dataset not found", [])
            mock_url.return_value = (True, "Reachable (HTTP 200)")
            
            report = verify_sources(data)
            
            assert report["summary"]["total"] == 1
            assert report["summary"]["warnings"] == 1
            assert report["details"][0]["status"] == "warning"
            assert "fallback" in report["details"][0]["message"].lower()
    
    def test_verify_unknown_type(self):
        """Test verification of unknown source type."""
        data = {
            "sources": {
                "test_unknown": {
                    "type": "unknown_type"
                }
            }
        }
        
        report = verify_sources(data)
        
        assert report["summary"]["failed"] == 1
        assert report["details"][0]["status"] == "failed"
        assert "Unknown source type" in report["details"][0]["message"]
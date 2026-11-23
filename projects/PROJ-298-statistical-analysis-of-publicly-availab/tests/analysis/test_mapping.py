"""
Unit tests for code/analysis/mapping.py (Task T015)
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.mapping import (
    select_best_candidate,
    map_tag_to_repos,
    run_mapping_pipeline,
    load_external_metrics
)

class TestSelectBestCandidate:
    def test_github_sort_by_stars(self):
        candidates = [
            {"name": "repo_b", "stargazers_count": 100, "updated_at": "2023-01-01"},
            {"name": "repo_a", "stargazers_count": 200, "updated_at": "2022-01-01"},
        ]
        best = select_best_candidate(candidates, "github")
        assert best["name"] == "repo_a"

    def test_github_sort_by_date_if_stars_equal(self):
        candidates = [
            {"name": "repo_old", "stargazers_count": 100, "updated_at": "2020-01-01"},
            {"name": "repo_new", "stargazers_count": 100, "updated_at": "2023-01-01"},
        ]
        best = select_best_candidate(candidates, "github")
        assert best["name"] == "repo_new"

    def test_npm_sort_by_downloads(self):
        candidates = [
            {"name": "pkg_b", "downloads": 5000},
            {"name": "pkg_a", "downloads": 10000},
        ]
        best = select_best_candidate(candidates, "npm")
        assert best["name"] == "pkg_a"

    def test_empty_list(self):
        assert select_best_candidate([], "github") is None

class TestMapTagToRepos:
    def test_successful_mapping_both(self):
        tag_data = {
            "github_candidates": [
                {"full_name": "org/repo", "stargazers_count": 500, "html_url": "http://gh"}
            ],
            "npm_candidates": [
                {"name": "pkg-name", "downloads": 10000}
            ]
        }
        result = map_tag_to_repos(tag_data, "test-tag")
        assert result["status"] == "mapped"
        assert result["github"]["repo_name"] == "org/repo"
        assert result["npm"]["package_name"] == "pkg-name"

    def test_no_candidates(self):
        tag_data = {
            "github_candidates": [],
            "npm_candidates": []
        }
        result = map_tag_to_repos(tag_data, "test-tag")
        assert result["status"] == "unmapped"
        assert result["github"] is None
        assert result["npm"] is None

    def test_github_only(self):
        tag_data = {
            "github_candidates": [
                {"full_name": "org/repo", "stargazers_count": 500}
            ],
            "npm_candidates": []
        }
        result = map_tag_to_repos(tag_data, "test-tag")
        assert result["status"] == "mapped"
        assert result["github"] is not None
        assert result["npm"] is None

class TestRunMappingPipeline:
    @patch('analysis.mapping.EXTERNAL_METRICS_PATH')
    @patch('analysis.mapping.DATA_PROCESSED_DIR')
    @patch('builtins.open', new_callable=MagicMock)
    def test_pipeline_execution(self, mock_open, mock_dir, mock_path):
        # Setup mock data
        mock_data = {
            "react": {
                "github_candidates": [{"full_name": "facebook/react", "stargazers_count": 200000}],
                "npm_candidates": [{"name": "react", "downloads": 5000000}]
            },
            "empty-tag": {
                "github_candidates": [],
                "npm_candidates": []
            }
        }
        
        # Mock file reading
        mock_file_read = mock_open.return_value.__enter__.return_value
        mock_file_read.read.return_value = json.dumps(mock_data)
        
        # Mock file writing
        mock_file_write = mock_open.return_value.__enter__.return_value

        # Mock paths
        mock_path.exists.return_value = True
        mock_dir.mkdir.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch paths to temp dir
            import analysis.mapping as mapping_module
            original_mapping_path = mapping_module.OUTPUT_MAPPING_PATH
            original_unmapped_path = mapping_module.OUTPUT_UNMAPPED_LOG_PATH
            
            mapping_module.OUTPUT_MAPPING_PATH = Path(tmpdir) / "tag_mappings.json"
            mapping_module.OUTPUT_UNMAPPED_LOG_PATH = Path(tmpdir) / "unmapped_tags.log"
            
            try:
                run_mapping_pipeline()
                
                # Verify outputs exist
                assert mapping_module.OUTPUT_MAPPING_PATH.exists()
                assert mapping_module.OUTPUT_UNMAPPED_LOG_PATH.exists()
                
                # Verify content
                with open(mapping_module.OUTPUT_MAPPING_PATH, 'r') as f:
                    results = json.load(f)
                    assert len(results) == 2
                    assert results[0]["status"] == "mapped"
                    assert results[1]["status"] == "unmapped"
            finally:
                mapping_module.OUTPUT_MAPPING_PATH = original_mapping_path
                mapping_module.OUTPUT_UNMAPPED_LOG_PATH = original_unmapped_path

    @patch('analysis.mapping.EXTERNAL_METRICS_PATH')
    def test_missing_input_file(self, mock_path):
        mock_path.exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            load_external_metrics()
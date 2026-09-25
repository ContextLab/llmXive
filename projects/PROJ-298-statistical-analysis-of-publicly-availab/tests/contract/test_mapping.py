"""
Contract test for T015: Tag-to-Repo Mapping.

Verifies:
1. Output adheres to schema.
2. Unmapped tags are correctly logged.
3. Handles API failure scenarios (404/rate-limit) gracefully by logging and skipping.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(project_root / "code"))

from analysis.mapping import (
    validate_external_metrics,
    select_best_candidate,
    map_tag_to_repos,
    run_mapping_pipeline,
    ensure_log_dir
)

class TestMappingContract:
    
    def test_validate_external_metrics_valid(self):
        """Test validation with valid structure."""
        data = {
            "metrics": [
                {
                    "tag": "python",
                    "github": {"status": "success", "candidates": []},
                    "npm": {"status": "success", "candidates": []}
                }
            ]
        }
        assert validate_external_metrics(data) is True

    def test_validate_external_metrics_invalid_structure(self):
        """Test validation with missing 'metrics' key."""
        data = {"data": []}
        assert validate_external_metrics(data) is False

    def test_validate_external_metrics_invalid_type(self):
        """Test validation with non-dict input."""
        assert validate_external_metrics("string") is False
        assert validate_external_metrics([]) is False

    def test_select_best_candidate_github(self):
        """Test selection of best GitHub candidate by stars."""
        candidates = [
            {"full_name": "repo/low", "stars": 100},
            {"full_name": "repo/high", "stars": 5000},
            {"full_name": "repo/med", "stars": 500}
        ]
        best = select_best_candidate(candidates, "github")
        assert best is not None
        assert best["full_name"] == "repo/high"

    def test_select_best_candidate_npm(self):
        """Test selection of best NPM candidate by downloads."""
        candidates = [
            {"name": "pkg/low", "downloads": 1000},
            {"name": "pkg/high", "downloads": 50000},
            {"name": "pkg/med", "downloads": 5000}
        ]
        best = select_best_candidate(candidates, "npm")
        assert best is not None
        assert best["name"] == "pkg/high"

    def test_select_best_candidate_empty(self):
        """Test selection with empty candidates list."""
        best = select_best_candidate([], "github")
        assert best is None

    def test_map_tag_to_repos_success(self):
        """Test mapping when candidates are found."""
        tag_data = {
            "tag": "react",
            "github": {
                "status": "success",
                "candidates": [{"full_name": "facebook/react", "stars": 200000, "html_url": "https://github.com/facebook/react"}]
            },
            "npm": {
                "status": "success",
                "candidates": [{"name": "react", "downloads": 10000000, "url": "https://npmjs.com/package/react"}]
            }
        }
        github_map, npm_map = map_tag_to_repos(tag_data)
        
        assert github_map is not None
        assert github_map["repo"] == "facebook/react"
        assert npm_map is not None
        assert npm_map["package"] == "react"

    def test_map_tag_to_repos_failure(self):
        """Test mapping when no candidates are found (simulating 404/rate limit)."""
        tag_data = {
            "tag": "nonexistent_tag_xyz",
            "github": {
                "status": "error", # Simulate API error
                "candidates": []
            },
            "npm": {
                "status": "error",
                "candidates": []
            }
        }
        github_map, npm_map = map_tag_to_repos(tag_data)
        
        assert github_map is None
        assert npm_map is None

    def test_run_mapping_pipeline_missing_input(self):
        """Test pipeline behavior when input file is missing."""
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Override global paths for this test
            import analysis.mapping as mapping_module
            original_input = mapping_module.INPUT_FILE
            original_output = mapping_module.OUTPUT_FILE
            original_unmapped = mapping_module.UNMAPPED_LOG
            
            mapping_module.INPUT_FILE = tmp_path / "nonexistent.json"
            mapping_module.OUTPUT_FILE = tmp_path / "output.json"
            mapping_module.UNMAPPED_LOG = tmp_path / "unmapped.log"
            
            try:
                success = run_mapping_pipeline()
                assert success is True
                assert mapping_module.UNMAPPED_LOG.exists()
                with open(mapping_module.UNMAPPED_LOG, 'r') as f:
                    content = f.read()
                    assert content == "" # Should be empty
            finally:
                # Restore original paths
                mapping_module.INPUT_FILE = original_input
                mapping_module.OUTPUT_FILE = original_output
                mapping_module.UNMAPPED_LOG = original_unmapped

    def test_run_mapping_pipeline_empty_metrics(self):
        """Test pipeline with empty metrics list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_file = tmp_path / "external_metrics.json"
            output_file = tmp_path / "tag_mappings.json"
            unmapped_file = tmp_path / "unmapped.log"
            
            # Write empty metrics
            with open(input_file, 'w') as f:
                json.dump({"metrics": []}, f)
            
            import analysis.mapping as mapping_module
            original_input = mapping_module.INPUT_FILE
            original_output = mapping_module.OUTPUT_FILE
            original_unmapped = mapping_module.UNMAPPED_LOG
            
            mapping_module.INPUT_FILE = input_file
            mapping_module.OUTPUT_FILE = output_file
            mapping_module.UNMAPPED_LOG = unmapped_file
            
            try:
                success = run_mapping_pipeline()
                assert success is True
                assert output_file.exists()
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    assert data["mappings"] == []
                assert unmapped_file.exists()
            finally:
                mapping_module.INPUT_FILE = original_input
                mapping_module.OUTPUT_FILE = original_output
                mapping_module.UNMAPPED_LOG = original_unmapped

    def test_run_mapping_pipeline_partial_success(self):
        """Test pipeline with mix of success and failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_file = tmp_path / "external_metrics.json"
            output_file = tmp_path / "tag_mappings.json"
            unmapped_file = tmp_path / "unmapped.log"
            
            input_data = {
                "metrics": [
                    {
                        "tag": "valid_tag",
                        "github": {"status": "success", "candidates": [{"full_name": "org/repo", "stars": 100, "html_url": "url"}]},
                        "npm": {"status": "success", "candidates": [{"name": "pkg", "downloads": 100, "url": "url"}]}
                    },
                    {
                        "tag": "invalid_tag",
                        "github": {"status": "error", "candidates": []},
                        "npm": {"status": "error", "candidates": []}
                    }
                ]
            }
            
            with open(input_file, 'w') as f:
                json.dump(input_data, f)
            
            import analysis.mapping as mapping_module
            original_input = mapping_module.INPUT_FILE
            original_output = mapping_module.OUTPUT_FILE
            original_unmapped = mapping_module.UNMAPPED_LOG
            
            mapping_module.INPUT_FILE = input_file
            mapping_module.OUTPUT_FILE = output_file
            mapping_module.UNMAPPED_LOG = unmapped_file
            
            try:
                success = run_mapping_pipeline()
                assert success is True
                
                # Check output
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    assert len(data["mappings"]) == 1
                    assert data["mappings"][0]["tag"] == "valid_tag"
                
                # Check unmapped log
                assert unmapped_file.exists()
                with open(unmapped_file, 'r') as f:
                    lines = f.readlines()
                    assert len(lines) == 1
                    entry = json.loads(lines[0])
                    assert entry["tag"] == "invalid_tag"
            finally:
                mapping_module.INPUT_FILE = original_input
                mapping_module.OUTPUT_FILE = original_output
                mapping_module.UNMAPPED_LOG = original_unmapped
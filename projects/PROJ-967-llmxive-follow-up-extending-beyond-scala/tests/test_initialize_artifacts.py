import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala" / "code"))

from initialize_artifacts import initialize_empty_artifacts


class TestInitializeArtifacts:
    def test_creates_features_json_with_empty_list(self, tmp_path):
        """Verify that features.json is created with content []"""
        # Create a temporary directory structure
        base_dir = tmp_path / "test_project"
        base_dir.mkdir()
        
        # Run the initialization
        initialize_empty_artifacts(base_dir, None)
        
        # Check that the file exists
        features_path = base_dir / "data" / "processed" / "features.json"
        assert features_path.exists(), "features.json should be created"
        
        # Check the content
        with open(features_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        
        assert content == [], "features.json should contain an empty list"

    def test_creates_results_json_with_empty_dict(self, tmp_path):
        """Verify that results.json is created with content {}"""
        # Create a temporary directory structure
        base_dir = tmp_path / "test_project"
        base_dir.mkdir()
        
        # Run the initialization
        initialize_empty_artifacts(base_dir, None)
        
        # Check that the file exists
        results_path = base_dir / "results" / "results.json"
        assert results_path.exists(), "results.json should be created"
        
        # Check the content
        with open(results_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        
        assert content == {}, "results.json should contain an empty dict"

    def test_creates_directories(self, tmp_path):
        """Verify that required directories are created if they don't exist"""
        base_dir = tmp_path / "test_project"
        base_dir.mkdir()
        
        # Run the initialization
        initialize_empty_artifacts(base_dir, None)
        
        # Check directories exist
        assert (base_dir / "data" / "processed").exists(), "data/processed directory should exist"
        assert (base_dir / "results").exists(), "results directory should exist"
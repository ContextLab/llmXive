import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala" / "code"))
from initialize_artifacts import initialize_empty_artifacts


class TestInitializeArtifacts:
    def test_creates_features_json(self, tmp_path):
        """Test that features.json is created with an empty list."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        initialize_empty_artifacts(str(project_root))
        
        features_path = project_root / "data" / "processed" / "features.json"
        assert features_path.exists(), "features.json was not created"
        
        with open(features_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        
        assert isinstance(content, list), "features.json content should be a list"
        assert len(content) == 0, "features.json should be initialized as an empty list"

    def test_creates_results_json(self, tmp_path):
        """Test that results.json is created with an empty dict."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        initialize_empty_artifacts(str(project_root))
        
        results_path = project_root / "results" / "results.json"
        assert results_path.exists(), "results.json was not created"
        
        with open(results_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        
        assert isinstance(content, dict), "results.json content should be a dict"
        assert len(content) == 0, "results.json should be initialized as an empty dict"

    def test_creates_directories(self, tmp_path):
        """Test that required directories are created if they don't exist."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        initialize_empty_artifacts(str(project_root))
        
        processed_dir = project_root / "data" / "processed"
        results_dir = project_root / "results"
        
        assert processed_dir.exists(), "data/processed directory was not created"
        assert results_dir.exists(), "results directory was not created"
        
        # Verify files are inside the created directories
        assert (processed_dir / "features.json").exists()
        assert (results_dir / "results.json").exists()
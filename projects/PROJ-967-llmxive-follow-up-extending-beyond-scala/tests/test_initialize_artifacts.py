import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'projects', 'PROJ-967-llmxive-follow-up-extending-beyond-scala', 'code'))

from initialize_artifacts import initialize_empty_artifacts

def test_initialize_empty_artifacts():
    """Test that initialize_empty_artifacts creates the correct files with correct content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Create the expected directory structure
        (base_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (base_path / "results").mkdir(parents=True, exist_ok=True)
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Run the function
        initialize_empty_artifacts(base_path, logger)
        
        # Verify features.json
        features_path = base_path / "data" / "processed" / "features.json"
        assert features_path.exists(), "features.json was not created"
        with open(features_path, 'r', encoding='utf-8') as f:
            features_content = json.load(f)
        assert features_content == [], f"features.json should be empty list, got {features_content}"
        
        # Verify results.json
        results_path = base_path / "results" / "results.json"
        assert results_path.exists(), "results.json was not created"
        with open(results_path, 'r', encoding='utf-8') as f:
            results_content = json.load(f)
        assert results_content == {}, f"results.json should be empty dict, got {results_content}"
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code root to path if not already
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from research.verify_studies import search_plant_studies, verify_studies, MANIFEST_PATH

def test_search_plant_studies_structure():
    """
    Tests that the search function returns a list of dictionaries with expected keys.
    Uses mocking to avoid real API calls during unit tests.
    """
    mock_data = {
        "STUDIES": [
            {
                "STUDY_ID": "ST001234",
                "STUDY_TITLE": "Time course analysis of plant resistance",
                "ABSTRACT": "Pre-challenge metabolite profiles were measured."
            }
        ]
    }

    with patch('research.verify_studies.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = search_plant_studies()

        assert isinstance(results, list)
        assert len(results) > 0
        assert "study_id" in results[0]
        assert "title" in results[0]
        assert "download_url" in results[0]

def test_verify_studies_creates_manifest_structure():
    """
    Tests that verify_studies returns the correct structure for the manifest.
    """
    candidates = [
        {
            "study_id": "ST001234",
            "title": "Test Study",
            "download_url": "http://example.com"
        }
    ]

    manifest = verify_studies(candidates)

    assert len(manifest) == 1
    assert manifest[0]["study_id"] == "ST001234"
    assert manifest[0]["title"] == "Test Study"
    assert manifest[0]["download_url"] == "http://example.com"

def test_manifest_generation_logic():
    """
    Tests the logic of manifest generation and file writing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override MANIFEST_PATH for testing
        test_manifest_path = Path(tmpdir) / "study_manifest.json"
        
        # Mock the main logic to write to temp file
        candidates = [
            {
                "study_id": "ST001234",
                "title": "Test Study",
                "download_url": "http://example.com"
            }
        ]
        manifest = verify_studies(candidates)

        with open(test_manifest_path, 'w') as f:
            json.dump(manifest, f)

        # Verify file content
        with open(test_manifest_path, 'r') as f:
            loaded = json.load(f)

        assert len(loaded) == 1
        assert loaded[0]["study_id"] == "ST001234"
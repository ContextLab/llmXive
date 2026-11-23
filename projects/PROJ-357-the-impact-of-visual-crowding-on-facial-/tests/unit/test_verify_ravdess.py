import pytest
from pathlib import Path
import sys
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.verify_ravdess import verify_huggingface_dataset
from config import RAVDESS_DEFAULT_URL

class TestVerifyRavdess:
    """Tests for the RAVDESS dataset verification logic."""

    def test_verify_known_dataset(self):
        """Test that the verified canonical URL resolves successfully."""
        # We expect the canonical URL to exist on HF
        result = verify_huggingface_dataset(RAVDESS_DEFAULT_URL)
        
        assert result["verified"] is True
        assert result["dataset_id"] == RAVDESS_DEFAULT_URL
        assert "message" in result
        assert "metadata" in result
        assert result["metadata"]["id"] == RAVDESS_DEFAULT_URL

    def test_verify_nonexistent_dataset_raises(self):
        """Test that a non-existent dataset raises a ValueError."""
        fake_dataset = "this-dataset-does-not-exist-12345"
        
        with pytest.raises(ValueError, match="Failed to verify dataset"):
            verify_huggingface_dataset(fake_dataset)

    def test_verify_invalid_format_raises(self):
        """Test that an invalid dataset ID format raises an error."""
        invalid_dataset = "not/a/valid/dataset/id/structure"
        
        # Depending on HF API behavior, this might raise ValueError or specific API error
        # We expect it to fail verification
        with pytest.raises(Exception):
            verify_huggingface_dataset(invalid_dataset)

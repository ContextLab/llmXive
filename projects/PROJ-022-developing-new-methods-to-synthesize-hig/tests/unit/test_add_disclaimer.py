"""
Unit tests for the associational disclaimer addition to model metadata.

Tests verify that:
1. The disclaimer is correctly added to the model metadata.
2. The disclaimer text matches the required FR-007 content.
3. The model can be re-saved and re-loaded with the disclaimer intact.
"""
import os
import sys
import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from modeling.add_associational_disclaimer import (
    add_disclaimer,
    DISCLAIMER_KEY,
    DISCLAIMER_TEXT
)

class TestAddAssociationalDisclaimer(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_model_data = {
            "model": "mock_random_forest",
            "training_params": {"max_depth": 10, "n_estimators": 100},
            "metadata": {
                "version": "1.0",
                "author": "automated_pipeline"
            }
        }
    
    def test_add_disclaimer_to_existing_metadata(self):
        """Test that disclaimer is added to existing metadata."""
        result = add_disclaimer(self.mock_model_data.copy())
        
        self.assertIn("metadata", result)
        self.assertIn(DISCLAIMER_KEY, result["metadata"])
        self.assertEqual(result["metadata"][DISCLAIMER_KEY], DISCLAIMER_TEXT)
    
    def test_add_disclaimer_to_empty_metadata(self):
        """Test that disclaimer is added when metadata is missing."""
        model_no_meta = {"model": "mock_rf"}
        result = add_disclaimer(model_no_meta)
        
        self.assertIn("metadata", result)
        self.assertIn(DISCLAIMER_KEY, result["metadata"])
    
    def test_disclaimer_content_matches_fr007(self):
        """Test that the disclaimer text contains required FR-007 keywords."""
        required_terms = [
            "associational",
            "not causal",
            "statistical correlations",
            "causal relationships",
            "experimental validation"
        ]
        
        disclaimer_lower = DISCLAIMER_TEXT.lower()
        for term in required_terms:
            self.assertIn(term.lower(), disclaimer_lower, 
                          f"Disclaimer missing required term: {term}")
    
    def test_disclaimer_does_not_modify_other_metadata(self):
        """Test that adding disclaimer doesn't alter other metadata fields."""
        original_meta = self.mock_model_data["metadata"].copy()
        result = add_disclaimer(self.mock_model_data.copy())
        
        for key, value in original_meta.items():
            self.assertEqual(result["metadata"][key], value)
    
    def test_disclaimer_is_persistent_after_pickle(self):
        """Test that disclaimer survives serialization and deserialization."""
        model_with_disclaimer = add_disclaimer(self.mock_model_data.copy())
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
            tmp_path = tmp.name
            pickle.dump(model_with_disclaimer, tmp)
        
        try:
            with open(tmp_path, 'rb') as f:
                loaded_data = pickle.load(f)
            
            self.assertIn(DISCLAIMER_KEY, loaded_data["metadata"])
            self.assertEqual(loaded_data["metadata"][DISCLAIMER_KEY], DISCLAIMER_TEXT)
        finally:
            os.unlink(tmp_path)

if __name__ == "__main__":
    unittest.main()
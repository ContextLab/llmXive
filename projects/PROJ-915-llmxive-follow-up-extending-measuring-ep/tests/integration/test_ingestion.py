"""
Integration tests for ingestion pipeline.
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.ingestion import (
    run_ingestion_pipeline,
    OUTPUT_FILE,
    CHECKSUM_FILE
)

class TestIngestionIntegration:
    @patch('code.ingestion.load_dataset')
    def test_full_pipeline_with_mocked_dataset(self, mock_load_dataset):
        """Test full pipeline with mocked dataset."""
        # Mock dataset iterator
        mock_item1 = {
            "prompt_id": "1",
            "prompt_text": "Test question",
            "false_claim": "False claim here",
            "correct_answer": "Correct answer",
            "label": "Authority-framed"
        }
        mock_item2 = {
            "prompt_id": "2",
            "prompt_text": "Another question",
            "false_claim": "Another false claim",
            "correct_answer": "Another correct answer",
            "label": "Exception-poisoning"
        }
        mock_item3 = {
            "prompt_id": "3",
            "prompt_text": "Skip this",
            "false_claim": "Skip claim",
            "correct_answer": "Skip answer",
            "label": "Other-label"
        }
        
        mock_dataset = [mock_item1, mock_item2, mock_item3]
        mock_load_dataset.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override output paths
            import code.ingestion as ingestion_module
            original_output = ingestion_module.OUTPUT_FILE
            original_checksum = ingestion_module.CHECKSUM_FILE
            
            ingestion_module.OUTPUT_FILE = os.path.join(temp_dir, "medmis_subset.csv")
            ingestion_module.CHECKSUM_FILE = os.path.join(temp_dir, "state", "artifact_hashes.yaml")
            
            try:
                # Run pipeline
                run_ingestion_pipeline()
                
                # Verify output file exists
                assert os.path.exists(ingestion_module.OUTPUT_FILE)
                
                # Verify CSV content
                with open(ingestion_module.OUTPUT_FILE, 'r') as f:
                    content = f.read()
                    assert "prompt_id" in content
                    assert "Test question" in content
                    assert "Authority-framed" not in content  # Labels not in CSV
                
                # Verify checksum file
                assert os.path.exists(ingestion_module.CHECKSUM_FILE)
                with open(ingestion_module.CHECKSUM_FILE, 'r') as f:
                    state = yaml.safe_load(f)
                    assert "medmis_subset" in state
                    assert "sha256" in state["medmis_subset"]
                
            finally:
                # Restore original paths
                ingestion_module.OUTPUT_FILE = original_output
                ingestion_module.CHECKSUM_FILE = original_checksum

    @patch('code.ingestion.load_dataset')
    def test_pipeline_filters_correctly(self, mock_load_dataset):
        """Test that pipeline correctly filters labels."""
        mock_items = [
            {"label": "Authority-framed", "prompt_id": "1", "prompt_text": "test", "false_claim": "c", "correct_answer": "a"},
            {"label": "Exception-poisoning", "prompt_id": "2", "prompt_text": "test", "false_claim": "c", "correct_answer": "a"},
            {"label": "Other", "prompt_id": "3", "prompt_text": "test", "false_claim": "c", "correct_answer": "a"},
            {"label": "Authority-framed", "prompt_id": "4", "prompt_text": "test", "false_claim": "c", "correct_answer": "a"},
        ]
        
        mock_load_dataset.return_value = mock_items
        
        with tempfile.TemporaryDirectory() as temp_dir:
            import code.ingestion as ingestion_module
            original_output = ingestion_module.OUTPUT_FILE
            original_checksum = ingestion_module.CHECKSUM_FILE
            
            ingestion_module.OUTPUT_FILE = os.path.join(temp_dir, "medmis_subset.csv")
            ingestion_module.CHECKSUM_FILE = os.path.join(temp_dir, "state", "artifact_hashes.yaml")
            
            try:
                run_ingestion_pipeline()
                
                # Should have 3 items (2 Authority-framed, 1 Exception-poisoning)
                with open(ingestion_module.OUTPUT_FILE, 'r') as f:
                    lines = f.readlines()
                    # Header + 3 data rows
                    assert len(lines) == 4
                
            finally:
                ingestion_module.OUTPUT_FILE = original_output
                ingestion_module.CHECKSUM_FILE = original_checksum

    def test_pipeline_fails_on_empty_dataset(self):
        """Test that pipeline fails when dataset is empty."""
        with patch('code.ingestion.load_dataset') as mock_load:
            mock_load.return_value = []
            
            with pytest.raises(Exception) as exc_info:
                run_ingestion_pipeline()
            
            assert "No items found matching filter criteria" in str(exc_info.value)

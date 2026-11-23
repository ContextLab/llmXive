"""
Unit tests for dataset_substitution.py
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.data.dataset_substitution import (
    load_bigvul_metadata,
    generate_substitution_justification,
    write_justification_log,
    run_dataset_substitution_logic
)
from src.utils.config import get_project_root, get_data_logs_path


class TestDatasetSubstitutionJustification:
    def test_load_bigvul_metadata_structure(self):
        """Verify that load_bigvul_metadata returns expected keys."""
        meta = load_bigvul_metadata()
        assert "source" in meta
        assert meta["source"] == "BigVul"
        assert "fields" in meta
        assert "language" in meta["fields"]
        assert "vulnerability_type" in meta["fields"]
        assert "code" in meta["fields"]
        assert "is_vulnerable" in meta["fields"]

    def test_generate_justification_content(self):
        """Verify the structure of the generated justification."""
        reason = "Test failure"
        just = generate_substitution_justification(reason)
        
        assert "substitution_event" in just
        assert just["substitution_event"]["failure_reason"] == reason
        assert "primary_dataset" in just["substitution_event"]
        assert "fallback_dataset" in just["substitution_event"]
        
        assert "schema_mapping_rules" in just
        assert isinstance(just["schema_mapping_rules"], list)
        assert len(just["schema_mapping_rules"]) > 0
        
        # Check specific mapping rules
        target_fields = [r["target_field"] for r in just["schema_mapping_rules"]]
        assert "language" in target_fields
        assert "ground_truth_category" in target_fields
        assert "ground_truth_label" in target_fields

class TestWriteJustificationLog:
    def test_write_justification_creates_file(self, tmp_path):
        """Test that write_justification_log creates the JSON file."""
        # Mock the get_data_logs_path to use tmp_path
        with patch('src.data.dataset_substitution.get_data_logs_path', return_value=tmp_path):
            justification = generate_substitution_justification("Test error")
            log_path = write_justification_log(justification, "Test error")
            
            assert log_path.exists()
            assert log_path.name == "dataset_substitution_justification.json"
            
            with open(log_path, 'r') as f:
                data = json.load(f)
            
            assert data["status"] == "SUBSTITUTION_EXECUTED"
            assert data["reason"] == "Test error"
            assert "details" in data

class TestRunDatasetSubstitutionLogic:
    @patch('src.data.dataset_substitution.get_data_logs_path')
    def test_run_logic_success(self, mock_logs_path, tmp_path):
        """Test the full run logic writes the file and returns True."""
        mock_logs_path.return_value = tmp_path
        
        success = run_dataset_substitution_logic("Network error")
        
        assert success is True
        assert (tmp_path / "dataset_substitution_justification.json").exists()

    @patch('src.data.dataset_substitution.get_data_logs_path')
    def test_run_logic_failure_handling(self, mock_logs_path, tmp_path):
        """Test that exceptions are caught and False is returned."""
        mock_logs_path.return_value = tmp_path
        
        # Force an exception in write_justification_log
        with patch('src.data.dataset_substitution.write_justification_log', side_effect=Exception("Simulated failure")):
            success = run_dataset_substitution_logic("Network error")
            
            assert success is False

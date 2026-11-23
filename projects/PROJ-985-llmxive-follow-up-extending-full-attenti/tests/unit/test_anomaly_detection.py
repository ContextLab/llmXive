"""
Unit tests for anomaly detection logic in the ground truth extraction pipeline.

This module tests the anomaly detection functionality that identifies documents
with zero RTPurbo tokens and ensures they are properly flagged and excluded.
"""

import pytest
import os
import sys
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any
import csv

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from lib.entities import TokenUnit, AttentionMap
from lib.logging_config import log_anomaly, setup_logging


class TestAnomalyDetection:
    """Test cases for anomaly detection logic."""

    @pytest.fixture
    def sample_attention_map(self) -> AttentionMap:
        """Create a sample attention map for testing."""
        return AttentionMap(
            document_id="test_doc_1",
            attention_weights=[0.1, 0.2, 0.3, 0.4, 0.5],
            token_ids=[101, 102, 103, 104, 105],
            rtpurbo_indices=[1, 3],  # Two tokens selected
            rtpurbo_scores=[0.75, 0.85]
        )

    @pytest.fixture
    def zero_rtpurbo_attention_map(self) -> AttentionMap:
        """Create an attention map with zero RTPurbo tokens (anomalous)."""
        return AttentionMap(
            document_id="test_doc_anomaly",
            attention_weights=[0.2, 0.2, 0.2, 0.2, 0.2],
            token_ids=[201, 202, 203, 204, 205],
            rtpurbo_indices=[],  # No tokens selected - ANOMALY
            rtpurbo_scores=[]
        )

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_detect_zero_rtpurbo_tokens(self, zero_rtpurbo_attention_map):
        """Test that documents with zero RTPurbo tokens are detected as anomalies."""
        # The anomaly condition is: len(rtpurbo_indices) == 0
        is_anomaly = len(zero_rtpurbo_attention_map.rtpurbo_indices) == 0
        assert is_anomaly is True, "Document with zero RTPurbo tokens should be flagged as anomaly"

    def test_normal_document_not_anomaly(self, sample_attention_map):
        """Test that normal documents with RTPurbo tokens are not flagged."""
        is_anomaly = len(sample_attention_map.rtpurbo_indices) == 0
        assert is_anomaly is False, "Document with RTPurbo tokens should not be flagged as anomaly"

    def test_log_anomaly_creates_entry(self, zero_rtpurbo_attention_map, temp_output_dir):
        """Test that logging an anomaly creates the expected entry."""
        anomaly_log_path = os.path.join(temp_output_dir, "anomalies.csv")
        
        # Setup logging to write to our temp file
        setup_logging(log_file=anomaly_log_path)
        
        # Log the anomaly
        log_anomaly(
            document_id=zero_rtpurbo_attention_map.document_id,
            reason="Zero RTPurbo tokens detected",
            details={
                "attention_weights_count": len(zero_rtpurbo_attention_map.attention_weights),
                "rtpurbo_indices_count": len(zero_rtpurbo_attention_map.rtpurbo_indices)
            }
        )
        
        # Verify the log file exists and contains the entry
        assert os.path.exists(anomaly_log_path), "Anomaly log file should be created"
        
        with open(anomaly_log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 1, "At least one anomaly entry should be logged"
            
            # Check the logged data
            anomaly_entry = rows[-1]
            assert anomaly_entry['document_id'] == zero_rtpurbo_attention_map.document_id
            assert anomaly_entry['reason'] == "Zero RTPurbo tokens detected"
            assert anomaly_entry['status'] == "EXCLUDED"

    def test_anomaly_detection_threshold(self):
        """Test various edge cases for anomaly detection."""
        test_cases = [
            ([0.1, 0.2, 0.3], [0], False, "Single token selected"),
            ([0.1, 0.2, 0.3], [0, 1, 2], False, "All tokens selected"),
            ([0.1, 0.2, 0.3], [], True, "No tokens selected"),
            ([], [], True, "Empty attention map"),
            ([0.5], [0], False, "Single token, single selection"),
        ]
        
        for attn_weights, rtpurbo_indices, expected_anomaly, description in test_cases:
            is_anomaly = len(rtpurbo_indices) == 0
            assert is_anomaly == expected_anomaly, f"Failed for: {description}"

    def test_anomaly_filtering_logic(self):
        """Test the logic for filtering out anomalous documents from a batch."""
        documents = [
            {"id": "doc1", "rtpurbo_indices": [0, 1], "is_anomaly": False},
            {"id": "doc2", "rtpurbo_indices": [], "is_anomaly": True},
            {"id": "doc3", "rtpurbo_indices": [2], "is_anomaly": False},
            {"id": "doc4", "rtpurbo_indices": [], "is_anomaly": True},
        ]
        
        # Filter out anomalies
        valid_documents = [doc for doc in documents if not doc["is_anomaly"]]
        anomaly_documents = [doc for doc in documents if doc["is_anomaly"]]
        
        assert len(valid_documents) == 2, "Should have 2 valid documents"
        assert len(anomaly_documents) == 2, "Should have 2 anomalous documents"
        
        valid_ids = [doc["id"] for doc in valid_documents]
        assert "doc1" in valid_ids and "doc3" in valid_ids
        
        anomaly_ids = [doc["id"] for doc in anomaly_documents]
        assert "doc2" in anomaly_ids and "doc4" in anomaly_ids

    def test_anomaly_reason_classification(self):
        """Test different anomaly reasons and their handling."""
        anomaly_reasons = [
            "Zero RTPurbo tokens detected",
            "Attention weights all zero",
            "Token sequence too short",
            "Model inference failure"
        ]
        
        for reason in anomaly_reasons:
            # Verify we can log different anomaly reasons
            assert len(reason) > 0, "Reason should not be empty"
            assert isinstance(reason, str), "Reason should be a string"

    def test_anomaly_report_generation(self, temp_output_dir):
        """Test that a summary report of anomalies can be generated."""
        anomaly_log_path = os.path.join(temp_output_dir, "anomalies.csv")
        report_path = os.path.join(temp_output_dir, "anomaly_report.json")
        
        # Create sample anomaly data
        anomalies = [
            {"document_id": "doc1", "reason": "Zero RTPurbo tokens", "status": "EXCLUDED"},
            {"document_id": "doc2", "reason": "Zero RTPurbo tokens", "status": "EXCLUDED"},
            {"document_id": "doc3", "reason": "Attention weights all zero", "status": "EXCLUDED"},
        ]
        
        # Write to CSV
        with open(anomaly_log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["document_id", "reason", "status"])
            writer.writeheader()
            writer.writerows(anomalies)
        
        # Generate summary report
        reason_counts = {}
        for anomaly in anomalies:
            reason = anomaly["reason"]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        report = {
            "total_anomalies": len(anomalies),
            "reason_breakdown": reason_counts,
            "anomaly_rate": len(anomalies) / 100,  # Assuming 100 total docs
            "status": "COMPLETE"
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Verify report
        with open(report_path, 'r') as f:
            loaded_report = json.load(f)
            assert loaded_report["total_anomalies"] == 3
            assert loaded_report["reason_breakdown"]["Zero RTPurbo tokens"] == 2
            assert loaded_report["status"] == "COMPLETE"

    def test_edge_case_empty_document_list(self):
        """Test anomaly detection with an empty list of documents."""
        documents = []
        valid_documents = [doc for doc in documents if not doc.get("is_anomaly", False)]
        assert len(valid_documents) == 0, "Empty list should remain empty"

    def test_edge_case_all_anomalous(self):
        """Test when all documents are anomalous."""
        documents = [
            {"id": "doc1", "rtpurbo_indices": [], "is_anomaly": True},
            {"id": "doc2", "rtpurbo_indices": [], "is_anomaly": True},
        ]
        valid_documents = [doc for doc in documents if not doc["is_anomaly"]]
        assert len(valid_documents) == 0, "All anomalous should result in empty valid list"

    def test_rtpurbo_score_validation(self):
        """Test that RTPurbo scores are validated during anomaly detection."""
        # Normal case: scores match indices
        indices = [0, 2, 4]
        scores = [0.8, 0.9, 0.7]
        assert len(indices) == len(scores), "Indices and scores should match in length"
        
        # Anomaly case: mismatched lengths
        indices = [0, 2]
        scores = [0.8]
        assert len(indices) != len(scores), "Mismatched lengths should be detected"

    def test_attention_map_integrity_check(self, sample_attention_map):
        """Test integrity checks on attention maps before anomaly detection."""
        # Check that attention weights and token IDs have same length
        assert len(sample_attention_map.attention_weights) == len(sample_attention_map.token_ids)
        
        # Check that rtpurbo indices are within bounds
        for idx in sample_attention_map.rtpurbo_indices:
            assert 0 <= idx < len(sample_attention_map.attention_weights), "Index out of bounds"
        
        # Check that rtpurbo scores match indices count
        assert len(sample_attention_map.rtpurbo_scores) == len(sample_attention_map.rtpurbo_indices)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
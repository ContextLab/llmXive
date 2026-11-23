"""
Unit tests for data_validation.py module.

Tests FR-007 (Data Completeness) and FR-008 (Metadata Matching) logic.
"""

import os
import json
import tempfile
import shutil
import pytest

from code.data_validation import (
    check_data_completeness,
    check_metadata_matching,
    DataValidationError,
    COMPLETENESS_THRESHOLD
)

class TestDataValidation:
    """Test cases for data validation functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_raw_dir = os.path.join(self.test_dir, "data", "raw")
        self.stimuli_ai_dir = os.path.join(self.test_dir, "data", "stimuli", "ai")
        self.stimuli_human_dir = os.path.join(self.test_dir, "data", "stimuli", "human")
        
        os.makedirs(self.data_raw_dir, exist_ok=True)
        os.makedirs(self.stimuli_ai_dir, exist_ok=True)
        os.makedirs(self.stimuli_human_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_completeness_passes(self):
        """Test FR-007: Completeness check passes when >= 95% complete."""
        # Create complete session files
        for i in range(20):
            session_file = os.path.join(self.data_raw_dir, f"session_{i}.jsonl")
            with open(session_file, 'w') as f:
                for j in range(5):
                    record = {
                        "participant_id": f"P{i}",
                        "stimulus_id": f"S{j}",
                        "origin": "AI",
                        "timestamp": "2024-01-01T00:00:00",
                        "BISS_score": 5,
                        "INCOM_score": 10,
                        "usage_frequency": 2.5
                    }
                    f.write(json.dumps(record) + "\n")
        
        # Create one incomplete session (missing one field)
        session_file = os.path.join(self.data_raw_dir, "session_20.jsonl")
        with open(session_file, 'w') as f:
            record = {
                "participant_id": "P20",
                "stimulus_id": "S0",
                "origin": "AI",
                "timestamp": "2024-01-01T00:00:00",
                # Missing BISS_score
                "INCOM_score": 10,
                "usage_frequency": 2.5
            }
            f.write(json.dumps(record) + "\n")
        
        # 19 complete out of 20 = 95%
        is_valid, metrics = check_data_completeness(self.data_raw_dir)
        
        assert is_valid is True
        assert metrics['completeness'] == 0.95
        assert metrics['complete_sessions'] == 19
        assert metrics['total_sessions'] == 20

    def test_completeness_fails(self):
        """Test FR-007: Completeness check fails when < 95% complete."""
        # Create 10 sessions, 5 complete, 5 incomplete
        for i in range(5):
            session_file = os.path.join(self.data_raw_dir, f"session_{i}.jsonl")
            with open(session_file, 'w') as f:
                record = {
                    "participant_id": f"P{i}",
                    "stimulus_id": "S0",
                    "origin": "AI",
                    "timestamp": "2024-01-01T00:00:00",
                    "BISS_score": 5,
                    "INCOM_score": 10,
                    "usage_frequency": 2.5
                }
                f.write(json.dumps(record) + "\n")
        
        for i in range(5, 10):
            session_file = os.path.join(self.data_raw_dir, f"session_{i}.jsonl")
            with open(session_file, 'w') as f:
                record = {
                    "participant_id": f"P{i}",
                    # Missing required fields
                    "INCOM_score": 10,
                }
                f.write(json.dumps(record) + "\n")
        
        # 5 complete out of 10 = 50%
        with pytest.raises(DataValidationError) as exc_info:
            check_data_completeness(self.data_raw_dir)
        
        assert "below threshold" in str(exc_info.value).lower()

    def test_completeness_no_data(self):
        """Test FR-007: Completeness check fails when no data found."""
        with pytest.raises(DataValidationError) as exc_info:
            check_data_completeness(self.data_raw_dir)
        
        assert "no session files found" in str(exc_info.value).lower()

    def test_metadata_matching_passes(self):
        """Test FR-008: Metadata matching passes when all matched."""
        # Create AI metadata
        ai_meta_path = os.path.join(self.stimuli_ai_dir, "metadata.json")
        ai_data = [
            {"stimulus_id": "AI_0", "origin": "AI", "pose": "front", "lighting": "bright", "image_path": "ai/0.jpg"},
            {"stimulus_id": "AI_1", "origin": "AI", "pose": "side", "lighting": "dim", "image_path": "ai/1.jpg"},
        ]
        with open(ai_meta_path, 'w') as f:
            json.dump(ai_data, f)
        
        # Create Human metadata with matching pose/lighting
        human_meta_path = os.path.join(self.stimuli_human_dir, "metadata.json")
        human_data = [
            {"stimulus_id": "H_0", "origin": "Human", "pose": "front", "lighting": "bright", "image_path": "human/0.jpg"},
            {"stimulus_id": "H_1", "origin": "Human", "pose": "side", "lighting": "dim", "image_path": "human/1.jpg"},
        ]
        with open(human_meta_path, 'w') as f:
            json.dump(human_data, f)
        
        is_valid, metrics = check_metadata_matching(self.stimuli_ai_dir, self.stimuli_human_dir)
        
        assert is_valid is True
        assert metrics['matched_pairs'] == 2
        assert metrics['unmatched_ai'] == 0
        assert metrics['unmatched_human'] == 0
        assert metrics['match_rate'] == 1.0

    def test_metadata_matching_fails_unmatched(self):
        """Test FR-008: Metadata matching fails when unmatched items exist."""
        # Create AI metadata
        ai_meta_path = os.path.join(self.stimuli_ai_dir, "metadata.json")
        ai_data = [
            {"stimulus_id": "AI_0", "origin": "AI", "pose": "front", "lighting": "bright", "image_path": "ai/0.jpg"},
            {"stimulus_id": "AI_1", "origin": "AI", "pose": "side", "lighting": "dim", "image_path": "ai/1.jpg"},
            {"stimulus_id": "AI_2", "origin": "AI", "pose": "back", "lighting": "bright", "image_path": "ai/2.jpg"}, # Unmatched
        ]
        with open(ai_meta_path, 'w') as f:
            json.dump(ai_data, f)
        
        # Create Human metadata missing one match
        human_meta_path = os.path.join(self.stimuli_human_dir, "metadata.json")
        human_data = [
            {"stimulus_id": "H_0", "origin": "Human", "pose": "front", "lighting": "bright", "image_path": "human/0.jpg"},
            {"stimulus_id": "H_1", "origin": "Human", "pose": "side", "lighting": "dim", "image_path": "human/1.jpg"},
        ]
        with open(human_meta_path, 'w') as f:
            json.dump(human_data, f)
        
        with pytest.raises(DataValidationError) as exc_info:
            check_metadata_matching(self.stimuli_ai_dir, self.stimuli_human_dir)
        
        assert "unmatched" in str(exc_info.value).lower()

    def test_metadata_matching_no_data(self):
        """Test FR-008: Metadata matching fails when no metadata found."""
        with pytest.raises(DataValidationError) as exc_info:
            check_metadata_matching(self.stimuli_ai_dir, self.stimuli_human_dir)
        
        # Should fail because metadata files don't exist
        assert "metadata" in str(exc_info.value).lower() or "validation" in str(exc_info.value).lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
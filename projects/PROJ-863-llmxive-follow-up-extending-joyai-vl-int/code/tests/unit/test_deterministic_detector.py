"""
Unit tests for Deterministic Rule-Based Visual Detector (T026a)

Verifies:
1. Strict thresholds are applied without noise.
2. Correct identification of critical events based on visual rules.
3. Deterministic behavior (same input -> same output).
"""
import json
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.baseline.deterministic_detector import (
    DeterministicRuleEngine, 
    DeterministicPrediction, 
    run_deterministic_detector
)

class TestDeterministicRuleEngine:
    """Tests for the core rule engine logic."""

    def test_falling_state_triggers_critical(self):
        """Rule: activity_state == 'falling' -> is_critical=True"""
        engine = DeterministicRuleEngine()
        frame = {
            "frame_id": "f1",
            "timestamp": 1.0,
            "activity_state": "falling",
            "person_y": 0.5,
            "velocity": 0.5
        }
        pred = engine.evaluate_frame(frame)
        assert pred.is_critical is True
        assert pred.rule_triggered == "state_falling"
        assert pred.confidence == 1.0

    def test_high_velocity_low_y_triggers_critical(self):
        """Rule: person_y > 0.8 AND velocity > 2.0 -> is_critical=True"""
        engine = DeterministicRuleEngine()
        frame = {
            "frame_id": "f2",
            "timestamp": 2.0,
            "activity_state": "walking",
            "person_y": 0.85,
            "velocity": 2.5
        }
        pred = engine.evaluate_frame(frame)
        assert pred.is_critical is True
        assert pred.rule_triggered == "velocity_y_threshold"

    def test_high_velocity_high_y_is_safe(self):
        """Rule: High velocity but high Y (standing) -> is_critical=False"""
        engine = DeterministicRuleEngine()
        frame = {
            "frame_id": "f3",
            "timestamp": 3.0,
            "activity_state": "jumping",
            "person_y": 0.2,  # High up
            "velocity": 5.0
        }
        pred = engine.evaluate_frame(frame)
        assert pred.is_critical is False
        assert pred.rule_triggered == "none"

    def test_low_velocity_low_y_is_safe(self):
        """Rule: Low velocity, low Y -> is_critical=False (sitting/lying still)"""
        engine = DeterministicRuleEngine()
        frame = {
            "frame_id": "f4",
            "timestamp": 4.0,
            "activity_state": "sitting",
            "person_y": 0.85,
            "velocity": 0.1
        }
        pred = engine.evaluate_frame(frame)
        assert pred.is_critical is False
        assert pred.rule_triggered == "none"

    def test_motionless_duration_trigger(self):
        """Rule: motionless for > 5s -> is_critical=True"""
        engine = DeterministicRuleEngine()
        
        # Start motionless
        frame1 = {
            "frame_id": "f5",
            "timestamp": 5.0,
            "activity_state": "motionless",
            "person_y": 0.8,
            "velocity": 0.0
        }
        pred1 = engine.evaluate_frame(frame1)
        assert pred1.is_critical is False  # Not enough duration yet

        # Continue motionless for 6 seconds total
        frame2 = {
            "frame_id": "f6",
            "timestamp": 11.0, # 6 seconds later
            "activity_state": "motionless",
            "person_y": 0.8,
            "velocity": 0.0
        }
        pred2 = engine.evaluate_frame(frame2)
        assert pred2.is_critical is True
        assert pred2.rule_triggered == "motionless_duration"

    def test_motionless_reset(self):
        """Rule: Motionless state breaks, then resumes -> timer resets"""
        engine = DeterministicRuleEngine()
        
        # Start motionless
        frame1 = {
            "frame_id": "f7",
            "timestamp": 1.0,
            "activity_state": "motionless",
            "person_y": 0.8,
            "velocity": 0.0
        }
        engine.evaluate_frame(frame1)

        # Break motionless
        frame2 = {
            "frame_id": "f7", # Same ID for tracking logic in this simple test
            "timestamp": 2.0,
            "activity_state": "walking",
            "person_y": 0.5,
            "velocity": 1.0
        }
        engine.evaluate_frame(frame2)

        # Resume motionless immediately (should not trigger yet)
        frame3 = {
            "frame_id": "f8", # New ID to simulate new sequence
            "timestamp": 3.0,
            "activity_state": "motionless",
            "person_y": 0.8,
            "velocity": 0.0
        }
        pred3 = engine.evaluate_frame(frame3)
        assert pred3.is_critical is False

    def test_deterministic_confidence(self):
        """Rule: Confidence must always be 1.0"""
        engine = DeterministicRuleEngine()
        frame = {
            "frame_id": "f8",
            "timestamp": 1.0,
            "activity_state": "falling"
        }
        pred = engine.evaluate_frame(frame)
        assert pred.confidence == 1.0

class TestDeterministicDetectorIntegration:
    """Integration tests for the file processing logic."""

    def test_run_detector_creates_output(self, tmp_path):
        """Verify run_deterministic_detector creates output file."""
        input_manifest = tmp_path / "manifest.jsonl"
        output_file = tmp_path / "predictions.jsonl"
        
        # Create minimal manifest
        data = [
            {"frame_id": "1", "timestamp": 1.0, "activity_state": "falling", "person_y": 0.9, "velocity": 3.0},
            {"frame_id": "2", "timestamp": 2.0, "activity_state": "walking", "person_y": 0.5, "velocity": 1.0}
        ]
        with open(input_manifest, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        
        count = run_deterministic_detector(str(input_manifest), str(output_file))
        
        assert count == 2
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        # Check first frame (falling)
        pred1 = json.loads(lines[0])
        assert pred1["is_critical"] is True
        assert pred1["rule_triggered"] == "state_falling"
        
        # Check second frame (walking)
        pred2 = json.loads(lines[1])
        assert pred2["is_critical"] is False
        assert pred2["rule_triggered"] == "none"

    def test_run_detector_handles_empty_file(self, tmp_path):
        """Verify handling of empty manifest."""
        input_manifest = tmp_path / "manifest.jsonl"
        output_file = tmp_path / "predictions.jsonl"
        
        input_manifest.touch() # Create empty file
        
        count = run_deterministic_detector(str(input_manifest), str(output_file))
        assert count == 0
        assert output_file.exists()
        assert output_file.stat().st_size == 0

    def test_run_detector_handles_missing_input(self, tmp_path):
        """Verify FileNotFoundError on missing input."""
        output_file = tmp_path / "predictions.jsonl"
        
        with pytest.raises(FileNotFoundError):
            run_deterministic_detector("non_existent_path.jsonl", str(output_file))

    def test_run_detector_skips_invalid_json(self, tmp_path):
        """Verify invalid JSON lines are skipped."""
        input_manifest = tmp_path / "manifest.jsonl"
        output_file = tmp_path / "predictions.jsonl"
        
        data = [
            {"frame_id": "1", "timestamp": 1.0, "activity_state": "falling"},
            "invalid json line",
            {"frame_id": "2", "timestamp": 2.0, "activity_state": "walking"}
        ]
        with open(input_manifest, 'w') as f:
            for item in data:
                if isinstance(item, dict):
                    f.write(json.dumps(item) + '\n')
                else:
                    f.write(item + '\n')
        
        count = run_deterministic_detector(str(input_manifest), str(output_file))
        
        # Should process 2 valid frames
        assert count == 2
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 2
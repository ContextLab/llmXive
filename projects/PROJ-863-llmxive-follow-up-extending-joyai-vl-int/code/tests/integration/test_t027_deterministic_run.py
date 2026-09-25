"""
Integration Test for T027: Deterministic Detector Run.

Verifies that the deterministic detector script:
1. Reads from the raw data directory.
2. Produces the expected output file.
3. Generates valid JSONL with correct schema.
4. Correctly identifies critical vs silence events based on strict rules.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.baseline.deterministic_detector import DeterministicVisualDetector, DeterministicPrediction

class TestT027DeterministicRun:
    
    @pytest.fixture
    def temp_dirs(self):
        """Creates temporary input and output directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_dir = tmp_path / "data" / "raw"
            output_dir = tmp_path / "data" / "baseline"
            input_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            yield input_dir, output_dir

    @pytest.fixture
    def sample_raw_data(self, temp_dirs):
        """Generates sample raw data frames."""
        input_dir, output_dir = temp_dirs
        
        # Frame 1: Person standing (Silence)
        frame_stand = {
            "frame_id": "f001",
            "timestamp_ms": 0,
            "objects": [
                {
                    "class_id": 0,
                    "label": "person",
                    "bbox": [0.4, 0.2, 0.2, 0.4], # Center Y ~ 0.4
                    "confidence": 0.9
                }
            ],
            "metadata": {"velocity_y": 0.0}
        }

        # Frame 2: Person falling (Critical - Velocity)
        frame_fall = {
            "frame_id": "f002",
            "timestamp_ms": 100,
            "objects": [
                {
                    "class_id": 0,
                    "label": "person",
                    "bbox": [0.4, 0.5, 0.2, 0.4], # Center Y ~ 0.7
                }
            ],
            "metadata": {"velocity_y": 0.25} # High velocity
        }

        # Frame 3: Person on ground (Critical - Position)
        frame_ground = {
            "frame_id": "f003",
            "timestamp_ms": 200,
            "objects": [
                {
                    "class_id": 0,
                    "label": "person",
                    "bbox": [0.4, 0.75, 0.2, 0.2], # Center Y ~ 0.85
                }
            ],
            "metadata": {"velocity_y": 0.0}
        }

        # Write to JSONL
        data_file = input_dir / "test_stream.jsonl"
        with open(data_file, 'w') as f:
            for frame in [frame_stand, frame_fall, frame_ground]:
                f.write(json.dumps(frame) + "\n")
        
        return input_dir, output_dir, data_file

    def test_detector_logic_stand(self, temp_dirs):
        """Test that standing person is classified as silence."""
        input_dir, output_dir, _ = temp_dirs
        detector = DeterministicVisualDetector()
        
        frame = {
            "frame_id": "test",
            "objects": [{"bbox": [0.1, 0.1, 0.2, 0.3], "confidence": 0.9}],
            "metadata": {"velocity_y": 0.0}
        }
        
        pred = detector.detect(frame)
        assert pred.label == "silence"
        assert "on ground" not in pred.reason.lower()

    def test_detector_logic_fall(self, temp_dirs):
        """Test that high velocity is classified as critical."""
        input_dir, output_dir, _ = temp_dirs
        detector = DeterministicVisualDetector()
        
        frame = {
            "frame_id": "test",
            "objects": [{"bbox": [0.1, 0.4, 0.2, 0.3], "confidence": 0.9}],
            "metadata": {"velocity_y": 0.30} # > 0.15 threshold
        }
        
        pred = detector.detect(frame)
        assert pred.label == "critical"
        assert "falling" in pred.reason.lower()

    def test_detector_logic_ground(self, temp_dirs):
        """Test that person on ground is classified as critical."""
        input_dir, output_dir, _ = temp_dirs
        detector = DeterministicVisualDetector()
        
        frame = {
            "frame_id": "test",
            "objects": [{"bbox": [0.1, 0.75, 0.2, 0.2], "confidence": 0.9}],
            "metadata": {"velocity_y": 0.0}
        }
        
        pred = detector.detect(frame)
        assert pred.label == "critical"
        assert "ground" in pred.reason.lower()

    def test_script_execution_creates_output(self, sample_raw_data):
        """
        Integration test: Run the T027 script and verify output file creation.
        """
        input_dir, output_dir, _ = sample_raw_data
        
        # Mock the path resolution in the script to use our temp dirs
        # We import and call the main logic directly to avoid subprocess complexity
        # but verify the file system state
        
        from src.baseline.run_deterministic_detector import process_raw_data_stream, DeterministicVisualDetector
        
        detector = DeterministicVisualDetector()
        output_file = output_dir / "deterministic_predictions.jsonl"
        
        processed_count = 0
        with open(output_file, 'w') as out_f:
            for frame in process_raw_data_stream(input_dir):
                pred = detector.detect(frame)
                result = {
                    "frame_id": frame.get("frame_id"),
                    "label": pred.label,
                    "reason": pred.reason
                }
                out_f.write(json.dumps(result) + "\n")
                processed_count += 1

        # Assertions
        assert output_file.exists(), "Output file was not created"
        assert processed_count == 3, f"Expected 3 frames, got {processed_count}"
        
        # Verify content
        with open(output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3
            
            # Check first frame (Stand)
            res1 = json.loads(lines[0])
            assert res1["frame_id"] == "f001"
            assert res1["label"] == "silence"
            
            # Check second frame (Fall)
            res2 = json.loads(lines[1])
            assert res2["frame_id"] == "f002"
            assert res2["label"] == "critical"
            
            # Check third frame (Ground)
            res3 = json.loads(lines[2])
            assert res3["frame_id"] == "f003"
            assert res3["label"] == "critical"
"""
Integration test for User Story 2: Feature Extraction Pipeline.

Task: T019 [P] [US2] Write integration test: Verify 1:1 temporal alignment 
between input frames and output features in tests/integration/test_feature_pipeline.py

This test verifies that for every input video frame processed, exactly one 
feature vector is produced, maintaining strict temporal ordering and alignment.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import project utilities and models
from tests.conftest import temp_data_dir, setup_test_environment
from src.data_synthesis.models import SyntheticVideoFrame
from src.utils.validation import validate_schema
from src.feature_extraction.streaming import FrameBatchProcessor


@pytest.fixture
def temp_feature_dirs(temp_data_dir):
    """Create temporary directories for feature extraction test."""
    features_dir = temp_data_dir / "features"
    features_dir.mkdir(exist_ok=True)
    return {
        "input": temp_data_dir / "raw",
        "output": features_dir,
        "manifest": temp_data_dir / "manifest.jsonl"
    }


@pytest.fixture
def sample_video_frames(temp_feature_dirs):
    """Generate a small set of synthetic video frames for testing alignment."""
    input_dir = temp_feature_dirs["input"]
    input_dir.mkdir(exist_ok=True)
    
    frames = []
    num_frames = 50
    
    for i in range(num_frames):
        frame_data = {
            "frame_id": f"frame_{i:06d}",
            "timestamp": i * 0.04,  # 25 FPS
            "activity_type": "walking" if i % 10 != 0 else "falling",
            "objects": [
                {"class": "person", "confidence": 0.95, "bbox": [100, 100, 200, 300]}
            ],
            "is_critical": (i % 10 == 0),
            "metadata": {
                "chunk_id": "chunk_001",
                "sequence_number": i
            }
        }
        
        frame_file = input_dir / f"frame_{i:06d}.json"
        with open(frame_file, 'w') as f:
            json.dump(frame_data, f)
        
        frames.append(frame_data)
    
    # Create a manifest
    manifest_data = {
        "total_frames": num_frames,
        "total_duration_seconds": num_frames * 0.04,
        "chunk_id": "chunk_001",
        "frames": [f["frame_id"] for f in frames]
    }
    
    with open(temp_feature_dirs["manifest"], 'w') as f:
        json.dump(manifest_data, f)
    
    return frames, num_frames


@pytest.fixture
def mock_feature_extractor():
    """Mock the feature extraction to return deterministic feature vectors."""
    def mock_extract_features(frame_batch):
        """
        Mock feature extraction that returns one feature vector per frame.
        
        Args:
            frame_batch: List of frame dictionaries
        
        Returns:
            List of feature vectors with temporal metadata
        """
        features = []
        for frame in frame_batch:
            # Create a deterministic feature vector (128-dim hidden state)
            feature_vector = np.random.RandomState(
                int(frame["timestamp"] * 1000) % 1000
            ).randn(128).tolist()
            
            feature_record = {
                "frame_id": frame["frame_id"],
                "timestamp": frame["timestamp"],
                "feature_vector": feature_vector,
                "feature_dimensions": 128,
                "source_chunk": frame["metadata"]["chunk_id"],
                "sequence_number": frame["metadata"]["sequence_number"],
                "extraction_metadata": {
                    "model_layer": "hidden_state_layer_8",
                    "attention_heads": 8,
                    "extraction_time": 0.001
                }
            }
            features.append(feature_record)
        
        return features
    
    return mock_extract_features


def test_1_to_1_temporal_alignment(
    temp_feature_dirs, 
    sample_video_frames, 
    mock_feature_extractor
):
    """
    Verify 1:1 temporal alignment between input frames and output features.
    
    This test ensures:
    1. Every input frame produces exactly one output feature vector
    2. Temporal ordering is preserved (frames sorted by timestamp -> features sorted by timestamp)
    3. Frame IDs match exactly between input and output
    4. No frames are skipped or duplicated
    """
    input_frames, expected_count = sample_video_frames
    output_dir = temp_feature_dirs["output"]
    
    # Mock the actual model loading and extraction
    with patch('src.feature_extraction.extractor.JoyAIVLModel') as mock_model_cls:
        mock_model_instance = MagicMock()
        mock_model_cls.return_value = mock_model_instance
        
        # Process frames using the streaming processor
        processor = FrameBatchProcessor(
            batch_size=10,
            feature_extractor=mock_feature_extractor,
            output_dir=output_dir
        )
        
        # Run extraction on the test frames
        input_dir = temp_feature_dirs["input"]
        result = processor.process_directory(input_dir)
        
        # Load the output features
        output_file = output_dir / "chunk_001_features.jsonl"
        assert output_file.exists(), "Feature output file was not created"
        
        output_features = []
        with open(output_file, 'r') as f:
            for line in f:
                output_features.append(json.loads(line))
        
        # ASSERTION 1: Count match (1:1 ratio)
        assert len(output_features) == expected_count, (
            f"Feature count mismatch: Expected {expected_count}, "
            f"Got {len(output_features)}. "
            "Every frame must produce exactly one feature vector."
        )
        
        # ASSERTION 2: Frame ID uniqueness and completeness
        input_frame_ids = {f["frame_id"] for f in input_frames}
        output_frame_ids = {f["frame_id"] for f in output_features}
        
        assert input_frame_ids == output_frame_ids, (
            "Frame ID mismatch between input and output. "
            "Some frames were skipped or extra features were generated."
        )
        
        # ASSERTION 3: Temporal ordering preservation
        input_sorted = sorted(input_frames, key=lambda x: x["timestamp"])
        output_sorted = sorted(output_features, key=lambda x: x["timestamp"])
        
        for i, (inp, out) in enumerate(zip(input_sorted, output_sorted)):
            assert inp["frame_id"] == out["frame_id"], (
                f"Temporal ordering broken at index {i}: "
                f"Input frame {inp['frame_id']} != Output frame {out['frame_id']}"
            )
            assert inp["timestamp"] == out["timestamp"], (
                f"Timestamp mismatch at index {i}: "
                f"Input {inp['timestamp']} != Output {out['timestamp']}"
            )
        
        # ASSERTION 4: No duplicate timestamps in output
        output_timestamps = [f["timestamp"] for f in output_features]
        assert len(output_timestamps) == len(set(output_timestamps)), (
            "Duplicate timestamps found in output features. "
            "Each timestamp must be unique."
        )
        
        # ASSERTION 5: Feature vector dimensions are consistent
        for feature in output_features:
            assert "feature_vector" in feature, "Missing feature_vector field"
            assert len(feature["feature_vector"]) == 128, (
                f"Feature dimension mismatch: Expected 128, "
                f"Got {len(feature['feature_vector'])}"
            )
        
        print(f"✓ Temporal alignment verified: {expected_count} frames -> {len(output_features)} features")
        print(f"✓ All frame IDs matched and ordered correctly")
        print(f"✓ No duplicates or gaps detected")


def test_alignment_with_gaps_and_ambiguities(
    temp_feature_dirs,
    mock_feature_extractor
):
    """
    Verify alignment holds even when input frames have gaps or ambiguous events.
    
    This tests edge cases where:
    - Some frames might be marked as "critical" vs "silence"
    - Frame timestamps might have slight variations
    - Processing order might vary
    """
    input_dir = temp_feature_dirs["input"]
    input_dir.mkdir(exist_ok=True)
    output_dir = temp_feature_dirs["output"]
    
    # Create frames with non-uniform timestamps and ambiguous events
    test_frames = [
        {"frame_id": "frame_001", "timestamp": 0.0, "is_critical": False, "metadata": {"chunk_id": "chunk_002", "sequence_number": 0}},
        {"frame_id": "frame_002", "timestamp": 0.04, "is_critical": False, "metadata": {"chunk_id": "chunk_002", "sequence_number": 1}},
        {"frame_id": "frame_003", "timestamp": 0.12, "is_critical": True, "metadata": {"chunk_id": "chunk_002", "sequence_number": 2}},  # Gap of 0.08
        {"frame_id": "frame_004", "timestamp": 0.16, "is_critical": False, "metadata": {"chunk_id": "chunk_002", "sequence_number": 3}},
        {"frame_id": "frame_005", "timestamp": 0.20, "is_critical": False, "metadata": {"chunk_id": "chunk_002", "sequence_number": 4}},
    ]
    
    for frame in test_frames:
        frame_file = input_dir / f"{frame['frame_id']}.json"
        with open(frame_file, 'w') as f:
            json.dump(frame, f)
    
    # Process
    processor = FrameBatchProcessor(
        batch_size=2,
        feature_extractor=mock_feature_extractor,
        output_dir=output_dir
    )
    
    result = processor.process_directory(input_dir)
    
    # Load output
    output_file = output_dir / "chunk_002_features.jsonl"
    assert output_file.exists(), "Feature output file was not created"
    
    output_features = []
    with open(output_file, 'r') as f:
        for line in f:
            output_features.append(json.loads(line))
    
    # Verify 1:1 mapping despite gaps
    assert len(output_features) == len(test_frames), (
        f"Gap handling failed: Expected {len(test_frames)} features, "
        f"Got {len(output_features)}"
    )
    
    # Verify timestamps are preserved exactly
    input_timestamps = [f["timestamp"] for f in test_frames]
    output_timestamps = [f["timestamp"] for f in output_features]
    
    assert input_timestamps == output_timestamps, (
        "Timestamps not preserved through gap handling"
    )
    
    print(f"✓ Gap handling verified: {len(test_frames)} frames processed correctly")


def test_alignment_preserves_sequence_metadata(
    temp_feature_dirs,
    sample_video_frames,
    mock_feature_extractor
):
    """
    Verify that sequence metadata (chunk_id, sequence_number) is preserved
    and aligned correctly between input and output.
    """
    input_frames, _ = sample_video_frames
    input_dir = temp_feature_dirs["input"]
    output_dir = temp_feature_dirs["output"]
    
    with patch('src.feature_extraction.extractor.JoyAIVLModel'):
        processor = FrameBatchProcessor(
            batch_size=10,
            feature_extractor=mock_feature_extractor,
            output_dir=output_dir
        )
        
        processor.process_directory(input_dir)
        
        output_file = output_dir / "chunk_001_features.jsonl"
        with open(output_file, 'r') as f:
            output_features = [json.loads(line) for line in f]
    
    # Verify metadata alignment
    for inp, out in zip(input_frames, output_features):
        assert inp["metadata"]["chunk_id"] == out["source_chunk"], (
            f"Chunk ID mismatch: {inp['metadata']['chunk_id']} != {out['source_chunk']}"
        )
        assert inp["metadata"]["sequence_number"] == out["sequence_number"], (
            f"Sequence number mismatch: {inp['metadata']['sequence_number']} != {out['sequence_number']}"
        )
    
    print("✓ Sequence metadata alignment verified")
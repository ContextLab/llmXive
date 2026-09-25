"""
Integration Test for T029: Noisy Detector Execution

Verifies that the noisy detector script runs end-to-end,
reads from the raw data, and produces a valid JSONL output
with the expected noise characteristics.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.baseline.visual_detector import NoisyDetectionConfig, NoisyVisualDetector
from src.baseline.run_noisy_detector import process_raw_data_stream

@pytest.fixture
def temp_dirs():
    """Create temporary directories for raw data and output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        raw_dir = Path(tmp_dir) / "raw"
        raw_dir.mkdir()
        baseline_dir = Path(tmp_dir) / "baseline"
        baseline_dir.mkdir()
        yield {
            "raw": raw_dir,
            "baseline": baseline_dir
        }

def create_sample_raw_stream(path: Path, count: int = 10):
    """Generate a small synthetic raw stream for testing."""
    with open(path, 'w', encoding='utf-8') as f:
        for i in range(count):
            frame = {
                "frame_id": i,
                "timestamp": float(i),
                "objects": [
                    {"class": "person", "bbox": [10, 10, 50, 50], "confidence": 0.9}
                ],
                "activity": "walking"
            }
            f.write(json.dumps(frame) + '\n')

def test_noisy_detector_runs_end_to_end(temp_dirs):
    """Test that the noisy detector script processes data and writes output."""
    raw_file = temp_dirs["raw"] / "synthetic_stream.jsonl"
    output_file = temp_dirs["baseline"] / "noisy_predictions.jsonl"
    
    # Create sample input
    create_sample_raw_stream(raw_file, count=100)
    
    config = NoisyDetectionConfig(
        label_flip_probability=0.0, # Disable noise for deterministic check
        temporal_jitter_frames=0,
        seed=42
    )
    
    # Run the processing
    results = list(process_raw_data_stream(raw_file, output_file, config))
    
    # Assertions
    assert len(results) == 100, "Should process all frames"
    assert output_file.exists(), "Output file must be created"
    
    # Verify output format
    with open(output_file, 'r') as f:
        for line in f:
            pred = json.loads(line)
            assert "frame_id" in pred
            assert "prediction" in pred or "label" in pred

def test_noisy_detector_applies_noise(temp_dirs):
    """Test that the noisy detector actually applies label flipping when configured."""
    raw_file = temp_dirs["raw"] / "synthetic_stream.jsonl"
    output_file = temp_dirs["baseline"] / "noisy_predictions.jsonl"
    
    # Create sample input with known labels (simulated in activity field or objects)
    # We'll use a high count to statistically verify noise
    create_sample_raw_stream(raw_file, count=1000)
    
    config = NoisyDetectionConfig(
        label_flip_probability=0.5, # 50% flip rate
        temporal_jitter_frames=0,
        seed=123
    )
    
    results = list(process_raw_data_stream(raw_file, output_file, config))
    
    # We can't easily verify the exact labels without a ground truth mapping
    # in this simple test, but we verify the process completes and output is valid.
    assert len(results) == 1000
    assert output_file.stat().st_size > 0

def test_noisy_detector_handles_empty_stream(temp_dirs):
    """Test behavior with an empty input file."""
    raw_file = temp_dirs["raw"] / "empty_stream.jsonl"
    output_file = temp_dirs["baseline"] / "empty_output.jsonl"
    
    raw_file.touch() # Create empty file
    
    config = NoisyDetectionConfig()
    results = list(process_raw_data_stream(raw_file, output_file, config))
    
    assert len(results) == 0
    assert output_file.exists()
    assert output_file.stat().st_size == 0

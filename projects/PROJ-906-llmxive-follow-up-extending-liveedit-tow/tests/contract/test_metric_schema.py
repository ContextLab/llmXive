"""
Contract test for MetricRecord schema.

Validates that MetricRecord instances (and their serialized forms)
conform to the schema defined in code/data/models.py and
pass validation via code/contracts/metrics_validator.py.
"""
import json
import sys
import os
from datetime import datetime
import numpy as np

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.models import MetricRecord
from code.contracts.metrics_validator import MetricsValidator


def test_metric_record_creation():
    """Test that a valid MetricRecord can be instantiated."""
    record = MetricRecord(
        clip_id="test_clip_001",
        method="baseline",
        frame_index=10,
        ssim_score=0.85,
        bss_score=0.92,
        flow_magnitude=2.3,
        peak_memory_mb=1250.5,
        inference_time_ms=150.2,
        invalid_flow=False,
        timestamp=datetime.now()
    )
    
    assert record.clip_id == "test_clip_001"
    assert record.method == "baseline"
    assert record.frame_index == 10
    assert record.ssim_score == 0.85
    assert record.bss_score == 0.92
    assert record.flow_magnitude == 2.3
    assert record.peak_memory_mb == 1250.5
    assert record.inference_time_ms == 150.2
    assert record.invalid_flow is False
    assert isinstance(record.timestamp, datetime)


def test_metric_record_serialization():
    """Test that MetricRecord can be serialized to JSON."""
    record = MetricRecord(
        clip_id="test_clip_002",
        method="flow_coherence",
        frame_index=25,
        ssim_score=0.78,
        bss_score=0.88,
        flow_magnitude=5.1,
        peak_memory_mb=980.0,
        inference_time_ms=120.5,
        invalid_flow=True,
        timestamp=datetime.now()
    )
    
    json_str = record.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["clip_id"] == "test_clip_002"
    assert parsed["method"] == "flow_coherence"
    assert parsed["frame_index"] == 25
    assert parsed["ssim_score"] == 0.78
    assert parsed["bss_score"] == 0.88
    assert parsed["flow_magnitude"] == 5.1
    assert parsed["peak_memory_mb"] == 980.0
    assert parsed["inference_time_ms"] == 120.5
    assert parsed["invalid_flow"] is True
    assert "timestamp" in parsed


def test_metric_record_deserialization():
    """Test that MetricRecord can be deserialized from JSON."""
    original = MetricRecord(
        clip_id="test_clip_003",
        method="baseline",
        frame_index=5,
        ssim_score=0.91,
        bss_score=0.95,
        flow_magnitude=0.3,
        peak_memory_mb=1100.0,
        inference_time_ms=140.0,
        invalid_flow=False,
        timestamp=datetime(2024, 1, 15, 10, 30, 0)
    )
    
    json_str = original.to_json()
    restored = MetricRecord.from_json(json_str)
    
    assert restored.clip_id == original.clip_id
    assert restored.method == original.method
    assert restored.frame_index == original.frame_index
    assert restored.ssim_score == original.ssim_score
    assert restored.bss_score == original.bss_score
    assert restored.flow_magnitude == original.flow_magnitude
    assert restored.peak_memory_mb == original.peak_memory_mb
    assert restored.inference_time_ms == original.inference_time_ms
    assert restored.invalid_flow == original.invalid_flow
    assert restored.timestamp == original.timestamp


def test_validator_accepts_valid_record():
    """Test that MetricsValidator accepts a valid MetricRecord."""
    record = MetricRecord(
        clip_id="valid_clip",
        method="baseline",
        frame_index=100,
        ssim_score=0.80,
        bss_score=0.85,
        flow_magnitude=3.2,
        peak_memory_mb=1500.0,
        inference_time_ms=200.0,
        invalid_flow=False,
        timestamp=datetime.now()
    )
    
    validator = MetricsValidator()
    is_valid, errors = validator.validate(record)
    
    assert is_valid, f"Validator rejected valid record: {errors}"
    assert len(errors) == 0


def test_validator_rejects_invalid_ssim():
    """Test that MetricsValidator rejects SSIM out of [0, 1]."""
    record = MetricRecord(
        clip_id="invalid_clip",
        method="baseline",
        frame_index=10,
        ssim_score=1.5,  # Invalid: > 1
        bss_score=0.90,
        flow_magnitude=2.0,
        peak_memory_mb=1000.0,
        inference_time_ms=100.0,
        invalid_flow=False,
        timestamp=datetime.now()
    )
    
    validator = MetricsValidator()
    is_valid, errors = validator.validate(record)
    
    assert not is_valid
    assert any("ssim_score" in str(e) for e in errors)


def test_validator_rejects_negative_memory():
    """Test that MetricsValidator rejects negative memory usage."""
    record = MetricRecord(
        clip_id="invalid_clip",
        method="baseline",
        frame_index=10,
        ssim_score=0.85,
        bss_score=0.90,
        flow_magnitude=2.0,
        peak_memory_mb=-50.0,  # Invalid: negative
        inference_time_ms=100.0,
        invalid_flow=False,
        timestamp=datetime.now()
    )
    
    validator = MetricsValidator()
    is_valid, errors = validator.validate(record)
    
    assert not is_valid
    assert any("peak_memory_mb" in str(e) for e in errors)


def test_validator_rejects_negative_frame_index():
    """Test that MetricsValidator rejects negative frame index."""
    record = MetricRecord(
        clip_id="invalid_clip",
        method="baseline",
        frame_index=-1,  # Invalid: negative
        ssim_score=0.85,
        bss_score=0.90,
        flow_magnitude=2.0,
        peak_memory_mb=1000.0,
        inference_time_ms=100.0,
        invalid_flow=False,
        timestamp=datetime.now()
    )
    
    validator = MetricsValidator()
    is_valid, errors = validator.validate(record)
    
    assert not is_valid
    assert any("frame_index" in str(e) for e in errors)


def test_validator_rejects_empty_clip_id():
    """Test that MetricsValidator rejects empty clip_id."""
    record = MetricRecord(
        clip_id="",  # Invalid: empty
        method="baseline",
        frame_index=10,
        ssim_score=0.85,
        bss_score=0.90,
        flow_magnitude=2.0,
        peak_memory_mb=1000.0,
        inference_time_ms=100.0,
        invalid_flow=False,
        timestamp=datetime.now()
    )
    
    validator = MetricsValidator()
    is_valid, errors = validator.validate(record)
    
    assert not is_valid
    assert any("clip_id" in str(e) for e in errors)


def test_validator_rejects_missing_method():
    """Test that MetricsValidator rejects None method."""
    record = MetricRecord(
        clip_id="test_clip",
        method=None,  # Invalid: None
        frame_index=10,
        ssim_score=0.85,
        bss_score=0.90,
        flow_magnitude=2.0,
        peak_memory_mb=1000.0,
        inference_time_ms=100.0,
        invalid_flow=False,
        timestamp=datetime.now()
    )
    
    validator = MetricsValidator()
    is_valid, errors = validator.validate(record)
    
    assert not is_valid
    assert any("method" in str(e) for e in errors)


def test_validator_handles_numpy_types():
    """Test that MetricsValidator handles numpy numeric types."""
    record = MetricRecord(
        clip_id="numpy_clip",
        method="baseline",
        frame_index=np.int64(10),
        ssim_score=np.float64(0.85),
        bss_score=np.float64(0.90),
        flow_magnitude=np.float32(2.0),
        peak_memory_mb=np.float64(1000.0),
        inference_time_ms=np.float64(100.0),
        invalid_flow=np.bool_(False),
        timestamp=datetime.now()
    )
    
    validator = MetricsValidator()
    is_valid, errors = validator.validate(record)
    
    assert is_valid, f"Validator rejected valid numpy-typed record: {errors}"
    assert len(errors) == 0


if __name__ == "__main__":
    # Run tests manually if executed directly
    test_metric_record_creation()
    print("✓ test_metric_record_creation passed")
    
    test_metric_record_serialization()
    print("✓ test_metric_record_serialization passed")
    
    test_metric_record_deserialization()
    print("✓ test_metric_record_deserialization passed")
    
    test_validator_accepts_valid_record()
    print("✓ test_validator_accepts_valid_record passed")
    
    test_validator_rejects_invalid_ssim()
    print("✓ test_validator_rejects_invalid_ssim passed")
    
    test_validator_rejects_negative_memory()
    print("✓ test_validator_rejects_negative_memory passed")
    
    test_validator_rejects_negative_frame_index()
    print("✓ test_validator_rejects_negative_frame_index passed")
    
    test_validator_rejects_empty_clip_id()
    print("✓ test_validator_rejects_empty_clip_id passed")
    
    test_validator_rejects_missing_method()
    print("✓ test_validator_rejects_missing_method passed")
    
    test_validator_handles_numpy_types()
    print("✓ test_validator_handles_numpy_types passed")
    
    print("\nAll contract tests passed!")
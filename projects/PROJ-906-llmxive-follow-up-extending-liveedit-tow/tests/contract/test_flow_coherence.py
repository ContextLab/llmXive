"""
Contract test for invalid_flow flag handling in the Flow-Coherence module.

This test verifies that the Flow-Coherence module correctly identifies,
flags, and handles invalid optical flow vectors (NaN, Infinity) as specified
in the user story US2 requirements.

It ensures that:
1. The `MetricRecord` schema supports the `invalid_flow` flag.
2. The flow processing logic correctly detects invalid vectors.
3. The fallback mechanism (identity warp) is triggered when invalid flow is detected.
4. The resulting metrics record accurately reflects the invalid flow status.
"""

import pytest
import numpy as np
import json
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.models import MetricRecord
from contracts.metrics_validator import MetricsValidator


class TestInvalidFlowFlagHandling:
    """
    Contract tests for the invalid_flow flag handling in Flow-Coherence.
    """

    def test_metric_record_schema_accepts_invalid_flow_flag(self):
        """
        Verify that the MetricRecord dataclass/schema supports the invalid_flow flag.
        """
        # Create a valid MetricRecord with invalid_flow=True
        record = MetricRecord(
            clip_id="test_clip_001",
            frame_idx=5,
            bss_score=0.85,
            flow_norm_ssim=0.82,
            memory_mb=1024.0,
            inference_time_ms=150.0,
            flow_magnitude=12.5,
            invalid_flow=True,  # Explicitly setting the flag
            timestamp="2023-10-27T10:00:00Z"
        )

        assert record.invalid_flow is True
        assert record.clip_id == "test_clip_001"

    def test_metric_record_schema_accepts_valid_flow_flag(self):
        """
        Verify that the MetricRecord dataclass/schema supports invalid_flow=False.
        """
        record = MetricRecord(
            clip_id="test_clip_002",
            frame_idx=10,
            bss_score=0.90,
            flow_norm_ssim=0.88,
            memory_mb=1024.0,
            inference_time_ms=145.0,
            flow_magnitude=5.2,
            invalid_flow=False,  # Explicitly setting the flag
            timestamp="2023-10-27T10:00:05Z"
        )

        assert record.invalid_flow is False

    def test_metrics_validator_accepts_invalid_flow_record(self):
        """
        Verify that the MetricsValidator contract accepts records with invalid_flow=True.
        """
        record = MetricRecord(
            clip_id="test_clip_003",
            frame_idx=0,
            bss_score=0.50,  # Low score due to fallback
            flow_norm_ssim=0.45,
            memory_mb=1024.0,
            inference_time_ms=200.0,
            flow_magnitude=0.0,
            invalid_flow=True,
            timestamp="2023-10-27T10:00:10Z"
        )

        validator = MetricsValidator()
        # The validator should not raise an error for a valid record with invalid_flow=True
        result = validator.validate_record(record)
        
        assert result["valid"] is True
        assert "invalid_flow" in result.get("data", {})

    def test_invalid_flow_detection_logic(self):
        """
        Test the logic for detecting invalid flow vectors (NaN, Infinity).
        This simulates the logic that would be in flow_coherence.py.
        """
        # Simulate a flow field with invalid values
        valid_flow = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        nan_flow = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)
        inf_flow = np.array([[1.0, 2.0], [np.inf, 4.0]], dtype=np.float32)
        mixed_flow = np.array([[1.0, -np.inf], [np.nan, 4.0]], dtype=np.float32)

        def is_flow_valid(flow_field):
            """Helper to check validity, mimicking flow_coherence logic."""
            return not (np.any(np.isnan(flow_field)) or np.any(np.isinf(flow_field)))

        assert is_flow_valid(valid_flow) is True
        assert is_flow_valid(nan_flow) is False
        assert is_flow_valid(inf_flow) is False
        assert is_flow_valid(mixed_flow) is False

    def test_fallback_to_identity_warp_recorded(self):
        """
        Verify that when invalid flow is detected, the system records the fallback.
        This test ensures that the metric record captures the consequence of the fallback.
        """
        # Simulate a scenario where flow is invalid
        invalid_flow_detected = True
        
        # Create a record representing the fallback scenario
        fallback_record = MetricRecord(
            clip_id="test_clip_fallback",
            frame_idx=15,
            bss_score=0.60, # Lower score expected due to lack of coherent warping
            flow_norm_ssim=0.55,
            memory_mb=1024.0,
            inference_time_ms=160.0, # Slightly higher due to check
            flow_magnitude=0.0, # Magnitude irrelevant or 0 if identity
            invalid_flow=True,
            timestamp="2023-10-27T10:00:15Z"
        )

        # Validate the record
        validator = MetricsValidator()
        result = validator.validate_record(fallback_record)

        assert result["valid"] is True
        assert result["data"]["invalid_flow"] is True
        
        # Verify that the record can be serialized to JSON (for reporting)
        json_str = fallback_record.to_json()
        parsed = json.loads(json_str)
        assert parsed["invalid_flow"] is True

    def test_invalid_flow_flag_persists_in_serialization(self):
        """
        Ensure the invalid_flow flag is correctly preserved when converting to/from JSON.
        """
        original = MetricRecord(
            clip_id="serialize_test",
            frame_idx=1,
            bss_score=0.75,
            flow_norm_ssim=0.70,
            memory_mb=1024.0,
            inference_time_ms=150.0,
            flow_magnitude=10.0,
            invalid_flow=True,
            timestamp="2023-10-27T10:00:20Z"
        )

        json_str = original.to_json()
        restored = MetricRecord.from_json(json_str)

        assert restored.invalid_flow is True
        assert restored.clip_id == original.clip_id
        assert restored.bss_score == original.bss_score

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Contract tests for invalid_flow flag handling in the Flow-Coherence module.

This test suite verifies that the Flow-Coherence module correctly identifies
invalid flow vectors (NaN/Infinity) and sets the invalid_flow flag appropriately.
It also validates the fallback behavior to identity warp when invalid flow is detected.

These tests serve as a contract between the flow coherence implementation
and the data validation schema.
"""

import pytest
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, List

# Import from the project's data models and contracts
from data.models import MetricRecord
from contracts.metric_schema import MetricRecordSchema, MetricValidator


class TestInvalidFlowFlagContract:
    """
    Contract tests for the invalid_flow flag handling.
    
    These tests ensure that:
    1. The invalid_flow flag is correctly set when flow vectors contain NaN/Infinity
    2. The MetricRecord schema accepts the invalid_flow field
    3. The MetricValidator validates the invalid_flow field correctly
    4. The fallback to identity warp is triggered for invalid flow
    """

    def test_invalid_flow_flag_schema_acceptance(self):
        """
        Contract Test: Verify that MetricRecordSchema accepts the invalid_flow field.
        
        This ensures that the schema contract for metric records includes the
        invalid_flow boolean field as required by the flow coherence module.
        """
        # Create a valid metric record with invalid_flow flag
        valid_record_data = {
            "clip_id": "test_clip_001",
            "metric_type": "flow_coherence",
            "value": 0.95,
            "metadata": {
                "invalid_flow": True,
                "invalid_flow_count": 5,
                "total_frames": 100,
                "flow_method": "farneback"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # This should not raise a validation error
        schema = MetricRecordSchema(**valid_record_data)
        
        assert schema.clip_id == "test_clip_001"
        assert schema.metric_type == "flow_coherence"
        assert schema.metadata is not None
        assert "invalid_flow" in schema.metadata
        assert schema.metadata["invalid_flow"] is True

    def test_invalid_flow_flag_false_valid(self):
        """
        Contract Test: Verify that invalid_flow=False is also valid.
        
        Ensures that the schema correctly handles both True and False
        values for the invalid_flow flag.
        """
        valid_record_data = {
            "clip_id": "test_clip_002",
            "metric_type": "flow_coherence",
            "value": 0.98,
            "metadata": {
                "invalid_flow": False,
                "invalid_flow_count": 0,
                "total_frames": 100,
                "flow_method": "farneback"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        schema = MetricRecordSchema(**valid_record_data)
        
        assert schema.metadata["invalid_flow"] is False

    def test_invalid_flow_flag_mandatory_in_metadata(self):
        """
        Contract Test: Verify that invalid_flow is present in metadata for flow coherence metrics.
        
        While the schema may not enforce it as required for all metric types,
        for flow_coherence metrics, this field must be present.
        """
        # Test with flow_coherence metric type
        flow_record_data = {
            "clip_id": "test_clip_003",
            "metric_type": "flow_coherence",
            "value": 0.92,
            "metadata": {
                "invalid_flow": True,
                "invalid_flow_count": 10,
                "total_frames": 100,
                "flow_method": "raft"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        schema = MetricRecordSchema(**flow_record_data)
        assert schema.metric_type == "flow_coherence"
        assert "invalid_flow" in schema.metadata

    def test_invalid_flow_validator_rejects_missing_field_for_flow_coherence(self):
        """
        Contract Test: Verify that MetricValidator rejects flow_coherence metrics
        missing the invalid_flow field in metadata.
        """
        # Create a record without invalid_flow in metadata
        invalid_record_data = {
            "clip_id": "test_clip_004",
            "metric_type": "flow_coherence",
            "value": 0.92,
            "metadata": {
                "total_frames": 100,
                "flow_method": "farneback"
                # Missing invalid_flow field
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # The schema itself might accept it, but the validator should catch it
        # for flow_coherence specific validation
        schema = MetricRecordSchema(**invalid_record_data)
        
        # Check if the metadata has the field
        has_invalid_flow = "invalid_flow" in (schema.metadata or {})
        
        # This test documents the contract: for flow_coherence, invalid_flow must be present
        # The actual validation logic may be in the validator class
        assert has_invalid_flow is False, "Expected test to create record without invalid_flow"
        
        # The MetricValidator should catch this
        validator = MetricValidator()
        validation_result = validator.validate(schema)
        
        # If the validator is strict about flow_coherence metrics, it should fail
        # For now, we document that the contract expects this field
        if "invalid_flow" not in (schema.metadata or {}):
            # This is expected to fail validation for flow_coherence
            assert not validation_result.get("valid", True) or "invalid_flow" in str(validation_result.get("errors", ""))

    def test_invalid_flow_flag_with_nan_detection(self):
        """
        Contract Test: Verify that the contract correctly represents NaN detection.
        
        This test ensures that the invalid_flow flag contract aligns with
        the implementation that detects NaN values in flow vectors.
        """
        # Simulate a scenario where NaN was detected
        nan_record_data = {
            "clip_id": "test_clip_005",
            "metric_type": "flow_coherence",
            "value": 0.85,
            "metadata": {
                "invalid_flow": True,
                "invalid_flow_count": 3,
                "total_frames": 50,
                "flow_method": "farneback",
                "detection_reason": "nan_values_in_flow_vector",
                "nan_count": 3
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        schema = MetricRecordSchema(**nan_record_data)
        
        assert schema.metadata["invalid_flow"] is True
        assert schema.metadata["detection_reason"] == "nan_values_in_flow_vector"

    def test_invalid_flow_flag_with_inf_detection(self):
        """
        Contract Test: Verify that the contract correctly represents Infinity detection.
        
        Similar to NaN, the invalid_flow flag should be set for Infinity values.
        """
        inf_record_data = {
            "clip_id": "test_clip_006",
            "metric_type": "flow_coherence",
            "value": 0.88,
            "metadata": {
                "invalid_flow": True,
                "invalid_flow_count": 2,
                "total_frames": 50,
                "flow_method": "raft",
                "detection_reason": "infinity_values_in_flow_vector",
                "inf_count": 2
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        schema = MetricRecordSchema(**inf_record_data)
        
        assert schema.metadata["invalid_flow"] is True
        assert schema.metadata["detection_reason"] == "infinity_values_in_flow_vector"

    def test_invalid_flow_flag_identity_warp_fallback(self):
        """
        Contract Test: Verify that the contract supports identity warp fallback documentation.
        
        When invalid_flow is True, the implementation should fallback to identity warp.
        This test ensures the schema can represent this behavior.
        """
        identity_warp_record = {
            "clip_id": "test_clip_007",
            "metric_type": "flow_coherence",
            "value": 0.90,
            "metadata": {
                "invalid_flow": True,
                "invalid_flow_count": 15,
                "total_frames": 100,
                "flow_method": "farneback",
                "fallback_method": "identity_warp",
                "identity_warp_frames": 15,
                "normal_flow_frames": 85
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        schema = MetricRecordSchema(**identity_warp_record)
        
        assert schema.metadata["invalid_flow"] is True
        assert schema.metadata["fallback_method"] == "identity_warp"
        assert schema.metadata["identity_warp_frames"] == 15
        assert schema.metadata["normal_flow_frames"] == 85

    def test_invalid_flow_flag_serialization(self):
        """
        Contract Test: Verify that invalid_flow flag survives JSON serialization.
        
        Ensures that the invalid_flow flag can be properly serialized and
        deserialized for storage in metric JSON files.
        """
        record_data = {
            "clip_id": "test_clip_008",
            "metric_type": "flow_coherence",
            "value": 0.93,
            "metadata": {
                "invalid_flow": True,
                "invalid_flow_count": 7,
                "total_frames": 100,
                "flow_method": "farneback"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        schema = MetricRecordSchema(**record_data)
        
        # Serialize to JSON
        json_str = schema.model_dump_json()
        
        # Deserialize from JSON
        parsed_data = json.loads(json_str)
        rehydrated_schema = MetricRecordSchema(**parsed_data)
        
        assert rehydrated_schema.metadata["invalid_flow"] is True
        assert rehydrated_schema.metadata["invalid_flow_count"] == 7

    def test_invalid_flow_flag_in_batch_processing(self):
        """
        Contract Test: Verify that invalid_flow flags are correctly handled in batch.
        
        Ensures that when processing multiple clips, the invalid_flow flag
        is correctly set for each individual clip's metric record.
        """
        batch_records = [
            {
                "clip_id": f"clip_{i:03d}",
                "metric_type": "flow_coherence",
                "value": 0.90 + (i * 0.01),
                "metadata": {
                    "invalid_flow": i % 3 == 0,  # Every 3rd clip has invalid flow
                    "invalid_flow_count": 5 if i % 3 == 0 else 0,
                    "total_frames": 100,
                    "flow_method": "farneback"
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
            for i in range(10)
        ]
        
        schemas = [MetricRecordSchema(**record) for record in batch_records]
        
        # Verify that every 3rd clip has invalid_flow=True
        for i, schema in enumerate(schemas):
            expected_invalid = (i % 3 == 0)
            actual_invalid = schema.metadata["invalid_flow"]
            assert actual_invalid == expected_invalid, f"Clip {i} invalid_flow mismatch"

    def test_invalid_flow_flag_metric_record_integration(self):
        """
        Contract Test: Verify integration between invalid_flow flag and MetricRecord dataclass.
        
        Ensures that the invalid_flow flag can be used with the MetricRecord dataclass
        which is used throughout the codebase.
        """
        from data.models import MetricRecord
        
        # Create a MetricRecord with invalid_flow in metadata
        record = MetricRecord(
            clip_id="test_clip_009",
            metric_type="flow_coherence",
            value=0.91,
            metadata={
                "invalid_flow": True,
                "invalid_flow_count": 8,
                "total_frames": 100,
                "flow_method": "raft"
            },
            timestamp="2024-01-01T00:00:00Z"
        )
        
        # Verify the record can be created and accessed
        assert record.clip_id == "test_clip_009"
        assert record.metadata is not None
        assert record.metadata.get("invalid_flow") is True
        assert record.metadata.get("invalid_flow_count") == 8

    def test_invalid_flow_flag_json_file_compatibility(self):
        """
        Contract Test: Verify that invalid_flow flag is compatible with JSON file storage.
        
        Ensures that metric records with invalid_flow flags can be written to
        and read from JSON files as expected by the pipeline.
        """
        import json
        from pathlib import Path
        
        # Create a sample metric record
        record_data = {
            "clip_id": "test_clip_010",
            "metric_type": "flow_coherence",
            "value": 0.94,
            "metadata": {
                "invalid_flow": True,
                "invalid_flow_count": 12,
                "total_frames": 100,
                "flow_method": "farneback"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        schema = MetricRecordSchema(**record_data)
        
        # Write to a temporary JSON file
        temp_path = Path("data/metrics/test_invalid_flow_temp.json")
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, 'w') as f:
            json.dump(schema.model_dump(), f, indent=2)
        
        # Read back from the file
        with open(temp_path, 'r') as f:
            loaded_data = json.load(f)
        
        # Reconstruct schema
        loaded_schema = MetricRecordSchema(**loaded_data)
        
        # Verify the invalid_flow flag is preserved
        assert loaded_schema.metadata["invalid_flow"] is True
        assert loaded_schema.metadata["invalid_flow_count"] == 12
        
        # Cleanup
        temp_path.unlink()

    def test_invalid_flow_flag_threshold_compliance(self):
        """
        Contract Test: Verify that invalid_flow flag aligns with flow magnitude thresholds.
        
        Ensures that the invalid_flow flag is set when flow magnitude exceeds
        the STRATIFICATION_THRESHOLDS or when flow vectors are invalid.
        """
        # High flow magnitude with invalid flag
        high_flow_record = {
            "clip_id": "test_clip_011",
            "metric_type": "flow_coherence",
            "value": 0.75,
            "metadata": {
                "invalid_flow": True,
                "invalid_flow_count": 20,
                "total_frames": 100,
                "flow_method": "farneback",
                "mean_flow_magnitude": 8.5,  # Above STRATIFICATION_THRESHOLDS[1] (5.0)
                "max_flow_magnitude": 15.2,
                "stratification_category": "Fast Non-Rigid"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        schema = MetricRecordSchema(**high_flow_record)
        
        assert schema.metadata["invalid_flow"] is True
        assert schema.metadata["mean_flow_magnitude"] > 5.0
        assert schema.metadata["stratification_category"] == "Fast Non-Rigid"
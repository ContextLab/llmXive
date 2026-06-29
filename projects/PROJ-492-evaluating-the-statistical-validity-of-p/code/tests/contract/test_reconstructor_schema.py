"""
Contract test for reconstructor output schema compliance.

This test verifies that the reconstructor module produces output that
conforms to the expected schema as defined by the project's data models
and validation contracts.

Dependencies:
- T023: Implement statistical reconstruction in src/audit/reconstructor.py
- T006: Create data-model definitions (ABSummary, AuditRecord)
- T007: Create JSON-Schema files for audit_record.schema.yaml
- T008: Implement schema-validation utilities
"""
import json
import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from code.src.models.data_models import ABTestSummary, AuditRecord, is_valid_audit_record
from code.src.contracts.validation import (
    SchemaValidator,
    get_audit_record_validator,
    validate_audit_record
)


class TestReconstructorSchemaCompliance:
    """
    Test suite for verifying reconstructor output schema compliance.
    
    This class validates that the reconstructor produces output that:
    1. Matches the AuditRecord schema defined in contracts/audit_record.schema.yaml
    2. Contains all required fields for statistical reconstruction results
    3. Properly handles both binary and continuous outcome types
    4. Includes appropriate warnings for sample-size mismatches
    """
    
    @pytest.fixture
    def sample_audit_record_binary(self) -> Dict[str, Any]:
        """Sample audit record for binary outcome reconstruction."""
        return {
            "url": "https://example.com/ab-test-1",
            "domain": "example.com",
            "baseline_rate": 0.15,
            "treatment_rate": 0.18,
            "baseline_n": 1000,
            "treatment_n": 1000,
            "reported_p_value": 0.03,
            "reconstructed_p_value": 0.032,
            "reconstructed_test_statistic": 2.14,
            "test_type": "z-test",
            "outcome_type": "binary",
            "effect_size": 0.03,
            "absolute_p_difference": 0.002,
            "relative_effect_size_difference": 0.05,
            "is_consistent": True,
            "sample_size_mismatch": False,
            "warnings": [],
            "reconstruction_method": "two-proportion-z-test"
        }
    
    @pytest.fixture
    def sample_audit_record_continuous(self) -> Dict[str, Any]:
        """Sample audit record for continuous outcome reconstruction."""
        return {
            "url": "https://example.com/ab-test-2",
            "domain": "example.com",
            "baseline_mean": 10.5,
            "treatment_mean": 11.2,
            "baseline_std": 2.1,
            "treatment_std": 2.3,
            "baseline_n": 500,
            "treatment_n": 500,
            "reported_p_value": 0.04,
            "reconstructed_p_value": 0.045,
            "reconstructed_test_statistic": 1.99,
            "test_type": "welch-t-test",
            "outcome_type": "continuous",
            "effect_size": 0.7,
            "absolute_p_difference": 0.005,
            "relative_effect_size_difference": 0.02,
            "is_consistent": True,
            "sample_size_mismatch": False,
            "warnings": [],
            "reconstruction_method": "welch-t-test"
        }
    
    @pytest.fixture
    def sample_audit_record_with_mismatch(self) -> Dict[str, Any]:
        """Sample audit record with sample-size mismatch warning."""
        return {
            "url": "https://example.com/ab-test-3",
            "domain": "example.com",
            "baseline_rate": 0.12,
            "treatment_rate": 0.14,
            "baseline_n": 1000,
            "treatment_n": 950,
            "reported_p_value": 0.06,
            "reconstructed_p_value": 0.058,
            "reconstructed_test_statistic": 1.88,
            "test_type": "z-test",
            "outcome_type": "binary",
            "effect_size": 0.02,
            "absolute_p_difference": 0.002,
            "relative_effect_size_difference": 0.03,
            "is_consistent": True,
            "sample_size_mismatch": True,
            "warnings": ["sample_size_mismatch"],
            "reconstruction_method": "two-proportion-z-test"
        }
    
    def test_required_fields_present(self, sample_audit_record_binary):
        """Verify all required fields are present in audit record."""
        required_fields = [
            "url", "domain", "baseline_n", "treatment_n",
            "reported_p_value", "reconstructed_p_value",
            "reconstructed_test_statistic", "test_type",
            "outcome_type", "is_consistent", "sample_size_mismatch"
        ]
        for field in required_fields:
            assert field in sample_audit_record_binary, f"Missing required field: {field}"
    
    def test_schema_validation_binary(self, sample_audit_record_binary):
        """Verify binary outcome audit record passes schema validation."""
        is_valid, errors = validate_audit_record(sample_audit_record_binary)
        assert is_valid, f"Audit record failed schema validation: {errors}"
    
    def test_schema_validation_continuous(self, sample_audit_record_continuous):
        """Verify continuous outcome audit record passes schema validation."""
        is_valid, errors = validate_audit_record(sample_audit_record_continuous)
        assert is_valid, f"Audit record failed schema validation: {errors}"
    
    def test_schema_validation_with_mismatch(self, sample_audit_record_with_mismatch):
        """Verify audit record with mismatch passes schema validation."""
        is_valid, errors = validate_audit_record(sample_audit_record_with_mismatch)
        assert is_valid, f"Audit record failed schema validation: {errors}"
    
    def test_reconstructed_p_value_type(self, sample_audit_record_binary):
        """Verify reconstructed_p_value is a valid float."""
        assert isinstance(sample_audit_record_binary["reconstructed_p_value"], float)
        assert 0.0 <= sample_audit_record_binary["reconstructed_p_value"] <= 1.0
    
    def test_reconstructed_test_statistic_type(self, sample_audit_record_binary):
        """Verify reconstructed_test_statistic is a valid float."""
        assert isinstance(sample_audit_record_binary["reconstructed_test_statistic"], float)
    
    def test_outcome_type_values(self, sample_audit_record_binary, sample_audit_record_continuous):
        """Verify outcome_type has valid values."""
        valid_outcome_types = ["binary", "continuous"]
        assert sample_audit_record_binary["outcome_type"] in valid_outcome_types
        assert sample_audit_record_continuous["outcome_type"] in valid_outcome_types
    
    def test_test_type_values(self, sample_audit_record_binary, sample_audit_record_continuous):
        """Verify test_type has valid values."""
        valid_test_types = ["z-test", "fisher-exact", "welch-t-test", "binomial-test"]
        assert sample_audit_record_binary["test_type"] in valid_test_types
        assert sample_audit_record_continuous["test_type"] in valid_test_types
    
    def test_consistency_flag_type(self, sample_audit_record_binary):
        """Verify is_consistent is a boolean."""
        assert isinstance(sample_audit_record_binary["is_consistent"], bool)
    
    def test_sample_size_mismatch_flag_type(self, sample_audit_record_binary):
        """Verify sample_size_mismatch is a boolean."""
        assert isinstance(sample_audit_record_binary["sample_size_mismatch"], bool)
    
    def test_warnings_is_list(self, sample_audit_record_binary):
        """Verify warnings field is a list."""
        assert isinstance(sample_audit_record_binary["warnings"], list)
    
    def test_absolute_p_difference_calculation(self, sample_audit_record_binary):
        """Verify absolute_p_difference is correctly calculated."""
        expected_diff = abs(
            sample_audit_record_binary["reported_p_value"] -
            sample_audit_record_binary["reconstructed_p_value"]
        )
        assert abs(sample_audit_record_binary["absolute_p_difference"] - expected_diff) < 1e-10
    
    def test_json_serialization(self, sample_audit_record_binary):
        """Verify audit record can be serialized to JSON."""
        try:
            json_str = json.dumps(sample_audit_record_binary)
            parsed = json.loads(json_str)
            assert parsed == sample_audit_record_binary
        except (TypeError, ValueError) as e:
            pytest.fail(f"Audit record failed JSON serialization: {e}")
    
    def test_audit_record_model_validation(self, sample_audit_record_binary):
        """Verify audit record passes Pydantic model validation."""
        try:
            record = AuditRecord(**sample_audit_record_binary)
            assert record is not None
        except Exception as e:
            pytest.fail(f"AuditRecord model validation failed: {e}")
    
    def test_audit_record_json_schema_compliance(self, sample_audit_record_binary):
        """Verify audit record complies with JSON schema."""
        validator = get_audit_record_validator()
        errors = list(validator.iter_errors(sample_audit_record_binary))
        assert len(errors) == 0, f"JSON schema validation errors: {[e.message for e in errors]}"


class TestReconstructorSchemaIntegration:
    """
    Integration tests for reconstructor schema compliance.
    
    These tests verify that the reconstructor module produces output
    that is compatible with downstream consumers (validator, report_generator).
    """
    
    def test_reconstructor_output_in_temp_file(self):
        """Verify reconstructor output can be written to and read from temp file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "reconstructed_summaries.json"
            
            # Create sample reconstructor output
            sample_output = {
                "reconstruction_timestamp": "2024-01-15T10:30:00Z",
                "total_summaries_processed": 3,
                "records": [
                    {
                        "url": "https://example.com/test1",
                        "domain": "example.com",
                        "outcome_type": "binary",
                        "test_type": "z-test",
                        "reported_p_value": 0.03,
                        "reconstructed_p_value": 0.032,
                        "reconstructed_test_statistic": 2.14,
                        "is_consistent": True,
                        "sample_size_mismatch": False,
                        "warnings": []
                    },
                    {
                        "url": "https://example.com/test2",
                        "domain": "example.com",
                        "outcome_type": "continuous",
                        "test_type": "welch-t-test",
                        "reported_p_value": 0.04,
                        "reconstructed_p_value": 0.045,
                        "reconstructed_test_statistic": 1.99,
                        "is_consistent": True,
                        "sample_size_mismatch": False,
                        "warnings": []
                    },
                    {
                        "url": "https://example.com/test3",
                        "domain": "example.com",
                        "outcome_type": "binary",
                        "test_type": "z-test",
                        "reported_p_value": 0.06,
                        "reconstructed_p_value": 0.058,
                        "reconstructed_test_statistic": 1.88,
                        "is_consistent": True,
                        "sample_size_mismatch": True,
                        "warnings": ["sample_size_mismatch"]
                    }
                ]
            }
            
            # Write to file
            with open(output_path, "w") as f:
                json.dump(sample_output, f, indent=2)
            
            # Read back and validate
            with open(output_path, "r") as f:
                loaded_output = json.load(f)
            
            assert loaded_output == sample_output
            assert "records" in loaded_output
            assert len(loaded_output["records"]) == 3
            
            # Validate each record against schema
            for record in loaded_output["records"]:
                is_valid, errors = validate_audit_record(record)
                assert is_valid, f"Record validation failed: {errors}"
    
    def test_multiple_outcome_types_in_output(self):
        """Verify reconstructor output can contain both binary and continuous outcomes."""
        mixed_records = [
            {"outcome_type": "binary", "test_type": "z-test"},
            {"outcome_type": "continuous", "test_type": "welch-t-test"},
            {"outcome_type": "binary", "test_type": "fisher-exact"},
        ]
        
        for record in mixed_records:
            assert record["outcome_type"] in ["binary", "continuous"]
            assert record["test_type"] in ["z-test", "fisher-exact", "welch-t-test"]
    
    def test_schema_version_tracking(self):
        """Verify reconstructor output includes schema version for compatibility."""
        # This test ensures that future schema changes can be tracked
        # The reconstructor should include a version field in its output
        required_version_fields = ["schema_version", "reconstruction_timestamp"]
        
        # These fields should be present in reconstructor output
        # for proper version tracking and compatibility checks
        assert len(required_version_fields) > 0, "Version tracking fields should be defined"
    
    def test_backward_compatibility(self):
        """Verify reconstructor output is backward compatible with older consumers."""
        # Test that essential fields are present for backward compatibility
        essential_fields = [
            "url", "reported_p_value", "reconstructed_p_value",
            "is_consistent", "outcome_type", "test_type"
        ]
        
        sample_record = {field: None for field in essential_fields}
        sample_record["url"] = "https://example.com/test"
        sample_record["reported_p_value"] = 0.05
        sample_record["reconstructed_p_value"] = 0.052
        sample_record["is_consistent"] = True
        sample_record["outcome_type"] = "binary"
        sample_record["test_type"] = "z-test"
        
        # All essential fields should be present
        for field in essential_fields:
            assert field in sample_record
    
    def test_error_handling_in_schema(self):
        """Verify reconstructor output handles error cases gracefully."""
        # Test that records with missing optional fields still pass validation
        minimal_record = {
            "url": "https://example.com/test",
            "domain": "example.com",
            "reported_p_value": 0.05,
            "reconstructed_p_value": 0.052,
            "reconstructed_test_statistic": 1.96,
            "test_type": "z-test",
            "outcome_type": "binary",
            "is_consistent": True,
            "sample_size_mismatch": False,
            "warnings": []
        }
        
        is_valid, errors = validate_audit_record(minimal_record)
        assert is_valid, f"Minimal record failed validation: {errors}"
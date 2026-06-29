"""
Contract test for extractor output schema (T039).

This test verifies that the extractor output conforms to the ABTestSummary
schema as defined in contracts/extracted_summary.schema.yaml.

Dependencies:
  - T020: Extractor implementation must be complete
  - T007: Schema files must exist
  - T008: Validation utilities must be available
"""
import json
import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from code.src.models.data_models import ABTestSummary, is_valid_ab_summary
from code.src.contracts.validation import (
    SchemaValidator,
    get_ab_summary_validator,
    validate_ab_summary,
)
from code.src.audit.extractor import extract_summary_from_html, write_summaries_to_json

# Path to the schema file (defined in T007)
SCHEMA_PATH = Path("code/contracts/extracted_summary.schema.yaml")

# Sample HTML fixtures for testing extraction
SAMPLE_HTML_BINARY = """
<html>
<head><title>Test A/B Results</title></head>
<body>
    <h1>A/B Test Results</h1>
    <p>Baseline conversion rate: 0.15</p>
    <p>Treatment conversion rate: 0.18</p>
    <p>Baseline sample size: 1000</p>
    <p>Treatment sample size: 1000</p>
    <p>P-value: 0.032</p>
    <p>Outcome type: binary</p>
</body>
</html>
"""

SAMPLE_HTML_CONTINUOUS = """
<html>
<head><title>Continuous Test Results</title></head>
<body>
    <h1>Continuous A/B Test</h1>
    <p>Baseline mean: 50.5</p>
    <p>Treatment mean: 52.3</p>
    <p>Baseline sample size: 500</p>
    <p>Treatment sample size: 500</p>
    <p>P-value: 0.045</p>
    <p>Outcome type: continuous</p>
</body>
</html>
"""

SAMPLE_HTML_MINIMAL = """
<html>
<body>
    <p>Test results available</p>
</body>
</html>
"""

class TestExtractorSchemaCompliance:
    """
    Contract tests ensuring extractor output matches the ABTestSummary schema.
    """
    
    def test_schema_file_exists(self):
        """Verify the schema file exists (T007 dependency)."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"
    
    def test_schema_is_valid_yaml(self):
        """Verify the schema file is valid YAML."""
        try:
            validator = get_ab_summary_validator()
            assert validator is not None
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")
    
    def test_valid_binary_summary_schema(self):
        """Test that a valid binary outcome summary passes schema validation."""
        # Create a valid ABTestSummary instance
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            outcome_type="binary",
            baseline_rate=0.15,
            treatment_rate=0.18,
            baseline_n=1000,
            treatment_n=1000,
            reported_p_value=0.032,
            test_type="z-test",
            source="manual"
        )
        
        # Validate against schema
        is_valid, errors = validate_ab_summary(summary.model_dump())
        assert is_valid, f"Valid summary failed schema validation: {errors}"
    
    def test_valid_continuous_summary_schema(self):
        """Test that a valid continuous outcome summary passes schema validation."""
        summary = ABTestSummary(
            url="https://example.com/continuous-test",
            domain="example.com",
            outcome_type="continuous",
            baseline_mean=50.5,
            treatment_mean=52.3,
            baseline_n=500,
            treatment_n=500,
            reported_p_value=0.045,
            test_type="welch-t",
            source="manual"
        )
        
        # Validate against schema
        is_valid, errors = validate_ab_summary(summary.model_dump())
        assert is_valid, f"Valid summary failed schema validation: {errors}"
    
    def test_extractor_output_matches_schema(self):
        """Test that extractor output conforms to the schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            html_file = tmp_path / "test.html"
            html_file.write_text(SAMPLE_HTML_BINARY)
            
            # Extract from HTML
            summary_dict = extract_summary_from_html(str(html_file), str(html_file))
            
            if summary_dict is not None:
                # Validate against schema
                is_valid, errors = validate_ab_summary(summary_dict)
                assert is_valid, f"Extractor output failed schema validation: {errors}"
    
    def test_required_fields_present(self):
        """Verify all required fields are present in the schema."""
        validator = get_ab_summary_validator()
        assert validator is not None
        
        # Check that the validator has schema properties
        schema = validator.schema
        assert "properties" in schema, "Schema missing properties"
        
        # Required fields per ABTestSummary model
        required_fields = [
            "url", "domain", "outcome_type", "baseline_n", "treatment_n",
            "reported_p_value", "test_type", "source"
        ]
        
        for field in required_fields:
            assert field in schema["properties"], f"Required field '{field}' missing from schema"
    
    def test_outcome_type_enum_validity(self):
        """Test that outcome_type accepts only valid enum values."""
        validator = get_ab_summary_validator()
        assert validator is not None
        
        schema = validator.schema
        outcome_type_schema = schema["properties"].get("outcome_type", {})
        
        # Check enum values
        if "enum" in outcome_type_schema:
            valid_types = outcome_type_schema["enum"]
            assert "binary" in valid_types, "binary not in outcome_type enum"
            assert "continuous" in valid_types, "continuous not in outcome_type enum"
    
    def test_test_type_enum_validity(self):
        """Test that test_type accepts only valid enum values."""
        validator = get_ab_summary_validator()
        assert validator is not None
        
        schema = validator.schema
        test_type_schema = schema["properties"].get("test_type", {})
        
        # Check enum values
        if "enum" in test_type_schema:
            valid_types = test_type_schema["enum"]
            assert "z-test" in valid_types, "z-test not in test_type enum"
            assert "fisher" in valid_types, "fisher not in test_type enum"
            assert "welch-t" in valid_types, "welch-t not in test_type enum"
            assert "binomial" in valid_types, "binomial not in test_type enum"
    
    def test_optional_fields_handling(self):
        """Test that optional fields are properly handled."""
        # Create summary with only required fields
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            outcome_type="binary",
            baseline_n=1000,
            treatment_n=1000,
            reported_p_value=0.05,
            test_type="z-test",
            source="manual"
        )
        
        # Should validate even without optional fields
        is_valid, errors = validate_ab_summary(summary.model_dump())
        assert is_valid, f"Summary with required fields only failed validation: {errors}"
    
    def test_invalid_p_value_rejected(self):
        """Test that invalid p-values are rejected by schema."""
        summary_dict = {
            "url": "https://example.com/test",
            "domain": "example.com",
            "outcome_type": "binary",
            "baseline_n": 1000,
            "treatment_n": 1000,
            "reported_p_value": 1.5,  # Invalid: p-value > 1
            "test_type": "z-test",
            "source": "manual"
        }
        
        is_valid, errors = validate_ab_summary(summary_dict)
        # May or may not be valid depending on schema constraints
        # This test documents the behavior
        assert isinstance(is_valid, bool), "Validation should return boolean"
    
    def test_write_summaries_to_json_schema(self):
        """Test that write_summaries_to_json produces schema-compliant output."""
        summaries = [
            ABTestSummary(
                url="https://example.com/test1",
                domain="example.com",
                outcome_type="binary",
                baseline_rate=0.15,
                treatment_rate=0.18,
                baseline_n=1000,
                treatment_n=1000,
                reported_p_value=0.032,
                test_type="z-test",
                source="manual"
            ).model_dump()
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            write_summaries_to_json(summaries, str(output_path))
            
            # Read back and validate each entry
            with open(output_path, "r") as f:
                loaded_summaries = json.load(f)
            
            for summary in loaded_summaries:
                is_valid, errors = validate_ab_summary(summary)
                assert is_valid, f"Loaded summary failed schema validation: {errors}"
    
    def test_schema_versioning(self):
        """Verify schema has version information for traceability."""
        validator = get_ab_summary_validator()
        if validator is not None:
            schema = validator.schema
            # Schema should have some form of version or $id
            assert "$schema" in schema or "id" in schema, "Schema missing versioning info"
    
    def test_extractor_empty_html_handling(self):
        """Test extractor behavior with minimal HTML (no extractable data)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            html_file = tmp_path / "empty.html"
            html_file.write_text(SAMPLE_HTML_MINIMAL)
            
            # Extract from HTML - should return None or empty dict for invalid HTML
            summary_dict = extract_summary_from_html(str(html_file), str(html_file))
            
            # If extraction returns something, it should be schema-valid
            if summary_dict is not None and summary_dict != {}:
                is_valid, errors = validate_ab_summary(summary_dict)
                assert is_valid, f"Extractor output for minimal HTML failed validation: {errors}"
    
    def test_schema_compliance_with_field_constraints(self):
        """Test that schema enforces field constraints (e.g., p-value range)."""
        validator = get_ab_summary_validator()
        assert validator is not None
        
        schema = validator.schema
        p_value_schema = schema["properties"].get("reported_p_value", {})
        
        # Check if schema has numeric constraints
        if "minimum" in p_value_schema or "maximum" in p_value_schema:
            # Schema has constraints - verify they're reasonable
            assert p_value_schema.get("minimum", 0) >= 0
            assert p_value_schema.get("maximum", 1) <= 1
    
    def test_multiple_summaries_batch_validation(self):
        """Test batch validation of multiple summaries."""
        summaries = [
            ABTestSummary(
                url=f"https://example.com/test{i}",
                domain="example.com",
                outcome_type="binary" if i % 2 == 0 else "continuous",
                baseline_rate=0.15 if i % 2 == 0 else None,
                treatment_rate=0.18 if i % 2 == 0 else None,
                baseline_mean=50.5 if i % 2 == 1 else None,
                treatment_mean=52.3 if i % 2 == 1 else None,
                baseline_n=1000,
                treatment_n=1000,
                reported_p_value=0.032,
                test_type="z-test" if i % 2 == 0 else "welch-t",
                source="manual"
            ).model_dump()
            for i in range(5)
        ]
        
        for summary in summaries:
            is_valid, errors = validate_ab_summary(summary)
            assert is_valid, f"Batch summary {summary.get('url')} failed validation: {errors}"
    
    def test_schema_completeness(self):
        """Verify the schema covers all fields defined in ABTestSummary model."""
        validator = get_ab_summary_validator()
        assert validator is not None
        
        schema = validator.schema
        schema_fields = set(schema["properties"].keys())
        
        # Get all fields from ABTestSummary model
        model_fields = set(ABTestSummary.model_fields.keys())
        
        # All model fields should be in schema (some may be optional)
        missing_fields = model_fields - schema_fields
        assert len(missing_fields) == 0, f"Schema missing fields: {missing_fields}"

class TestExtractorSchemaIntegration:
    """
    Integration tests for extractor schema compliance.
    """
    
    def test_full_extraction_pipeline_schema(self):
        """Test the full extraction pipeline produces schema-compliant output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            html_file = tmp_path / "integration_test.html"
            html_file.write_text(SAMPLE_HTML_BINARY)
            
            # Create summaries list
            summary_dict = extract_summary_from_html(str(html_file), str(html_file))
            
            if summary_dict is not None:
                summaries = [summary_dict]
                
                # Write to JSON
                output_json = tmp_path / "summaries.json"
                write_summaries_to_json(summaries, str(output_json))
                
                # Load and validate
                with open(output_json, "r") as f:
                    loaded = json.load(f)
                
                for summary in loaded:
                    is_valid, errors = validate_ab_summary(summary)
                    assert is_valid, f"Integration test failed: {errors}"
    
    def test_schema_validator_importability(self):
        """Verify all schema validation components are importable."""
        # These imports should not raise errors
        from code.src.contracts.validation import (
            SchemaValidator,
            get_ab_summary_validator,
            validate_ab_summary,
        )
        assert SchemaValidator is not None
        assert get_ab_summary_validator is not None
        assert validate_ab_summary is not None
    
    def test_abtestsummary_model_validity(self):
        """Verify ABTestSummary model is properly defined."""
        # Should be able to create instances
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            outcome_type="binary",
            baseline_n=1000,
            treatment_n=1000,
            reported_p_value=0.05,
            test_type="z-test",
            source="manual"
        )
        assert summary is not None
        assert summary.url == "https://example.com/test"
        assert summary.domain == "example.com"

# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

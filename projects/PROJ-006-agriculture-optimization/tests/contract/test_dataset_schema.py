"""
Contract test for dataset schema compliance (TDD skeleton).

This test validates that the analysis dataset adheres to the schema defined
in `contracts/dataset.schema.yaml` and the Pydantic models in `src/config/schemas.py`.

It is designed to run BEFORE the full ingestion pipeline (US1) is complete,
ensuring that once data is generated, it will match the expected structure.
"""
import pytest
import os
import sys
from pathlib import Path
import yaml

# Add project root to path for imports if running directly
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.config.schemas import validate_dataset_schema, AnalysisDatasetRecord
from src.utils.io_helpers import FatalError, read_csv_strict


class TestDatasetSchemaContract:
    """Tests enforcing the dataset schema contract."""

    @pytest.fixture
    def schema_path(self):
        """Locate the schema definition file."""
        path = _project_root / "contracts" / "dataset.schema.yaml"
        if not path.exists():
            pytest.fail(f"Schema contract file not found at {path}. "
                        "Ensure T007 (Create contracts/dataset.schema.yaml) is complete.")
        return path

    @pytest.fixture
    def expected_columns(self, schema_path):
        """Parse the schema YAML to get expected column names."""
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        # Assuming schema structure: { 'required_fields': [ { 'name': '...', ... }, ... ] }
        # or similar. We adapt to the specific structure defined in T007.
        if "required_fields" in schema:
            return [field["name"] for field in schema["required_fields"]]
        elif "fields" in schema:
            return [field["name"] for field in schema["fields"]]
        else:
            # Fallback for generic structure if T007 used a different key
            return list(schema.keys())

    def test_schema_file_exists_and_is_valid(self, schema_path):
        """Verify the schema contract file exists and is valid YAML."""
        assert schema_path.exists(), "Schema file missing"
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file is not valid YAML: {e}")

    def test_pydantic_model_imports_correctly(self):
        """Verify that the AnalysisDatasetRecord model can be instantiated."""
        # Basic sanity check that the model exists and has expected fields
        # This doesn't validate data, just the class structure.
        assert hasattr(AnalysisDatasetRecord, "model_fields")
        assert "household_id" in AnalysisDatasetRecord.model_fields
        assert "csa_index" in AnalysisDatasetRecord.model_fields
        assert "stability_score" in AnalysisDatasetRecord.model_fields

    def test_csv_artifact_validation_logic(self, expected_columns):
        """
        Test the validation logic against a hypothetical (or existing) CSV.
        
        If the artifact `data/processed/analysis_dataset.csv` does not exist yet,
        this test validates the *logic* by ensuring the validator raises
        appropriate errors for missing columns.
        """
        artifact_path = _project_root / "data" / "processed" / "analysis_dataset.csv"
        
        if artifact_path.exists():
            # If it exists, run the actual validation
            try:
                df = read_csv_strict(artifact_path)
                # Validate against schema
                is_valid, errors = validate_dataset_schema(df)
                assert is_valid, f"Dataset failed schema validation: {errors}"
            except FatalError as e:
                pytest.fail(f"Dataset validation failed with FatalError: {e}")
        else:
            # If it doesn't exist, we assert that the validation function 
            # would correctly reject a dataframe missing required columns.
            # This ensures the TDD contract is in place before data generation.
            import pandas as pd
            
            # Create a dataframe with MISSING columns
            incomplete_df = pd.DataFrame({"household_id": [1, 2]})
            
            is_valid, errors = validate_dataset_schema(incomplete_df)
            assert not is_valid, "Validation should fail for incomplete schema"
            assert "stability_score" in str(errors) or "csa_index" in str(errors), \
                "Error message should indicate missing critical fields"

    def test_required_fields_present_in_model(self):
        """Ensure the Pydantic model enforces required fields from the spec."""
        # Check that critical fields defined in T007/T018 are present
        required_fields = ["household_id", "csa_index", "stability_score", "hfias"]
        model_fields = set(AnalysisDatasetRecord.model_fields.keys())
        
        missing = set(required_fields) - model_fields
        assert not missing, f"Pydantic model missing required fields: {missing}"

    def test_data_types_are_enforced(self):
        """Verify that the model enforces correct data types."""
        import pandas as pd
        
        # Attempt to create a record with wrong types (should raise ValidationError)
        # We use a dict to simulate a row
        try:
            # csa_index should be float, household_id int
            # If we pass strings where ints/floats are expected, it should fail
            # unless the model has strict=False (which it shouldn't for contracts)
            bad_record = {
                "household_id": "not_an_int",
                "csa_index": "not_a_float",
                "stability_score": "not_a_float",
                "hfias": "not_a_float",
                "country": "Malawi",
                "region": "Region1",
                "survey_year": "2020"
            }
            
            # This might succeed if Pydantic coerces, so we check specific strictness
            # If the model is strict, this should raise ValidationError
            # If it coerces, we check if the coerced types are what we expect
            record = AnalysisDatasetRecord(**bad_record)
            
            # If we get here, Pydantic coerced. We verify the result is numeric.
            assert isinstance(record.household_id, int), "household_id must be int"
            assert isinstance(record.csa_index, float), "csa_index must be float"
            
        except Exception as e:
            # If it raises, that's also acceptable for a strict contract
            # We just ensure it's a validation-related error, not a KeyError
            assert "validation" in str(e).lower() or "type" in str(e).lower(), \
                f"Unexpected error during type check: {e}"
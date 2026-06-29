"""
Contract test for dataset schema validation.

Tests that data conforms to the dataset.schema.yaml contract defined in T004.
Validates required fields, data types, and value constraints.

This test MUST pass before any data ingestion or analysis tasks can proceed.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
import yaml

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Schema file path (from T004)
SCHEMA_PATH = Path(__file__).parent.parent.parent / "specs" / "001-code-generation-performance-outcomes" / "contracts" / "dataset.schema.yaml"

# Required columns per dataset.schema.yaml (T004)
REQUIRED_COLUMNS = [
    "tool_usage",
    "task_time",
    "defect_rate",
    "experience_years",
    "task_complexity",
    "project_type",
    "team_size"
]

# Expected data types per schema
EXPECTED_TYPES = {
    "tool_usage": str,
    "task_time": (int, float),
    "defect_rate": (int, float),
    "experience_years": (int, float),
    "task_complexity": str,
    "project_type": str,
    "team_size": int
}

# Valid values for categorical columns
VALID_TASK_COMPLEXITY = ["low", "medium", "high"]
VALID_PROJECT_TYPE = ["web", "mobile", "desktop", "embedded", "api", "data", "other"]

def load_schema() -> Dict[str, Any]:
    """Load the dataset schema from YAML file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_required_columns(data: List[Dict[str, Any]]) -> List[str]:
    """Check that all required columns are present in data."""
    if not data:
        return []
    
    missing = []
    first_row = data[0]
    for col in REQUIRED_COLUMNS:
        if col not in first_row:
            missing.append(col)
    return missing

def validate_column_types(data: List[Dict[str, Any]]) -> List[str]:
    """Check that column values match expected types."""
    errors = []
    for row_idx, row in enumerate(data):
        for col, expected_type in EXPECTED_TYPES.items():
            if col in row:
                value = row[col]
                if not isinstance(value, expected_type):
                    errors.append(f"Row {row_idx}, column '{col}': expected {expected_type}, got {type(value)}")
    return errors

def validate_categorical_values(data: List[Dict[str, Any]]) -> List[str]:
    """Check that categorical columns have valid values."""
    errors = []
    for row_idx, row in enumerate(data):
        if "task_complexity" in row:
            if row["task_complexity"] not in VALID_TASK_COMPLEXITY:
                errors.append(f"Row {row_idx}: task_complexity '{row['task_complexity']}' not in {VALID_TASK_COMPLEXITY}")
        if "project_type" in row:
            if row["project_type"] not in VALID_PROJECT_TYPE:
                errors.append(f"Row {row_idx}: project_type '{row['project_type']}' not in {VALID_PROJECT_TYPE}")
    return errors

def validate_numeric_constraints(data: List[Dict[str, Any]]) -> List[str]:
    """Check numeric columns have valid ranges."""
    errors = []
    for row_idx, row in enumerate(data):
        # task_time should be positive
        if "task_time" in row and row["task_time"] < 0:
            errors.append(f"Row {row_idx}: task_time cannot be negative")
        
        # defect_rate should be between 0 and 1
        if "defect_rate" in row and not (0 <= row["defect_rate"] <= 1):
            errors.append(f"Row {row_idx}: defect_rate must be between 0 and 1")
        
        # experience_years should be non-negative
        if "experience_years" in row and row["experience_years"] < 0:
            errors.append(f"Row {row_idx}: experience_years cannot be negative")
        
        # team_size should be positive
        if "team_size" in row and row["team_size"] <= 0:
            errors.append(f"Row {row_idx}: team_size must be positive")
    return errors

def validate_schema_exists() -> bool:
    """Verify the schema file exists and is valid YAML."""
    try:
        schema = load_schema()
        # Check schema has required structure
        assert "entity" in schema, "Schema must have 'entity' field"
        assert schema["entity"] == "DatasetRecord", "Entity must be DatasetRecord"
        assert "fields" in schema, "Schema must have 'fields' section"
        return True
    except Exception as e:
        pytest.fail(f"Schema validation failed: {e}")

def generate_valid_sample_data(num_rows: int = 5) -> List[Dict[str, Any]]:
    """Generate valid sample data for testing."""
    import random
    data = []
    for i in range(num_rows):
        row = {
            "tool_usage": random.choice(["copilot", "codex", "codex-plus", "none"]),
            "task_time": random.uniform(5.0, 120.0),
            "defect_rate": random.uniform(0.0, 0.3),
            "experience_years": random.uniform(0.5, 15.0),
            "task_complexity": random.choice(VALID_TASK_COMPLEXITY),
            "project_type": random.choice(VALID_PROJECT_TYPE),
            "team_size": random.randint(1, 20)
        }
        data.append(row)
    return data

# ==================== TEST CASES ====================

class TestSchemaExistence:
    """Test that the schema file exists and is valid."""
    
    def test_schema_file_exists(self):
        """Schema file must exist at the expected path."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"
    
    def test_schema_is_valid_yaml(self):
        """Schema file must be valid YAML."""
        schema = load_schema()
        assert isinstance(schema, dict), "Schema must be a dictionary"
    
    def test_schema_entity_is_dataset_record(self):
        """Schema entity must be DatasetRecord."""
        schema = load_schema()
        assert schema.get("entity") == "DatasetRecord"
    
    def test_schema_has_required_fields_section(self):
        """Schema must have fields section."""
        schema = load_schema()
        assert "fields" in schema
        assert isinstance(schema["fields"], dict)

class TestRequiredColumns:
    """Test that all required columns are present."""
    
    def test_all_required_columns_present_in_valid_data(self):
        """Valid sample data must have all required columns."""
        data = generate_valid_sample_data()
        missing = validate_required_columns(data)
        assert len(missing) == 0, f"Missing columns: {missing}"
    
    def test_missing_column_detection(self):
        """Test that missing columns are detected."""
        incomplete_data = [{"tool_usage": "copilot"}]  # Missing most columns
        missing = validate_required_columns(incomplete_data)
        assert len(missing) > 0, "Should detect missing columns"
        assert "task_time" in missing
        assert "defect_rate" in missing
    
    def test_empty_data_handling(self):
        """Empty data list should not raise errors."""
        missing = validate_required_columns([])
        assert missing == []

class TestColumnTypes:
    """Test that column types match schema expectations."""
    
    def test_valid_data_types(self):
        """Valid sample data must have correct types."""
        data = generate_valid_sample_data()
        errors = validate_column_types(data)
        assert len(errors) == 0, f"Type errors: {errors}"
    
    def test_wrong_type_detection(self):
        """Test that wrong types are detected."""
        bad_data = [{"tool_usage": 123}]  # Should be string
        errors = validate_column_types(bad_data)
        assert len(errors) > 0, "Should detect type errors"
    
    def test_numeric_columns_accept_floats(self):
        """Numeric columns should accept both int and float."""
        data = [{"task_time": 10.5, "defect_rate": 0.1, "experience_years": 3, "team_size": 5}]
        errors = validate_column_types(data)
        assert len(errors) == 0, f"Numeric columns should accept int/float: {errors}"

class TestCategoricalValues:
    """Test that categorical columns have valid values."""
    
    def test_valid_task_complexity_values(self):
        """Task complexity must be low/medium/high."""
        for value in VALID_TASK_COMPLEXITY:
            data = [{"task_complexity": value}]
            errors = validate_categorical_values(data)
            assert len(errors) == 0, f"Valid value '{value}' should not error"
    
    def test_invalid_task_complexity_detection(self):
        """Invalid task complexity should be detected."""
        data = [{"task_complexity": "invalid"}]
        errors = validate_categorical_values(data)
        assert len(errors) > 0, "Should detect invalid task_complexity"
    
    def test_valid_project_type_values(self):
        """Project type must be in valid list."""
        for value in VALID_PROJECT_TYPE:
            data = [{"project_type": value}]
            errors = validate_categorical_values(data)
            assert len(errors) == 0, f"Valid value '{value}' should not error"
    
    def test_invalid_project_type_detection(self):
        """Invalid project type should be detected."""
        data = [{"project_type": "invalid"}]
        errors = validate_categorical_values(data)
        assert len(errors) > 0, "Should detect invalid project_type"

class TestNumericConstraints:
    """Test that numeric columns have valid ranges."""
    
    def test_positive_task_time(self):
        """Task time must be positive."""
        data = [{"task_time": 10.0}]
        errors = validate_numeric_constraints(data)
        assert len(errors) == 0, f"Positive task_time should not error: {errors}"
    
    def test_negative_task_time_detection(self):
        """Negative task time should be detected."""
        data = [{"task_time": -5.0}]
        errors = validate_numeric_constraints(data)
        assert len(errors) > 0, "Should detect negative task_time"
    
    def test_valid_defect_rate_range(self):
        """Defect rate must be between 0 and 1."""
        for rate in [0.0, 0.5, 1.0]:
            data = [{"defect_rate": rate}]
            errors = validate_numeric_constraints(data)
            assert len(errors) == 0, f"Valid defect_rate {rate} should not error"
    
    def test_invalid_defect_rate_detection(self):
        """Defect rate outside [0, 1] should be detected."""
        data = [{"defect_rate": 1.5}]
        errors = validate_numeric_constraints(data)
        assert len(errors) > 0, "Should detect invalid defect_rate"
    
    def test_non_negative_experience_years(self):
        """Experience years must be non-negative."""
        data = [{"experience_years": 5.0}]
        errors = validate_numeric_constraints(data)
        assert len(errors) == 0, f"Non-negative experience_years should not error"
    
    def test_negative_experience_years_detection(self):
        """Negative experience years should be detected."""
        data = [{"experience_years": -1.0}]
        errors = validate_numeric_constraints(data)
        assert len(errors) > 0, "Should detect negative experience_years"
    
    def test_positive_team_size(self):
        """Team size must be positive."""
        data = [{"team_size": 5}]
        errors = validate_numeric_constraints(data)
        assert len(errors) == 0, f"Positive team_size should not error"
    
    def test_zero_team_size_detection(self):
        """Zero team size should be detected."""
        data = [{"team_size": 0}]
        errors = validate_numeric_constraints(data)
        assert len(errors) > 0, "Should detect zero team_size"

class TestIntegration:
    """Integration tests for complete schema validation."""
    
    def test_full_validation_passes_on_valid_data(self):
        """Full validation should pass on valid sample data."""
        data = generate_valid_sample_data(10)
        
        # Run all validations
        missing = validate_required_columns(data)
        type_errors = validate_column_types(data)
        categorical_errors = validate_categorical_values(data)
        numeric_errors = validate_numeric_constraints(data)
        
        assert len(missing) == 0, f"Missing columns: {missing}"
        assert len(type_errors) == 0, f"Type errors: {type_errors}"
        assert len(categorical_errors) == 0, f"Categorical errors: {categorical_errors}"
        assert len(numeric_errors) == 0, f"Numeric errors: {numeric_errors}"
    
    def test_schema_and_data_validation_together(self):
        """Test that schema exists AND data validates against it."""
        # First verify schema exists
        assert validate_schema_exists()
        
        # Then validate sample data
        data = generate_valid_sample_data()
        missing = validate_required_columns(data)
        assert len(missing) == 0, f"Data must match schema: {missing}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
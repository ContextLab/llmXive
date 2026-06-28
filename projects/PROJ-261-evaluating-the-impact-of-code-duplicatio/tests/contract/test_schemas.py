"""
Contract tests for all schema definitions (T011).
Validates that schema files are valid YAML and conform to expected structure.
"""
import pytest
import yaml
from pathlib import Path
import json
from jsonschema import validate, ValidationError, SchemaError

# Get the project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-evaluate-code-duplication-llm-understanding" / "contracts"

# Schema file paths
SCHEMA_FILES = {
    "clone_metrics": CONTRACTS_DIR / "clone_metrics.schema.yaml",
    "model_metrics": CONTRACTS_DIR / "model_metrics.schema.yaml",
    "correlation_results": CONTRACTS_DIR / "correlation_results.schema.yaml",
    "pipeline_config": CONTRACTS_DIR / "pipeline_config.schema.yaml",
}

# Sample valid data for each schema (for positive testing)
SAMPLE_DATA = {
    "clone_metrics": {
        "file_path": "data/raw/sample.py",
        "segment_id": 1,
        "clone_density": 0.75,
        "segment_length": 150,
        "clone_count": 3,
        "threshold_used": 0.8,
        "timestamp": "2026-01-15T10:30:00",
        "checksum": "a" * 64,
    },
    "model_metrics": {
        "file_path": "data/raw/sample.py",
        "segment_id": 1,
        "perplexity": 12.45,
        "token_count": 256,
        "model_name": "Salesforce/codegen-350M-mono",
        "quantization_bits": 8,
        "validation_status": "valid",
        "timestamp": "2026-01-15T10:30:00",
        "memory_peak_mb": 3500.0,
    },
    "correlation_results": {
        "correlation_id": 1,
        "threshold": 0.8,
        "correlation_type": "clone_perplexity",
        "spearman_rho": -0.42,
        "p_value": 0.003,
        "sample_size": 1500,
        "significance_level": 0.05,
        "is_significant": True,
        "confidence_interval_95": [-0.52, -0.31],
        "method": "spearman",
        "timestamp": "2026-01-15T10:30:00",
        "checksum": "b" * 64,
    },
    "pipeline_config": {
        "random_seed": 42,
        "clone_thresholds": [0.7, 0.8, 0.9],
        "memory_limit_mb": 7168,
        "max_runtime_seconds": 86400,
        "min_valid_segments": 1000,
        "correlation_method": "spearman",
        "significance_threshold": 0.05,
        "figure_format": "both",
        "figure_dpi": 300,
        "checksum_algorithm": "sha256",
        "dataset_name": "codeparrot/github-code",
        "model_name": "Salesforce/codegen-350M-mono",
        "quantization_bits": 8,
        "streaming_enabled": True,
        "pii_scan_enabled": True,
        "version": "1.0.0",
        "created_at": "2026-01-15T10:30:00",
    },
}

@pytest.fixture(scope="module")
def schemas():
    """Load all schema definitions."""
    loaded_schemas = {}
    for name, path in SCHEMA_FILES.items():
        with open(path, "r") as f:
            loaded_schemas[name] = yaml.safe_load(f)
    return loaded_schemas

class TestSchemaFilesExist:
    """Test that all schema files exist."""

    @pytest.mark.parametrize("name,path", SCHEMA_FILES.items())
    def test_schema_file_exists(self, name, path):
        assert path.exists(), f"Schema file {path} does not exist"

    @pytest.mark.parametrize("name,path", SCHEMA_FILES.items())
    def test_schema_file_is_yaml(self, name, path):
        assert path.suffix == ".yaml", f"Schema file {name} should have .yaml extension"

class TestSchemaFilesAreValidYaml:
    """Test that all schema files are valid YAML."""

    @pytest.mark.parametrize("name,path", SCHEMA_FILES.items())
    def test_yaml_parsing(self, path):
        with open(path, "r") as f:
            content = yaml.safe_load(f)
        assert content is not None, f"Schema {name} loaded as None"
        assert isinstance(content, dict), f"Schema {name} should be a dict"

class TestSchemaStructure:
    """Test that schemas have required structure."""

    def test_clone_metrics_has_required_fields(self, schemas):
        schema = schemas["clone_metrics"]
        assert "required" in schema, "clone_metrics schema missing 'required' field"
        required = schema["required"]
        assert "file_path" in required
        assert "segment_id" in required
        assert "clone_density" in required

    def test_model_metrics_has_required_fields(self, schemas):
        schema = schemas["model_metrics"]
        assert "required" in schema, "model_metrics schema missing 'required' field"
        required = schema["required"]
        assert "file_path" in required
        assert "perplexity" in required
        assert "validation_status" in required

    def test_correlation_results_has_required_fields(self, schemas):
        schema = schemas["correlation_results"]
        assert "required" in schema, "correlation_results schema missing 'required' field"
        required = schema["required"]
        assert "correlation_id" in required
        assert "spearman_rho" in required
        assert "p_value" in required

    def test_pipeline_config_has_required_fields(self, schemas):
        schema = schemas["pipeline_config"]
        assert "required" in schema, "pipeline_config schema missing 'required' field"
        required = schema["required"]
        assert "random_seed" in required
        assert "clone_thresholds" in required
        assert "version" in required

class TestSchemaValidation:
    """Test that sample data validates against schemas."""

    @pytest.mark.parametrize("name,schema", schemas.items())
    def test_sample_data_validates(self, name, schema, schemas):
        sample = SAMPLE_DATA[name]
        try:
            validate(instance=sample, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Sample data for {name} failed validation: {e.message}")

    def test_clone_density_range(self, schemas):
        schema = schemas["clone_metrics"]
        invalid_data = SAMPLE_DATA["clone_metrics"].copy()
        invalid_data["clone_density"] = 1.5  # Out of range
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_perplexity_non_negative(self, schemas):
        schema = schemas["model_metrics"]
        invalid_data = SAMPLE_DATA["model_metrics"].copy()
        invalid_data["perplexity"] = -1.0  # Negative
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_spearman_rho_range(self, schemas):
        schema = schemas["correlation_results"]
        invalid_data = SAMPLE_DATA["correlation_results"].copy()
        invalid_data["spearman_rho"] = 1.5  # Out of range
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_threshold_enum(self, schemas):
        schema = schemas["correlation_results"]
        invalid_data = SAMPLE_DATA["correlation_results"].copy()
        invalid_data["threshold"] = 0.5  # Not in enum
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

class TestSchemaVersioning:
    """Test that schemas follow versioning conventions."""

    def test_all_schemas_have_schema_url(self, schemas):
        for name, schema in schemas.items():
            assert "$schema" in schema, f"Schema {name} missing $schema"
            assert "json-schema" in schema["$schema"], f"Schema {name} should reference JSON Schema"

    def test_all_schemas_have_type_object(self, schemas):
        for name, schema in schemas.items():
            assert schema.get("type") == "object", f"Schema {name} should be type object"

class TestPipelineConfigThresholds:
    """Specific tests for pipeline config thresholds."""

    def test_clone_thresholds_includes_0_7_0_8_0_9(self, schemas):
        schema = schemas["pipeline_config"]
        sample = SAMPLE_DATA["pipeline_config"]
        assert 0.7 in sample["clone_thresholds"]
        assert 0.8 in sample["clone_thresholds"]
        assert 0.9 in sample["clone_thresholds"]

    def test_memory_limit_meets_sc002(self, schemas):
        sample = SAMPLE_DATA["pipeline_config"]
        # SC-002: 7GB limit = 7168 MB
        assert sample["memory_limit_mb"] <= 7168

    def test_min_segments_meets_sc003(self, schemas):
        sample = SAMPLE_DATA["pipeline_config"]
        # SC-003: At least 1000 valid segments
        assert sample["min_valid_segments"] >= 1000

    def test_runtime_meets_sc001(self, schemas):
        sample = SAMPLE_DATA["pipeline_config"]
        # SC-001: 24-hour completion = 86400 seconds
        assert sample["max_runtime_seconds"] <= 86400
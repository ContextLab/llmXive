import pytest
import json
import yaml
from pathlib import Path
import jsonschema

# Path to contracts directory relative to test execution
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"

def load_schema(schema_name: str) -> dict:
    """Load a JSON schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_sample_data():
    """Generate valid sample data for testing."""
    return {
        "sample_id": "S001",
        "timestamp": "2023-10-27T10:00:00Z",
        "pH": 6.5,
        "temperature": 12.5,
        "location": "Vent_A",
        "deployment_event": "DEP_001",
        "sensor_id": "SEN_123",
        "coordinates": "45.123,-123.456",
        "pH_sd": 0.05,
        "pH_heterogeneous": False
    }

def validate_otu_data():
    """Generate valid OTU data for testing."""
    return {
        "sample_id": "S001",
        "otu_id": "OTU_999",
        "count": 150,
        "taxonomy": ["Bacteria", "Proteobacteria", "Gammaproteobacteria"]
    }

def validate_diversity_data():
    """Generate valid diversity metric data for testing."""
    return {
        "sample_id": "S001",
        "metric_name": "shannon",
        "value": 3.45,
        "rarefaction_depth": 10000,
        "model_type": None,
        "estimate": None,
        "se": None,
        "p_value": None
    }

@pytest.fixture
def sample_schema():
    return load_schema("sample_schema.schema.yaml")

@pytest.fixture
def otu_schema():
    return load_schema("otu_table_schema.schema.yaml")

@pytest.fixture
def analysis_schema():
    return load_schema("analysis_results_schema.schema.yaml")

class TestSampleSchema:
    def test_valid_sample(self, sample_schema):
        data = validate_sample_data()
        jsonschema.validate(data, sample_schema)

    def test_missing_required_field(self, sample_schema):
        data = validate_sample_data()
        del data["sample_id"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, sample_schema)

    def test_invalid_ph_range(self, sample_schema):
        data = validate_sample_data()
        data["pH"] = 15.0
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, sample_schema)

class TestOTUSchema:
    def test_valid_otu(self, otu_schema):
        data = validate_otu_data()
        jsonschema.validate(data, otu_schema)

    def test_negative_count(self, otu_schema):
        data = validate_otu_data()
        data["count"] = -1
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, otu_schema)

class TestAnalysisSchema:
    def test_valid_diversity(self, analysis_schema):
        data = validate_diversity_data()
        jsonschema.validate(data, analysis_schema)

    def test_invalid_metric_name(self, analysis_schema):
        data = validate_diversity_data()
        data["metric_name"] = "invalid_metric"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, analysis_schema)

    def test_p_value_range(self, analysis_schema):
        data = validate_diversity_data()
        data["metric_name"] = "lme_result"
        data["p_value"] = 1.5
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, analysis_schema)
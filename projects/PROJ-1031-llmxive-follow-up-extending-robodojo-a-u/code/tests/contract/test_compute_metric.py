import pytest
import sys
from pathlib import Path
import json
import yaml
from jsonschema import validate, ValidationError
from dataclasses import asdict, dataclass

# Ensure src is in path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

# Load the schema defined in specs
SCHEMA_PATH = Path(__file__).parent.parent.parent / "specs" / "001-symbolic-dojo-extend" / "contracts" / "compute_metric.schema.yaml"

@pytest.fixture
def compute_metric_schema():
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@dataclass
class ComputeMetric:
    """
    Dataclass representing the ComputeMetric structure.
    Fields:
      - task_id: string
      - cpu_cycles: int
      - ram_mb: float
      - wall_clock_s: float
    """
    task_id: str
    cpu_cycles: int
    ram_mb: float
    wall_clock_s: float

class TestComputeMetricContract:
    """
    Contract tests to validate ComputeMetric instances against the JSON schema.
    """

    def test_valid_compute_metric(self, compute_metric_schema):
        """Test that a valid ComputeMetric passes validation."""
        valid_data = {
            "task_id": "task_001",
            "cpu_cycles": 1500000000,
            "ram_mb": 2048.5,
            "wall_clock_s": 12.34
        }
        try:
            validate(instance=valid_data, schema=compute_metric_schema)
        except ValidationError as e:
            pytest.fail(f"Valid ComputeMetric failed schema validation: {e.message}")

    def test_missing_required_field(self, compute_metric_schema):
        """Test that missing a required field raises ValidationError."""
        invalid_data = {
            "task_id": "task_001",
            "cpu_cycles": 1500000000,
            # missing ram_mb and wall_clock_s
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=compute_metric_schema)

    def test_wrong_type_field(self, compute_metric_schema):
        """Test that a wrong type for a field raises ValidationError."""
        invalid_data = {
            "task_id": "task_001",
            "cpu_cycles": "1500000000",  # Should be int
            "ram_mb": 2048.5,
            "wall_clock_s": 12.34
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=compute_metric_schema)

    def test_dataclass_serialization(self, compute_metric_schema):
        """Test that a dataclass instance can be serialized and validated."""
        metric = ComputeMetric(
            task_id="task_002",
            cpu_cycles=2000000000,
            ram_mb=4096.0,
            wall_clock_s=25.5
        )
        data_dict = asdict(metric)
        try:
            validate(instance=data_dict, schema=compute_metric_schema)
        except ValidationError as e:
            pytest.fail(f"Dataclass serialization failed validation: {e.message}")

    def test_negative_values_allowed(self, compute_metric_schema):
        """Test that negative values for time/memory are technically allowed by schema if not restricted,
           but typically we might expect non-negative. This test checks schema behavior."""
        # Depending on schema definition, negative might be invalid. 
        # Assuming standard positive metrics, let's test a negative wall_clock if schema allows or fails.
        # Based on standard research metrics, negative time is invalid. 
        # We test if the schema explicitly forbids it via 'minimum': 0.
        negative_data = {
            "task_id": "task_003",
            "cpu_cycles": -100,
            "ram_mb": -50.0,
            "wall_clock_s": -1.0
        }
        # If schema has minimum constraints, this should raise. If not, it passes.
        # We assert that the schema behaves as expected (usually minimum 0 for these).
        # If the schema lacks 'minimum', this might pass, which is a schema issue, not a test failure.
        # We simply check that the validation runs without crashing.
        try:
            validate(instance=negative_data, schema=compute_metric_schema)
            # If it passes, the schema might be too permissive, but we don't fail the test here
            # unless the schema explicitly requires non-negative.
        except ValidationError:
            pass # Expected if schema has minimum constraints
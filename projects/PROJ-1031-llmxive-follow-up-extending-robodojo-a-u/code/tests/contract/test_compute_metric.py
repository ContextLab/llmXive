import pytest
import sys
from pathlib import Path
import json
import yaml
from jsonschema import validate, ValidationError

# Load the schema
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "specs" / "001-symbolic-dojo-extend" / "contracts" / "compute_metric.schema.yaml"

@pytest.fixture(scope="module")
def compute_metric_schema():
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Please ensure T005c has been completed.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

class ComputeMetric:
    """Simple dataclass-like structure for testing."""
    def __init__(self, task_id, cpu_cycles, ram_mb, wall_clock_s):
        self.task_id = task_id
        self.cpu_cycles = cpu_cycles
        self.ram_mb = ram_mb
        self.wall_clock_s = wall_clock_s

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "cpu_cycles": self.cpu_cycles,
            "ram_mb": self.ram_mb,
            "wall_clock_s": self.wall_clock_s
        }

class TestComputeMetricContract:
    def test_valid_compute_metric(self, compute_metric_schema):
        """Test that a valid ComputeMetric object passes validation."""
        valid_data = {
            "task_id": "task_001",
            "cpu_cycles": 1500000,
            "ram_mb": 2048.5,
            "wall_clock_s": 12.34
        }
        validate(instance=valid_data, schema=compute_metric_schema)

    def test_missing_required_field(self, compute_metric_schema):
        """Test that missing required fields raise ValidationError."""
        invalid_data = {
            "task_id": "task_001",
            "cpu_cycles": 1500000,
            "ram_mb": 2048.5
            # Missing wall_clock_s
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=compute_metric_schema)

    def test_invalid_type_cpu_cycles(self, compute_metric_schema):
        """Test that non-integer cpu_cycles raises ValidationError."""
        invalid_data = {
            "task_id": "task_001",
            "cpu_cycles": "1500000",  # Should be int
            "ram_mb": 2048.5,
            "wall_clock_s": 12.34
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=compute_metric_schema)

    def test_negative_values(self, compute_metric_schema):
        """Test that negative values for numeric fields raise ValidationError."""
        invalid_data = {
            "task_id": "task_001",
            "cpu_cycles": -100,
            "ram_mb": 2048.5,
            "wall_clock_s": 12.34
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=compute_metric_schema)

    def test_extra_properties(self, compute_metric_schema):
        """Test that extra properties raise ValidationError (additionalProperties: false)."""
        invalid_data = {
            "task_id": "task_001",
            "cpu_cycles": 1500000,
            "ram_mb": 2048.5,
            "wall_clock_s": 12.34,
            "extra_field": "should_not_exist"
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=compute_metric_schema)

    def test_from_compute_metric_object(self, compute_metric_schema):
        """Test validation using the ComputeMetric helper class."""
        obj = ComputeMetric(
            task_id="task_002",
            cpu_cycles=2000000,
            ram_mb=4096.0,
            wall_clock_s=25.5
        )
        validate(instance=obj.to_dict(), schema=compute_metric_schema)

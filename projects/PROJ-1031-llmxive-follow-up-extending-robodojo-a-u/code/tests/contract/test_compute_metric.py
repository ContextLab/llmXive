import pytest
import sys
from pathlib import Path
import json
import yaml
from jsonschema import validate, ValidationError

# Load schema
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "specs" / "001-symbolic-dojo-extend" / "contracts" / "compute_metric.schema.yaml"

@pytest.fixture(scope="module")
def compute_metric_schema():
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

class ComputeMetric:
    """Simple data class to mimic the structure expected by the schema."""
    def __init__(self, task_id: str, cpu_cycles: int, ram_mb: float, wall_clock_s: float):
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
        """Test that a valid ComputeMetric passes validation."""
        metric = ComputeMetric(
            task_id="task_001",
            cpu_cycles=1500000,
            ram_mb=512.5,
            wall_clock_s=12.3
        )
        validate(instance=metric.to_dict(), schema=compute_metric_schema)

    def test_missing_required_field(self, compute_metric_schema):
        """Test that missing a required field raises ValidationError."""
        invalid_metric = {
            "task_id": "task_002",
            "cpu_cycles": 1000000,
            # Missing ram_mb and wall_clock_s
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_metric, schema=compute_metric_schema)

    def test_wrong_type_field(self, compute_metric_schema):
        """Test that wrong types raise ValidationError."""
        invalid_metric = {
            "task_id": "task_003",
            "cpu_cycles": "not_an_int",  # Should be int
            "ram_mb": 256.0,
            "wall_clock_s": 5.0
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_metric, schema=compute_metric_schema)

    def test_extra_properties_rejected(self, compute_metric_schema):
        """Test that extra properties are rejected (additionalProperties: false)."""
        invalid_metric = {
            "task_id": "task_004",
            "cpu_cycles": 1000000,
            "ram_mb": 256.0,
            "wall_clock_s": 5.0,
            "extra_field": "should_fail"
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_metric, schema=compute_metric_schema)
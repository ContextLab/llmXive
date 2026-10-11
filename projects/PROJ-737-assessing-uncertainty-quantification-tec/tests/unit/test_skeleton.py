"""Unit tests for task T001 – project skeleton verification."""

import yaml
from pathlib import Path

from llmxive_toolkit import paths

def test_directories_exist():
    """All required directories must exist after the skeleton script runs."""
    required = [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
        paths.figures(),
        paths.code("models"),
        paths.code("metrics"),
        paths.code("stats"),
        paths.code("utils"),
        paths.tests("unit"),
        paths.tests("integration"),
    ]
    missing = [str(p) for p in required if not p.is_dir()]
    assert not missing, f"Missing required directories: {', '.join(missing)}"

def test_schema_file_exists_and_valid():
    """The per_sample_errors.schema.yaml file must exist and contain the expected columns."""
    schema_path = Path(
        paths.root,
        "specs",
        "001-assessing-uncertainty-quantification-tec",
        "contracts",
        "per_sample_errors.schema.yaml",
    )
    assert schema_path.is_file(), f"Schema file not found at {schema_path}"

    with schema_path.open("r", encoding="utf-8") as f:
        content = yaml.safe_load(f)

    expected_columns = [
        "sample_id",
        "dataset",
        "method",
        "prediction",
        "lower_bound",
        "upper_bound",
        "ground_truth",
        "abs_error",
    ]
    assert isinstance(content, dict), "Schema content must be a mapping."
    assert "columns" in content, "Schema must define a 'columns' key."
    assert content["columns"] == expected_columns, (
        f"Schema columns mismatch. Expected {expected_columns}, got {content['columns']}"
    )
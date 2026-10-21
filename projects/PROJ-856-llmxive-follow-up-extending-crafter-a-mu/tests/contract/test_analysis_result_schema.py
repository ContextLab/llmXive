import json
from pathlib import Path

import jsonschema
import pytest

from llmxive_toolkit import paths

# Load the JSON schema for analysis results
schema_path = Path(__file__).parents[2] / "specs" / "001-llmxive-cognitive-load" / "contracts" / "analysis_result.schema.yaml"
with schema_path.open("r", encoding="utf-8") as f:
    schema = jsonschema.Draft7Validator(json.load(f))

def test_analysis_results_schema():
    # The analysis script writes its output to ``outputs/analysis_results.jsonl``
    results_path = paths.outputs("analysis_results.jsonl")
    assert results_path.is_file(), f"Expected analysis results at {results_path}"

    with results_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            # Validate each record against the schema
            schema.validate(record)
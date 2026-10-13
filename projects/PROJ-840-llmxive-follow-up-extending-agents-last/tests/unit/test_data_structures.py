import json
import pathlib
import pytest
from jsonschema import validate, ValidationError

# The schema we need to validate against
SCHEMA_PATH = pathlib.Path(__file__).parents[2] / "specs" / "001-llmxive-follow-up-extending-agents-last" / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

def test_generated_golden_fixture_structure(schema):
    """
    Runs the generator and validates each step object against the dataset schema.
    """
    # Import the generator function from the module under test
    from code.data.generator import generate_golden_fixture

    # Produce the fixture in a temporary location
    output_path = pathlib.Path("data/raw/golden_fixture_test.json")
    traces = generate_golden_fixture(seed_base=42, num_tasks=10, output_path=str(output_path))

    # Load the written file and validate each step
    with open(output_path, "r") as f:
        data = json.load(f)

    # Each trace contains a list of step dicts under the key "trace" -> "steps"
    for entry in data:
        trace = entry.get("trace", {})
        steps = trace.get("steps", [])
        for step in steps:
            # The schema validates a single step object
            try:
                validate(instance=step, schema=schema)
            except ValidationError as ve:
                pytest.fail(f"Step validation failed: {ve.message}")

    # Clean up
    output_path.unlink()
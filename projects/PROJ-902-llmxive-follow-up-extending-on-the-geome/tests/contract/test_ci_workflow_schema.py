import pathlib
import yaml
from jsonschema import Draft7Validator, ValidationError

def _load_yaml(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_ci_workflow_schema():
    # Resolve repository root (two levels up from the test file's directory)
    repo_root = pathlib.Path(__file__).resolve().parents[3]

    ci_path = repo_root / ".github" / "workflows" / "ci.yml"
    schema_path = repo_root / "contracts" / "ci_workflow.schema.yaml"

    ci_yaml = _load_yaml(ci_path)
    schema_yaml = _load_yaml(schema_path)

    # Validate against JSON Schema
    validator = Draft7Validator(schema_yaml)
    errors = sorted(validator.iter_errors(ci_yaml), key=lambda e: e.path)
    if errors:
        messages = "\n".join(
            f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors
        )
        raise AssertionError(f"CI workflow does not conform to schema:\n{messages}")

    # Additional custom check: ensure a RAM‑limit step is present
    steps = ci_yaml.get("jobs", {}).get("experiment", {}).get("steps", [])
    ram_step_present = any(
        "ram limit" in step.get("name", "").lower() for step in steps
    )
    assert ram_step_present, "CI workflow must contain a step that enforces the 7 GB RAM limit"

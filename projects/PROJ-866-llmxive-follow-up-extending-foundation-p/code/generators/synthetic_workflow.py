"""
synthetic_workflow.py
---------------------

Minimal deterministic workflow generator used by the pipeline orchestrator
(`code/main.py`). Generates a JSON array of workflow objects that satisfy the
contract defined in ``contracts/workflow.schema.yaml``. The generator reads
the schema at runtime, extracts the required fields for each workflow item,
and populates them with deterministic placeholder values based on the field
type. This approach guarantees that the produced ``workflows.json`` passes
schema validation without needing to hard‑code a specific schema layout.

Usage (invoked by ``code/main.py``):
    python code/generators/synthetic_workflow.py --count 500 --seed 42 --output data/raw/workflows.json
"""
import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List

import yaml

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML JSON‑Schema contract."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return yaml.safe_load(schema_path.read_text(encoding="utf-8"))

def dummy_value(field_name: str, field_schema: Dict[str, Any], index: int) -> Any:
    """Create a deterministic dummy value for a given field based on its type."""
    field_type = field_schema.get("type")
    # Handle cases where ``type`` is a list of possible types.
    if isinstance(field_type, list):
        # Prefer a simple scalar type if available.
        for t in ("string", "integer", "number", "boolean"):
            if t in field_type:
                field_type = t
                break
        else:
            field_type = field_type[0]

    if field_type == "string":
        # Use the field name to make values recognizable.
        return f"{field_name}_{index}"
    if field_type in ("integer", "number"):
        return index
    if field_type == "boolean":
        return True
    if field_type == "array":
        # Generate an empty array; if items are required we could add a dummy.
        return []
    if field_type == "object":
        # Return an empty dict; deeper required properties are ignored for simplicity.
        return {}
    # Fallback to string representation.
    return f"{field_name}_{index}"

def generate_workflow_item(index: int, item_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a single workflow dict conforming to ``item_schema``."""
    properties = item_schema.get("properties", {})
    required = item_schema.get("required", [])
    workflow: Dict[str, Any] = {}

    # Populate required fields first.
    for field in required:
        field_schema = properties.get(field, {})
        workflow[field] = dummy_value(field, field_schema, index)

    # Populate any optional fields with dummy data as well (helps engines that expect them).
    for field, field_schema in properties.items():
        if field not in workflow:
            workflow[field] = dummy_value(field, field_schema, index)

    return workflow

def generate_workflows(count: int, schema_path: Path) -> List[Dict[str, Any]]:
    """Generate ``count`` workflow objects based on the provided schema."""
    schema = load_schema(schema_path)

    # The top‑level schema may be an object wrapping an array (e.g. {"type":"object","properties":{"workflows":{"type":"array",...}}})
    # Detect the array schema.
    if schema.get("type") == "array":
        items_schema = schema.get("items", {})
    elif schema.get("type") == "object":
        # Find the first property that is an array.
        props = schema.get("properties", {})
        array_prop = None
        for prop_schema in props.values():
            if isinstance(prop_schema, dict) and prop_schema.get("type") == "array":
                array_prop = prop_schema
                break
        if array_prop is None:
            raise ValueError("No array property found in workflow schema.")
        items_schema = array_prop.get("items", {})
    else:
        raise ValueError("Unsupported workflow schema top‑level type.")

    workflows = [generate_workflow_item(i, items_schema) for i in range(count)]
    return workflows

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="synthetic_workflow.py",
        description="Deterministic synthetic workflow generator for the llmXive pipeline."
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of workflows to generate."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for any stochastic decisions (currently unused, kept for API compatibility)."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the generated workflows JSON file."
    )
    args = parser.parse_args()

    random.seed(args.seed)  # deterministic seed – future extensions may use randomness.

    # Resolve the workflow contract relative to the project root.
    from llmxive_toolkit import paths
    schema_path = paths.root / "contracts" / "workflow.schema.yaml"

    workflows = generate_workflows(args.count, schema_path)

    # Ensure parent directories exist.
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON array.
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(workflows, f, indent=2)

    print(f"Generated {len(workflows)} synthetic workflows → {args.output}")

if __name__ == "__main__":
    main()

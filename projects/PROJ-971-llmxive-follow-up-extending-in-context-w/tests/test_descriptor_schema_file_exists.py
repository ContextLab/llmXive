"""
Simple sanity test to ensure the descriptor JSON‑Schema file is present.
This helps catch missing‑file errors early in CI.
"""
import pathlib

def test_schema_file_exists():
    schema_path = (
        pathlib.Path(__file__).parents[2]
        / "specs"
        / "001-llmxive-follow-up-extending-in-context-w"
        / "contracts"
        / "descriptor.schema.yaml"
    )
    assert schema_path.is_file(), f"Schema file not found at {schema_path}"
"""
Simple sanity test to ensure the descriptor JSON‑Schema file is present.
This helps catch missing‑file errors early in CI.
"""
import pathlib

def test_schema_file_exists():
    # The schema resides in the project’s own ``specs`` directory.
    # Adjusted path to correctly locate the file relative to this test file.
    schema_path = (
        pathlib.Path(__file__).parents[1]  # project root (where ``specs`` lives)
        / "specs"
        / "001-llmxive-follow-up-extending-in-context-w"
        / "contracts"
        / "descriptor.schema.yaml"
    )
    assert schema_path.is_file(), f"Schema file not found at {schema_path}"

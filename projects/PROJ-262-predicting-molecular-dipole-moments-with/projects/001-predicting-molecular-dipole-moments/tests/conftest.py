import pathlib
import yaml
import jsonschema
import pytest


def _load_schema(schema_name: str):
    """
    Load a YAML schema from the ``contracts`` directory.

    Parameters
    ----------
    schema_name: str
        Base name of the schema file (without extension).

    Returns
    -------
    dict
        The parsed JSON schema.
    """
    schema_path = pathlib.Path(__file__).parent / "contracts" / f"{schema_name}.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def validate_schema():
    """
    Fixture that returns a callable to validate a data object against a named schema.

    Usage in a test::

        def test_example(validate_schema):
            data = {"name": "water", "dipole": 1.85}
            validate_schema(data, "molecule")
    """

    def _validate(data, schema_name: str):
        schema = _load_schema(schema_name)
        jsonschema.validate(instance=data, schema=schema)

    return _validate

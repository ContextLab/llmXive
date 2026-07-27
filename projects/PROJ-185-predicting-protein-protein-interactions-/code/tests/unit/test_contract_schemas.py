import pathlib
import yaml
import pytest

# Relative paths from the repository root to each schema file.
SCHEMA_FILES = [
    "contracts/predicted_ppi.schema.yaml",
    "contracts/evaluation.schema.yaml",
    "contracts/threshold_sensitivity.schema.yaml",
    "contracts/pipeline_log.schema.yaml",
]

@pytest.mark.parametrize("schema_path", SCHEMA_FILES)
def test_schema_is_valid_yaml(schema_path):
    """
    Ensure each contract schema can be parsed as valid YAML and
    results in a dictionary (i.e., a JSON‑Schema object).
    """
    # The test file lives in <repo>/code/tests/unit/
    repo_root = pathlib.Path(__file__).resolve().parents[3]  # up to repo root
    full_path = repo_root / schema_path
    with open(full_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"{schema_path} did not load as a dict"

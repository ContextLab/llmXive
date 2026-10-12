import pathlib
import yaml
import jsonschema
import pytest

# Directory containing the contract schemas
SPEC_ROOT = (
    pathlib.Path(__file__).resolve()
    .parents[2]  # move from tests/contract to project root
    / "specs"
    / "001‑exploring‑the‑correlation‑between‑molecu"
    / "contracts"
)

# Mapping from schema filename to a minimal instance that complies with it
MINIMAL_INSTANCES = {
    "dataset.schema.yaml": {
        "smiles": "CCO",
        "logPapp": 1.23,
        "protocol_metadata": {"standard_type": "MEASUREMENT"},
    },
    "descriptor.schema.yaml": {
        "smiles": "CCO",
        "dihedral_variance": 0.001,
        "bond_variance": 0.0005,
        "angle_variance": 0.0002,
        "conformer_count": 50,
        "converged": True,
    },
    "analysis_output.schema.yaml": {
        "model_performance": {
            "mean_r2": 0.45,
            "std_r2": 0.10,
            "rmse": 0.75,
            "mae": 0.60,
            "coefficients": {
                "dihedral_variance": 0.3,
                "logP": -0.2,
                "mw": 0.01,
                "psa": -0.05,
            },
        }
    },
    "correlation.schema.yaml": {
        "descriptor": "dihedral_variance",
        "pearson_r": 0.42,
        "pearson_p": 0.001,
        "spearman_r": 0.38,
        "spearman_p": 0.003,
    },
    "flexibility.schema.yaml": {
        "smiles": "CCO",
        "dihedral_variance": 0.001,
        "size_normalized_flexibility": 0.0002,
    },
    "output.schema.yaml": {
        "path": "data/processed/model_results.json",
        "type": "json",
        "checksum": "d41d8cd98f00b204e9800998ecf8427e" * 2,  # 64‑char dummy SHA‑256
    },
}


@pytest.mark.parametrize("schema_file", list(MINIMAL_INSTANCES.keys()))
def test_schema_validity(schema_file):
    """
    Load each contract schema and validate a minimal compliant instance.
    """
    schema_path = SPEC_ROOT / schema_file
    assert schema_path.is_file(), f"Schema file missing: {schema_path}"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    instance = MINIMAL_INSTANCES[schema_file]

    # jsonschema.validate will raise if the instance does not conform
    jsonschema.validate(instance=instance, schema=schema)


def test_all_schemas_covered():
    """
    Ensure that every YAML file in the contracts directory has a corresponding test entry.
    """
    yaml_files = sorted(p.name for p in SPEC_ROOT.glob("*.yaml"))
    missing = [f for f in yaml_files if f not in MINIMAL_INSTANCES]
    assert not missing, f"Missing minimal instance definitions for: {missing}"
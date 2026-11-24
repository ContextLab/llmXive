"""
Contract validation tests for JSON‑Schema files in the ``contracts`` directory.
Each schema is exercised with a minimal in‑memory example that satisfies the
required fields. The test ensures that ``jsonschema.validate`` succeeds,
providing confidence that downstream scripts can rely on these contracts.
"""

import json
import yaml
from pathlib import Path

import jsonschema


# Helper to load a YAML schema from the contracts folder
def load_schema(schema_name: str) -> dict:
    schema_path = Path(__file__).parents[2] / "contracts" / schema_name
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Minimal valid instances for each schema
MINIMAL_INSTANCES = {
    "dataset.schema.yaml": {
        "species_id": "TRY12345",
        "species_name": "Quercus robur",
    },
    "rsametrics.schema.yaml": {
        "species_id": "TRY12345",
        "depth": 150.0,
        "branching_density": 0.35,
        "surface_area": 4200.0,
    },
    "merged_data.schema.yaml": {
        "species_id": "TRY12345",
        "depth": 150.0,
        "branching_density": 0.35,
        "surface_area": 4200.0,
        "stomatal_conductance": 0.28,
        "photosynthetic_rate": 12.5,
    },
    "model_results.schema.yaml": {
        "model_type": "MLR",
        "predictor": "depth",
        "coefficient": 0.012,
        "p_value": 0.043,
        "r2": 0.31,
        "adj_p_value": 0.048,
    },
    "output.schema.yaml": {
        "report_path": "results/reports/final_report.md",
        "sections": [
            "VIF & PCA",
            "Regression Results",
            "Classification",
            "Sensitivity Analysis",
            "Phylogenetic Correction"
        ],
    },
    "results.schema.yaml": {
        "file_path": "results/sensitivity_fpr_fnr.csv",
        "columns": [
            "threshold",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "fpr",
            "fnr"
        ],
    },
}


def test_all_contracts():
    """
    Iterate over every schema in ``contracts`` and validate a minimal
    instance against it.
    """
    contracts_dir = Path(__file__).parents[2] / "contracts"
    for schema_file in contracts_dir.glob("*.schema.yaml"):
        schema = load_schema(schema_file.name)
        instance = MINIMAL_INSTANCES.get(schema_file.name)
        assert instance is not None, f"No test instance defined for {schema_file.name}"
        
        # jsonschema.validate will raise ValidationError if the instance does not
        # conform; the test will fail in that case.
        jsonschema.validate(instance=instance, schema=schema)
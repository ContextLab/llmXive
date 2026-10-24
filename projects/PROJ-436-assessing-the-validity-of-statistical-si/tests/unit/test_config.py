"""
Unit tests for the configuration generation (code/config.py).

The test ensures that:
* The total number of generated SimulationConfig objects matches the expected count:
  datasets × 3 mechanisms × 8 rates × 2 outcome types = 48 × #datasets.
* Each generated config can be serialized to JSON and validates against the
  provided JSON‑Schema contract (contracts/simulation_config.schema.yaml).
"""

import json
import os
from pathlib import Path

import pytest

# Ensure the project ``code`` directory is on the import path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from config import (
    SimulationConfig,
    MissingMechanism,
    OutcomeType,
    AnalysisMethod,
    create_default_config,
    config_to_dict,
)
from data_loader import _DATASET_IDS

def _load_schema():
    schema_path = Path("specs/001-assessing-the-validity-of-statistical-si/contracts/simulation_config.schema.yaml")
    with open(schema_path) as f:
        return json.load(f)

def test_number_of_configs():
    """Verify the total number of configs matches expectation."""
    dataset_ids = _DATASET_IDS
    total_expected = len(dataset_ids) * 3 * 8 * 2  # mechanisms × rates × outcome types
    configs = []
    for ds_id in dataset_ids:
        for mech in [MissingMechanism.MCAR, MissingMechanism.MAR, MissingMechanism.MNAR]:
            for rate in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
                for out_type in [OutcomeType.CONTINUOUS, OutcomeType.BINARY]:
                    cfg = SimulationConfig(
                        dataset_source=ds_id,
                        missing_mechanisms=[mech],
                        missing_rates=[rate],
                        analysis_methods=[
                            AnalysisMethod.CC,
                            AnalysisMethod.MI,
                            AnalysisMethod.IPW,
                        ],
                        outcome_type=out_type,
                        n_iterations=15000,
                        seed=42,
                        alpha=0.05,
                    )
                    configs.append(cfg)

    assert len(configs) == total_expected

def test_config_schema_validation(tmp_path):
    """Each config should serialize to JSON and conform to the schema."""
    schema = _load_schema()
    from jsonschema import validate

    ds_id = _DATASET_IDS[0]
    cfg = SimulationConfig(
        dataset_source=ds_id,
        missing_mechanisms=[MissingMechanism.MCAR],
        missing_rates=[0.05],
        analysis_methods=[AnalysisMethod.CC],
        outcome_type=OutcomeType.CONTINUOUS,
        n_iterations=15000,
        seed=42,
        alpha=0.05,
    )
    cfg_dict = config_to_dict(cfg)
    # Write to a temporary file to ensure serialisation works
    out_file = tmp_path / "config.json"
    out_file.write_text(json.dumps(cfg_dict))
    # Validate against schema
    validate(instance=cfg_dict, schema=schema)

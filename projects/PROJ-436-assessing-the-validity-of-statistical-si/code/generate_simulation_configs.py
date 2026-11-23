"""
Generate exhaustive SimulationConfig JSON files for all verified datasets.

For each dataset identified by ``data_loader._DATASET_IDS`` this script creates
configuration JSON files covering every combination of:

* Missingness mechanism: MCAR, MAR, MNAR
* Missingness rate: 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40
* Outcome type: continuous, binary
* Analysis methods: CC, MI, IPW (included in every config)

The resulting JSON follows the ``simulation_config.schema.yaml`` contract:
it contains the fields ``dataset_id``, ``missingness_mechanism``,
``missingness_rate``, ``outcome_type``, ``seed``, ``n_iterations`` and
``analysis_methods``.  Each config uses a unique seed (incremented per
configuration) and a fixed ``n_iterations`` of 15000.

All files are written under ``data/processed/configs/`` using the
``paths`` helper from ``llmxive_toolkit`` which guarantees the directory
exists.  After writing each file the script validates the JSON against the
schema; any validation error aborts the run with a clear exception.
"""

import json
import logging
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from jsonschema import validate, ValidationError

# Import the list of verified dataset identifiers.
# The data_loader module defines ``_DATASET_IDS`` as a list of integers.
from data_loader import _DATASET_IDS

logger = get_logger(__name__, level=logging.INFO)

# ----------------------------------------------------------------------
# Schema loading
# ----------------------------------------------------------------------
def _load_schema() -> dict:
    """Load the JSON‑Schema for SimulationConfig."""
    schema_path = Path("specs/001-assessing-the-validity-of-statistical-si/contracts/simulation_config.schema.yaml")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------------------------------------
# Configuration generation
# ----------------------------------------------------------------------
MISSING_MECHANISMS = ["MCAR", "MAR", "MNAR"]
MISSING_RATES = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
OUTCOME_TYPES = ["continuous", "binary"]
ANALYSIS_METHODS = ["CC", "MI", "IPW"]
BASE_SEED = 42
N_ITERATIONS = 15000

def _make_config_dict(
    dataset_id: int,
    mechanism: str,
    rate: float,
    outcome_type: str,
    seed: int,
) -> dict:
    """
    Build a dictionary that conforms to the simulation_config.schema.yaml.

    The schema expects ``dataset_id`` as a string, so we cast accordingly.
    """
    return {
        "dataset_id": str(dataset_id),
        "missingness_mechanism": mechanism,
        "missingness_rate": rate,
        "outcome_type": outcome_type,
        "seed": seed,
        "n_iterations": N_ITERATIONS,
        "analysis_methods": ANALYSIS_METHODS,
    }

def generate_configs() -> None:
    """
    Iterate over all combinations and write a JSON file for each.
    Files are named ``{dataset}_{mech}_{rate}_{outcome}.json``.
    """
    schema = _load_schema()
    total = 0
    for dataset_id in _DATASET_IDS:
        for mech in MISSING_MECHANISMS:
            for rate in MISSING_RATES:
                for out_type in OUTCOME_TYPES:
                    # Increment seed per config to guarantee uniqueness.
                    seed = BASE_SEED + total
                    config_dict = _make_config_dict(
                        dataset_id=dataset_id,
                        mechanism=mech,
                        rate=rate,
                        outcome_type=out_type,
                        seed=seed,
                    )

                    # Validate against the schema before writing.
                    try:
                        validate(instance=config_dict, schema=schema)
                    except ValidationError as exc:
                        logger.error(
                            f"Generated config failed schema validation: {exc.message}"
                        )
                        raise

                    # Determine output path.
                    filename = f"{dataset_id}_{mech}_{int(rate*100)}_{out_type}.json"
                    out_path = paths.data("processed", "configs", filename)

                    # Write JSON.
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(
                        json.dumps(config_dict, indent=2, ensure_ascii=False)
                    )
                    logger.info(f"Wrote config: {out_path}")
                    total += 1

    logger.info(f"Generated {total} simulation config files.")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    generate_configs()

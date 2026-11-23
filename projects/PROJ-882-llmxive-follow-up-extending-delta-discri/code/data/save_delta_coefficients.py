"""
Save Delta coefficients to a JSON file while validating against the
contract schema.

This script is the implementation of task **T015a**. It:
  1. Executes the Oracle generation pipeline (`code/data/generate_oracle.py`)
     to obtain a list of `DeltaCoefficient` objects.
  2. Serialises those objects into plain Python dictionaries.
  3. Loads the JSON‑Schema definition from
     `contracts/delta_oracle.schema.yaml`.
  4. Validates the serialised data against the schema using
     ``jsonschema``.
  5. Writes the validated data to
     ``data/processed/delta_coefficients.json``.
The script can be run directly:
    python code/data/save_delta_coefficients.py
"""
import json
import logging
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError

# Import the public API of the Oracle generation module.
# The module provides a ``main`` function that returns a list of
# ``DeltaCoefficient`` objects (or dict‑like structures).
from data.generate_oracle import main as generate_oracle_main, DeltaCoefficient

def load_schema(schema_path: Path):
    """Load a JSON‑Schema from a YAML file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _as_dict(obj):
    """Convert a DeltaCoefficient (or any dataclass‑like object) to a plain dict."""
    if isinstance(obj, dict):
        return obj
    # ``vars`` works for dataclasses and simple objects with ``__dict__``.
    return vars(obj)

def serialize_coefficients(coeffs):
    """
    Turn the list returned by ``generate_oracle_main`` into a list of plain
    dictionaries ready for JSON serialisation.
    """
    return [_as_dict(c) for c in coeffs]

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # 1. Run the Oracle to obtain raw coefficient objects.
    # ------------------------------------------------------------------
    logger.info("Running Delta Oracle to compute coefficients...")
    try:
        raw_coeffs = generate_oracle_main()
    except Exception as exc:
        logger.error("Oracle generation failed: %s", exc)
        raise

    # ------------------------------------------------------------------
    # 2. Serialise to plain Python structures.
    # ------------------------------------------------------------------
    logger.info("Serialising %d coefficient records...", len(raw_coeffs))
    records = serialize_coefficients(raw_coeffs)

    # ------------------------------------------------------------------
    # 3. Load and validate against the contract schema.
    # ------------------------------------------------------------------
    schema_path = Path("contracts/delta_oracle.schema.yaml")
    logger.info("Loading schema from %s", schema_path)
    schema = load_schema(schema_path)

    logger.info("Validating records against the schema...")
    try:
        validate(instance=records, schema=schema)
    except ValidationError as ve:
        logger.error("Schema validation error: %s", ve)
        # Propagate the error so the pipeline fails loudly.
        raise

    # ------------------------------------------------------------------
    # 4. Write the validated JSON output.
    # ------------------------------------------------------------------
    out_path = Path("data/processed/delta_coefficients.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Writing validated coefficients to %s", out_path)
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(records, fp, indent=2, ensure_ascii=False)

    logger.info("Delta coefficients saved successfully.")

if __name__ == "__main__":
    main()

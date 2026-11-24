"""
Pytest schema‑lint test for the GameRecord contract.
It verifies that:
1. The YAML schema file can be loaded without error.
2. A known‑good DataFrame conforms to the schema.
"""

import pandas as pd
from pathlib import Path

from src.validation.validate_contracts import (
    load_schema,
    validate_dataframe_against_contract,
    SchemaValidationError,
)


def test_game_record_schema_load_and_validate():
    # Path to the contract schema
    schema_path = Path("specs/contracts/game_record.schema.yaml")
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

    # Load the schema (will raise if malformed)
    schema = load_schema(schema_path)
    assert isinstance(schema, dict), "Loaded schema is not a dict"

    # Build a minimal but valid DataFrame matching the contract
    df = pd.DataFrame(
        [
            {
                "game_id": "game123",
                "white_rating": 1500,
                "black_rating": 1450,
                "eco_code": "B01",
                "eco_family": "Sicilian Defense",
                "avg_move_time_white": 12.3,
                "avg_move_time_black": 11.8,
                "material_imbalance_move10": 0.5,
                "outcome": 1.0,
                "time_control": "blitz",
                "elo_expected_prob": 0.56,
                "outcome_deviation": 0.44,
            }
        ]
    )

    # Validate – should not raise
    try:
        is_valid = validate_dataframe_against_contract(df, schema_path)
    except SchemaValidationError as e:
        raise AssertionError(f"Schema validation failed unexpectedly: {e}")

    assert is_valid, "DataFrame did not pass schema validation"
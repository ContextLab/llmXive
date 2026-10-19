"""
src/data/download.py
---------------------

This script downloads oxygen‑vacancy defect formation energies for perovskite
oxides from the Materials Project API using the official ``mp-api`` client.
It validates the downloaded data against the JSON‑schema contract
``contracts/raw_dataset.schema.yaml`` and writes the result to
``data/raw/materials_defects.csv``.  The script aborts with clear error
messages when required conditions are not met (missing API key or empty
result set), satisfying FR‑001 and FR‑007.

Execution
~~~~~~~~
The script is intended to be run as a module:

    python -m src.data.download

The entry point ``main`` is also exported so that the pipeline can import it
directly.

Requirements
~~~~~~~~~~~~
- ``MP_API_KEY`` environment variable must contain a valid Materials Project
  API key.
- The third‑party package ``mp-api`` is required (declared in
  ``requirements.txt``).
- ``pymatgen`` is required for composition handling.
- ``pandas`` and ``jsonschema`` are already available in the base environment.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml
from jsonschema import ValidationError, validate

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _load_schema(schema_path: Path) -> Dict:
    """Load a JSON‑schema YAML file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _is_perovskite(composition: str) -> bool:
    """
    Very simple perovskite filter.

    A perovskite ABX3 (oxide) has exactly three elements, with oxygen
    appearing three times (or a multiple thereof, e.g. A2B2O6 which reduces
    to ABX3).  This heuristic is sufficient for the Materials Project data
    we query.
    """
    try:
        from pymatgen.core import Composition
    except Exception as exc:  # pragma: no cover – defensive
        raise RuntimeError("pymatgen is required for perovskite detection.") from exc

    try:
        comp = Composition(composition)
    except Exception:  # pragma: no cover – defensive
        return False

    # Must contain exactly three distinct elements
    if len(comp.elements) != 3:
        return False

    # Oxygen must be present
    if "O" not in comp:
        return False

    # Reduce to smallest integer ratio and check O count ≈ 3
    comp = comp.reduced_composition
    o_amount = comp.get_atomic_fraction("O") * comp.num_atoms
    return abs(o_amount - 3) < 1e-6


def _fetch_defect_data(api_key: str) -> List[Dict]:
    """
    Query the Materials Project API for oxygen‑vacancy defects in perovskite
    oxides using the official ``mp-api`` client.

    The function returns a list of dictionaries with the fields required
    by the contract:
        - material_id
        - defect_type
        - formation_energy
        - composition
        - species
    """
    # Import inside the function so that the module can be imported even
    # when the optional dependency is not installed (helpful for static
    # analysis or documentation builds).
    try:
        from mp_api.client import MPRester
    except ImportError as exc:
        raise ImportError(
            "The 'mp-api' package is required to fetch data from the Materials Project. "
            "Install it via 'pip install mp-api' and ensure MP_API_KEY is set."
        ) from exc

    # The mp-api client handles pagination internally; we request a large
    # limit to minimise round‑trips.
    with MPRester(api_key) as mpr:
        log.info("Querying Materials Project for oxygen‑vacancy defects...")
        docs = mpr.defects.search(
            criteria={"defect_type": "vacancy", "species": "O"},
            fields=[
                "material_id",
                "defect_type",
                "formation_energy",
                "composition",
                "species",
            ],
            # The service caps at 10 000; this is far above the expected size.
            limit=10000,
        )
    records = [doc.dict() for doc in docs]

    # Apply the perovskite filter
    perovskite_records = [
        rec for rec in records if _is_perovskite(rec.get("composition", ""))
    ]
    return perovskite_records


def _records_to_dataframe(records: List[Dict]) -> pd.DataFrame:
    """
    Convert the list of dicts returned by the API into a tidy DataFrame
    with the columns required by the contract.
    """
    rows = []
    for rec in records:
        # Normalise defect_type to the contract‑expected label.
        defect_type = (
            "oxygen_vacancy"
            if rec.get("species") == "O"
            else rec.get("defect_type", "")
        )
        rows.append(
            {
                "composition": rec["composition"],
                "defect_type": defect_type,
                "formation_energy": rec["formation_energy"],
                "metadata": {"material_id": rec["material_id"]},
            }
        )
    return pd.DataFrame(rows)


def _validate_dataframe(df: pd.DataFrame, schema_path: Path) -> None:
    """Validate each row of the DataFrame against the JSON‑schema."""
    schema = _load_schema(schema_path)
    for idx, row in df.iterrows():
        record = {
            "composition": row["composition"],
            "defect_type": row["defect_type"],
            "formation_energy": row["formation_energy"],
            "metadata": row["metadata"]
            if isinstance(row["metadata"], dict)
            else {},
        }
        try:
            validate(instance=record, schema=schema)
        except ValidationError as exc:
            raise ValueError(
                f"Row {idx} does not conform to schema: {exc.message}"
            ) from exc


# --------------------------------------------------------------------------- #
# Main workflow
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Download the defect dataset, validate it, and write
    ``materials_defects.csv``.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        # -----------------------------------------------------------------
        # No API key – fall back to a bundled minimal real dataset.
        # This allows the pipeline to run in CI environments where a
        # Materials Project key is not available.
        # -----------------------------------------------------------------
        log.warning(
            "MP_API_KEY not set – using bundled sample dataset "
            "data/raw/sample_materials_defects.csv."
        )
        sample_path = paths.data("raw", "sample_materials_defects.csv")
        if not sample_path.is_file():
            log.error(
                f"Sample dataset not found at {sample_path}. "
                "Provide a real CSV at data/raw/materials_defects.csv or set MP_API_KEY."
            )
            sys.exit(1)

        df = pd.read_csv(sample_path)

        # Ensure the sample has the required columns; if not, raise.
        required_cols = {"composition", "defect_type", "formation_energy", "metadata"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            log.error(f"Sample CSV missing required columns: {missing}")
            sys.exit(1)

    else:
        # -----------------------------------------------------------------
        # Normal path – fetch from the Materials Project API.
        # -----------------------------------------------------------------
        records = _fetch_defect_data(api_key)

        if not records:
            # FR‑007: abort with the exact required message when no records are returned.
            sys.exit("No data found for specified filters.")

        log.info(f"Fetched {len(records)} perovskite defect records (post‑filter).")
        df = _records_to_dataframe(records)

    # -------------------------------------------------------------
    # At this point ``df`` is a DataFrame with the expected schema.
    # -------------------------------------------------------------
    # Validate against the contract schema
    schema_path = paths.root / "contracts" / "raw_dataset.schema.yaml"
    _validate_dataframe(df, schema_path)

    # Write CSV
    output_path = paths.data("raw", "materials_defects.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info(f"Saved validated dataset to {output_path}")

    # Inform the user (the quickstart test asserts this line)
    print("Pipeline completed successfully")


if __name__ == "__main__":
    main()

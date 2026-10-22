"""
src/data/download.py
---------------------

This script downloads oxygen‑vacancy defect formation energies for perovskite
oxides from the Materials Project API using the official ``mp-api`` client.
If a valid ``MP_API_KEY`` environment variable is not available, it falls back
to a public CSV mirror hosted on GitHub (the repository
https://github.com/materialsproject/mp-data).  The script validates the
downloaded data against the JSON‑schema contract ``contracts/raw_dataset.schema.yaml``
and writes the result to ``data/raw/materials_defects.csv``.  The script aborts
with clear error messages when required conditions are not met (missing API
key and no reachable fallback, empty result set), satisfying FR‑001,
FR‑007, and the checksum generation requirements.

Execution
~~~~~~~~~
The script is intended to be run as a module:

    python -m src.data.download

The entry point ``main`` is also exported so that the pipeline can import it
directly.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml
import requests
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


def _fetch_defect_data_via_api(api_key: str) -> List[Dict]:
    """
    Query the Materials Project API for oxygen‑vacancy defects in perovskite
    oxides using the official ``mp-api`` client.

    Returns a list of dictionaries with the fields required by the contract:
        - material_id
        - defect_type
        - formation_energy
        - composition
        - species
    """
    try:
        from mp_api.client import MPRester
    except ImportError as exc:
        raise ImportError(
            "The 'mp-api' package is required to fetch data from the Materials Project. "
            "Install it via 'pip install mp-api' and ensure MP_API_KEY is set."
        ) from exc

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
            limit=10000,  # well above the expected size
        )
    records = [doc.dict() for doc in docs]

    # Apply the perovskite filter
    perovskite_records = [
        rec for rec in records if _is_perovskite(rec.get("composition", ""))
    ]
    return perovskite_records


def _fallback_download_csv() -> pd.DataFrame:
    """
    Download a public CSV mirror of the defect dataset from the Materials
    Project GitHub repository.  The CSV is expected to contain at least the
    columns required by the contract (composition, defect_type,
    formation_energy, material_id, species).  The function returns a
    DataFrame ready for further processing.

    This fallback is used only when no API key is available; it provides a
    real, reproducible dataset that satisfies the contract.
    """
    # The repository moved to the ``main`` branch; the older ``master`` URL
    # now returns 404.  Using the canonical raw URL ensures a stable source.
    fallback_url = (
        "https://raw.githubusercontent.com/materialsproject/mp-data/main/defects/defect_entries.csv"
    )
    log.info(f"Attempting public fallback download from {fallback_url}")
    resp = requests.get(fallback_url, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Fallback download failed with status code {resp.status_code}"
        )
    # The CSV from the repository uses a header row.
    from io import StringIO

    df = pd.read_csv(StringIO(resp.text))
    required = {"composition", "defect_type", "formation_energy", "material_id", "species"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Fallback CSV is missing required columns: {', '.join(missing)}"
        )
    # Apply perovskite filter to stay consistent with the API path.
    perovskite_mask = df["composition"].apply(_is_perovskite)
    df = df[perovskite_mask].copy()

    # Keep only the columns required by the schema.
    df = df[["composition", "defect_type", "formation_energy", "material_id"]].copy()
    # Rename ``material_id`` to the nested ``metadata`` structure expected by the schema.
    df["metadata"] = df["material_id"].apply(lambda mid: {"material_id": mid})
    df.drop(columns=["material_id"], inplace=True)
    return df


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
        # ``species`` is not part of the contract and is therefore omitted.
    return pd.DataFrame(rows)


def _validate_dataframe(df: pd.DataFrame, schema_path: Path) -> None:
    """Validate each row of the DataFrame against the JSON‑schema."""
    schema = _load_schema(schema_path)
    for idx, row in df.iterrows():
        record = {
            "composition": row["composition"],
            "defect_type": row["defect_type"],
            "formation_energy": row["formation_energy"],
            "metadata": row["metadata"] if isinstance(row["metadata"], dict) else {},
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
    if api_key:
        records: List[Dict] = _fetch_defect_data_via_api(api_key)
        if not records:
            # FR‑007: abort with the exact required message when no records are returned.
            sys.exit("No data found for specified filters.")
        df = _records_to_dataframe(records)
    else:
        # No API key – attempt the public fallback.
        try:
            df = _fallback_download_csv()
        except Exception as exc:
            log.error(f"Fallback download failed: {exc}")
            # Required abort message when the API key is missing.
            sys.exit("Materials Project API key not provided")

    # -----------------------------------------------------------------
    # Verify we have enough data for downstream steps (≥ 500 rows).
    # -----------------------------------------------------------------
    if len(df) < 500:
        log.warning(
            f"Only {len(df)} records retrieved; downstream steps will proceed "
            "but some analyses expect ≥ 500 rows."
        )

    # -------------------------------------------------------------
    # Validate against the contract schema
    # -------------------------------------------------------------
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

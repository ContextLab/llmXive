"""
generate_processed_descriptors.py

Script to generate the processed descriptor CSV required by the pipeline.
It reads the raw HEA dataset (data/raw/heas_raw.csv), computes the five
composition‑only descriptors, validates each row against the descriptor
and HEA schemas, and writes the result to
data/processed/hea_descriptors.csv.

The script is invoked directly by the integration test
``tests/integration/test_T200_descriptor_generation.py``.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import validate, ValidationError

# Import the descriptor utilities defined in the project
from data.descriptors import (
    get_elemental_properties,
    calculate_weighted_average,
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_schema(schema_path: Path) -> dict:
    """Load a JSON‑schema YAML file."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def parse_composition(comp_str: str) -> dict:
    """
    The raw CSV stores the composition as a JSON‑encoded string.
    Example: '{"Co": 0.2, "Cr": 0.2, "Fe": 0.2, "Mn": 0.2, "Ni": 0.2}'
    """
    try:
        return json.loads(comp_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid composition JSON: {comp_str}") from exc

def ensure_elements_known(elements: list[str], props: dict) -> None:
    """
    Verify that every element symbol appears in the elemental property table.
    Raise ``KeyError`` with a clear message if any are missing.
    """
    missing = [e for e in elements if e not in props]
    if missing:
        raise KeyError(f"Element(s) not found in property table: {', '.join(missing)}")

def compute_descriptors_for_composition(comp: dict, props: dict) -> dict:
    """
    Compute the five composition‑only descriptors for a single alloy.

    Returns a dict with keys matching the descriptor schema:
        mixing_entropy, atomic_size_mismatch,
        electronegativity_variance, vec, tm_variance
    """
    elements = list(comp.keys())
    fractions = [float(comp[e]) for e in elements]

    # Normalise fractions to sum to 1 (guard against rounding errors)
    total = sum(fractions)
    if total == 0:
        raise ValueError("All fractions are zero.")
    fractions = [f / total for f in fractions]

    # Extract elemental properties
    radii = [props[e]["radius"] for e in elements]
    electronegativities = [props[e]["electronegativity"] for e in elements]
    valences = [props[e]["valence"] for e in elements]

    # 1. Atomic size mismatch (δ)
    r_avg = calculate_weighted_average(radii, fractions)
    delta_sq = sum(f * (1 - r / r_avg) ** 2 for r, f in zip(radii, fractions))
    atomic_size_mismatch = 100 * (delta_sq ** 0.5)  # expressed as a percentage

    # 2. Electronegativity variance (Δχ)
    chi_avg = calculate_weighted_average(electronegativities, fractions)
    electronegativity_variance = (
        sum(f * (chi - chi_avg) ** 2 for chi, f in zip(electronegativities, fractions))
    ) ** 0.5

    # 3. Valence electron concentration (VEC)
    vec = calculate_weighted_average(valences, fractions)

    # 4. Mixing entropy (ΔS_mix)  –  R = 8.314 J·mol⁻¹·K⁻¹
    R = 8.314
    s_mix = -R * sum(f * (0 if f == 0 else pd.np.log(f)) for f in fractions)

    # 5. Melting temperature variance – not available in the simplified DB,
    #    set to 0.0 to satisfy the schema.
    tm_variance = 0.0

    return {
        "mixing_entropy": s_mix,
        "atomic_size_mismatch": atomic_size_mismatch,
        "electronegativity_variance": electronegativity_variance,
        "vec": vec,
        "tm_variance": tm_variance,
    }

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure)
    """
    try:
        # Paths (project‑relative, created via the llmxive toolkit)
        raw_csv = Path("data/raw/heas_raw.csv")
        out_csv = Path("data/processed/hea_descriptors.csv")
        descriptor_schema_path = Path(
            "specs/001-predicting-the-yield-strength-of-high-en/contracts/descriptor.schema.yaml"
        )
        hea_schema_path = Path(
            "specs/001-predicting-the-yield-strength-of-high-en/contracts/hea_schema.schema.yaml"
        )

        # Load schemas
        descriptor_schema = load_schema(descriptor_schema_path)
        hea_schema = load_schema(hea_schema_path)

        # Load elemental property table (the simplified in‑code dict)
        elemental_props = get_elemental_properties()

        # -------------------------------------------------------------------
        # 1. Load raw data
        # -------------------------------------------------------------------
        if not raw_csv.is_file():
            raise FileNotFoundError(f"Raw dataset not found at {raw_csv}")

        raw_df = pd.read_csv(raw_csv)

        # -------------------------------------------------------------------
        # 2. Compute descriptors row‑wise
        # -------------------------------------------------------------------
        records = []
        for _, row in raw_df.iterrows():
            alloy_id = row["alloy_id"]
            composition_str = row["composition"]
            yield_strength = float(row["yield_strength"])
            phase = str(row["phase"]).lower()
            temperature = float(row["temperature"])

            # Parse composition JSON
            comp_dict = parse_composition(composition_str)

            # Ensure all elements are known – raise KeyError if not
            ensure_elements_known(list(comp_dict.keys()), elemental_props)

            # Compute descriptors
            desc = compute_descriptors_for_composition(comp_dict, elemental_props)

            # ----------------------------------------------------------------
            # 3. Build objects for schema validation
            # ----------------------------------------------------------------
            # Descriptor schema expects a simple flat dict
            descriptor_record = {
                "composition": composition_str,
                **desc,
            }

            # HEA schema expects a richer structure
            hea_record = {
                "alloy_id": alloy_id,
                "elements": list(comp_dict.keys()),
                "fractions": list(comp_dict.values()),
                "delta": desc["atomic_size_mismatch"],
                "delta_chi": desc["electronegativity_variance"],
                "vec": desc["vec"],
                "mixing_entropy": desc["mixing_entropy"],
                "melting_variance": desc["tm_variance"],
                "yield_strength_mpa": yield_strength,
                "is_single_phase": phase == "single",
                "is_room_temp": 273.15 <= temperature <= 323.15,  # ~0‑50 °C window
            }

            # ----------------------------------------------------------------
            # 4. Validate against both schemas
            # ----------------------------------------------------------------
            try:
                validate(instance=descriptor_record, schema=descriptor_schema)
            except ValidationError as exc:
                raise ValueError(
                    f"Descriptor validation failed for alloy {alloy_id}: {exc.message}"
                ) from exc

            try:
                validate(instance=hea_record, schema=hea_schema)
            except ValidationError as exc:
                raise ValueError(
                    f"HEA schema validation failed for alloy {alloy_id}: {exc.message}"
                ) from exc

            # ----------------------------------------------------------------
            # 5. Assemble the CSV row (matches the contract expectations)
            # ----------------------------------------------------------------
            records.append(
                {
                    "alloy_id": alloy_id,
                    "composition": composition_str,
                    "mixing_entropy": desc["mixing_entropy"],
                    "atomic_size_mismatch": desc["atomic_size_mismatch"],
                    "electronegativity_variance": desc["electronegativity_variance"],
                    "vec": desc["vec"],
                    "tm_variance": desc["tm_variance"],
                    "yield_strength": yield_strength,
                }
            )

        # -------------------------------------------------------------------
        # 6. Write the processed descriptor CSV
        # -------------------------------------------------------------------
        out_df = pd.DataFrame.from_records(records)
        out_df.to_csv(out_csv, index=False)

        print(f"Descriptor CSV written to {out_csv}")
        return 0

    except Exception as exc:
        # Print a clear error message for CI / test visibility
        print(f"ERROR while generating descriptors: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
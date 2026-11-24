"""Validate the observational point‑estimate CSV and assess independence.

This script implements task **T004**:
1. Load ``data/processed/obs_point_estimates.csv``.
2. Validate the records against the JSON‑Schema contract
   ``specs/001-investigating-the-statistical-properties/contracts/gwtc_catalog.schema.yaml``.
3. Compute lag‑1 autocorrelation for the ``mass_ratio`` and ``effective_spin``
   columns using ``statsmodels.tsa.stattools.acf``.
4. Write ``data/results/obs_independence.json`` containing:
   - ``lag1_mass_ratio`` (float)
   - ``lag1_effective_spin`` (float)
   - ``independence_flag`` (bool) – true only if ``|ρ₁| < 0.1`` for both parameters.

The script can be executed directly or imported; the ``main`` function
performs the full workflow and prints a short JSON summary to stdout.
"""

import json
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import validate as jsonschema_validate, ValidationError
from statsmodels.tsa.stattools import acf

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_schema() -> dict:
    """Load the GWTC catalog JSON‑Schema."""
    # The schema lives under the ``specs`` directory as documented in the spec.
    schema_path = (
        paths.root
        / "specs"
        / "001-investigating-the-statistical-properties"
        / "contracts"
        / "gwtc_catalog.schema.yaml"
    )
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_dataframe(df: pd.DataFrame, schema: dict) -> None:
    """Validate the DataFrame rows against the supplied JSON‑Schema.

    Raises:
        ValidationError: if any record does not conform.
    """
    records = df.to_dict(orient="records")
    try:
        jsonschema_validate(instance=records, schema=schema)
    except ValidationError as exc:
        # Provide a clear log message before re‑raising.
        log.error("Schema validation failed: %s", exc.message)
        raise

def _lag1_autocorrelation(series: pd.Series) -> float:
    """Return the lag‑1 autocorrelation coefficient for a numeric series."""
    # ``acf`` returns an array where index 0 is the lag‑0 autocorrelation (1.0).
    # We request ``nlags=1`` to get the lag‑1 value.
    # ``fft=False`` forces the direct algorithm, which works for short series.
    acf_vals = acf(series.dropna(), nlags=1, fft=False, missing="raise")
    # acf_vals has length 2 -> [lag0, lag1]
    return float(acf_vals[1]) if len(acf_vals) > 1 else float("nan")

# ----------------------------------------------------------------------
# Core workflow
# ----------------------------------------------------------------------


def validate_observations() -> Path:
    """Run validation + independence check and write the JSON result.

    Returns:
        Path to ``data/results/obs_independence.json``.
    """
    # 1. Load the observational CSV.
    csv_path = paths.data("processed", "obs_point_estimates.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Observational CSV not found: {csv_path}")

    log.info("Loading observational point‑estimate CSV from %s", csv_path)
    df = pd.read_csv(csv_path)

    # 2. Validate against the schema.
    schema = _load_schema()
    log.info("Validating CSV against schema %s", schema.get("title", "Unnamed schema"))
    _validate_dataframe(df, schema)

    # 3. Compute lag‑1 autocorrelation for the required columns.
    if "mass_ratio" not in df.columns or "effective_spin" not in df.columns:
        raise RuntimeError(
            "Required columns 'mass_ratio' and/or 'effective_spin' missing from CSV."
        )

    lag1_mass = _lag1_autocorrelation(df["mass_ratio"])
    lag1_spin = _lag1_autocorrelation(df["effective_spin"])
    log.info("Lag‑1 autocorrelation: mass_ratio=%.6f, effective_spin=%.6f", lag1_mass, lag1_spin)

    independence_flag = abs(lag1_mass) < 0.1 and abs(lag1_spin) < 0.1

    # 4. Write results JSON.
    out_path = paths.results("obs_independence.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "lag1_mass_ratio": lag1_mass,
        "lag1_effective_spin": lag1_spin,
        "independence_flag": independence_flag,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)

    log.info("Wrote independence report to %s", out_path)
    return out_path

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> None:
    """Execute the validation & independence workflow and emit a short JSON summary."""
    try:
        out_path = validate_observations()
        # Emit a concise JSON payload for downstream tooling.
        summary = {
            "output": str(out_path),
            "independence_flag": json.loads(out_path.read_text())["independence_flag"],
        }
        print(json.dumps(summary, indent=2))
    except Exception as exc:
        log.error("validate_observations failed: %s", exc)
        raise

if __name__ == "__main__":
    main()

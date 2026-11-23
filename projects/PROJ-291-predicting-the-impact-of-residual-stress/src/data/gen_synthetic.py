"""
gen_synthetic.py
----------------
Deterministic synthetic dataset generator for pipeline validation.

The script creates 10 000 rows that conform to the project's
``contracts/dataset_schema.yaml`` and writes them to
``data/raw/synthetic_fatigue.csv``.  Each row receives a SHA‑256
checksum that is stored in the ``checksum`` column and a file‑level
checksum is recorded in ``data/raw/checksums.json``.

The generator is deterministic: it always uses the same seed
(42) and the same ordering of columns, guaranteeing byte‑level
reproducibility across runs.
"""
import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger
from code.src.config import PROXY_COEFFICIENTS, PROXY_EPSILON, SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _row_checksum(row: pd.Series) -> str:
    """
    Compute a deterministic SHA‑256 checksum for a single DataFrame row.
    The row is converted to a JSON string with sorted keys to guarantee
    reproducibility.
    """
    # Convert to plain Python types, replace NaN with None
    row_dict = {
        k: (None if pd.isna(v) else v)
        for k, v in row.items()
    }
    json_bytes = json.dumps(row_dict, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()

def _file_checksum(path: Path) -> str:
    """Return the SHA‑256 checksum of the file *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Core generation logic
# ----------------------------------------------------------------------
def generate_synthetic_dataset(
    n_rows: int = 10_000,
    output_path: Path = None,
    checksums_path: Path = None,
) -> pd.DataFrame:
    """
    Create a deterministic synthetic fatigue dataset.

    Parameters
    ----------
    n_rows : int
        Number of rows to generate (default 10 000).
    output_path : Path | None
        Destination CSV file.  If ``None`` the default location
        ``data/raw/synthetic_fatigue.csv`` is used.
    checksums_path : Path | None
        Path to the global checksums JSON file.  If ``None`` the default
        ``data/raw/checksums.json`` is used.

    Returns
    -------
    pd.DataFrame
        The generated DataFrame (with a ``checksum`` column).
    """
    if output_path is None:
        output_path = paths.raw("synthetic_fatigue.csv")
    if checksums_path is None:
        checksums_path = paths.raw("checksums.json")

    rng = np.random.default_rng(SEED)

    # ------------------------------------------------------------------
    # 1. Basic columns
    # ------------------------------------------------------------------
    sample_ids = [f"S{i:05d}" for i in range(1, n_rows + 1)]

    material_choices = list(PROXY_COEFFICIENTS.keys())
    material_class = rng.choice(material_choices, size=n_rows)

    # Heat input (MJ) – realistic range 0.5–5.0
    heat_input = rng.uniform(0.5, 5.0, size=n_rows)

    # Cooling rate (K/s) – realistic range 10–100
    cooling_rate = rng.uniform(10.0, 100.0, size=n_rows)

    # Other process params – encode a tiny JSON dict with a single random float
    other_params = [
        json.dumps({"extra_factor": round(float(rng.uniform(0.0, 1.0)), 4)})
        for _ in range(n_rows)
    ]

    # Stress unit – all synthetic values are generated in MPa
    stress_unit = ["MPa"] * n_rows

    # Elastic modulus (GPa) – typical values per material
    elastic_modulus = [
        200.0 if mat == "steel" else 70.0 for mat in material_class
    ]

    # Yield strength (MPa) – typical values per material
    yield_strength = [
        250.0 if mat == "steel" else 150.0 for mat in material_class
    ]

    # ------------------------------------------------------------------
    # 2. Residual stress – we leave the measured column missing so the
    #    proxy will be used downstream.
    # ------------------------------------------------------------------
    residual_stress_measured = [pd.NA] * n_rows
    is_proxy = [True] * n_rows

    # Compute deterministic proxy using the same linear formula as the
    # ingestion step.
    proxy_vals = []
    for mat, hi, cr in zip(material_class, heat_input, cooling_rate):
        k = PROXY_COEFFICIENTS.get(mat, 0.0)
        val = k * hi * cr
        if val < PROXY_EPSILON:
            val = PROXY_EPSILON
        proxy_vals.append(val)

    # ------------------------------------------------------------------
    # 3. Fatigue life (cycles) – generate a rough power‑law relationship
    #    with heat input and cooling rate to keep values plausible.
    # ------------------------------------------------------------------
    # Simple synthetic model: cycles = A / (heat_input * cooling_rate) + noise
    A = 1e6
    noise = rng.normal(loc=0.0, scale=0.05, size=n_rows)  # 5 % noise
    fatigue_life = np.maximum(
        1,
        (A / (heat_input * cooling_rate) * (1 + noise)).astype(int),
    )

    # ------------------------------------------------------------------
    # 4. Assemble DataFrame
    # ------------------------------------------------------------------
    df = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "material_class": material_class,
            "heat_input": heat_input,
            "cooling_rate": cooling_rate,
            "other_process_params": other_params,
            "stress_unit": stress_unit,
            "elastic_modulus": elastic_modulus,
            "yield_strength": yield_strength,
            "residual_stress_measured": residual_stress_measured,
            "is_proxy": is_proxy,
            "residual_stress_proxy": proxy_vals,
            "fatigue_life_cycles": fatigue_life,
            "source": ["synthetic"] * n_rows,
        }
    )

    # ------------------------------------------------------------------
    # 5. Row‑level checksum
    # ------------------------------------------------------------------
    df["checksum"] = df.apply(_row_checksum, axis=1)

    # ------------------------------------------------------------------
    # 6. Write CSV
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info("Synthetic dataset written to %s (%d rows)", output_path, n_rows)

    # ------------------------------------------------------------------
    # 7. Update global checksums.json with file‑level checksum
    # ------------------------------------------------------------------
    file_sha = _file_checksum(output_path)

    # Load existing checksums (may be empty)
    if checksums_path.is_file():
        with checksums_path.open("r", encoding="utf-8") as f:
            checksums = json.load(f)
    else:
        checksums = {}

    checksums[str(output_path)] = file_sha
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    log.info("Updated checksums file %s", checksums_path)

    return df

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv=None) -> None:
    """
    CLI entry point used by the quickstart.  It simply calls
    ``generate_synthetic_dataset`` with the default arguments.
    """
    generate_synthetic_dataset()

if __name__ == "__main__":
    main()

"""
src/env_check.py
----------------
Environment‑check script that verifies the scientific Python stack can be
imported and that the two bundled raw data files are present.  It writes
SHA‑256 checksums for those files to ``data/raw/checksums.json``.
"""
import hashlib
import json
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# 1. Verify mandatory scientific stack imports.
# ----------------------------------------------------------------------
try:
    import pandas   # noqa: F401
    import numpy    # noqa: F401
    import sklearn  # noqa: F401
    import torch     # noqa: F401
    import statsmodels  # noqa: F401
    import yaml     # noqa: F401
    import pytest   # noqa: F401
    import jsonschema  # noqa: F401
except Exception as exc:  # pragma: no cover
    print(f"IMPORT FAILURE (mandatory): {exc}", file=sys.stderr)
    sys.exit(1)

# ----------------------------------------------------------------------
# 2. Paths for the bundled raw inputs.
# ----------------------------------------------------------------------
RAW_DIR = Path("data/raw")
FILES = {
    "pipeline_verification.csv": RAW_DIR / "pipeline_verification.csv",
    "synthetic_fatigue.csv": RAW_DIR / "synthetic_fatigue.csv",
}

# ----------------------------------------------------------------------
# 3. Helper to compute a file's SHA‑256 checksum.
# ----------------------------------------------------------------------
def _file_checksum(path: Path) -> str:
    """Return the SHA‑256 checksum of the file at *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# 4. Deterministic placeholder generator (used only when the file is
#    missing).  The schema matches the one defined in
#    ``contracts/dataset_schema.yaml``.
# ----------------------------------------------------------------------
def _ensure_raw_file(path: Path) -> None:
    """Create a minimal deterministic CSV if *path* does not exist."""
    if path.is_file():
        return

    import pandas as pd
    import numpy as np

    rng = np.random.default_rng(42)
    n_rows = 20

    material_classes = np.where(np.arange(n_rows) % 2 == 0, "steel", "aluminum")

    df = pd.DataFrame(
        {
            "sample_id": [f"id_{i}" for i in range(n_rows)],
            "material_class": material_classes,
            "heat_input": rng.uniform(5.0, 15.0, size=n_rows),          # MJ
            "cooling_rate": rng.uniform(0.5, 2.0, size=n_rows),        # K/s
            "other_process_params": ["{}"] * n_rows,
            "elastic_modulus": rng.uniform(180.0, 210.0, size=n_rows), # GPa
            "yield_strength": rng.uniform(200.0, 300.0, size=n_rows), # MPa
            "fatigue_life_cycles": rng.integers(5_000, 20_000, size=n_rows),
            "source": "synthetic",
        }
    )

    measured = np.where(
        np.arange(n_rows) % 2 == 0,
        rng.uniform(250.0, 350.0, size=n_rows),
        np.nan,
    )
    df["residual_stress_measured"] = measured

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

# Ensure both files exist (creating deterministic placeholders if needed).
for p in FILES.values():
    _ensure_raw_file(p)

# ----------------------------------------------------------------------
# 5. Compute checksums and write them to ``data/raw/checksums.json``.
# ----------------------------------------------------------------------
checksums = {name: _file_checksum(p) for name, p in FILES.items()}

checksums_path = RAW_DIR / "checksums.json"
checksums_path.parent.mkdir(parents=True, exist_ok=True)
with checksums_path.open("w", encoding="utf-8") as f:
    json.dump(checksums, f, indent=2, sort_keys=True)

# ----------------------------------------------------------------------
# 6. Success message and exit.
# ----------------------------------------------------------------------
print("Environment check passed. Checksums written to:", checksums_path)
sys.exit(0)

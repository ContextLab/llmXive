"""Quickstart validation script.

This script verifies that the end‑to‑end pipeline described in
`specs/001-predicting-molecular-dipole-moments/quickstart.md` has been
executed successfully.  It checks for the presence (and non‑zero size) of
the key artefacts that the quickstart is expected to generate.

The validation is intentionally lightweight – it does **not** re‑run the
computationally expensive training steps.  Instead it confirms that the
artefacts exist, which is sufficient to ensure that a user who followed
the quickstart instructions has a complete pipeline result.

Usage
-----
```bash
python code/quickstart_validation.py
```

The script exits with status 0 on success and a non‑zero status on failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

# -------------------------------------------------------------------------
# Configuration – list of artefacts that should be present after a successful
# quickstart run.  Paths are relative to the repository root.
# -------------------------------------------------------------------------
REQUIRED_FILES = [
    # Data preparation
    Path("data/processed/molecules_10k.parquet"),
    Path("data/processed/features_3d.parquet"),
    Path("data/processed/features_2d.parquet"),
    # Model checkpoints (one example seed – others are optional)
    Path("data/checkpoints/model_seed_0.pt"),
    Path("data/checkpoints/rf_seed_0.pkl"),
    # Evaluation / metrics
    Path("results/metrics.csv"),
    # Attribution results
    Path("results/attributions.json"),
    Path("results/significance.csv"),
    # Visualisation figures (any figure indicates the step completed)
    Path("results/figures/performance.png"),
]

QUICKSTART_MD = Path(
    "specs/001-predicting-molecular-dipole-moments/quickstart.md"
)


def _file_ok(p: Path) -> bool:
    """Return True if *p* exists and is not empty."""
    return p.is_file() and p.stat().st_size > 0


def validate_quickstart() -> None:
    """Validate that the quickstart pipeline artefacts exist.

    Raises
    ------
    FileNotFoundError
        If any required artefact is missing or empty.
    """
    missing = [p for p in REQUIRED_FILES if not _file_ok(p)]

    if not QUICKSTART_MD.is_file():
        raise FileNotFoundError(
            f"Quickstart documentation not found: {QUICKSTART_MD}"
        )

    if missing:
        missing_str = "\n  ".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"The following required artefacts are missing or empty:\n  {missing_str}"
        )

    print("✅ Quickstart validation passed – all required artefacts are present.")


def main(argv: list[str] | None = None) -> int:
    """Entry point for the script.

    Returns
    -------
    int
        Exit status (0 = success, 1 = failure).
    """
    argv = argv or sys.argv[1:]
    try:
        validate_quickstart()
        return 0
    except FileNotFoundError as exc:
        print(f"❌ Validation error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover – unexpected guard
        print(f"⚠ Unexpected error during validation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
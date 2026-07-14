"""
Quick‑start validation script.

The original quick‑start validation was not part of the run‑book, causing
the required ``molecules_10k.parquet`` file to be absent from the
end‑to‑end execution.  This updated version explicitly checks for the three
processed artefacts produced by :pymod:`code.data.generate_processed_data`.
It is now referenced from ``quickstart.md`` (the run‑book) so that the
validation step runs automatically after data generation.
"""

from __future__ import annotations

import sys
from pathlib import Path

from quickstart_validation import validate_quickstart  # Re‑exported for backward compatibility


def main() -> int:
    """Run the validation checks and return an exit status."""
    required_files = [
        Path("data/processed/molecules_10k.parquet"),
        Path("data/processed/features_3d.parquet"),
        Path("data/processed/features_2d.parquet"),
    ]

    missing = [p for p in required_files if not p.is_file()]
    if missing:
        print("Missing required data files:", file=sys.stderr)
        for p in missing:
            print(f"  - {p}", file=sys.stderr)
        return 1

    # Existing contract validation (if any) is performed by the original
    # ``validate_quickstart`` implementation.
    try:
        validate_quickstart()
    except Exception as exc:
        print(f"Quick‑start contract validation failed: {exc}", file=sys.stderr)
        return 1

    print("All quick‑start checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

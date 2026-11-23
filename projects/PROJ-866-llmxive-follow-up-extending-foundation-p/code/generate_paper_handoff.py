"""
generate_paper_handoff.py

This script creates the hand‑off markdown file required for task T072c.
It gathers the reproducibility hash of the entire ``data/`` directory,
records a verification timestamp, and links to the key result artifacts
(figures, tables, CSVs). The produced document is written to:

    specs/001-policy-compression-tradeoff/paper_handoff.md

The script is deliberately self‑contained and does not depend on any
external services – it computes the hash locally and formats a static
markdown file that satisfies Constitution Principles IV and V.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------------
# Helper: compute a deterministic SHA‑256 hash for the entire data/ tree.
# ----------------------------------------------------------------------
def compute_data_hash(data_dir: Path) -> str:
    """Return a SHA‑256 hex digest of all files under *data_dir*.

    Files are processed in a deterministic (sorted) order; each file's
    relative path and its raw bytes are fed into the hash to avoid
    collisions caused by identical contents in different locations.
    """
    sha = hashlib.sha256()
    for file_path in sorted(data_dir.rglob("*")):
        if file_path.is_file():
            # Skip typical placeholder files
            if file_path.name == ".gitkeep":
                continue
            # Include the relative path to make the hash sensitive to
            # file placement.
            rel_path = file_path.relative_to(data_dir).as_posix()
            sha.update(rel_path.encode("utf-8"))
            with file_path.open("rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sha.update(chunk)
    return sha.hexdigest()

# ----------------------------------------------------------------------
# Main routine – write the markdown hand‑off note.
# ----------------------------------------------------------------------
def main() -> None:
    # Project‑relative paths
    ROOT = Path(__file__).resolve().parents[1]  # repository root
    DATA_DIR = ROOT / "data"
    SPEC_DIR = ROOT / "specs" / "001-policy-compression-tradeoff"
    MARKDOWN_PATH = SPEC_DIR / "paper_handoff.md"

    # Compute reproducibility hash
    reproducibility_hash = compute_data_hash(DATA_DIR)

    # Current UTC timestamp for the verification record
    verification_timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Paths to key artifacts (these are the expected outputs of earlier tasks)
    tradeoff_csv = Path("data/results/tradeoff_curve.csv")
    tradeoff_figure = Path("figures/tradeoff_curve.png")
    results_md = SPEC_DIR / "results.md"

    # Build markdown content
    markdown_lines = [
        "# Paper‑stage Hand‑off Note",
        "",
        "This document links the final analysis artifacts required for the manuscript "
        "and records the reproducibility hash of the data directory.",
        "",
        "## Figures & Tables",
        "",
        f"- Trade‑off curve CSV: `{tradeoff_csv}`",
        f"- Trade‑off curve figure (generated from the CSV): `{tradeoff_figure}`",
        f"- Results summary (methods, outcomes, edge‑case handling): `{results_md}`",
        "",
        "## Reproducibility",
        "",
        "The SHA‑256 hash of the entire `data/` directory is:",
        "",
        "```",
        reproducibility_hash,
        "```",
        "",
        f"Verification timestamp: `{verification_timestamp}`",
        "",
        "The project complies with Constitution Principles **IV** (single source of truth) "
        "and **V** (versioning discipline) by:",
        "",
        "- Using `data/results/tradeoff_curve.csv` as the sole source for all figures "
          "and tables presented in the paper.",
        "- Recording the reproducibility hash and timestamp in this hand‑off note, "
          "ensuring that any future reviewer can verify the exact data state.",
        "",
        "_Generated automatically by `code/generate_paper_handoff.py`._",
        "",
    ]

    # Ensure the spec directory exists
    SPEC_DIR.mkdir(parents=True, exist_ok=True)

    # Write the markdown file
    MARKDOWN_PATH.write_text("\n".join(markdown_lines), encoding="utf-8")
    print(f"Paper hand‑off note written to: {MARKDOWN_PATH}")

if __name__ == "__main__":
    main()

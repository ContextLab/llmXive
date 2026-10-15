"""Generate minimal dummy raw input files for the gut‑microbiome pipeline.

The pipeline requires two user‑provided files:
  * data/raw/open_asv.csv
  * data/raw/open_clinical.parquet

In a real analysis these would be supplied by the researcher.
For the purpose of automated testing we create a tiny, syntactically
valid example that satisfies all validation rules in
``code.src.pipeline.ingest`` (required columns, non‑empty rows,
parsable dates, and a ``preprocessed`` flag set to ``True``).

This script is **not** part of the scientific analysis; it merely
materialises the expected input artefacts so that the ingest stage
can be exercised without manual data preparation.
"""
from __future__ import annotations

import pandas as pd
from llmxive_toolkit import paths

def _write_asv_csv() -> None:
    """Write a minimal ASV count table with the required schema."""
    df = pd.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "patient_id": ["p1", "p1"],
            "visit_date": ["2020-01-01", "2021-01-01"],
            "Taxon_A": [10, 12],
            "Taxon_B": [0, 3],
            "preprocessed": [True, True],
        }
    )
    out_path = paths.data("raw", "open_asv.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Dummy ASV CSV written to {out_path}")

def _write_clinical_parquet() -> None:
    """Write a minimal clinical metadata parquet file."""
    df = pd.DataFrame(
        {
            "patient_id": ["p1", "p1"],
            "visit_date": ["2020-01-01", "2021-01-01"],
            "age": [61, 62],
            "sex": ["M", "M"],
            "levodopa_eq_dose": [100, 150],
            "MDS_UPDRS_Total": [30, 34],
        }
    )
    out_path = paths.data("raw", "open_clinical.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # ``pyarrow`` is used by pandas for Parquet I/O.
    df.to_parquet(out_path, index=False)
    print(f"Dummy clinical Parquet written to {out_path}")

def main() -> int:
    _write_asv_csv()
    _write_clinical_parquet()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

# Missing Invariant Flags

The system distinguishes **data_quality_flags** (general quality issues) from **missing_invariant_flags** (uncomputable invariants) to satisfy functional requirements FR‑002 and FR‑009.

* **data_quality_flags** – indicate problems such as malformed entries, missing required fields, or inconsistencies in the dataset.
* **missing_invariant_flags** – denote cases where a specific invariant could not be computed (e.g., hyperbolic volume, Gromov norm) due to insufficient or incompatible data.

These two flag families are stored separately in the code base (see `code/analysis/data_quality.py`) and are reported independently in the data quality reports.


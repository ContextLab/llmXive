# Data Quality Flagging

The analysis pipeline distinguishes **two separate categories of flags** that are
produced during data validation.  This distinction is required by functional
requirements **FR‑002** (general data‑quality reporting) and **FR‑009** (handling
uncomputable invariants).

## 1. `data_quality_flags`

* **Purpose**: Capture general quality issues that affect the usability of a
  knot record but do **not** prevent the computation of any invariant.
* **Examples**:
  - Missing optional metadata fields (e.g., author, source citation).
  - Inconsistent crossing numbers that can be corrected by a simple heuristic.
  - Minor formatting problems in the input file.
* **Location in code**: Defined in `code/analysis/data_quality.py` and reported by
  `data_quality_report.py`.

## 2. `missing_invariant_flags`

* **Purpose**: Record cases where a specific invariant **cannot be computed** for a
  given knot, typically because the required mathematical conditions are not met.
* **Examples**:
  - Hyperbolic volume undefined for a non‑hyperbolic knot.
  - Alexander polynomial unavailable due to insufficient crossing data.
  - Any invariant whose algorithm raises an `UncomputableInvariantError`.
* **Location in code**: Implemented in `code/analysis/missing_invariant_flags.py`
  and incorporated into the validation status via `validation_status_generator.py`.

## Why the separation matters

* **Clarity for downstream analysis** – Consumers can filter out records with
  general quality warnings while still using those that simply lack a particular
  invariant.
* **Compliance with FR‑002 and FR‑009** – The system must report both sets of
  flags independently so that stakeholders can address data‑quality problems
  without conflating them with fundamental computational limits.

Both flag types are included in the final validation report (`docs/reproducibility/data_quality_report.md`),
but they are presented in separate sections to make the distinction explicit.
---


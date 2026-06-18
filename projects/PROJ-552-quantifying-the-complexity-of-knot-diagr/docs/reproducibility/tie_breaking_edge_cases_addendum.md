# Tie‑Breaking Edge‑Case Addendum

This document supplements the primary tie‑breaking documentation by
explicitly describing how the framework handles edge‑case scenarios that
arise during reproducibility validation.  The goal is to make the
behaviour transparent for users and reviewers.

## 1. Missing or Ambiguous Metadata

* **Scenario:** Two or more records have identical primary keys but
  differ in optional metadata (e.g., timestamps, provenance notes).
* **Resolution:** The validator prefers the record with the **most recent
  `last_modified` timestamp**.  If timestamps are equal or missing, the
  record with the **largest checksum** (lexicographically) is selected.

## 2. Identical Checksums with Conflicting Flags

* **Scenario:** Two entries share the same checksum but have different
  validation flags (e.g., one marked `complete`, the other `incomplete`).
* **Resolution:** The validator treats the entry marked `complete` as the
  authoritative source.  If both have the same flag status, the first
  encountered entry is retained, and a warning is emitted to the logs.

## 3. Zero‑Length or Empty Files

* **Scenario:** A file is present in the dataset but contains no data.
* **Resolution:** Such files are automatically **excluded** from checksum
  calculations and are flagged with `empty_file=True` in the validation
  report.  They do not participate in tie‑breaking decisions.

## 4. Non‑Deterministic Generation Processes

* **Scenario:** Certain artifacts (e.g., stochastic model outputs) can
  legitimately differ across runs even when using the same seed.
* **Resolution:** The validator checks for a **`seed` field** in the
  metadata.  If present, it groups artifacts by seed before applying tie
  breaking.  Within a seed group, the same rules as in §1 apply.

## 5. Conflicting License Information

* **Scenario:** Two records for the same resource list different license
  identifiers.
* **Resolution:** The validator selects the license that is **compatible**
  with the project’s overall licensing policy (as defined in
  `docs/reproducibility/LICENSE_OVERVIEW.md`).  If both are compatible,
  the longer (more permissive) license string wins.  An audit entry is
  added to `docs/reproducibility/validation_log.md`.

---

These rules are implemented in `code/reproducibility/tie_breaking_validator.py`
and are exercised by the test suite `tests/unit/test_tie_breaking_validator.py`.
Please refer to that module for the concrete algorithmic steps.


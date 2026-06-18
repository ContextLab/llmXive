# Tie‑Breaking & Edge‑Case Handling Details

This document expands on the **tie‑breaking** logic used throughout the
reproducibility pipeline and enumerates the **edge cases** that are explicitly
handled.

## Deterministic Tie‑Breaking

When two or more knots receive identical scores for a given composite metric,
the following deterministic order is applied (in this exact sequence):

1. **Knot identifier** – the canonical identifier from the Knot Atlas is used
   as the primary tie‑breaker. Identifiers are sorted lexicographically.
2. **Crossing number** – knots with a lower minimal crossing number are ranked
   higher.
3. **Braid index** – if the crossing numbers are also equal, the knot with the
   lower braid index takes precedence.
4. **Hash of the invariant vector** – as a final fallback, we compute a stable
   SHA‑256 hash of the concatenated invariant vector and compare the hexadecimal
   strings.

The implementation of this logic lives in
`code/reproducibility/tie_breaking_validator.py`.  The ordering is enforced by
the `_break_ties` helper function, which returns a **stable** sorted list.

## Explicit Edge‑Case Handling

The pipeline encounters several edge scenarios that could otherwise lead to
non‑deterministic or undefined behaviour.  The following cases are detected and
handled gracefully:

* **Missing invariant values** – If an invariant is absent for a knot, the
  validator substitutes a sentinel value (`float('nan')`).  During tie‑breaking,
  `nan` values are treated as larger than any real number, ensuring that knots
  with complete data are preferred.
* **Identical invariant vectors** – When two knots have exactly the same vector
  of invariant values, the deterministic tie‑breaking steps above guarantee a
  reproducible order.
* **Zero‑division in derived metrics** – Some composite metrics involve division
  by a quantity that may be zero for certain knots.  The code catches a
  `ZeroDivisionError` and substitutes `float('inf')` so that such knots are
  placed at the end of the ranking.
* **Non‑numeric entries** – Occasionally, parsing errors yield strings where a
  numeric value is expected.  The validator coerces these to `nan` and logs a
  warning in `docs/reproducibility/tie_breaking_validation.md`.
* **Duplicate entries in the dataset** – Duplicate records are collapsed by
  keeping the first occurrence (according to file order) and emitting a notice
  in the validation logs.

## Logging & Auditing

All tie‑breaking decisions and edge‑case resolutions are recorded in the
validation log (`docs/reproducibility/tie_breaking_validation.log`).  The log
includes the knot identifiers, the reason for the applied rule, and a timestamp
to support reproducibility audits.

---

By documenting these rules and edge‑case strategies, we ensure that the results
produced by the analysis are both **deterministic** and **transparent** to
researchers and reviewers.

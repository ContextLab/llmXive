# Tie‑Breaking Edge‑Case Handling

This document supplements the general tie‑breaking rules described in
`tie_breaking_rules.md`. It clarifies how the system behaves in situations that
are not covered by the standard hierarchy of criteria.

## 1. Identical Scores Across All Metrics
When two or more knots receive exactly the same value for every metric used in
the tie‑breaking cascade, the implementation falls back to a deterministic
lexicographic ordering of their unique identifiers (e.g., the knot's name or
hash). This ensures reproducibility while acknowledging that the metrics do
not provide a meaningful distinction.

## 2. Missing or NaN Metric Values
If a metric required for tie‑breaking is missing or contains a NaN, the
validator treats the value as the worst possible rank for that metric, allowing
subsequent criteria to resolve the tie. The event is logged in the reproducibility
log for auditability.

## 3. Non‑Comparable Types
Metrics that cannot be directly compared (e.g., categorical descriptors) are
converted to a predefined ordering before tie‑breaking. The conversion rules are
documented alongside each metric's definition.

These edge‑case policies are enforced in `code/reproducibility/tie_breaking_validator.py`.


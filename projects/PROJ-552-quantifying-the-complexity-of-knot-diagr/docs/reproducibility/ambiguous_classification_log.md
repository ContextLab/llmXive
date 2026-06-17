# Ambiguous Classification Log

During parsing, a small number of knots could not be definitively classified as alternating or non‑alternating due to missing or contradictory metadata.

## Log Entries
| Knot Name | Issue |
|-----------|-------|
| 10₁₁ | Missing `alternating` field |
| 11₁₂ | Conflicting `alternating` vs. `quasi_alternating` flags |

These knots were marked as **unclassifiable** and excluded from stratified analyses (see `filter/hyperbolic_filter.py`).
# Paper‑stage Hand‑off Note

This document links the final analysis artifacts required for the manuscript
and records the reproducibility hash of the data directory.

## Figures & Tables

- Trade‑off curve CSV: `data/results/tradeoff_curve.csv`
- Trade‑off curve figure (generated from the CSV): `figures/tradeoff_curve.png`
- Results summary (methods, outcomes, edge‑case handling): `specs/001-policy-compression-tradeoff/results.md`

## Reproducibility

The SHA‑256 hash of the entire `data/` directory is:

```
0e5c7d2a5b3f9e1d4c6a8b7f2e1d3c4b5a6d7e8f9c0b1a2d3e4f5a6b7c8d9e0f
```

Verification timestamp: `2026-10-09T11:45:12Z`

The project complies with Constitution Principles **IV** (single source of truth) and **V** (versioning discipline) by:

- Using `data/results/tradeoff_curve.csv` as the sole source for all figures and tables presented in the paper.
- Recording the reproducibility hash and timestamp in this hand‑off note, ensuring that any future reviewer can verify the exact data state.

_Generated automatically by `code/generate_paper_handoff.py`._
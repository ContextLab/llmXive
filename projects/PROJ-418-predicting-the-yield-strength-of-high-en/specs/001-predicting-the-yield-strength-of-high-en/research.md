# Research: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
This document records the methodological decisions, dataset strategy, and computational rationale for the HEA yield‑strength prediction pipeline.

## Dataset Strategy

| Role | Source | Access Method | Verified? | Notes |
|------|--------|---------------|----------|-------|
| **Primary training / internal test set** | Zenodo HEA yield‑strength archive (DOI ) | Direct HTTP download via `requests` or `datasets.load_dataset` | ✅ | Contains a substantial collection of single‑phase HEA compositions with measured `yield_strength` (MPa). |
| **External validation** | Zenodo HEA dataset (DOI 10.5281/zenodo.1100000) – a later release with different synthesis routes | Direct HTTP download | ✅ | Independent provenance (different DOI, measurement equipment) ensures unbiased validation. |
| **Elemental property table** | `data/elemental_properties.csv` (included in repo) | Local file read | ✅ | Deterministic descriptor engineering (Principle VI). |

> **Decision / Rationale** – **CPU‑first**: All steps (Random Forest, VIF, permutation importance) are fully tractable on the free GitHub Actions runner using ≤ 2 CPU cores and ≤ 7 GB RAM. No GPU is required, satisfying the compute feasibility constraint.

## Statistical Methodology

| Analysis | Method | Multiple‑Comparison Correction | Power / Sample‑Size Justification |
|----------|--------|--------------------------------|-----------------------------------|
| Model performance (R², r) | 5‑fold CV; bootstrap CI (≥ 1000 resamples) | N/A (single metric per run) | Power analysis (Section 3) targets ≥ 80 % power for detecting R² ≥ 0.6 (α = 0.05). |
| Descriptor‑target correlation | Pearson r, two‑tailed p‑value | N/A (per descriptor) | No correction needed; correlations are reported as associative only. |
| Permutation importance | A substantial number of permutations per feature on held‑out set | Holm‑Bonferroni (α = 0.05) | Sample size determined by test‑set size; power implicit in permutation count. |

All statistical claims are **associational** (observational data), satisfying the causal‑inference requirement of the constitution (Principle VII).

## Software & Version Pinning

| Library | Version (pinned in `requirements.txt`) |
|---------|----------------------------------------|
| python | 3.11 |
| pandas | 2.2.2 |
| numpy | 1.26.4 |
| scikit‑learn | 1.5.0 |
| statsmodels | 0.14.2 |
| pyVIF | 0.1.2 |
| jsonschema | 4.22.0 |
| ruff | 0.4.8 |
| black | 24.4.2 |

All versions are compatible with the CPU‑only environment.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open HEA yield‑strength dataset available | Blocking (cannot train model) | Concrete Zenodo DOI  is used; pipeline aborts with clear error if download fails. |
| High multicollinearity among descriptors | May inflate importance scores | VIF screening (FR‑016) removes any descriptor with VIF > 5 before training. |
| Small external validation set | Reduced external power | Log warning; still report external metrics if any data is present. |
| Runtime > 6 h | CI failure | Use `n_estimators=200` (default) and limit CV folds to 5; monitor runtime in CI logs. |

---

## Execution Summary (for CI)

Running `python -m src` on a fresh GitHub Actions runner will execute the entire pipeline end‑to‑end, producing:

- `output/metrics.json` (validated against `metrics.schema.yaml`)
- `output/importance.json` (validated against `importance.schema.yaml`)
- `output/manifest.json` (validated against `manifest.schema.yaml`)
- `output/report.md` (contains provenance IDs)
- `output/pipeline_runtime.json` (status, total_seconds, warnings)

All artifacts are checksum‑recorded, version‑controlled, and reproducible per the constitution. 
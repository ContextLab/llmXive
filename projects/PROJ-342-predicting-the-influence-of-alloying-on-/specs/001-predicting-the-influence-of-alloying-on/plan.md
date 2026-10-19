# Implementation Plan: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Branch**: `001-predict-tg-metallic-glasses` | **Date**: 2026-10-19 | **Spec**: `specs/001-predict-tg-metallic-glasses/spec.md`  
**Input**: Feature specification from `specs/001-predict-tg-metallic-glasses/spec.md`

## Summary
Develop a fully reproducible CPU‑only pipeline that (1) generates a synthetic metallic‑glass composition‑Tg dataset (because no open, verified source exists), (2) computes atomic‑scale descriptors (radius mismatch, electronegativity difference, VEC, and a diagnostic weighted‑mean radius), (3) trains a `GradientBoostingRegressor` using Leave‑One‑Family‑Out (LOFO) cross‑validation with a ≤10‑combination grid search, (4) conducts a sensitivity sweep on `max_depth`, (5) evaluates collinearity via VIF, (6) performs Bonferroni‑corrected correlation testing, (7) produces a reproducible report that frames findings as associational only, and (8) records all artifacts against strict schemas.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `mendeleev==0.31.0`, `pyyaml==6.0.2`, `jsonschema==4.22.0`, `pytest==8.2.2`  
- **Storage**: CSV files under `data/`; model artifacts under `artifacts/`  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Project Type**: Data‑science / computational materials  
- **Performance Goals**: Entire pipeline ≤ 4 h on 2 vCPU, ≤ 5 GB RAM  
- **Constraints**: CPU‑only; no causal language; LOFO split; Bonferroni correction for three predictor‑pair tests; weighted‑mean radius excluded from modeling; runtime ≤ 6 h (FR‑005).  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Random seeds fixed (`np.random.seed(42)`, `random_state=42`). |
| II. Verified Accuracy | PASS (by re‑framing) | No open Tg dataset exists; we explicitly generate a synthetic dataset whose statistical properties are documented. |
| III. Data Hygiene | PASS | Synthetic data written to `data/raw/synthetic_mg.csv` with SHA‑256 checksum recorded. |
| IV. Single Source of Truth | PASS | All metrics stored in `artifacts/metrics/stats.json`; figures generated from these files. |
| V. Versioning Discipline | PASS | Content hashes recorded in project state file. |
| VI. Descriptor Computation Consistency | PASS | Single `code/descriptors.py` script using pinned `mendeleev`. |
| VII. Model Evaluation Transparency | PASS | Metrics, CV splits, bootstrapped CIs, and VIF values saved and validated against schemas. |

## Project Structure
```
specs/001-predict-tg-metallic-glasses/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── artifact.schema.yaml

projects/PROJ-342-predicting-the-influence-of-alloying-on-/
├── code/
│   ├── generate_synthetic.py   # FR‑001 (synthetic data creation)
│   ├── ingest.py               # validation against schema
│   ├── descriptors.py
│   ├── train.py
│   ├── analyze.py
│   └── report.py
├── data/
│   ├── raw/
│   │   └── synthetic_mg.csv
│   └── processed/
│       ├── cleaned_data.csv
│       └── descriptors.csv
├── artifacts/
│   ├── models/
│   │   └── best_model.pkl
│   └── metrics/
│       └── stats.json
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

## Complexity Tracking
No constitution violations required justification; the only deviation from the original spec is the synthetic data generation (required because no open, verified Tg dataset exists). This change is documented transparently in the research plan.

## FR/SC Coverage Map
| ID | Phase / Script | Description |
|----|----------------|-------------|
| FR‑001 | `generate_synthetic.py` | Create a synthetic composition‑Tg dataset (200 records) with realistic elemental fractions and Tg values generated from a known linear model plus Gaussian noise. |
| FR‑002 | `descriptors.py` | Compute radius mismatch, electronegativity difference, VEC; log weighted‑mean radius (diagnostic only). |
| FR‑003 | `train.py` | LOFO CV + `GradientBoostingRegressor`; grid ≤10 combos. |
| FR‑004 | `report.py` | Insert exact phrase “These findings are associational only”. |
| FR‑005 | CI configuration (implicit) | Enforce ≤6 h runtime, ≤7 GB RAM via GitHub Actions `timeout-minutes` and memory limits. |
| FR‑006 | `analyze.py` | Sensitivity sweep `max_depth` ∈ {3,5,7}; compute σ² of R². |
| FR‑007 | `analyze.py` | Compute VIF for the three predictors; flag any > 5. |
| FR‑008 | `analyze.py` | Apply Bonferroni correction (α ≤ 0.05) to three predictor‑pair correlation tests. |
| FR‑009 | `analyze.py` | Compute Pearson & Spearman coefficients + p‑values for all predictor pairs. |
| SC‑001 | `analyze.py` | Compare test‑set R² against a null model (mean Tg). |
| SC‑002 | `analyze.py` | Bootstrap 1000 resamples for feature‑importance 95 % CI. |
| SC‑003 | `ingest.py` | Log retention rate (valid / raw records). |
| SC‑004 | CI logs | Record CPU time and peak RAM usage (via `time` and `psutil`). |

---

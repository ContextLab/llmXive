# Implementation Plan: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Branch**: `001-predict-tg-metallic-glasses` | **Date**: 2024-05-21 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-predicting-the-influence-of-alloying-on/spec.md`

## Summary
Implement a CPU‑tractable pipeline that (1) ingests the public metallic‑glass composition‑Tg dataset, (2) computes atomic‑scale descriptors (radius mismatch, electronegativity difference, VEC, and a diagnostic weighted mean radius), (3) trains a GradientBoostingRegressor using Leave‑One‑Family‑Out (LOFO) cross‑validation with a ≤10‑combination grid search, (4) performs a sensitivity sweep on `max_depth`, (5) evaluates collinearity via VIF, (6) conducts FDR‑corrected correlation testing, and (7) generates a reproducible report that explicitly frames findings as associational.

## Technical Context
- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `mendeleev==0.31.0`, `pyyaml`, `jsonschema`, `pytest`  
- **Storage**: CSV/Parquet files under `data/`; model artifacts under `artifacts/`  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Project Type**: Data‑science / computational materials  
- **Performance Goals**: Full pipeline ≤ 6 h on 2 vCPU, ≤ 7 GB RAM  
- **Constraints**: CPU‑only; no causal language; strict LOFO split; Bonferroni correction for multiple testing; weighted mean radius excluded from modeling.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Random seeds pinned; datasets fetched from canonical DOI. |
| II. Verified Accuracy | BLOCKED | Requires confirmation that DOI 10.5281/zenodo.10043838 provides a usable CSV with Tg and composition. |
| III. Data Hygiene | PASS | Raw data checksummed; derived files versioned. |
| IV. Single Source of Truth | PASS | All metrics stored in JSON; figures generated from these files. |
| V. Versioning Discipline | PASS | Content hashes tracked in project state file. |
| VI. Descriptor Consistency | PASS | Single `descriptors.py` script using pinned `mendeleev`. |
| VII. Model Evaluation Transparency | PASS | Metrics, CV splits, and plots saved and validated against schemas. |

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
│   ├── ingest.py
│   ├── descriptors.py
│   ├── train.py
│   ├── analyze.py
│   └── report.py
├── data/
│   ├── raw/
│   └── processed/
├── artifacts/
│   ├── models/
│   └── metrics/
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| LOFO split | Guarantees prediction for unseen alloy families (FR‑003). | Standard K‑Fold would leak family information. |
| Bonferroni correction | Controls family‑wise error for the three pairwise correlations (FR‑008). | Benjamini‑Hochberg is weak for N=3. |
| Iterative VIF removal | Expected collinearity; ensures stable regression (FR‑007). | Ignoring VIF would leave unstable coefficients. |

## FR/SC Coverage Map
| ID | Phase / Script | Description |
|----|----------------|-------------|
| FR‑001 | `ingest.py` | Load Zenodo 10.5281/zenodo.10043838, drop rows missing Tg or composition. |
| FR‑002 | `descriptors.py` | Compute radius mismatch, electronegativity diff, VEC; log weighted mean radius. |
| FR‑003 | `train.py` | LOFO CV + GradientBoostingRegressor; grid ≤10 combos. |
| FR‑004 | `report.py` | Insert exact phrase “These findings are associational only”. |
| FR‑005 | CI config | Enforce ≤6 h runtime, ≤7 GB RAM. |
| FR‑006 | `analyze.py` | Sensitivity sweep `max_depth` ∈ {3,5,7}; report variance σ² of R². |
| FR‑007 | `analyze.py` | Compute VIF; iteratively drop highest‑VIF predictor until all < 5. |
| FR‑008 | `analyze.py` | Apply Bonferroni correction (α ≤ 0.05) to three pairwise predictor correlations. |
| FR‑009 | `analyze.py` | Compute Pearson & Spearman coefficients + p‑values for all predictor pairs. |
| SC‑001 | `analyze.py` | Compare test‑set R² to null (mean‑prediction) baseline. |
| SC‑002 | `analyze.py` | Bootstrap 1000 resamples for feature‑importance confidence intervals. |
| SC‑003 | `ingest.py` | Log retention rate (valid / raw records). |
| SC‑004 | CI logs | Record CPU time and peak RAM usage. |

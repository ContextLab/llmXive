# Implementation Plan: Gut Microbiome and Cognitive Decline Analysis

**Branch**: `001-gut-microbiome-cognition` | **Date**: 2026-10-15 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`  
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary
The project will build a reproducible, CPU‑only pipeline that (1) downloads open‑source 16S rRNA taxonomic data from the American Gut Project (AGP) and cognitive/clinical metadata from the Health and Retirement Study (HRS), (2) merges the two tables on a shared `participant_id`, (3) preprocesses the microbiome matrix (rarefaction → CLR), (4) computes Spearman rank correlations with Benjamini‑Hochberg FDR correction, (5) trains a Random Forest regressor on genus‑level abundances (plus covariates) with nested cross‑validation, (6) validates the model against a permutation‑based null distribution, and (7) runs a sensitivity analysis over rarefaction depth. All steps produce artifacts that are validated against JSON/YAML contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-bio==0.7.*`, `pycoda==0.1.*` (for CLR), `pyarrow==16.*` (Parquet I/O), `datasets==2.20.*` (HuggingFace), `shap==0.45.*`, `miceforest==5.6.*`  
- **Storage**: Local filesystem under `data/` (raw, processed, results)  
- **Testing**: `pytest` with contract tests in `tests/contract/`  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)  
- **Project Type**: Data‑science / computational‑biology pipeline  
- **Performance Goals**: Total runtime ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only, no GPU, deterministic random seeds, strict reproducibility  

## Constitution Check
| Principle | Status | Action / Note |
|-----------|--------|---------------|
| I. Reproducibility | PASS | `requirements.txt` pinned, seeds fixed, data fetched via deterministic URLs. |
| II. Verified Accuracy | PASS | Only the verified HuggingFace URLs listed in the “Verified datasets” block are used. |
| III. Data Hygiene | PASS | Raw files checksummed, derived files written with new filenames, no PII. |
| IV. Single Source of Truth | PASS | All figures/tables trace to rows in `data/processed/merged_age60.parquet` and code blocks in `code/`. |
| V. Versioning Discipline | PASS | Artifact hashes recorded in `state/projects/PROJ-189-...yaml`. |
| VI. Microbiome Data Provenance | PASS | AGP data loaded from the official Qiita‑derived HuggingFace mirror. |
| VII. Predictive Modeling Transparency | PASS | Random Forest hyper‑parameters, seeds, SHAP values logged and archived. |

## Project Structure
```text
specs/001-investigating-the-correlation-between-gu/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── correlation.schema.yaml
│   ├── dataset.schema.yaml
│   └── model.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-189-investigating-the-correlation-between-gu/
├── data/
│   ├── raw/
│   │   ├── agp.parquet               # AGP taxonomic table (verified URL)
│   │   ├── hrs.parquet               # HRS cognitive & covariate table (verified URL)
│   │   └── bmi.csv                   # Optional BMI supplement (verified URL)
│   ├── processed/
│   │   ├── merged_age60.parquet      # post‑merge, age‑filtered
│   │   ├── clr_normalized.parquet    # CLR‑transformed abundances
│   │   └── imputed.parquet           # after MICE imputation
│   └── results/
│       ├── correlations.json
│       ├── model_metrics.json
│       └── sensitivity.json
├── code/
│   ├── requirements.txt
│   ├── 01_data_ingestion.py
│   ├── 02_preprocessing.py
│   ├── 03_correlation_analysis.py
│   ├── 04_predictive_modeling.py
│   ├── 05_sensitivity_analysis.py
│   └── utils/
│       ├── io.py
│       └── stats.py
├── tests/
│   ├── contract/
│   │   ├── test_dataset_schema.py
│   │   ├── test_correlation_schema.py
│   │   └── test_model_schema.py
│   └── unit/
│       └── ... (helper tests)
└── docs/
    └── paper_draft.md
```

## Phase & Task Mapping (covers every FR & SC)

| Phase | Task ID | Description | FR / SC addressed |
|-------|---------|-------------|-------------------|
| **0 – Data Acquisition** | T001 | `code/01_data_ingestion.py` – programmatic download of AGP & HRS parquet files via `datasets.load_dataset`; checksum verification; store under `data/raw/`. | FR‑001, FR‑002, SC‑001 |
| **1 – Merge & Filtering** | T002 | Merge on `participant_id`; abort with clear error if overlap < 500. Apply age ≥ 60 filter; log overlap statistics. | FR‑001, SC‑001 |
| **2 – Imputation & Normalization** | T003 | MICE imputation for missing BMI; flag `is_missing_bmi`. Rarefy to `min_depth`, then apply CLR (`pycoda.clr`). | FR‑001, FR‑002, FR‑006 |
| **3 – Correlation Analysis** | T004 | Compute Spearman rho for every genus–cognitive_score pair on CLR data; generate raw p‑values; apply Benjamini‑Hochberg (α = 0.05). Save JSON adhering to `contracts/correlation.schema.yaml`. | FR‑003, SC‑002 |
| **4 – Predictive Modeling** | T005 | Nested CV Random Forest (5‑fold outer, 3‑fold inner) with hyper‑grid (`n_estimators`: [100,200], `max_depth`: [10,20, None]). Fixed `random_state=42`. | FR‑004 |
| **5 – Permutation Null** | T006 | 1000 permutations of `cognitive_score`; compute R² each; store 95th percentile; apply Holm‑Bonferroni to permutation‑derived p‑values. | FR‑004, SC‑003 |
| **6 – VIF Check** | T007 | Compute VIF on CLR‑transformed genus matrix; flag any pair with VIF > 5; include flags in `model_metrics.json`. | FR‑006 |
| **7 – Sensitivity Analysis** | T008 | Sweep rarefaction depth `{5_000, min_depth}`; repeat steps 2‑5 for each depth; record variance of R² in `sensitivity.json`. | FR‑005 |
| **8 – Contract Validation** | T009 | Run `pytest tests/contract/` to ensure all output files conform to schemas. | All FR/SC (implicit) |
| **9 – Resource Guardrails** | T010 | Monitor RAM/CPU via `psutil`; if RAM > 6 GB, automatically down‑sample taxa to top‑200 abundant genera and/or reduce permutations to 500; log warning. | FR‑007 |
| **10 – Reporting** | T011 | Assemble a concise `results/summary.md` referencing schema‑validated artifacts; embed key tables/figures (generated via `matplotlib`). | SC‑001‑SC‑004 |

All tasks are deterministic, produce real files, and are verifiable by the contract tests.

## Compute Feasibility
- **Data size**: AGP parquet (~2 GB), HRS parquet (~1 GB). Streaming load (`load_dataset(..., streaming=True)`) keeps RAM < 4 GB.
- **Permutation test**: 1000 × (N≈500) fits within 3 h on 2 CPU cores. If RAM spikes, T010 reduces permutations to 500.
- **No GPU**: All libraries are CPU‑only; `shap` runs in “kernel‑explainer” mode which is CPU‑friendly.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| No shared `participant_id` between AGP and HRS | Early check in T001/T002; if overlap < 500, pipeline aborts with explicit “Fatal Coverage Gap” message and suggests alternative linked dataset. |
| Memory overflow during permutation | T010 down‑samples taxa or reduces permutation count; logs the adjustment. |
| Missing BMI for many participants | MICE imputation plus delta‑adjustment sensitivity (built into T003). |
| Multiple‑testing inflation | BH FDR for correlations; Holm‑Bonferroni for permutation p‑values. |

---

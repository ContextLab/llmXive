# Implementation Plan: Gut Microbiome and Cognitive Decline Analysis

**Branch**: `001-gut-microbiome-cognition` | **Date**: 2026-10-21 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`  
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) downloads open‑source 16S rRNA counts from the American Gut Project (AGP) and cognitive/clinical metadata from the Health and Retirement Study (HRS); (2) verifies provenance via checksums; (3) merges on `participant_id`, filters to age ≥ 60, and imputes missing BMI; (4) rarefies and applies a Centered Log‑Ratio (CLR) transform; (5) computes Spearman correlations with Benjamini‑Hochberg FDR correction; (6) trains a Random Forest regressor with nested cross‑validation, validates against a permutation‑based null distribution, and checks VIF; (7) runs a sensitivity sweep over rarefaction depth; (8) validates every output against a single unified `results.schema.yaml`; (9) enforces CI resource limits; and (10) produces a concise markdown summary.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-bio==0.7.*`, `pycoda==0.1.*`, `datasets==2.20.*`, `shap==0.45.*`, `miceforest==5.6.*`, `psutil==5.9.*`  
- **Storage**: Local filesystem under `data/` (raw, processed, results)  
- **Testing**: `pytest` with contract tests in `tests/contract/`  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)  
- **Project Type**: Data‑science / computational‑biology pipeline  
- **Performance Goals**: Total runtime ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only execution, deterministic random seeds, strict reproducibility, provenance verification (checksum)  

## Constitution Check
| Principle | Status | Action / Note |
|-----------|--------|---------------|
| I. Reproducibility | PASS | Fixed seeds, pinned `requirements.txt`, deterministic URLs. |
| II. Verified Accuracy | PASS | Only the verified HuggingFace URLs listed in the “Verified datasets” block are used. |
| III. Data Hygiene | PASS | Raw files checksummed; derived files receive new filenames; no PII. |
| IV. Single Source of Truth | PASS | All figures/tables trace to rows in `data/processed/merged_age60.parquet` and code blocks in `code/`. |
| V. Versioning Discipline | PASS | Artifact hashes recorded in `state/projects/PROJ-189-...yaml`. |
| VI. Microbiome Data Provenance | PASS | AGP data loaded from the official Qiita‑derived HuggingFace mirror. |
| VII. Predictive Modeling Transparency | PASS | Hyper‑parameters, seeds, SHAP rankings, and permutation null are logged and archived. |

## Project Structure
```text
specs/001-investigating-the-correlation-between-gu/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── results.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-189-investigating-the-correlation-between-gu/
├── data/
│   ├── raw/
│   │   ├── agp.parquet
│   │   ├── hrs.parquet
│   │   └── bmi.csv
│   ├── processed/
│   │   ├── merged_age60.parquet
│   │   ├── clr_normalized.parquet
│   │   └── imputed.parquet
│   └── results/
│       ├── correlations.json
│       ├── model_metrics.json
│       ├── sensitivity.json
│       └── summary.md
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
│   └── contract/
│       └── test_results_schema.py
└── docs/
    └── paper_draft.md
```

## Phase & Task Mapping (covers every FR & SC)

| Phase | Task ID | Description | FR / SC addressed |
|-------|---------|-------------|-------------------|
| **0 – Provenance Validation** | **T001** | `code/01_data_ingestion.py` downloads AGP, HRS, and BMI files via `datasets.load_dataset`. After each download it computes a SHA‑256 checksum and compares it to the reference checksum stored in `state/projects/…yaml`. Failure aborts with a clear log message. | FR‑001, FR‑002, SC‑001 |
| **1 – Merge & Age Filter** | **T002** | Inner join on `participant_id`; abort if overlap < 500. Apply `age >= 60`. Log overlap statistics. | FR‑001, SC‑001 |
| **2 – Imputation & Normalization** | **T003** | MICE imputation for missing BMI (`miceforest`), flag imputed rows. Rarefy to `min_depth`, then CLR transform (`pycoda.clr`). Compute VIF on CLR matrix; flag any pair with VIF > 5. | FR‑001, FR‑002, FR‑006 |
| **3 – Correlation Analysis** | **T004** | Compute Spearman rho for every genus–cognitive_score pair on CLR data, generate raw p‑values, apply Benjamini‑Hochberg FDR (α = 0.05). Save JSON adhering to `contracts/results.schema.yaml` under `data/results/correlations.json`. | FR‑003, SC‑002 |
| **4 – Predictive Modeling** | **T005** | Nested CV Random Forest (5‑fold outer, 3‑fold inner) with grid `{n_estimators: [100,200], max_depth: [10,20,None]}`, `random_state=42`. Evaluate on 20 % hold‑out. | FR‑004 |
| **5 – Permutation Null Distribution** | **T006** | Shuffle `cognitive_score` 1000 times, retrain using the same nested CV pipeline, collect R² distribution. Compute 95th percentile and apply Holm‑Bonferroni correction. Store results in `model_metrics.json`. | FR‑004, SC‑003 |
| **6 – VIF Reporting** | **T007** | Include VIF summary (threshold = 5, flagged pairs) in `model_metrics.json`. | FR‑006 |
| **7 – Sensitivity Analysis** | **T008** | Sweep rarefaction depth over `{5_000, min_depth}`; repeat steps 2‑5 for each depth; record variance of R² in `sensitivity.json`. | FR‑005 |
| **8 – Contract Validation** | **T009** | Run `pytest tests/contract/` to ensure `results.schema.yaml` validation passes for *all* result files. | All FR/SC (implicit) |
| **9 – Resource Guardrails** | **T010** | Use `psutil` to monitor RAM/CPU. If RAM > 6 GB, automatically down‑sample taxa to top‑200 abundant genera and/or truncate permutations to 500, logging the adjustment. | FR‑007 |
| **10 – Reporting** | **T011** | Assemble `data/results/summary.md` that references schema‑validated artifacts, includes key tables/figures (generated with `matplotlib`). | SC‑001 – SC‑004 |

All tasks are deterministic, produce real files, and are verifiable by the contract tests.

## Compute Feasibility
- **Data size**: AGP parquet ≈ 2 GB, HRS parquet ≈ 1 GB. Loaded with `datasets.load_dataset(..., streaming=True)` → RAM < 4 GB.  
- **Permutation testing**: 1000 × ≈ 500 samples fits within 3–4 h on 2 CPU cores. If RAM spikes, T010 trims taxa or permutations.  
- **No GPU**: All libraries are CPU‑only; `shap` runs in kernel‑explainer mode (CPU‑friendly).  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| No shared `participant_id` | Early overlap check (T001/T002); abort with “Fatal Coverage Gap” if < 500. |
| Memory overflow during permutation | T010 down‑samples taxa or reduces permutations, logs adjustment. |
| Missing BMI for many participants | MICE imputation + `is_missing_bmi` flag; sensitivity check in T003. |
| Multiple‑testing inflation | BH FDR for correlations; Holm‑Bonferroni for permutation p‑values. |
| Power insufficiency (N < 100) | Emit warning (SC‑004) but still run; results flagged accordingly. |

---

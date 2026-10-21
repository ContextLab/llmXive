# Implementation Plan: Gut Microbiome and Cognitive Decline Analysis

**Branch**: `001-gut-microbiome-cognition` | **Date**: 2026-10-21 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`  
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary
Create a fully reproducible, CPU‑only analysis pipeline that:

1. **Downloads** open‑source 16S rRNA counts (AGP) and cognitive/clinical metadata (HRS) plus an optional BMI supplement, **verifies** each file with a SHA‑256 checksum stored in version‑controlled `expected_checksums.json`.
2. **Merges** on `participant_id`, **filters** to age ≥ 60, and aborts if the overlap is < 500 (fatal coverage gap).
3. **Rarefies** to the minimum read depth, **CLR‑transforms** genus abundances, **imputes** missing BMI via MICE, and **computes VIF** on the CLR matrix (flagging any VIF > 5).
4. **Computes** Spearman correlations for every genus–cognitive score pair, applies Benjamini‑Hochberg FDR (α = 0.05), and writes a schema‑validated `correlations.json`.
5. **Trains** a Random Forest regressor (scikit‑learn, CPU‑only) with an 80/20 split and 5‑fold outer / 3‑fold inner CV, records hyperparameters, performance, and SHAP rankings.
6. **Generates** a permutation‑null distribution (1000 shuffles) and reports whether the observed R² exceeds the 95th percentile after Holm‑Bonferroni correction.
7. **Performs** a sensitivity sweep over rarefaction depths `{5 000, min_depth}` and records variance of R².
8. **Validates** every output file against the unified `results.schema.yaml` (and component schemas) via contract tests.
9. **Monitors** RAM/CPU; if limits are exceeded, automatically down‑samples taxa or reduces permutation count, logging the adjustment (FR‑007).
10. **Assembles** a concise `summary.md` that references all schema‑validated artifacts.

All steps are deterministic, produce real files, and are verifiable by the CI contract tests.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-bio==0.7.*`, `pycoda==0.1.*`, `datasets==2.20.*`, `shap==0.45.*`, `miceforest==5.6.*`, `psutil==5.9.*`  
- **Storage**: Local filesystem under `data/` (raw, processed, results, provenance).  
- **Testing**: `pytest` with contract tests in `tests/contract/`.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
- **Project Type**: Data‑science / computational‑biology pipeline.  
- **Performance Goals**: Total wall‑clock ≤ 6 h, peak RAM ≤ 6 GB.  
- **Constraints**: CPU‑only execution, deterministic random seeds, strict reproducibility, provenance verification via checksums.  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, pinned `requirements.txt`, deterministic downloads, checksum verification. |
| II. Verified Accuracy | PASS | Only the verified HuggingFace URLs listed in the “Verified datasets” block are used. |
| III. Data Hygiene | PASS | Raw files are immutable; each transformation writes a new file with a checksum recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | PASS | Every figure/table originates from a single row in `data/processed/merged_age60.parquet` and a single code block. |
| V. Versioning Discipline | PASS | All artifacts are hashed; hashes stored in the project state file. |
| VI. Microbiome Data Provenance | PASS | AGP data fetched from the official Qiita‑derived HuggingFace mirror. |
| VII. Predictive Modeling Transparency | PASS | Hyper‑parameters, seeds, SHAP rankings, and permutation null are logged and archived. |

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
│   ├── model.schema.yaml
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
│   ├── provenance/
│   │   ├── expected_checksums.json   # version‑controlled
│   │   └── observed_checksums.json   # produced by validate_provenance.py
│   ├── processed/
│   │   ├── merged_age60.parquet
│   │   ├── clr_normalized.parquet
│   │   └── imputed.parquet
│   └── results/
│       ├── correlations.json
│       ├── model.json
│       ├── sensitivity.json
│       ├── unified_results.json
│       └── summary.md
├── code/
│   ├── requirements.txt
│   ├── 01_download_and_provenance.py
│   ├── 02_merge_preprocess.py
│   ├── 03_correlation.py
│   ├── 04_modeling.py
│   ├── 05_sensitivity.py
│   └── utils/
│       ├── io.py
│       └── stats.py
├── tests/
│   └── contract/
│       ├── test_dataset_schema.py
│       ├── test_correlation_schema.py
│       ├── test_model_schema.py
│       └── test_results_schema.py
└── docs/
    └── paper_draft.md
```

## Phase & Task Mapping (covers every FR & SC)

| Phase | Task ID | Script | Output | FR / SC addressed |
|-------|---------|--------|--------|-------------------|
| **0 – Provenance Validation** | **T001** | `code/01_download_and_provenance.py` (download) + `code/validate_provenance.py` (checksum) | `data/provenance/observed_checksums.json` | FR‑001, FR‑002, SC‑001 |
| **1 – Merge & Age Filter** | **T002** | `code/02_merge_preprocess.py` (merge, age ≥ 60) | `data/processed/merged_age60.parquet` (also `data/processed/dataset.json` conforming to `dataset.schema.yaml`) | FR‑001, SC‑001 |
| **2 – Rarefaction, CLR, Imputation, VIF** | **T003** | `code/02_merge_preprocess.py` (rarefaction, CLR, MICE BMI, VIF) | `data/processed/clr_normalized.parquet`, `data/processed/imputed.parquet` | FR‑002, FR‑006 |
| **3 – Correlation Analysis** | **T004** | `code/03_correlation.py` | `data/results/correlations.json` (validated by `correlation.schema.yaml`) | FR‑003, SC‑002 |
| **4 – Predictive Modeling** | **T005** | `code/04_modeling.py` (Random Forest, nested CV) | `data/results/model.json` (validated by `model.schema.yaml`) | FR‑004 |
| **5 – Permutation Null Distribution** | **T006** | `code/04_modeling.py` (permutation block) | Included inside `model.json` (null_distribution field) | FR‑004, SC‑003 |
| **6 – VIF Reporting** | **T007** | `code/04_modeling.py` (VIF summary) | Included inside `model.json` (vif_check field) | FR‑006 |
| **7 – Sensitivity Analysis** | **T008** | `code/05_sensitivity.py` (depth sweep) | `data/results/sensitivity.json` (part of unified results) | FR‑005 |
| **8 – Unified Results Assembly** | **T009** | `code/05_sensitivity.py` (final assembly) | `data/results/unified_results.json` (validated by `results.schema.yaml`) | All FR/SC (implicit) |
| **9 – Resource Guardrails** | **T010** | `code/utils/stats.py` (psutil monitor) invoked by each script | Runtime logs; automatic down‑sampling if RAM > 6 GB | FR‑007 |
| **10 – Reporting** | **T011** | `code/05_sensitivity.py` (summary generation) | `data/results/summary.md` (human‑readable) | SC‑001 – SC‑004 |

All tasks are deterministic, produce real files, and are verified by contract tests (Task T009).

## Compute Feasibility
- **Data size**: AGP ≈ 2 GB, HRS ≈ 1 GB. Loaded with `datasets.load_dataset(..., streaming=True)` → RAM < 4 GB.  
- **Permutation testing**: 1000 × ≈ 500 samples ≈ 3–4 h on 2 CPU cores.  
- **No GPU**: All libraries are CPU‑compatible; `shap` uses the kernel explainer (CPU).  
- **Memory guardrails**: `psutil` monitors RAM; if > 6 GB, taxa are limited to the top‑200 abundant genera and permutations reduced to 500 (logged).  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Fatal coverage gap (overlap < 500) | Early overlap check aborts with clear message; user must supply a linked dataset. |
| Checksum mismatch (T001) | Expected checksums are version‑controlled; any change forces a deliberate update of `expected_checksums.json`. |
| Memory overflow during permutation | Guardrail T010 down‑samples taxa or reduces permutations, logs adjustment. |
| Missing BMI for many participants | MICE imputation + `is_missing_bmi` flag; sensitivity check on imputation effect. |
| Multiple‑testing inflation | BH FDR for correlations; Holm‑Bonferroni for permutation p‑values. |
| Power insufficiency (N < 100) | Emit warning (SC‑004) but still run; results flagged accordingly. |
| Collinearity | VIF computed; any VIF > 5 flagged and reported. |

---

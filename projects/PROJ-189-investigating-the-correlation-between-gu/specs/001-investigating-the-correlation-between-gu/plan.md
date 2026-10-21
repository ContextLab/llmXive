# Implementation Plan: Gut Microbiome and Cognitive Decline Analysis

**Branch**: `001-gut-microbiome-cognition` | **Date**: 2026-10-21 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`  
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary
Create a reproducible, CPU‑only pipeline that (1) downloads the AGP 16S taxonomic table and HRS cognitive metadata from verified HuggingFace mirrors, (2) verifies SHA‑256 checksums, (3) merges on participant ID and filters to age ≥ 60, (4) rarefies to the minimum read depth, (5) computes VIF on raw genus abundances (pre‑CLR) and excludes taxa with VIF > 5, (6) applies a CLR transformation, (7) imputes missing BMI via MICE, (8) performs covariate‑adjusted partial Spearman correlations with BH‑FDR, (9) fits a Random Forest regressor (including demographics) with nested 5‑fold CV, (10) evaluates significance against a 1 000‑permutation null distribution, (11) generates permutation importance and SHAP summary artifacts, (12) conducts a formal power analysis for correlation and regression components, (13) runs a sensitivity sweep over rarefaction depth, (14) enforces RAM guardrails (≤ 6 GB) and logs any automatic down‑sampling, and (15) assembles a unified JSON results file that includes the required checksums. All steps are deterministic, validated against JSON schemas, and respect the project constitution.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:  
- `pandas==2.2.*`  
- `numpy==1.26.*`  
- `scikit-learn==1.5.*`  
- `statsmodels==0.14.*`  
- `scipy==1.13.*`  
- `pingouin==0.5.*`  
- `shap==0.45.*`  
- `miceforest==5.6.*`  
- `psutil==5.9.*`  
- `datasets==2.20.*` (for streaming download)  
- `pycoda==0.2.*` (CLR transformation)  

**Storage**: Local filesystem under `data/` (raw, processed, results, provenance).  
**Testing**: `pytest` with contract tests in `tests/contract/`.  
**Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
**Project Type**: Research‑oriented data‑analysis library (no web service).  
**Performance Goals**: End‑to‑end wall‑clock ≤ 6 h, peak RAM ≤ 6 GB.  
**Constraints**: CPU‑only execution; all random seeds pinned (`42`).  
**Scale/Scope**: Process the full AGP‑HRS linked cohort (≥ 500 participants) without down‑sampling unless guardrails trigger.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, pinned `requirements.txt`, deterministic downloads, checksum verification. |
| II. Verified Accuracy | PASS | All external URLs are verified HuggingFace mirrors; no unverified sources. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with recorded checksum. |
| IV. Single Source of Truth | PASS | Every figure/statistic traces to a single row in `data/processed/merged_age60.parquet` and a single code block. |
| V. Versioning Discipline | PASS | All artifacts hashed; hashes stored in project state file. |
| VI. Microbiome Data Provenance | PASS* | Data obtained from verified HuggingFace mirrors because a direct open Qiita/EBI endpoint is not publicly downloadable. This limitation is documented in `research.md`. |
| VII. Predictive Modeling Transparency | PASS | Hyper‑parameters, seeds, performance metrics, permutation null, VIF report, and SHAP rankings are logged and archived. |

\* *See `research.md` for explicit discussion of the provenance limitation.*

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
│   │   └── observed_checksums.json   # produced by 01_download_and_provenance.py
│   ├── processed/
│   │   ├── merged_age60.parquet
│   │   ├── dataset.json               # conforms to contracts/dataset.schema.yaml
│   │   ├── clr_normalized.parquet
│   │   └── imputed.parquet
│   └── results/
│       ├── correlations.json          # contracts/correlation.schema.yaml
│       ├── model.json                 # contracts/model.schema.yaml
│       ├── sensitivity.json
│       ├── unified_results.json       # contracts/results.schema.yaml
│       ├── summary.md
│       └── figures/
│           ├── correlation_heatmap.png
│           └── model_shap_summary.png
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

| Phase | Task ID | Script | Primary Output | FR / SC addressed |
|-------|---------|--------|----------------|-------------------|
| **0 – Provenance Validation** | **T001** | `code/01_download_and_provenance.py` (download + checksum) | `data/provenance/observed_checksums.json` | FR‑001, FR‑002, SC‑001 |
| **1 – Merge & Age Filter** | **T002** | `code/02_merge_preprocess.py` (merge, age ≥ 60) | `data/processed/merged_age60.parquet` & `data/processed/dataset.json` | FR‑001, SC‑001 |
| **2 – VIF Pre‑CLR & Rarefaction** | **T003** | `code/02_merge_preprocess.py` (VIF, rarefaction) | `data/processed/merged_age60.parquet` (with VIF flags) | FR‑010 |
| **3 – CLR Transform, BMI Imputation, Pearson Collinearity** | **T004** | `code/02_merge_preprocess.py` (CLR, MICE, Pearson |r|) | `data/processed/clr_normalized.parquet`, `data/processed/imputed.parquet` | FR‑002, FR‑010 (collinearity reported), FR‑009 (imputation check) |
| **4 – Partial Spearman Correlation + BH‑FDR** | **T005** | `code/03_correlation.py` | `data/results/correlations.json` | FR‑003, SC‑002 |
| **5 – Random Forest Modeling (Nested CV) + Covariates** | **T006** | `code/04_modeling.py` (training) | `data/results/model.json` (model block) | FR‑004, FR‑008 |
| **6 – Permutation Null Distribution & Significance** | **T007** | `code/04_modeling.py` (permutation) | Embedded in `model.json` (null_distribution) | FR‑004, SC‑003 |
| **7 – VIF Report Integration** | **T008** | `code/04_modeling.py` (adds VIF report) | `model.json` (vif_check) | FR‑010 |
| **8 – Sensitivity Analysis (Rarefaction Depth Sweep)** | **T009** | `code/05_sensitivity.py` | `data/results/sensitivity.json` | FR‑005 |
| **9 – Power Analysis (Correlation & Regression)** | **T010** | `code/05_sensitivity.py` (power module) | Power warnings stored in `summary.md` | FR‑009, SC‑004 |
| **10 – Resource Guardrails (RAM ≤ 6 GB)** | **T011** | `code/utils/stats.py` (monitor) invoked by all scripts | Runtime logs; automatic taxa truncation / permutation reduction if needed | FR‑007 |
| **11 – Unified Results Assembly (Checksums Included)** | **T012** | `code/05_sensitivity.py` (final assembly) | `data/results/unified_results.json` (includes `checksum_agp`, `checksum_hrs`) | All FR/SC (implicit) |
| **12 – Reporting** | **T013** | `code/05_sensitivity.py` (summary generation) | `data/results/summary.md` | SC‑001 – SC‑004 |

All tasks are deterministic, produce real files, and are validated by contract tests (Task T012).

## Compute Feasibility (CPU‑first)
- **Data download & checksum**: < 15 min, < 200 MB RAM.  
- **Pre‑processing (VIF, rarefaction, CLR, imputation)**: < 10 min, ≤ 4 GB RAM.  
- **Correlation**: < 20 min, ≤ 2 GB RAM.  
- **Random Forest + 1 000 permutations**: 3–4 h, ≤ 6 GB RAM (fits free‑tier limits).  
- **Sensitivity sweep (2 depths)**: ~1 h.  
- **Total wall‑clock**: ≤ 6 h, ≤ 6 GB RAM.  
All libraries run on CPU; no GPU is required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Fatal coverage gap (overlap < 500) | Early overlap check aborts with clear error; user must provide linked data. |
| Checksum mismatch | Expected checksums are version‑controlled; any change forces an explicit update of `expected_checksums.json`. |
| RAM overflow during permutation | Guardrail T011 truncates to top‑200 genera and reduces permutations to 500, logging the adjustment. |
| Missing BMI for many participants | MICE imputation + `is_missing_bmi` flag; sensitivity check on imputation effect (Task T004). |
| Multiple‑testing inflation | BH‑FDR for correlations; Holm‑Bonferroni for permutation p‑values. |
| Power insufficiency | Formal power analysis (Task T010) emits warnings if effective N < 100 or detectable effect size is unrealistic. |
| Collinearity after CLR | Pearson |r| > 0.9 flagged; VIF > 5 flagged pre‑CLR (FR‑010). |
| Covariate omission in modeling | Demographic covariates are explicitly included as features (Task T006). |

---

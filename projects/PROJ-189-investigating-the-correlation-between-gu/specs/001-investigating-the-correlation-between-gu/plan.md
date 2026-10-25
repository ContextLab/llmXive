# Implementation Plan: Gut Microbiome and Cognitive Decline Analysis

**Branch**: `001-gut-microbiome-cognition` | **Date**: 2026-10-25 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`  
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary
Create a fully reproducible, CPU‑only pipeline that (1) downloads the American Gut Project (AGP) 16S rRNA taxonomic table and Health and Retirement Study (HRS) cognitive metadata from verified HuggingFace mirrors, (2) validates SHA‑256 checksums, (3) attempts to merge on a shared `participant_id` and filters to age ≥ 60, (4) **if the participant‑ID overlap is < 500 the pipeline aborts with a clear diagnostic** (the merge is infeasible with current public releases), (5) rarefies to the minimum read depth, (6) computes pre‑CLR VIF and excludes collinear taxa, (7) applies CLR transformation, (8) imputes missing BMI via MICE, (9) performs covariate‑adjusted partial Spearman correlations with BH‑FDR, (10) fits a Random Forest regressor (nested 5‑fold CV) with demographic covariates, (11) evaluates against a 1 000‑permutation null distribution, (12) conducts a **standard linear regression** of cognitive scores on CLR‑transformed genera (adjusting for covariates) when a linked dataset is available, (13) generates permutation importance and SHAP artefacts, (14) conducts a rarefaction‑depth sensitivity sweep, (15) runs formal power analyses for correlation and regression components, (16) enforces RAM ≤ 6 GB guardrails, and (17) assembles a unified JSON results file that includes the required SHA‑256 checksums. All outputs are validated against JSON schemas.

## Scientific Limitation
Public releases of AGP and HRS contain **no shared participant identifier**; therefore a cross‑sectional merge yielding ≥ 500 overlapping records is impossible. The pipeline will perform the overlap check, abort early if the threshold is not met, and log the limitation. **To answer the core research question a truly linked microbiome‑cognition dataset must be supplied in a future specification revision** (or an open substitute that contains both microbiome and cognition for the same participants). Until such data are available, downstream analyses (correlation, modeling, etc.) will not run.

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
- `datasets==2.20.*` (streaming download)
- `pycoda==0.2.*` (CLR)
- `statsmodels==0.14.*` (VIF)

**Storage**: Local filesystem under `data/` (raw, processed, results, provenance).  
**Testing**: `pytest` with contract tests in `tests/contract/`.  
**Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
**Performance Goals**: End‑to‑end wall‑clock ≤ 6 h, peak RAM ≤ 6 GB.  
**Constraints**: CPU‑only execution; no GPU required.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, deterministic downloads, checksum validation. |
| II. Verified Accuracy | PASS | All external URLs are verified HuggingFace mirrors. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with recorded checksum. |
| IV. Single Source of Truth | PASS | Every figure/statistic traces to a single row in `data/processed/merged_age60.parquet` and a single code block. |
| V. Versioning Discipline | PASS | All artifacts hashed; hashes stored in project state. |
| VI. Microbiome Data Provenance | PASS* | Data are obtained from verified mirrors; however **no public participant‑level linkage exists**. The pipeline therefore aborts if overlap < 500 and documents this limitation. |
| VII. Predictive Modeling Transparency | PASS | Hyper‑parameters, seeds, performance, permutation null, VIF, and SHAP are logged and archived. |

\*See `research.md` for the explicit discussion of the linkage limitation and its impact on downstream analysis.

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
│   │   ├── expected_checksums.json
│   │   └── observed_checksums.json
│   ├── processed/
│   │   ├── merged_age60.parquet
│   │   ├── clr_normalized.parquet
│   │   └── imputed.parquet
│   └── results/
│       ├── correlations.json
│       ├── model.json
│       ├── linear_regression.json
│       ├── sensitivity.json
│       ├── unified_results.json
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
│   ├── 05_linear_regression.py
│   ├── 06_sensitivity.py
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
| **0 – Provenance Validation** | **T001** | `code/01_download_and_provenance.py` | `data/provenance/observed_checksums.json` | FR‑001, FR‑002, SC‑001 |
| **1 – Merge & Age Filter (Conditional)** | **T002** | `code/02_merge_preprocess.py` (inner‑join on `participant_id`) | `data/processed/merged_age60.parquet`, `data/processed/dataset.json` | FR‑001, SC‑001 |
| **2 – Overlap Check (Abort if < 500)** | **T002‑OV** | `code/02_merge_preprocess.py` (post‑merge) | Log entry; abort if `overlap < 500` | FR‑001 (implicit), SC‑001 |
| **3 – VIF Pre‑CLR & Rarefaction** | **T003** | `code/02_merge_preprocess.py` | Updated `merged_age60.parquet` (VIF flags) | FR‑010 |
| **4 – CLR, BMI Imputation, Pearson Collinearity** | **T004** | `code/02_merge_preprocess.py` | `clr_normalized.parquet`, `imputed.parquet` | FR‑002, FR‑010 (post‑CLR collinearity), FR‑009 (imputation check) |
| **5 – Partial Spearman Correlation + BH‑FDR** | **T005** | `code/03_correlation.py` | `data/results/correlations.json` | FR‑003, SC‑002 |
| **6 – Random Forest Modeling (Nested CV)** | **T006** | `code/04_modeling.py` | `data/results/model.json` | FR‑004, FR‑008 |
| **7 – Permutation Null Distribution** | **T007** | `code/04_modeling.py` (permutation) | Embedded in `model.json` | FR‑004, SC‑003 |
| **8 – VIF Report Integration** | **T008** | `code/04_modeling.py` | `model.json` (vif_check) | FR‑010 |
| **9 – Linear Regression (Cross‑sectional)** | **T014** | `code/05_linear_regression.py` | `data/results/linear_regression.json` | FR‑013, SC‑002 |
| **10 – Sensitivity Analysis (Rarefaction Depth Sweep)** | **T009** | `code/06_sensitivity.py` | `data/results/sensitivity.json` | FR‑005 |
| **11 – Power Analysis (Correlation & Regression)** | **T010** | `code/06_sensitivity.py` (power module) | Warnings in `summary.md` | FR‑009, SC‑004 |
| **12 – Resource Guardrails (RAM ≤ 6 GB)** | **T011** | `code/utils/stats.py` (monitor) invoked by all scripts | Runtime logs; automatic taxa truncation / permutation reduction if needed | (internal safeguard) |
| **13 – Unified Results Assembly (Checksums Included)** | **T012** | `code/06_sensitivity.py` | `data/results/unified_results.json` | All FR/SC (implicit) |
| **14 – Reporting** | **T013** | `code/06_sensitivity.py` (summary generation) | `data/results/summary.md` | SC‑001 – SC‑004 |

All tasks are deterministic, produce real files, and are validated by contract tests (Task T012).

## US-2 – Associational Correlation Analysis
The system MUST compute Spearman rank correlations between genus‑level microbial abundances and cognitive test scores **adjusting for the covariates age, sex, BMI, and education**. It MUST first regress each microbial genus and each cognitive score on these covariates, use the residuals for correlation, and then apply the Benjamini‑Hochberg FDR method (α = 0.05). The system MUST also perform a **standard linear regression** of cognitive scores on CLR‑transformed genus abundances with random intercepts **only if repeated measures exist**, adjusting for the same covariates, and report fixed‑effect coefficients and associated p‑values. The system MUST apply a Centered Log‑Ratio (CLR) transformation to the taxonomic data prior to the residualisation step to address compositionality.

## Compute Feasibility (CPU‑first)
- **Download & checksum**: < 15 min, < 200 MB RAM.  
- **Pre‑processing**: < 10 min, ≤ 4 GB RAM.  
- **Correlation**: < 20 min, ≤ 2 GB RAM.  
- **Random Forest + 1 000 permutations**: 3–4 h, ≤ 6 GB RAM.  
- **Linear regression**: < 5 min, ≤ 2 GB RAM.  
- **Sensitivity sweeps**: ~1 h.  
- **Total**: ≤ 6 h, ≤ 6 GB RAM.  
No GPU is required; all libraries run on CPU.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Zero overlap between AGP and HRS** | Early overlap check aborts with clear diagnostic; specification must supply a dataset that contains both microbiome and cognition for the same participants or revise the question. |
| **Checksum mismatch** | Expected checksums are version‑controlled; a change forces an explicit update. |
| **RAM overflow during permutation testing** | Guardrail T011 automatically truncates to the top‑200 genera and/or reduces permutation count to 500, logging the adjustment. |
| **Missing BMI for many participants** | MICE imputation plus `is_missing_bmi` flag; sensitivity check on imputation effect. |
| **Multiple‑testing inflation** | BH‑FDR for correlation matrix; Holm‑Bonferroni for permutation‑derived model p‑value. |
| **Power insufficiency** | Formal power analysis (Task T010) emits warnings if (a) effective N < 100 or (b) required sample size exceeds observed N. |
| **Collinearity after CLR** | Pearson |r| > 0.9 flagged; VIF > 5 flagged pre‑CLR. |
| **Covariate omission in modeling** | Demographic covariates are explicitly added as features in the Random Forest and linear regression models. |

---


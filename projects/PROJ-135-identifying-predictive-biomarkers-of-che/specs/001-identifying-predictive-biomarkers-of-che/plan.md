# Implementation Plan: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

**Branch**: `001-chemo-biomarker-discovery` | **Date**: 2024-01-15 | **Spec**: `specs/001-chemo-biomarker-discovery/spec.md`
**Input**: Feature specification from `/specs/001-chemo-biomarker-discovery/spec.md`

## Summary

This project implements a computational pipeline to identify gene-expression signatures predicting chemotherapy response across multiple tumor types. The approach involves: (1) acquiring TCGA RNA-seq and GEO microarray data; (2) harmonizing identifiers and normalizing expression via DESeq2 VST; (3) performing differential expression analysis to find cross-tumor biomarkers using a **Leave-One-Cancer-Type-Out (LOO) Blind Meta-Analysis** protocol; (4) training elastic-net logistic regression models with nested cross-validation; and (5) validating on independent cohorts with strict statistical rigor (Bonferroni correction, calibration checks, and **ComBat** for continuous data). The pipeline is designed to run on CPU-only GitHub Actions runners (≤6h, ≤7GB RAM) by using separate R processes for DESeq2 and streaming data where necessary.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `tcga-biolinks` (via `rpy2`), `GEOquery` (via `rpy2`), `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `biopython`, `pyyaml`, `rpy2` (configured for separate R process execution)  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`)  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions free-tier)  
**Project Type**: Computational Biology Pipeline / CLI  
**Performance Goals**: Complete full pipeline (3 tumor types, 2 GEO) in ≤6 hours; Memory ≤7 GB RAM.  
**Constraints**: 
- No local GPU; 
- Must handle data streaming to avoid OOM; 
- Must handle missing response annotations gracefully (fallback to survival proxy or halt); 
- Must enforce strict statistical thresholds (FDR < 0.05, AUC ≥ 0.75); 
- **Must use ComBat (not ComBat-seq) for continuous data alignment (FR-014)**; 
- **Must use Random-Effects Meta-Analysis (REML) for cross-tumor integration**; 
- **Must implement LOO-Blind Meta-Analysis**; 
- **Must report Bonferroni correction (FR-010) and DeLong's test (FR-011)**.  
**Scale/Scope**: ~3 tumor types (TCGA), ~2 GEO datasets; ~1000 samples total; [deferred] genes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Compliant | Plan mandates pinned `requirements.txt`, random seeds, and reproducible data fetching (TCGA/GEO via official APIs). |
| **II. Verified Accuracy** | ✅ Compliant | All dataset URLs in `research.md` are restricted to the "Verified datasets" block provided in the prompt. No fabricated URLs. **Process**: The Reference-Validator Agent runs at three points (artifact write, Advancement-Evaluator, blocking gate) to verify citations against primary sources with title-token-overlap ≥ 0.7. |
| **III. Data Hygiene** | ✅ Compliant | Pipeline design includes checksumming raw data, preserving raw files, and writing derivations to new files. PII scan exclusion noted. |
| **IV. Single Source of Truth** | ✅ Compliant | Plan requires all figures/stats to be generated directly from `data/` and `code/` outputs, not hand-typed. |
| **V. Versioning Discipline** | ✅ Compliant | Artifacts will carry content hashes. **Action**: The pipeline MUST update `state/projects/PROJ-135-...yaml` with content hashes after each artifact generation to maintain the SSoT. |
| **VI. Cross‑Cohort Validation** | ✅ Compliant | Plan explicitly includes LOO (Leave-One-Cancer-Type-Out) and external GEO validation as mandatory phases. |
| **VII. Statistical Rigor** | ✅ Compliant | Plan enforces FDR < 0.05, log2FC > 1.0, Bonferroni correction, and AUC ≥ 0.75 thresholds in logic. **Method**: Uses REML for meta-analysis to account for correlation. |

**Resolution of Unresolved Panel Concerns**:
1.  **LOO Pre-check (T033)**: The plan explicitly defines a pre-execution validation step in the "Model Training & Validation" phase. Before attempting LOO, the system counts available tumor types. If `N < 3` (since leaving one out requires `N-1 >= 2`), the system halts immediately with a `ValidationError`, preventing invalid data generation. **Alternative**: If LOO is invalid, the system switches to 'Nested Cross-Validation within a single large cohort' or 'External GEO-only validation' if available.
2.  **Fallback Flag (T026)**: The "Cross-Cancer Biomarker Identification" phase includes a mandatory logic branch: if the intersection is empty, the system MUST write `results/summary.md` with `fallback_reason: "intersection_empty"` and `panel_source: "union_top_50"` before proceeding. **See FR-006**. This is a hard completion criterion.
3.  **Construct Validity (Survival vs. Response)**: The plan includes a "Construct Validity Check" phase. If direct response labels are missing, the pipeline attempts to use survival proxies (PFS/OS) with a mandatory `prognostic_vs_predictive: "proxy"` flag in the summary. If no valid labels or proxies exist, it halts with `NoValidCohort`.
4.  **Circular Validation**: The plan implements "LOO-Blind Meta-Analysis": the meta-analysis (gene panel selection) is performed ONLY on the training set (N-1 tumor types) for each LOO iteration, excluding the held-out type.
5.  **Memory/Compute**: DESeq2 is executed in a separate R process (via `rpy2` with memory limits) or using chunked processing to stay within 7GB RAM.
6.  **Batch Correction**: FR-014 is updated to mandate **ComBat** (for continuous data) instead of ComBat-seq.

## Project Structure

### Documentation (this feature)

```text
specs/001-chemo-biomarker-discovery/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── gene_panel.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data_acquisition.py      # TCGA/GEO downloaders (TCGA, GEOquery wrappers)
├── preprocessing.py         # Harmonization, filtering, VST, batch correction (ComBat)
├── biomarker_discovery.py   # DE analysis, REML meta-analysis, panel selection (LOO-Blind)
├── model_training.py        # Elastic-net, nested CV, LOO logic
├── evaluation.py            # ROC-AUC, calibration, DeLong's test, Bonferroni
├── utils/
│   ├── config.py            # Path constants, seed management
│   └── logging.py           # Structured logging
└── main.py                  # Pipeline orchestrator

data/
├── raw/                     # Downloaded raw files (checksummed)
└── processed/               # Harmonized, normalized matrices

results/
├── meta_analysis/           # REML results, gene lists
├── models/                  # Saved sklearn models
└── summary.md               # Final report (includes fallback flags, proxy flags)

tests/
├── unit/                    # Logic tests (e.g., LOO pre-check, proxy logic)
├── integration/             # End-to-end subset runs
└── contract/                # Schema validation tests
```

**Structure Decision**: Single Python project structure (`src/`) chosen to minimize overhead on the GitHub Actions runner and simplify dependency management. Modular design separates data, logic, and evaluation to allow independent testing and debugging.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual-platform normalization (RNA-seq + Microarray)** | Required by FR-014 to align GEO microarray data with TCGA RNA-seq. | Simple merging is impossible due to different scales/distributions; requires VST + **ComBat** (continuous) or quantile matching. |
| **Nested Cross-Validation** | Required by FR-07 to prevent data leakage in hyperparameter tuning. | Simple k-fold CV would overestimate performance, violating SC-001 (AUC ≥ 0.75) validity. |
| **LOO Validation Pre-check** | Required by FR-008 to prevent invalid model evaluation. | Running LOO with N=2 would leave only 1 type for training, making generalizability assessment impossible. **See FR-008**. |
| **LOO-Blind Meta-Analysis** | Required to prevent circular validation (scientific_soundness-c0fd5455). | Including the held-out type in meta-analysis biases the panel toward that type, invalidating the generalizability claim. |
| **Separate R Process for DESeq2** | Required to stay within 7GB RAM (methodology-d58c678f). | Running DESeq2 in the same Python process risks OOM; separate process with memory limits is safer. |
| **Random-Effects Meta-Analysis (REML)** | Required to account for correlation between tumor types (methodology-6afa132a). | Stouffer's method assumes independence, which is invalid for correlated biological data. |

## Phase 0: Data Acquisition & Construct Validity Check

**Goal**: Fetch data and verify the existence of valid response labels or proxies.

1.  **Fetch TCGA Data**: Use `TCGAbiolinks` (R) via `rpy2` to download RNA-seq HTSeq-Counts and clinical metadata for ≥3 tumor types.
    - **Check**: Verify presence of `response_label` (e.g., RECIST).
    - **Fallback**: If missing, attempt to derive `response_label` from survival data (PFS/OS < median). Flag as `prognostic_vs_predictive: "proxy"`.
    - **Halt**: If no valid labels or proxies exist, halt with `NoValidTCGACohort`.
2.  **Fetch GEO Data**: Use `GEOquery` (R) via `rpy2` to download GSE25055, GSE42752 (or verified alternatives).
    - **Check**: Verify presence of `response_label`.
    - **Fallback**: If missing, attempt survival proxy. Flag as `prognostic_vs_predictive: "proxy"`.
    - **Halt**: If no valid labels or proxies exist in ≥2 datasets, halt with `NoValidValidationCohort`.
3.  **Checksum**: Record checksums in `state/...yaml`.

## Phase 1: Preprocessing & Harmonization

1.  **Harmonize**: Map Ensembl/Entrez to HGNC (≥95% coverage).
2.  **Filter**: Remove low-expression genes (CPM < 1 in >80% samples).
3.  **Normalize**: Apply DESeq2 VST (via separate R process).
4.  **Batch Correct**: Apply **ComBat** (for continuous VST data) to align GEO and TCGA. **See FR-014**.

## Phase 2: Cross-Cancer Biomarker Identification (LOO-Blind)

**Goal**: Identify a gene panel that generalizes across tumor types.

1.  **LOO Loop**: For each tumor type `T` (held-out):
    - **Subset**: Select data from all other tumor types (N-1).
    - **DE Analysis**: Perform DESeq2 Wald test on the N-1 subset (FDR < 0.05, |log2FC| > 1.0). **See FR-005**.
    - **Meta-Analysis**: Perform **Random-Effects Meta-Analysis (REML)** on the N-1 DE results to generate a candidate panel. **See FR-006**.
    - **Fallback**: If intersection is empty, use union of top 50 genes. **Write `results/summary.md` with `fallback_reason: "intersection_empty"`. See FR-006**.
2.  **Validation**: Train model on N-1 types, test on `T`.
3.  **Aggregation**: Aggregate results across all LOO iterations.

## Phase 3: Model Training & Validation

**Goal**: Train and validate the final model.

1.  **Pre-check**: If total tumor types < 3, halt with `ValidationError` (See FR-008).
2.  **Training**: Train elastic-net logistic regression with nested CV (5x5) on the full dataset (if LOO valid) or on the largest cohort (if LOO invalid).
3.  **External Validation**: Apply model to GEO datasets (after ComBat alignment).
4.  **Evaluation**:
    - Compute ROC-AUC, Precision-Recall, Calibration.
    - **Bonferroni Correction**: Apply for multiple hypothesis testing (m = number of genes or comparisons). **See FR-010**.
    - **DeLong's Test**: Compare model vs. clinical covariates-only baseline. **See FR-011**.
    - **Calibration**: Check deciles (N ≥ 20) for ±10% alignment. Flag underpowered deciles.

## Phase 4: Reporting & Versioning

1.  **Generate Summary**: Write `results/summary.md` including all flags (`fallback_reason`, `prognostic_vs_predictive`, `validation_status`).
2.  **Update State**: Update `state/projects/PROJ-135-...yaml` with content hashes of all artifacts.
3.  **Reference Validation**: Trigger Reference-Validator Agent to verify all citations.

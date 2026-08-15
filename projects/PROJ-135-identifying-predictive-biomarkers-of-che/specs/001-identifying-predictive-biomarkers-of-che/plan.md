# Implementation Plan: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

**Branch**: `001-chemo-biomarker-discovery` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-chemo-biomarker-discovery/spec.md`

## Summary

This project implements a computational pipeline to identify cross-tumor predictive biomarkers for chemotherapy response. The approach integrates TCGA RNA-seq data and GEO microarray datasets, harmonizes gene identifiers, performs differential expression analysis (DESeq2), and conducts **Random-Effects Meta-Analysis (DerSimonian-Laird)** to derive a unified gene panel. Elastic-net logistic regression models are trained with nested cross-validation and validated via **Nested Leave-One-Cancer-Type-Out (LOO)** (where gene selection is re-run inside the loop) and external GEO cohorts. The pipeline is designed to execute within GitHub Actions free-tier constraints (limited CPU, constrained RAM, 6h) by prioritizing streaming data access, CPU-tractable statistical methods, and strict resource monitoring.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `rpy2` (for DESeq2), `pyyaml`, `requests`, `datasets` (Hugging Face), `numpy`, `matplotlib`, `seaborn`, `statsmodels` (for meta-analysis).  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`). No external database.  
**Testing**: `pytest` (unit, integration, contract).  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Data Science Pipeline / Computational Biology.  
**Performance Goals**: Complete full pipeline in **≤6 hours**; Memory usage **≤7 GB RAM**.  
**Constraints**: CPU-only execution (with Kaggle GPU offload for any unavoidable CUDA tasks, though none are planned for this statistical workflow); No local GPU; Data must be streamed or sampled to fit memory.  
**Scale/Scope**: TCGA tumor types, GEO datasets, ≤50 genes in final panel, ≤1000 samples per type.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds will be pinned in `config.py`. External datasets fetched from verified Hugging Face URLs. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` and `data-model.md` will be validated against primary sources before acceptance. The **Reference-Validator Agent** runs at three points: (1) on artifact write, (2) before Advancement-Evaluator, (3) as a blocking gate on `research_review` → `research_accepted`. |
| **III. Data Hygiene** | **PASS** | `data/` files will be checksummed; raw data preserved; derivations written to new files. PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` will trace to `data/` rows and `code/` blocks. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; `state/` YAML updated on changes. |
| **VI. Cross‑Cohort Validation** | **PASS** | Plan explicitly includes **Nested LOO** and external GEO validation steps (US-3, FR-008, FR-009, FR-011). *Note: FR-014 (Batch Correction) is distinct from validation.* |
| **VII. Statistical Rigor** | **PASS** | DESeq2 FDR < 0.05, |log2FC| > 1.0, **Random-Effects Meta-Analysis**, Bonferroni correction, AUC ≥ 0.75 targets documented in code and plan. |

## Project Structure

### Documentation (this feature)

```text
specs/001-chemo-biomarker-discovery/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── sample.schema.yaml
│   ├── gene_panel.schema.yaml
│   ├── meta_analysis.schema.yaml
│   ├── model.schema.yaml
│   └── ...
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── config.py            # Configuration, seeds, paths
├── data_acquisition.py  # TCGA/GEO download, streaming
├── preprocessing.py     # Harmonization, filtering, VST/ComBat (via rpy2)
├── differential_expression.py # DESeq2 Wald test wrapper
├── meta_analysis.py     # DerSimonian-Laird, panel selection
├── modeling.py          # Elastic-net, nested CV, LOO logic
├── validation.py        # External validation, calibration, DeLong's test
└── utils.py             # Logging, checksums, plotting

tests/
├── contract/            # Schema validation tests
├── integration/         # Pipeline flow tests
└── unit/                # Logic unit tests

data/
├── raw/                 # Downloaded raw files (checksummed)
├── processed/           # Normalized, harmonized matrices
└── interim/             # Intermediate results (DE stats, etc.)

results/
├── meta_analysis/       # Gene panels, p-values
├── models/              # Trained models, coefficients
└── summary.md           # Final report
```

**Structure Decision**: Single project structure (`src/`) chosen for simplicity and direct integration with Python data science stack. No frontend/backend split required.

## Complexity Tracking

> **No violations found.** The complexity is managed by strict data streaming, CPU-first methods, and modular task separation.

## FR/SC Coverage Mapping

| Requirement | Plan Phase/Step | Description |
| :--- | :--- | :--- |
| **FR-001** (TCGA Download) | Phase 1, Step 1.1 | `data_acquisition.py`: Stream TCGA RNA-seq from verified HF URLs. |
| **FR-002** (GEO Download) | Phase 1, Step 1.2 | `data_acquisition.py`: Fetch GEO metadata/expr from verified HF URLs. |
| **FR-003** (Harmonization) | Phase 2, Step 2.1 | `preprocessing.py`: Map Ensembl/Entrez to HGNC, ≥95% retention. |
| **FR-004** (Filtering/VST) | Phase 2, Step 2.2 | `preprocessing.py`: CPM < 1 filter, DESeq2 VST (TCGA) / RMA (GEO). |
| **FR-005** (DE Analysis) | Phase 3, Step 3.1 | `differential_expression.py`: DESeq2 Wald, FDR < 0.05, |log2FC| > 1.0. |
| **FR-006** (Intersection/Meta) | Phase 3, Step 3.2 | `meta_analysis.py`: Random-Effects (DerSimonian-Laird); fallback to union. |
| **FR-007** (Elastic-Net) | Phase 4, Step 4.1 | `modeling.py`: Elastic-net logistic regression, nested CV. |
| **FR-008** (LOO Validation) | Phase 4, Step 4.2 | `modeling.py`: **Nested LOO** (re-run DE+Meta on N-1 types); halt if N < 3. |
| **FR-009** (Metrics) | Phase 5, Step 5.1 | `validation.py`: ROC-AUC, PR, Calibration curves. |
| **FR-010** (Bonferroni) | Phase 5, Step 5.2 | `validation.py`: Adjust p-values (m=genes or m=comparisons). |
| **FR-011** (DeLong's Test) | Phase 5, Step 5.3 | `validation.py`: Compare model vs. clinical baseline (external GEO only). |
| **FR-012** (CPU Constraints) | Phase 0, Strategy | CPU-first design, streaming, sampling if >7GB. |
| **FR-013** (Data Split) | Phase 2, Step 2.3 | `preprocessing.py`: Split into discovery/training sets (80/20). |
| **FR-014** (Batch Correction) | Phase 2, Step 2.4 | `preprocessing.py`: ComBat/ComBat-seq with 'response' covariate. |
| **SC-001** (AUC ≥ 0.75) | Phase 5, Step 5.1 | Measured against target in `results/summary.md`. |
| **SC-002** (Significance) | Phase 5, Step 5.2 | Bonferroni-adjusted p < 0.01. |
| **SC-003** (Generalizability) | Phase 4, Step 4.2 | Performance drop (AUC diff) > 0.10 indicates failure. |
| **SC-004** (Runtime ≤ 6h) | Phase 0, Strategy | Monitored via CI logs; sampling if exceeded. |
| **SC-005** (RAM ≤ 7GB) | Phase 0, Strategy | Streaming and chunked processing. |
| **SC-006** (≥2 Tumor Types) | Phase 3, Step 3.1 | Explicit check before meta-analysis. |

## Implementation Phases

### Phase 0: Strategy & Power Analysis

**Goal**: Define constraints and verify statistical power.

-   **Step 0.1: Resource Setup**
    -   Define `config.py` with `MAX_RAM=7GB`, `MAX_RUNTIME=6h`.
    -   Set random seeds (e.g., `42`) for reproducibility.
-   **Step 0.2: CPU-First Strategy**
    -   Confirm all methods (DESeq2, Elastic-net, DerSimonian-Laird) are CPU-tractable.
    -   Plan streaming for large datasets to avoid OOM.
-   **Step 0.3: Power Analysis**
 - Calculate required sample size for detecting log2FC > 1.0 with [deferred] power at FDR 0.05.
    -   If available cohorts < required N, flag limitation in `results/summary.md`.

### Phase 1: Data Acquisition

**Goal**: Download and verify datasets (FR-001, FR-002).

-   **Step 1.1: TCGA Download**
    -   Stream TCGA RNA-seq (HTSeq-Counts) and clinical metadata for ≥3 tumor types.
    -   Verify presence of response labels (RECIST/equivalent).
-   **Step 1.2: GEO Download**
    -   Fetch GEO microarray datasets with response annotations.
    -   Verify presence of 'responder'/'non-responder' labels.
    -   Log warning if specific GSE IDs (GSE25055/GSE42752) are missing; use verified proxies.

### Phase 2: Preprocessing

**Goal**: Harmonize, normalize, and split data (FR-003, FR-004, FR-013, FR-014).

-   **Step 2.1: Gene Harmonization**
    -   Map Ensembl/Entrez to HGNC symbols.
    -   **Threshold**: Retain ≥95% of genes; log dropouts.
-   **Step 2.2: Filtering & Normalization**
    -   **TCGA**: Filter CPM < 1 in >80% samples; apply DESeq2 VST.
    -   **GEO**: Apply RMA or Quantile normalization (log2 scale).
-   **Step 2.3: Data Splitting**
    -   Split each tumor type into **Discovery Set** (for DE) and **Training Set** (for modeling).
 - **Ratio**: Majority/Minority split (e.g., [deferred] Discovery, [deferred] Training) or 70/30 depending on power.
    -   Ensure stratification by response label.
-   **Step 2.4: Batch Correction**
    -   Align GEO (microarray) with TCGA (RNA-seq) using **ComBat** (for log2) or **ComBat-seq** (for counts).
    -   **Critical**: Include `response_label` as a covariate in the batch correction model to prevent erasing the biological signal associated with response.
    -   Output to `data/processed/`.

### Phase 3: Differential Expression & Meta-Analysis

**Goal**: Identify cross-tumor biomarkers (FR-005, FR-006).

-   **Step 3.1: Tumor-Specific DE**
    -   Run DESeq2 Wald test on Discovery Set for each tumor type.
    -   **Thresholds**: FDR < 0.05, |log2FC| > 1.0.
    -   **Check**: Verify ≥2 tumor types contribute significant genes. If <2, halt or reframe.
-   **Step 3.2: Meta-Analysis (Random-Effects)**
    -   **Method**: **DerSimonian-Laird Random-Effects Model** (accounts for heterogeneity).
    -   **Input**: P-values and effect sizes from Step 3.1.
    -   **Selection**: Intersect significant genes across types. If intersection is empty, fallback to union of top 50 genes (ranked by meta p-value).
    -   **Output**: Ranked gene panel with combined p-values.

### Phase 4: Modeling & Nested Validation

**Goal**: Train and validate predictive models (FR-007, FR-008).

-   **Step 4.1: Model Training**
    -   Train Elastic-net logistic regression on Training Set using the gene panel.
    -   Use **Nested Cross-Validation**: Inner loop for alpha/lambda tuning; Outer loop for AUC estimation.
-   **Step 4.2: Nested Leave-One-Cancer-Type-Out (LOO)**
    -   **Protocol**: For each tumor type $T_i$ (the "left-out" type):
        1.  **Re-run DE** on $N-1$ types (Discovery Sets).
        2.  **Re-run Meta-Analysis** on $N-1$ types to derive a new gene panel.
        3.  **Train Model** on $N-1$ types (Training Sets) using the new panel.
        4.  **Evaluate** on $T_i$ (Validation Set).
    -   **Halt Condition**: If total tumor types < 3, halt and report error (FR-008).
    -   **Metric**: Compute **Performance Drop** = (Internal CV AUC) - (LOO AUC). If Drop > 0.10, flag as poor generalizability.

### Phase 5: Evaluation & Reporting

**Goal**: Final metrics and significance testing (FR-009, FR-010, FR-011).

-   **Step 5.1: Performance Metrics**
    -   Compute ROC-AUC, Precision-Recall, Calibration Curves.
    -   **Target**: AUC ≥ 0.75.
-   **Step 5.2: Multiple Testing Correction**
    -   Apply **Bonferroni Correction**:
        -   For Meta-Analysis significance: $m$ = number of genes in panel.
        -   For Model Comparisons: $m$ = number of comparisons.
    -   **Threshold**: Adjusted p < 0.01.
-   **Step 5.3: Baseline Comparison**
    -   Perform **DeLong's Test** comparing the gene model vs. clinical covariates-only baseline.
    -   **Constraint**: Comparison performed **only on external GEO validation sets** to ensure independence.
-   **Step 5.4: Summary Report**
    -   Generate `results/summary.md` with all metrics, limitations, and fallback reasons.

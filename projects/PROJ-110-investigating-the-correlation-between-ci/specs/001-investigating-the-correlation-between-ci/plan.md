# Implementation Plan: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Branch**: `001-circadian-metabolic-correlation` | **Date**: 2026-06-28 | **Spec**: `specs/001-investigating-the-correlation-between-ci/spec.md`
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-ci/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate the correlation between core circadian gene expression (e.g., *PER1*, *BMAL1*) and Metabolic Syndrome (MetS) risk using GTEx v8 data. The approach involves: (1) classifying donors into MetS/Control groups based strictly on ATP-III criteria using clinical phenotype data; (2) performing differential expression analysis (Wilcoxon rank-sum) with global Benjamini-Hochberg FDR correction; (3) building multivariate logistic regression models with cross-validation to predict MetS status while controlling for confounders (age, sex, PMI), **excluding** the clinical traits that define MetS to avoid tautology; and (4) generating diagnostic visualizations. The pipeline prioritizes CPU-tractable methods (scikit-learn, statsmodels, pandas) to ensure execution on GitHub Actions free-tier runners. Streaming is used for data loading, but FDR correction is applied to the collected list of summary statistics (which fits in RAM). Time of Death is used as a covariate if present; if missing, samples are excluded from circadian-specific analysis or PMI is used as a proxy, with the study reframed as "associational" for those samples.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `datasets` (Hugging Face), `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`); No external database.  
**Testing**: `pytest` (unit tests for classification logic, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free tier).  
**Project Type**: Data analysis pipeline / research script.  
**Performance Goals**: Complete analysis within 6 hours on 2 vCPU, ~7GB RAM. Memory usage < 6GB via streaming/chunked processing.  
**Constraints**: CPU-only execution; no GPU acceleration; strict adherence to ATP-III thresholds; exclusion of samples with missing clinical variables; global FDR correction mandatory.  
**Scale/Scope**: GTEx dataset (a large-scale collection of samples, but significantly reduced by clinical variable completeness); A core set of circadian genes; ~ clinical traits.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility (NON-NEGOTIABLE)** | ✅ PASS | Plan mandates pinned `requirements.txt`, random seeds, and direct download from canonical open sources. |
| **II. Verified Accuracy** | ✅ PASS | All dataset citations restricted to verified open sources. No fabricated URLs. |
| **III. Data Hygiene** | ✅ PASS | Plan requires checksums for raw data, immutable raw files, and new filenames for derivations. PII scan compliance noted. |
| **IV. Single Source of Truth** | ✅ PASS | All statistics will be derived from `data/processed` artifacts; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | ✅ PASS | Content hashes tracked in `state/` YAML; artifact updates trigger state updates. |
| **VI. Clinical Criteria and Gene Panel Integrity** | ✅ PASS | MetS classification strictly follows ATP-III (BMI≥30, Glu≥100, etc.) as defined in FR-002. Gene panel fixed (PER-3, CRY1-2, BMAL1, CLOCK, NR1D1, RORα) per Principle VI. |
| **VII. Statistical Correction and Validation** | ✅ PASS | Benjamini-Hochberg FDR mandated for DE and correlation (global); k-fold CV for logistic regression. |

## Project Structure

### Documentation (this feature)

```text
specs/001-circadian-metabolic-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── classification.schema.yaml
│   ├── model.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-110-investigating-the-correlation-between-ci/
├── data/
│   ├── raw/                 # Downloaded GTEx parquet/TSV (immutable)
│   ├── processed/           # Classifications, cleaned matrices, model outputs
│   └── interim/             # Temporary intermediate files (e.g., filtered samples)
├── code/
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, thresholds
│   ├── data_loader.py       # GTEx download, streaming, cleaning
│   ├── classifier.py        # ATP-III logic, baseline_labels generation
│   ├── analysis.py          # Wilcoxon, FDR, Logistic Regression
│   ├── viz.py               # Heatmaps, ROC, scatter plots
│   └── main.py              # Pipeline orchestration
├── tests/
│   ├── unit/
│   │   ├── test_classifier.py
│   │   └── test_data_loader.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── methodology.md
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected to match the "research pipeline" nature. `data/` is split into `raw` (immutable), `processed` (derived), and `interim` (scratch) to satisfy Data Hygiene (Principle III). `code/` is modularized by function (load, classify, analyze, viz) to support unit testing and reproducibility.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Phase Breakdown

### Phase 0: Research & Data Strategy
- **Goal**: Confirm data availability, verify variable presence, and define the statistical approach.
- **Actions**:
  - Inspect GTEx v8 schema via Hugging Face `load_dataset` (streaming) to confirm presence of `bmi`, `fasting_glucose`, `triglycerides`, `hdl`, `systolic_bp`, `diastolic_bp`, `pmi`, `time_of_death`.
  - Validate that the dataset does not require authentication or credentials (open access).
  - Confirm the list of core circadian genes exists in the expression matrix. **This list is fixed per Constitution Principle VI (PER1-3, CRY1-2, BMAL1/ARNTL, CLOCK, NR1D1, RORα).**
  - Define the "Verified datasets" strategy for the `research.md`.
  - **Fallback Strategy**: If `time_of_death` is missing, the plan will exclude those samples from circadian-specific analysis or use `pmi` as a proxy, reframing the study as "associational" for those samples. It will NOT halt the entire pipeline.
- **FR/SC Mapping**: FR-001 (Data download), SC-001 (Classification proportion), SC-002 (Gene count).

### Phase 1: Data Model & Contracts
- **Goal**: Define schemas for input data, intermediate classifications, and model outputs.
- **Actions**:
  - Create `contracts/dataset.schema.yaml` defining the expected columns and types for GTEx input.
  - Create `contracts/classification.schema.yaml` defining the structure of the classification CSV.
  - Create `contracts/model.schema.yaml` defining the logistic regression results.
  - Create `contracts/output.schema.yaml` defining the final aggregated results.
  - Define the `data-model.md` with entity relationships (Donor -> GeneExpression -> MetabolicStatus).
- **FR/SC Mapping**: FR-001 (Data parsing), FR-002 (Classification), SC-005 (Sensitivity).

### Phase 2: Implementation (Code Generation)
- **Goal**: Generate the Python scripts for the pipeline.
- **Actions**:
  - Implement `classifier.py`: Strict ATP-III logic, handling of missing data (exclusion), logging.
  - Implement `analysis.py`: 
    - Wilcoxon test (stratified by tissue), **global** Benjamini-Hochberg FDR correction across all gene-tissue tests.
    - Logistic Regression: Predict `MetS` (binary) using `gene_expression` + `age` + `sex` + `tissue` + `pmi` + `time_of_death` (if present). **DO NOT include BMI, glucose, etc. as predictors for the binary outcome to avoid tautology.**
    - Separate model: Predict `Severity_Score` (continuous) using `gene_expression` + covariates.
    - 5-fold Cross-Validation.
    - VIF check for collinearity.
  - Implement `viz.py`: Heatmaps, ROC curves.
  - Implement `main.py`: Orchestration, seed setting, error handling.
- **FR/SC Mapping**: FR-003 (Wilcoxon), FR-004 (FDR), FR-005 (LogReg), FR-006 (CV), FR-007 (Correlation), FR-008 (Plots), FR-009 (Odds Ratios).

### Phase 3: Testing & Validation
- **Goal**: Verify pipeline correctness and reproducibility.
- **Actions**:
  - Run unit tests on classification logic (edge cases: BMI=29.9, missing values).
  - Run integration test on a small subset of data to ensure full pipeline execution.
  - Verify that `data/processed/baseline_labels.csv` is generated correctly.
- **FR/SC Mapping**: SC-003 (AUC), SC-004 (Correlation magnitude), SC-005 (Sensitivity).

### Phase 4: Execution & Reporting
- **Goal**: Run full pipeline on CI and generate final reports.
- **Actions**:
  - Execute `main.py` on GitHub Actions.
  - Generate `paper/` artifacts (figures, tables) from `data/processed`.
  - Update `state/` with artifact hashes.
- **FR/SC Mapping**: All SCs.

## Compute Feasibility Strategy

- **CPU-First**: All statistical methods (Wilcoxon, Logistic Regression, Correlation) are classical and run efficiently on CPU.
- **Memory Management**: Use `datasets.load_dataset(..., streaming=True)` to avoid loading the full GTEx matrix into RAM. 
- **FDR Implementation**: P-values are collected in a temporary list as they are generated per tissue/gene chunk. Since the total number of tests is small (~15 genes * ~50 tissues < 1000 tests), the full list of p-values fits easily in RAM. FDR is applied to this collected list, not the raw data stream.
- **Disk Usage**: Raw data is streamed; processed data is written to disk. The memory limit is respected by not storing full intermediate matrices if not needed.
- **No GPU Required**: The spec explicitly assumes CPU-only. No transformers or deep learning models are used, eliminating the need for the GPU escape hatch.
- **No Synthetic Data**: All results must be derived from real, downloaded data. If the real data is insufficient, the study is labeled "exploratory" or halted.

## Data Availability Strategy

- **Primary Source**: GTEx v8 via Hugging Face `datasets` library (e.g., `genomicsGTEx/gtex_v8` or the official GTEx Portal if an open mirror is verified).
- **Verification**: The plan relies *only* on the URLs provided in the "Verified datasets" block of the research.md.
  - *Note*: The implementation will attempt to load these. If the specific columns required for ATP-III are missing, the system will log a critical error and **halt**, as no open substitute with these specific clinical variables is currently verified. The plan does *not* fabricate data or use test files.
  - *Fallback*: If the specific GTEx test files lack the required clinical variables, the plan explicitly states that the study cannot proceed with *these* specific URLs and must wait for a verified source with the full phenotype data. The plan does *not* substitute a different dataset or synthesize data.
- **Streaming**: The code will use `streaming=True` to handle large files, ensuring the 7GB RAM limit is not exceeded.
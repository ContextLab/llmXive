# Implementation Plan: Predict Plant Disease Resistance from Multi‑omics Data

**Branch**: `001-predict-plant-disease-resistance` | **Date**: 2026-06-25 | **Spec**: `specs/001-predict-plant-disease-resistance/spec.md`

## Summary

This plan implements a reproducible, CPU-tractable pipeline to predict plant disease resistance using paired genomic (SNP) and metabolomic data. **Crucially, due to the confirmed absence of public, matched multi-omics plant datasets (see Research.md), the pipeline executes in "Simulation Mode" by default.** In this mode, the system generates synthetic data with known signal structures to validate the *pipeline logic* (preprocessing, feature selection, modeling, and statistical testing). 

The system attempts to retrieve public data (if available), preprocesses it (variant calling, normalization), performs rigorous feature selection (LASSO/RF with sensitivity sweeps), trains Elastic-Net/Gradient-Boosting models with 5-fold cross-validation, and validates via permutation testing. The pipeline strictly adheres to the GitHub Actions free-tier constraints (2 CPU, 7 GB RAM, 6h runtime) and enforces data integrity checks (minimum 100 paired samples). 

**Scope Note**: The "Accuracy ≥ 75%" and "p < 0.05" success criteria in this phase apply to **Pipeline Validation** (i.e., the code correctly identifies the injected signals in synthetic data). They do not constitute scientific validation of the biological hypothesis, which remains blocked until a real matched dataset is discovered.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `bcftools` (via Docker), `fastp` (via Docker), `pyyaml`, `requests`  
**Storage**: Local filesystem (`data/`, `code/`, `artifacts/`)  
**Testing**: `pytest` (unit/contract), `shellcheck` (bash scripts)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Biology Pipeline / CLI  
**Performance Goals**: Runtime ≤ 6h, Peak RAM ≤ 7 GB.  
**Constraints**: CPU-only (no GPU), no large-LLM inference, strict data modality matching, sample size ≥ 100.  
**Scale/Scope**: Multi-omics integration (SNP + Metabolite). **Note**: Since no real dataset exists, the pipeline **defaults to generating a synthetic dataset** with ~150 samples to demonstrate functionality. Real data fetch is an optional attempt that triggers immediate fallback if no matched data is found.

> **Dataset Fit Critical Note**: The "Verified datasets" block provided in the input contains financial, transport, and generic SNP datasets (e.g., `33param_snp500`) that **do not** contain the required paired plant genomic, metabolomic, and resistance phenotype data. The plan below addresses this by defining a **Data Acquisition Strategy** that relies on the `data_manifest.yaml` to fetch from NCBI SRA/MetaboLights (per Constitution Principle VI) or to **generate a synthetic dataset** for the *implementation* of the pipeline logic. The code MUST be robust to "Data Not Found" errors and MUST immediately switch to "Simulation Mode" if real data is missing, as per FR-007/FR-008.

## Constitution Check

*Gates determined based on `projects/PROJ-259.../memory/constitution.md`*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` pins versions; random seeds set in `code/`; Docker container ensures environment consistency. |
| **II. Verified Accuracy** | **Pass (Process Only)** | The plan explicitly verifies that **no** real source exists. The project runs in "Simulation Mode". Accuracy metrics are for **Pipeline Logic Validation** only, not biological claims. The pipeline validates its *logic* against a synthetic ground truth. |
| **III. Data Hygiene** | **Pass** | `data_manifest.yaml` records checksums; raw data preserved in `data/raw/`; derivatives in `data/processed/`. Synthetic data is treated as a raw artifact with its own hash. |
| **IV. Single Source of Truth** | **Pass** | Metrics in `paper/` will be generated programmatically from `artifacts/` JSON/CSV; no manual typing. |
| **V. Versioning Discipline** | **Pass** | Content hashes tracked in `state/`; `updated_at` timestamps updated on artifact changes. |
| **VI. Multi‑omics Provenance** | **Pass** | Data acquisition scripts will record NCBI SRA/MetaboLights accession numbers. If the synthetic fallback is triggered, these fields in `data_manifest.yaml` will be populated with `SIMULATED` and `N/A` to maintain provenance integrity. |
| **VII. Statistical Validation** | **Pass** | Plan mandates BH correction, permutation testing (n=1000), and 95% CIs for all metrics as per FR-005/SC-003. In simulation mode, these validate the *pipeline's ability to detect injected signals*. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-disease-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schema Definitions)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration loading
├── main.py              # Entry point (CLI)
├── data/
│   ├── download.py      # Fetch from NCBI/MetaboLights (or simulate if missing)
│   ├── preprocess.py    # fastp/bcftools wrappers, normalization
│   ├── split.py         # Stratified splitting logic (FR-009)
│   ├── manifest.py      # Manifest handling
│   └── generate_synthetic.py # Synthetic data generator
├── analysis/
│   ├── feature_selection.py # LASSO/RF, sensitivity sweep
│   ├── modeling.py      # Elastic-Net/GBM training, CV
│   └── validation.py    # Permutation testing, VIF
├── utils/
│   ├── logging.py
│   ├── stats.py         # BH correction, VIF calculation
│   └── exceptions.py    # Custom exception classes (FR-007, FR-008)
└── tests/
    ├── test_data.py
    ├── test_analysis.py
    └── test_validation.py

data/
├── raw/                 # Downloaded raw files (gitignored) or Synthetic Data
├── processed/           # Aligned matrices
└── data_manifest.yaml   # Provenance record

artifacts/
├── models/              # Serialized models
├── reports/             # CSVs, JSON metrics
└── figures/             # Plots (if generated)

Dockerfile
requirements.txt
```

**Structure Decision**: A modular Python package structure (`code/`) is selected to support the complex multi-step pipeline (download -> preprocess -> model -> validate). This allows for isolated testing of each stage and easy integration into the Docker container.

## Implementation Phases

### Phase 1: Data Acquisition & Integrity Checks (FR-001, FR-007, FR-008)

**Goal**: Retrieve or generate data, validate modalities, and enforce sample size constraints.

1.  **Data Fetch**:
    *   Attempt to download raw FASTQ and MS spectra from NCBI SRA/MetaboLights using `data/download.py`.
    *   **Fallback**: If no data is found (expected), trigger `code/data/generate_synthetic.py` to create a dataset with known signal properties (SNPs, Metabolites, Phenotype).
    *   Record all accession numbers (or `SIMULATED`) in `data/data_manifest.yaml`.
2.  **Preprocessing**:
    *   Run `fastp` and `bcftools` (via Docker) on raw reads to generate a SNP matrix.
    *   Normalize metabolomics data using MetaboAnalyst-compatible methods.
    *   Align samples across modalities.
3.  **Integrity & Power Checks**:
    *   **FR-007**: If `n_samples < 100` after alignment, raise `EX_DATA_INTEGRITY (02)` with message: "Insufficient data modalities: Remaining samples < 100".
    *   **FR-008**: If `n_samples < 100`, raise `EX_POWER_INSUFFICIENT (03)` with message: "Power deficiency: n < 100 required for multivariate omics analysis with BH correction".
    *   **Exit Codes**: Implement these in `code/utils/exceptions.py`.

### Phase 2: Data Splitting (FR-009)

**Goal**: Split data into training and independent hold-out sets.

1.  **Stratified Split**:
    *   Implement `code/data/split.py` to perform stratified sampling based on the resistance phenotype.
    *   **FR-009**: Split data into Training Set (majority proportion) and Independent Hold-Out Test Set (remaining proportion).
    *   **Strict Reservation**: The hold-out set MUST be strictly reserved for final evaluation and permutation testing. No feature selection or model training shall use this set.

### Phase 3: Feature Selection (FR-003)

**Goal**: Identify top predictive features with sensitivity analysis.

1.  **Feature Selection**:
    *   Apply LASSO regression or Random Forest importance on the **Training Set**.
    *   **FR-003**: Select a subset of SNPs and metabolites for analysis.
2.  **Sensitivity Sweep**:
    *   Run selection over thresholds `{0.01, 0.05, 0.1}`.
    *   Calculate selection frequency for each feature across the three thresholds.
3.  **Artifact Generation**:
    *   **FR-003**: Output `selection_frequency.csv` listing feature IDs, thresholds, and selection frequency.

### Phase 4: Model Training (FR-004)

**Goal**: Train predictive models with cross-validation.

1.  **Model Selection**:
    *   Train Elastic-Net (continuous) or Gradient-Boosting (categorical) on the **Training Set**.
2.  **Cross-Validation**:
    *   Perform k-fold cross-validation.
    *   Report CV accuracy (or AUC-ROC / R²).
    *   Compare against a null model baseline (random labels).

### Phase 5: Validation & Diagnostics (FR-005, SC-003)

**Goal**: Validate model significance and check for collinearity.

1.  **Hold-Out Evaluation**:
    *   Evaluate the trained model on the **Independent Hold-Out Test Set**.
    *   Report final performance metrics.
2.  **Permutation Testing**:
    *   **FR-005**: Perform permutation testing (n=1000) on the hold-out set.
    *   Output model-level p-value.
    *   **Note**: In Simulation Mode, a significant p-value confirms the pipeline correctly detected the injected signal. In Sparse Real Data (n < 100), this step is skipped due to the hard halt in Phase 1.
3.  **Collinearity Diagnostics**:
    *   Calculate Variance Inflation Factor (VIF) for all selected features.
    *   Flag any VIF > 5.

### Phase 6: Reporting (SC-001, SC-002, SC-004)

**Goal**: Generate final reports and verify success criteria.

1.  **Metrics**:
    *   Generate `artifacts/reports/metrics.json` with CV accuracy, permutation p-value, VIF diagnostics.
2.  **Biomarkers**:
    *   Generate `artifacts/reports/top_features.csv`.
3.  **Validation**:
    *   Verify runtime ≤ 6h and RAM ≤ 7 GB.
    *   Verify `cv_accuracy` ≥ 0.75 (in Simulation Mode, this validates the generator's signal strength and pipeline logic).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Docker Container** | Required to bundle `fastp` and `bcftools` (C++ tools) with Python libraries for reproducible execution on CI. | Pure Python alternatives for variant calling are either non-existent or significantly less accurate/standardized for genomic data. |
| **Sensitivity Sweep** | FR-003 requires testing thresholds {0.01, 0.05, 0.1} to assess robustness. | Single-threshold selection is insufficient for the required scientific rigor and may miss stable biomarkers. |
| **Permutation Testing** | FR-005 requires model-level p-values to rule out chance. | Standard cross-validation alone does not provide a significance test against a null hypothesis of random labels. |
| **Synthetic Data Generator** | No real matched dataset exists. Required to validate pipeline logic without inventing URLs. | Running on empty or incomplete data would fail FR-001/FR-007 immediately, preventing any software validation. |
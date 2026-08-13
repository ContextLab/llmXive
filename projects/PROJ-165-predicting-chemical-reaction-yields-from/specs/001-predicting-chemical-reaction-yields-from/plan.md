# Implementation Plan: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Branch**: `001-predict-reaction-yields-from-spectra` | **Date**: 2026-07-14 | **Spec**: `specs/001-predicting-chemical-reaction-yields-from-spectra/spec.md`
**Input**: Feature specification from `specs/001-predicting-chemical-reaction-yields-from-spectra/spec.md`

## Summary
This project implements a multi-head self-attention neural network to predict chemical reaction yields using concatenated inputs: resampled spectroscopic data (IR/NMR/Raman), ECFP4 structural fingerprints, and reaction condition vectors. The plan strictly adheres to the constraint of running on a CPU-only GitHub Actions runner (≤6h, ~7GB RAM). 

**Critical Feasibility Note**: Verified open datasets (ZINC, SMILES Transformers) do not contain paired reaction yields and spectroscopic data. Consequently, the "Real Data Path" yields zero valid samples. The project defaults to the **Simulated Data Path** as the primary execution mode. The simulation logic is explicitly designed to include stochastic noise and environment-dependent shifts (solvent effects) that are NOT captured by static ECFP4 fingerprints, ensuring the "independent predictive signal" hypothesis remains testable. All data is generated at runtime; no hardcoded values are used.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `scikit-learn`, `pandas`, `pyarrow`, `rdkit`, `datasets` (HuggingFace), `numpy`, `matplotlib`, `pyyaml`, `ruff`, `black`.  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/artifacts`); Parquet/CSV formats for intermediate data.  
**Testing**: `pytest` with `pytest-cov`.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Complete end-to-end training and evaluation within 6 hours on 2 CPU cores; memory usage < 7GB.  
**Constraints**: NO local GPU; NO access to gated datasets; NO hardcoded results.  
**Scale/Scope**: Generate a synthetic dataset (a sufficiently large number of reactions) using a physics-based simulator with stochastic noise to fit within RAM limits while maintaining statistical validity.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file (FR-030)*

1.  **Principle I (Reproducibility)**:
    *   **Action**: All random seeds will be pinned in `src/utils/seeds.py`.
    *   **Action**: The simulated dataset generation logic will be deterministic given the seed, ensuring reproducibility.
    *   **Action**: A `requirements.txt` will be generated at `code/` (or `src/` per structure) to ensure isolated virtualenvs.
    *   **Status**: **COMPLIANT** (Plan explicitly mandates these steps).

2.  **Principle II (Verified Accuracy)**:
    *   **Action**: Citations in `research.md` will reference ONLY the URLs provided in the `# Verified datasets` block or the public documentation for the NIST Chemistry WebBook (static tables).
    *   **Action**: NIST reference values will be retrieved via a static, code-generated lookup table (`src/data/nist_references.py`) populated from verified public tables, not dynamic scraping. The Reference-Validator will verify the source of the table.
    *   **Status**: **COMPLIANT**.

3.  **Principle III (Data Hygiene)**:
    *   **Action**: Generated synthetic data will be checksummed (SHA256) upon generation and logged in `state/...yaml`.
    *   **Action**: No data modification in place; all preprocessing (resampling, normalization) writes to new files in `data/processed/`.
    *   **Status**: **COMPLIANT**.

4.  **Principle IV (Single Source of Truth)**:
    *   **Action**: All figures (attention heatmaps) and statistics (RMSE, R²) in the final report will be generated directly from the `data/` artifacts and `code/` execution (including the NIST lookup logic), never hand-typed.
    *   **Status**: **COMPLIANT**.

5.  **Principle V (Versioning Discipline)**:
    *   **Action**: The plan includes a step to update `state/...yaml` with artifact hashes after data generation and model training.
    *   **Status**: **COMPLIANT**.

6.  **Principle VI (Spectral Preprocessing and Grid Alignment)**:
    *   **Action**: `src/data/preprocessing.py` will implement resampling to 400–4000 cm⁻¹ (IR/Raman) and 0–10 ppm (NMR) with unit variance normalization.
    *   **Status**: **COMPLIANT**.

7.  **Principle VII (Structural Baseline and Attention Interpretability)**:
    *   **Action**: Baselines (fingerprint-only, spectrum-only, condition-only) will be trained and compared against the attention model.
    *   **Action**: Attention heatmaps will be generated and validated against the *simulation injection parameters* (for simulated data) or NIST literature (for real data, if ever obtained).
    *   **Status**: **COMPLIANT**.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-reaction-yields-from-spectra/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── reaction_sample.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── cli/
│   └── main.py              # Entry point for pipeline execution
├── data/
│   ├── ingestion.py         # Generates synthetic data, checksums, logs
│   ├── preprocessing.py     # Resampling, normalization, template splitting
│   ├── loaders.py           # PyTorch Dataset classes
│   ├── nist_references.py   # Static lookup table for functional group frequencies
│   └── utils.py             # Helper functions (MD5 hashing, etc.)
├── models/
│   ├── attention_net.py     # Multi-head attention architecture
│   └── baselines.py         # Fingerprint-only, Spectrum-only, Condition-only
├── utils/
│   ├── seeds.py             # Global seed management
│   └── validators.py        # Schema validation, leakage checks
├── metrics/
│   └── evaluation.py        # RMSE, MAE, R², t-tests, permutation tests, VIF
└── viz/
    └── attention_plot.py    # Heatmap generation

tests/
├── contract/
│   └── test_schemas.py      # Validates data against YAML contracts
├── integration/
│   └── test_pipeline.py     # End-to-end generation -> train -> eval
└── unit/
    ├── test_preprocessing.py
    └── test_models.py

data/
├── raw/                     # Generated synthetic data (checksummed)
├── processed/               # Resampled, normalized, split data
└── artifacts/               # Logs, leakage reports, model checkpoints

state/
└── projects/PROJ-165-.../artifact_hashes.yaml  # Checksums for versioning
```

**Structure Decision**: Single-project structure (`src/`) is selected to minimize overhead on the CI runner. The separation of `data/`, `models/`, and `utils/` ensures modularity for testing and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multi-head Attention vs Simple MLP | Required by Spec (FR-003) to capture non-local spectral dependencies and provide interpretability via attention weights. | A simple MLP would fail the "Interpretability" success criteria (SC-003) and cannot isolate specific spectral regions. |
| Template-based Splitting | Required by Spec (FR-002) to prevent data leakage between train/test sets based on reaction chemistry. | Random splitting would allow the same reaction template in both sets, inflating performance metrics and violating scientific validity. |
| Streaming Data Loading | Required to fit large datasets (or large synthetic sets) into 7GB RAM. | Loading the full dataset into memory would cause OOM crashes on the GitHub Actions runner. |
| Simulated Data Path | Real open datasets lack paired yield/spectrum data. | Using real data is infeasible; simulation with stochastic noise is the only valid path to test the hypothesis. |

## FR/SC Coverage Map

| ID | Description | Plan Element |
| :--- | :--- | :--- |
| FR-001 | Preprocess spectra (resample, normalize, encode conditions) | `src/data/preprocessing.py` (Resampling, Normalization, Encoding) |
| FR-002 | Split by template (zero overlap) | `src/data/preprocessing.py` (Template extraction, MD5 hashing, Stratified Split) |
| FR-003 | Multi-head self-attention network | `src/models/attention_net.py` |
| FR-004 | Train with Adam, lr=1e-3, batch=32, max 10 epochs, early stopping | `src/cli/main.py` (Training loop configuration) |
| FR-005 | Compute RMSE, MAE, R² for attention and baselines | `src/metrics/evaluation.py` |
| FR-006 | Paired t-test on absolute errors | `src/metrics/evaluation.py` (t-test + Bonferroni) |
| FR-007 | Generate attention weight visualizations | `src/viz/attention_plot.py` |
| FR-008 | Permutation test (shuffled labels) | `src/metrics/evaluation.py` |
| FR-009 | Sensitivity analysis over 3 thresholds | `src/metrics/evaluation.py` (Thresholds: Top 1%, 5%, 10%) |
| FR-010 | Validate against independent data (or Simulated Report) | `src/data/ingestion.py` (Simulated Validation Report generation) |
| FR-010a | Generate evaluation report artifact | `src/cli/main.py` (Report generation) |
| FR-011 | Encode reaction conditions as features | `src/data/preprocessing.py` (Condition encoding) |
| FR-012 | Retrieve NIST functional group frequencies | `src/data/nist_references.py` (Static lookup table from public docs) |
| FR-013 | Correlation between attention weights and residuals | `src/metrics/evaluation.py` |
| FR-014 | MD5 hashing for template overlap check | `src/data/utils.py` |
| FR-015 | Simulated Data Integrity Check (collinearity) | `src/data/ingestion.py` (Integrity check step) |
| FR-016 | Compute VIF for all models | `src/metrics/evaluation.py` (Standard step) |

## Compute Feasibility

- **CPU-First**: The model is designed to be small (few layers, low hidden dimension) to fit within 2 CPU cores and 7GB RAM.
- **No GPU**: The plan does not rely on GPU acceleration.
- **Streaming**: Data is generated and streamed to avoid memory spikes.
- **Time Limit**: The pipeline is designed to complete in < 4 hours to allow for CI overhead.
- **Simulation**: The synthetic data generator is optimized to run quickly on CPU.

## Statistical Rigor

- **Multiple Comparisons**: Bonferroni correction applied to t-tests.
- **Non-Parametric Tests**: Wilcoxon signed-rank test and bootstrap confidence intervals included as robust alternatives for heteroscedastic data.
- **Power Analysis**: Acknowledges limited statistical power due to synthetic nature; results reported with confidence intervals.
- **Causal Claims**: No causal claims. Claims are strictly associational.
- **Collinearity**: VIF computed for all models; if VIF > 5, collinearity is reported and independent effects are not claimed.
- **Simulation Design**: Stochastic noise and solvent effects ensure spectra are not deterministic functions of fingerprints.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Simulated Data Path** | Real open datasets (ZINC, SMILES) lack paired yield/spectrum data. Simulation with stochastic noise is the only valid path. |
| **Template-based Splitting** | Essential to prevent data leakage and ensure generalization to new reaction types (FR-002). |
| **Attention Mechanism** | Required to provide interpretability (SC-003) and identify spectral regions. |
| **Static NIST Lookup** | Satisfies FR-012 and Constitution Principle II without dynamic scraping; ensures reproducibility. |
| **Stratified Splitting** | Prevents confounding by reaction conditions (solvent/catalyst) in addition to template leakage. |
| **Sensitivity Analysis** | Required by FR-009 to ensure robustness of identified spectral regions. |
| **VIF Computation** | Required by FR-016 for all models to detect lack of independent variance. |
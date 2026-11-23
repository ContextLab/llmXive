# Implementation Plan: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

**Branch**: `001-assess-uncertainty-quantification` | **Date**: 2026-06-22 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-assess-uncertainty-quantification/spec.md`

## Summary

This project implements a comparative analysis of three lightweight Uncertainty Quantification (UQ) techniques—Deep Ensembles, Monte-Carlo Dropout, and Sparse Gaussian Processes—applied to a baseline feed-forward neural network predicting material properties (formation energy, bulk modulus, band gap) from the OQMD dataset. The plan adheres to a strict 5-hour runtime budget on a 2-core CPU GitHub Actions runner, prioritizing CPU-tractable methods (small models, PCA-reduced features) while ensuring rigorous calibration metrics (ECE, Interval Score) and downstream screening utility are measured against real, open-access data.

**Critical Update on Data & Models**: 
1. Structural descriptors (atomic radius, packing fraction) are **not** present in the raw OQMD dataset and will be computed from crystal structures using `pymatgen`.
2. The baseline NN uses a **heteroscedastic loss** to output both mean and variance, enabling proper aleatoric/epistemic separation.
3. ECE and all metrics are computed dynamically from real predictions; no placeholders are used.
4. **Data Splitting**: Splitting is performed by **Material-ID** to prevent leakage from duplicate entries.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `torch` (CPU), `gpytorch` (CPU), `scikit-learn`, `pandas`, `numpy`, `datasets` (Hugging Face), `matplotlib`, `pymatgen`  
**Storage**: Local filesystem (`data/`, `results/`), Hugging Face Hub (dataset download)  
**Testing**: `pytest` (contract tests on schemas, unit tests on metrics)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Total pipeline runtime ≤ 5 hours; Deep Ensemble training ≤ 30 mins; UQ evaluation ≤ 20 mins/property.  
**Constraints**: CPU-first execution; strict memory limit (~7 GB); no fabricated results.  
**Scale/Scope**: Dataset subset ~k compounds (streamed/sampled to fit RAM); Model parameters ≤ 10k.

> **Note on Compute Feasibility**: All selected methods (FFNN with ≤10k params, Sparse GP with PCA) are designed to run on the CPU runner. No GPU-specific methods (e.g., full BNNs, large transformers) are included. If the Sparse GP fails to converge on CPU due to scale, the plan falls back to a Standard GP on a smaller subset (N=2000) or logs a warning, ensuring the pipeline completes within the time budget.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | Plan mandates `seed=42` (and 43, 44 for robustness), pinned `requirements.txt`, and deterministic data splits (Material-ID Stratified). All datasets fetched from verified HF URLs. |
| **II. Verified Accuracy** | ✅ PASS | Citations limited to the "Verified datasets" block and the specific arXiv paper for MC Dropout passes. No invented URLs. |
| **III. Data Hygiene** | ✅ PASS | Plan includes `validation_report.json` for missing data, checksumming of downloaded artifacts, and immutable raw data storage. |
| **IV. Single Source of Truth** | ✅ PASS | All metrics (ECE, Sharpness) derived programmatically from `results/` CSVs. No hand-typed numbers in plan. |
| **V. Versioning Discipline** | ✅ PASS | `main.py` includes a `hash_artifacts()` step that computes SHA256 hashes of all outputs and updates `state/...yaml` timestamps. |
| **VI. Lightweight UQ Execution** | ✅ PASS | Model architecture constrained to ≤10k params; PCA applied to reduce GP dimensionality; runtime budget enforced via `timeout` logic. |
| **VII. Calibration-Driven Evaluation** | ✅ PASS | Plan explicitly requires ECE, Interval Score, and Sharpness for [deferred]/90% intervals as the primary success metric. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-uncertainty-quantification/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (schemas)
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download.py          # Downloads OQMD subset, handles retries
│   ├── preprocess.py        # Cleans, splits (Material-ID Stratified), computes descriptors, PCA, exports CSVs
│   └── validation.py        # Generates validation_report.json
├── models/
│   ├── baseline_nn.py       # 2-layer NN with heteroscedastic output, parameter counter, trainer
│   ├── deep_ensemble.py     # Ensemble training & inference
│   ├── mc_dropout.py        # MC-Dropout model & inference loop
│   └── sparse_gp.py         # Sparse GP with PCA integration
├── eval/
│   ├── metrics.py           # ECE (binned by total uncertainty), Interval Score, Sharpness calculators
│   └── screening.py         # Downstream screening logic (Bootstrap Permutation Test)
├── utils/
│   ├── config.py            # Load config.yaml (seeds, paths)
│   └── logging.py           # Structured logging
├── main.py                  # Orchestration script (timeout enforced, versioning/hashing)
└── requirements.txt         # Pinned dependencies

data/
├── raw/                     # Downloaded parquet/CSV (checksummed)
└── processed/               # Train/Val/Test CSVs, PCA transformer, validation_report.json

results/
├── models/                  # Saved checkpoints (.pt)
│   ├── baseline_nn_arch.pt
│   ├── ensemble/
│   ├── mc_dropout/
│   └── sparse_gp_model.pt
├── predictions/             # UQ output CSVs
│   ├── uq_predictions_ensemble.csv
│   ├── uq_predictions_mc_dropout.csv
│   └── uq_predictions_sparse_gp.csv
└── metrics/                 # Final evaluation JSONs/CSVs
    └── calibration_summary.csv
```

**Structure Decision**: Single-project structure chosen to minimize overhead for a research pipeline. `code/` contains modular scripts for data, models, and eval to allow independent testing and re-running of specific phases (e.g., re-run eval without re-training).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Three UQ Methods** | Required by Spec (FR-003, FR-004, FR-005) to compare aleatoric/epistemic separation and calibration. | A single method would fail to answer the comparative research question (US-2). |
| **Sparse GP + PCA** | Full GP is O(N^3) and infeasible for N>10k on 7GB RAM. Sparse GP with PCA reduces dimensionality and complexity to O(M^2 N) where M << N. | Standard GP would exceed memory/time budget; Deep Ensemble alone would miss the GP baseline comparison. |
| **Material-ID Stratified Split** | Ensures no data leakage if multiple entries exist per material ID. | Random/Quantile split could lead to training on a sample and testing on its duplicate, invalidating ECE. |
| **Heteroscedastic Loss** | Required to output variance for aleatoric uncertainty estimation (FR-008). | Standard MSE loss only outputs mean, making aleatoric separation impossible. |

## Methodology & Implementation Steps

### Phase 1: Data Ingestion & Preprocessing
1.  **Download**: Fetch OQMD subset from verified HF URL. Retry on failure.
2.  **Validate**: Check for nulls in targets. Log to `validation_report.json`.
3.  **Feature Engineering**: Parse CIF structures using `pymatgen` to compute `atomic_radius` and `packing_fraction`. Exclude rows where CIF is missing.
4.  **Split**: Perform **Material-ID Stratified Split** (80/10/10) based on `formation_energy` quantiles. Ensure no material ID appears in multiple splits.
5.  **Transform**: Fit PCA on Training set (retain >90% variance). Save `pca_transformer.pkl`. Apply to Train/Val/Test.

### Phase 2: Model Training
1.  **Baseline NN**: Train 2-layer FFNN with **heteroscedastic loss** (outputs mean + log_var). Verify parameter count ≤ 10,000. Save `baseline_nn_arch.pt`.
2.  **Deep Ensemble**: Train multiple independent models (seeds 42-46). Save to `results/models/ensemble/`.
3.  **MC-Dropout**: Train 1 model with dropout (p=0.2). Save to `results/models/mc_dropout/`.
4.  **Sparse GP**: Fit Sparse GP on PCA-reduced training data with a set of inducing points. If CPU timeout risk, fallback to N=2000 subset. Save `sparse_gp_model.pt`.

### Phase 3: Inference & Prediction
1.  **Ensemble Inference**: Generate 5 predictions per sample. Compute mean, variance, and decompose into Aleatoric/Epistemic.
2.  **MC-Dropout Inference**: Run multiple stochastic forward passes (per verified fact 2007.03293) to estimate variance. Decompose uncertainty.
3.  **GP Inference**: Generate predictions with variance. Calculate `reconstruction_variance` (FR-005).
4.  **Output**: Save predictions to `results/predictions/uq_predictions_*.csv` using `prediction_output.schema.yaml`.

### Phase 4: Evaluation & Robustness
1. **Calibration Metrics**: Compute ECE (binned by predicted uncertainty), Interval Score, and Sharpness for [deferred] and [deferred] intervals.
2.  **Robustness Check**: Train models on multiple random seeds. Calculate Coefficient of Variation (CV) of ECE scores. Flag if CV > 0.1 (SC-004).
3.  **Screening**: Perform Bootstrap Permutation Test (sufficient iterations) to compare UQ-filtered precision vs. random baseline.

### Phase 5: Versioning & Reporting
1.  **Hashing**: `main.py` computes SHA256 hashes of all artifacts in `results/`.
2.  **State Update**: Update `state/projects/PROJ-764...yaml` with `updated_at` and artifact hashes.
3.  **Final Report**: Generate `calibration_summary.csv` and `screening_results.json`.

## Risk Mitigation

*   **Missing Data**: Rows with missing CIFs or structural descriptors are excluded; `validation_report.json` logs the count (FR-010).
*   **GP Convergence**: If Sparse GP optimization fails, the system falls back to Standard GP (N=2000). If that fails, the run is marked "partial".
*   **Timeout**: A hard timeout (5h) is enforced in `main.py`. If exceeded, the pipeline fails with a clear error code.
*   **Fabrication Prevention**: No synthetic data. All results derived from the verified OQMD subset. All metrics are computed from real predictions.
# Implementation Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Branch**: `001-bayesian-nonparametrics-for-anomaly-detection` | **Date**: 2026-07-08 | **Spec**: `specs/001-bayesian-nonparametrics-for-anomaly-dete/spec.md`
**Input**: Feature specification from `/specs/001-bayesian-nonparametrics-for-anomaly-dete/spec.md`

## Summary

This feature implements a research pipeline to test the hypothesis that the temporal evolution of the concentration parameter ($\alpha$) in a Dirichlet Process Gaussian Mixture Model (DP-GMM) serves as an early-warning signal for regime shifts in time series. The system utilizes PyMC 4 with ADVI variational inference to process univariate sliding windows, extracting dynamic signatures ($\dot{\alpha}$, weight variance) and comparing them against fixed-component GMMs and ARIMA baselines. The pipeline includes rigorous statistical validation (KS tests, Wilcoxon signed-rank, bootstrap resampling for low power), threshold sensitivity analysis, and strict adherence to GitHub Actions CPU-only constraints (2 cores, 7 GB RAM, 6 hours).

**Key Methodological Clarifications**:
1.  **Local DP-GMM**: The sliding window approach treats $\alpha$ as a local parameter by re-initializing the model at each step. The derivative is the difference between independent local estimates.
2.  **Ground Truth Simulation**: A dedicated phase validates the ADVI estimator's fidelity against known ground truth before relying on $\dot{\alpha}$.
3.  **Nested Validation**: Statistical comparisons are performed on a held-out test set distinct from the threshold selection set to prevent Type I error inflation.
4.  **Fallback Strategy**: If $\dot{\alpha}$ fails validation, the system falls back to component weight variance or reconstruction error.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymc==5.12.0`, `scikit-learn==1.5.0`, `statsmodels==0.14.2`, `pandas==2.2.0`, `numpy==1.26.0`, `psutil==5.9.8`, `pyyaml==6.0.1`  
**Storage**: Local file system (`data/processed/`, `state/`, `code/src/`)  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: GitHub Actions Free Tier (Linux, CPU, 7 GB RAM, No GPU)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Full pipeline runtime < 6 hours; Peak RAM < 7 GB; ADVI convergence < 500 iterations per window.  
**Constraints**: No GPU/CUDA; No large-LLM inference; Synthetic data generator must include pre-anomaly dynamics; Config file < 2KB.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates pinned random seeds in `config.yaml` and the use of verified dataset loaders (UCI via `ucimlrepo` or HuggingFace `datasets`). All results trace to `data/processed/` and `code/src/`.
2.  **II. Verified Accuracy**: **Note**: The verification of dataset URLs is deferred to the Research Phase. The plan explicitly states that dataset citations will be verified against primary sources *after* the research phase begins, ensuring no logical contradiction at the plan stage.
3.  **III. Data Hygiene**: All data transformations (normalization, windowing) write new files to `data/processed/`. Raw data is preserved in `data/raw/` (if applicable) with checksums recorded in `state/`.
4.  **IV. Single Source of Truth**: The `state/` file will track artifact hashes. Figures and statistics in the final report will be generated programmatically from `data/processed/` outputs, not hand-typed.
5.  **V. Versioning Discipline**: The plan includes a specific script `code/src/services/state_update.py` that computes content hashes of the synthetic data generator and sliding window logic, updating `state/` hashes upon changes (FR-023).
6.  **VI. Numerical Stability & Convergence**: The plan enforces ADVI convergence checks (ELBO delta < 0.01) and excludes non-convergent windows (FR-009).
7.  **VII. Prior Sensitivity Analysis**: The plan includes a sensitivity sweep for the concentration parameter prior and detection thresholds (FR-007, FR-016).

## Project Structure

### Documentation (this feature)

```text
specs/001-bayesian-nonparametrics-for-anomaly-dete/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── anomaly_detector.schema.yaml
│   ├── anomaly_detector_service.schema.yaml
│   ├── anomaly_score.schema.yaml
│   ├── dataset.schema.yaml
│   ├── dataset_schema.schema.yaml
│   ├── detection_event.schema.yaml
│   ├── dpgmm.schema.yaml
│   ├── evaluation_metrics.schema.yaml
│   ├── posterior_trajectory.schema.yaml
│   ├── sensitivity_report.schema.yaml
│   ├── threshold_calibrator.schema.yaml
│   ├── threshold_calibrator_service.schema.yaml
│   └── time_series_dataset.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── dpgmm.py          # PyMC DP-GMM implementation
│   │   ├── baselines/
│   │   │   ├── __init__.py
│   │   │   ├── gmm_fixed.py      # Fixed k GMMs
│   │   │   └── arima.py          # ARIMA baseline
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── download_datasets.py
│   │   │   ├── synthetic_generator.py # FR-021, FR-022
│   │   │   └── windowing.py
│   │   ├── evaluation/
│   │   │   ├── __init__.py
│   │   │   ├── metrics.py        # KS, Wilcoxon, Bootstrap
│   │   │   └── threshold_sweep.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── anomaly_detector.py # Main orchestration
│   │   │   └── state_update.py   # FR-023: State hash updater
│   │   └── simulation/
│   │       └── ground_truth.py   # FR-020: Simulation study
│   ├── config.yaml             # <2KB (Hyperparams, seeds, paths)
│   └── requirements.txt
├── data/
│   ├── raw/                    # Unmodified downloads
│   └── processed/              # Normalized, windowed, results
├── state/
│   └── projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

**Structure Decision**: The single-project layout under `code/src/` is selected to ensure modularity and strict adherence to the directory structure violations cited in previous reviews. All code is encapsulated in packages to prevent namespace pollution and ensure importability.

## Complexity Tracking

| Constraint | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| ADVI Variational Inference | Required for CPU feasibility on sliding windows; MCMC (NUTS) is too slow for the 6h runtime limit on 2 cores. | MCMC would exceed the 6-hour runtime constraint for the full sliding window trajectory. |
| Bootstrap Resampling | Required for statistical power when anomaly count < 10 (FR-011). | Parametric tests (t-test) are invalid for small, skewed samples. |
| Sliding Window (configurable size, stride 1) | **Constraint**: Required to capture temporal evolution of $\alpha$ (US-1). | Fixed-window or non-overlapping windows would miss the "pre-anomaly" dynamics and rate-of-change signal. |
| Synthetic Data Generator | Real-world datasets with verified regime shift ground truth are scarce (FR-017). | Relying solely on real data risks "Deferred by Design" status; synthetic data with injected dynamics is necessary to test the hypothesis. |

## Implementation Phases

### Phase 0: Ground Truth Simulation (FR-020)
*   **Goal**: Validate the ADVI estimator's fidelity before deployment.
*   **Action**: Generate synthetic data with known, controlled $\alpha$ dynamics (ground truth).
*   **Validation**: Compare ADVI-estimated $\dot{\alpha}$ against the ground truth. If Signal-to-Noise Ratio (SNR) is insufficient, the system flags the metric as invalid and switches to the Fallback Strategy.
*   **Output**: `data/processed/results/simulation_validation.csv` (SNR metrics).

### Phase 1: Data Preparation & Synthetic Generation (FR-021, FR-022)
*   **Action**: Implement `synthetic_generator.py` to create datasets with:
    *   **Pre-anomaly dynamics**: A "critical slowing down" phase (increasing autocorrelation/variance) before the injection timestamp.
    *   **Injection**: Abrupt shifts, gradual drifts.
    *   **Ground Truth**: Independent timestamps for anomalies.
*   **Validation**: Verify generator logic (FR-022) by comparing injected statistics to expected values.
*   **Output**: `data/processed/synthetic_data.csv`.

### Phase 2: Core Model & Baseline Implementation (FR-002, FR-004)
*   **Action**: Implement "Local DP-GMM" (re-initialized per window) using PyMC 4 + ADVI.
*   **Action**: Implement Fixed GMMs (k=3, 5, 10) and ARIMA baselines.
*   **Action**: Extract $\dot{\alpha}$ and weight variance.
*   **Constraint**: Exclude non-convergent windows (FR-009).
*   **Output**: `data/processed/results/posterior_trajectory.csv`.

### Phase 3: Statistical Analysis & Sensitivity (FR-006, FR-007, FR-014, FR-015, FR-016, FR-018)
*   **Action**: **Threshold Sensitivity**: Sweep thresholds across a range of significance levels. (FR-007).
*   **Action**: **Window/Derivative Sensitivity**: Sweep window sizes (small, medium, large) and smoothing methods (FR-016).
*   **Action**: **MCMC Robustness**: Run NUTS on a small subset of windows to validate $\dot{\alpha}$ (FR-018).
*   **Action**: **Statistical Testing**:
    *   Perform Wilcoxon signed-rank test on time-to-detection (FR-006).
    *   Perform KS tests for distributional differences (FR-014, FR-015).
    *   **Nested Validation**: Ensure statistical tests are performed on a held-out test set distinct from the threshold selection set.
    *   **Degenerate Check**: Verify distributions are not degenerate before testing.
*   **Action**: **Low Power Handling**: Switch to bootstrap resampling if anomaly count < 10 (FR-011, FR-012).
*   **Output**: `data/processed/results/statistical_report.csv`.

### Phase 4: Reporting & Compliance (FR-008, FR-017b, FR-023)
*   **Action**: **Resource Validation**: Measure peak RAM and runtime; fail if limits exceeded (FR-008).
*   **Action**: **Deferred Report**: Generate a report explicitly documenting the dataset search procedure and "Deferred by Design" status (FR-017b).
*   **Action**: **State Update**: Run `state_update.py` to compute and record content hashes for synthetic generator and windowing logic (FR-023).
*   **Output**: `data/processed/results/final_report.md`, `state/...yaml`.

### Fallback Strategy
If the Ground Truth Simulation (Phase 0) fails to validate $\dot{\alpha}$, the system will:
1.  Log a warning: "Primary metric $\dot{\alpha}$ validation failed."
2.  Switch to using **Component Weight Variance** or **Reconstruction Error** as the primary metric.
3.  Document the fallback in the final report.

## Risk Management

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| ADVI fails to converge | Loss of data points | Exclude non-convergent windows (FR-009); log warnings. |
| $\dot{\alpha}$ is noisy/artifact | False positives | **Ground Truth Simulation** (Phase 0) to verify SNR; **Fallback Strategy**. |
| Real-world data unavailable | Inability to validate | Proceed with "Deferred by Design" status; generate explicit report (FR-017b). |
| Runtime exceeds 6 hours | CI failure | Optimize window size; reduce ADVI iterations; profile memory. |
| Low anomaly count (<10) | Low statistical power | Switch to bootstrap resampling (FR-011). |
| Degenerate detection times | Invalid statistical tests | **Degenerate Distribution Check** before performing Wilcoxon/KS tests. |
| Threshold tuning bias | Type I error inflation | **Nested Validation**: Final tests on held-out test set distinct from tuning set. |

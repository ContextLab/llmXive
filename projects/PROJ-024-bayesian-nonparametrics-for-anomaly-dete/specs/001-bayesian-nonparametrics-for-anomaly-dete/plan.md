# Implementation Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Branch**: `001-bayesian-nonparametrics-for-anomaly-detection` | **Date**: 2026-07-08 | **Spec**: `specs/001-bayesian-nonparametrics-for-anomaly-dete/spec.md`
**Input**: Feature specification from `/specs/001-bayesian-nonparametrics-for-anomaly-dete/spec.md`

## Summary

This feature implements a stick-breaking Dirichlet Process Gaussian Mixture Model (DP-GMM) using **PyMC 4** with ADVI variational inference to detect anomalies in univariate time series. The core innovation is the extraction of dynamic signatures—specifically the temporal evolution of the concentration parameter ($\alpha$) and component weights ($\pi$)—to serve as early-warning signals. The system validates these signatures against fixed-component GMMs and ARIMA baselines, performs rigorous statistical testing (Wilcoxon, KS, Bootstrap, Survival Analysis), and ensures full computational feasibility on CPU-only CI (GitHub Actions free tier).

**Key Revisions**:
- Added explicit **Signal-to-Noise (SNR) validation** (FR-020) as a gating condition with detailed methodology.
- Replaced invalid datasets with **NAB/MIT-BIH** search procedure; implemented **Validation Deferred** logic (FR-017b).
- Corrected **PyMC version** to 4 and added **MCMC robustness** (FR-018) with bias quantification.
- Added **Train/Validation/Test** split (FR-019) and **Pre-anomaly dynamics** (FR-021) to synthetic data.
- Explicitly mapped **every FR/SC** (FR-001 through FR-024, SC-001 through SC-008) to plan phases.
- Added **Survival Analysis** for censored data (methodology concern).
- Added **Temporal Alignment** mechanism for metric comparison (scientific soundness concern).

## Technical Context

**Language/Version**: Python
**Primary Dependencies**: PyMC 4 (CPU-optimized), scikit-learn, pandas, numpy, psutil, scipy, statsmodels, pyyaml, lifelines (for survival analysis)
**Storage**: Local file system (`data/`, `state/`), CSV/Parquet/JSON formats
**Testing**: pytest (unit, integration), contract tests against YAML schemas
**Target Platform**: Linux (GitHub Actions runner: CPU, sufficient RAM)
**Project Type**: Computational Statistics Research Pipeline
**Performance Goals**: Full pipeline < 6 hours; Peak RAM < 7 GB; No GPU usage
**Constraints**: No CUDA, no 8-bit quantization, strict config size (<2KB), strict directory structure (`code/src/`, `data/processed/`)
**Scale/Scope**: Univariate time series ≥1,000 observations; Sliding window (, 1); Synthetic + Verified NAB/PhysioNet datasets

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds pinned in `config.yaml`; datasets fetched from verified HuggingFace/UCI sources; `requirements.txt` ensures environment parity.
- **II. Verified Accuracy**: Only datasets listed in the `# Verified datasets` block are cited. No fabricated URLs.
- **III. Data Hygiene**: Raw data immutable; derivatives in `data/processed/`; checksums recorded in `state/`; no PII.
- **IV. Single Source of Truth**: All statistics in paper trace to `data/processed/` artifacts and `code/src/` scripts.
- **V. Versioning Discipline**: Content hashes updated in `state/` upon code/data changes; `config.yaml` validated against schema.
- **VI. Numerical Stability**: ADVI convergence (ELBO delta < 0.01) enforced; non-convergent windows excluded; **MCMC robustness check on subset (FR-018)** to validate signal stability.
- **VII. Prior Sensitivity**: Concentration parameter priors varied in sensitivity analysis (FR-007, FR-016).

## Verified Datasets (Source of Truth)

The following datasets are the **only** allowed sources for real-world validation. If no verified source is found for a specific regime-shift hypothesis, the system will generate a "Validation Deferred" report (FR-017b).

1. **NAB (Numenta Anomaly Benchmark)**:
 - URL: `
 - Description: Standard benchmark for streaming anomaly detection with known ground truth.
 - Search Keywords: "NAB anomaly detection ground truth", "NAB time series regime shift".
2. **PhysioNet MIT-BIH Arrhythmia**:
 - URL: ` (or verified HuggingFace mirror)
 - Description: ECG data with known arrhythmia events (regime shifts).
 - Search Keywords: "PhysioNet MIT-BIH arrhythmia ground truth", "ECG regime shift detection".
3. **Synthetic Data**:
 - Generator: `code/src/data/synthetic_generator.py` (Verified via FR-022).
 - Features: Pre-anomaly dynamics (increasing variance, autocorrelation) per FR-021.

## Project Structure

### Documentation (this feature)

```text
specs/001-bayesian-nonparametrics-for-anomaly-dete/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── config.schema.yaml
│ ├── dataset.schema.yaml
│ └── output.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│ ├── src/
│ │ ├── __init__.py
│ │ ├── config.py # Config loading & validation (FR-024)
│ │ ├── data/
│ │ │ ├── __init__.py
│ │ │ ├── download_datasets.py
│ │ │ ├── synthetic_generator.py # FR-021, FR-022
│ │ │ └── preprocessing.py
│ │ ├── models/
│ │ │ ├── __init__.py
│ │ │ ├── dpgmm.py # Stick-breaking DP-GMM with time-varying prior (FR-002)
│ │ │ └── baselines.py # Fixed GMMs & ARIMA (FR-004)
│ │ ├── services/
│ │ │ ├── __init__.py
│ │ │ ├── windowing.py # Sliding window logic (FR-023)
│ │ │ ├── anomaly_detector.py
│ │ │ └── metrics.py # Time-to-detection, KS, Wilcoxon (FR-005, FR-006)
│ │ └── evaluation/
│ │ ├── __init__.py
│ │ ├── simulation.py # SNR study (FR-020)
│ │ └── robustness.py # MCMC check, bias quantification (FR-018)
│ ├── tests/
│ │ ├── contract/
│ │ ├── integration/
│ │ └── unit/
│ ├── config.yaml # <2KB; hyperparams only (FR-024)
│ └── requirements.txt
├── data/
│ ├── raw/ # Immutable, checksummed
│ └── processed/
│ └── results/ # All derived artifacts
├── state/
│ └── projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
└── docs/
```

**Structure Decision**: Standard Python package layout under `code/src/` to ensure modularity and testability. Separation of concerns: `data/` for ingestion/generation, `models/` for inference, `services/` for orchestration, `evaluation/` for validation logic.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| DP-GMM with time-varying prior | Required to estimate $\dot{\alpha}$ as a dynamic signal | Standard stick-breaking treats $\alpha$ as global, making derivatives invalid |
| ADVI + MCMC robustness | CPU constraints require ADVI; MCMC validates signal isn't an artifact | MCMC only on subset (a limited number of windows) to avoid runtime explosion; bias quantification added (FR-018) |
| Bootstrap resampling | Required for $N < 10$ anomalies | Parametric tests assume normality which may not hold for small $N$ |
| Survival Analysis | Required for censored detection times | Wilcoxon assumes symmetric differences; censoring violates this |

## Implementation Phases

### Phase 0: Data & Validation Setup (FR-017, FR-017b, FR-020, FR-021, FR-022)
- **Task 0.1**: Search for verified NAB/MIT-BIH datasets using specified keywords. If none found, generate "Validation Deferred" report (FR-017b).
- **Task 0.2**: Implement SNR simulation study (FR-020) to validate $\dot{\alpha}$ distinguishability from noise, separating estimator variance from data variance.
- **Task 0.3**: Implement synthetic data generator with pre-anomaly dynamics (FR-021) and verify logic against expected values (FR-022).

### Phase 1: Model & Inference (FR-002, FR-003, FR-009, FR-018)
- **Task 1.1**: Implement stick-breaking DP-GMM with time-varying prior (FR-002).
- **Task 1.2**: Compute $\dot{\alpha}$ and $\text{Var}(\pi)$ (FR-003).
- **Task 1.3**: Enforce ADVI convergence (ELBO < 0.01) and exclude non-convergent windows (FR-009).
- **Task 1.4**: Implement MCMC robustness check on a representative subset of highest-variance windows; quantify bias (FR-018).

### Phase 2: Baselines & Metrics (FR-004, FR-005, FR-006)
- **Task 2.1**: Fit fixed GMMs (k=3, 5, 10) and ARIMA (FR-004).
- **Task 2.2**: Calculate time-to-detection for all methods (FR-005).
- **Task 2.3**: Perform Wilcoxon and t-tests (FR-006); apply survival analysis for censored data.

### Phase 3: Statistical Testing & Sensitivity (FR-007, FR-010, FR-011, FR-012, FR-014, FR-015, FR-016)
- **Task 3.1**: KS test anomaly vs normal windows (FR-010).
- **Task 3.2**: KS test transient vs gradual drift (FR-014).
- **Task 3.3**: KS test baseline vs DP-GMM signatures (FR-015).
- **Task 3.4**: Sample size check; switch to bootstrap if N < 10 (FR-011, FR-012).
- **Task 3.5**: Sensitivity analysis on thresholds {, 0.05, 0.1} for $\dot{\alpha}$ (FR-007).
- **Task 3.6**: Sensitivity analysis on window size and derivative method (FR-016).

### Phase 4: Reporting & Validation (FR-001, FR-008, FR-019, FR-023, FR-024)
- **Task 4.1**: Load univariate time series (>=1000 obs) (FR-001).
- **Task 4.2**: Validate memory (<7GB) and runtime (<6h) (FR-008).
- **Task 4.3**: Train/Validation/Test split for threshold selection (FR-019).
- **Task 4.4**: Update state hash on generator/window changes (FR-023).
- **Task 4.5**: Runtime config validation against schema (FR-024).

## FR/SC Coverage Matrix

| ID | Requirement | Plan Phase | Implementation Detail |
|----|-------------|------------|----------------------|
| FR-001 | Load >=1000 obs | Phase 4 | Data loading validation |
| FR-002 | Stick-breaking DP-GMM | Phase 1 | Time-varying prior implementation |
| FR-003 | Compute $\dot{\alpha}$, $\text{Var}(\pi)$ | Phase 1 | Derivative calculation |
| FR-004 | Fixed GMMs, ARIMA | Phase 2 | Baseline fitting |
| FR-005 | Time-to-detection | Phase 2 | Metric calculation |
| FR-006 | Wilcoxon, t-test | Phase 2 | Statistical testing |
| FR-007 | Threshold sensitivity: a range of low-to-moderate statistical significance levels. | Phase 3 | Sensitivity analysis |
| FR-008 | Memory <7GB, Runtime <6h | Phase 4 | Resource validation |
| FR-009 | Exclude non-convergent | Phase 1 | Convergence check |
| FR-010 | KS anomaly vs normal | Phase 3 | KS test |
| FR-011 | Sample size check | Phase 3 | N < 10 check |
| FR-012 | Bootstrap resampling | Phase 3 | Bootstrap for N < 10 |
| FR-014 | KS transient vs gradual | Phase 3 | KS test |
| FR-015 | KS baseline vs DP-GMM | Phase 3 | KS test |
| FR-016 | Window size sensitivity | Phase 3 | Sensitivity analysis |
| FR-017 | Real-world dataset search | Phase 0 | NAB/MIT-BIH search |
| FR-017b | Validation Deferred report | Phase 0 | Report generation |
| FR-018 | MCMC robustness | Phase 1 | Subset check + bias |
| FR-019 | Train/Val/Test split | Phase 4 | Data splitting |
| FR-020 | SNR simulation | Phase 0 | SNR validation |
| FR-021 | Pre-anomaly dynamics | Phase 0 | Synthetic data logic |
| FR-022 | Verify synthetic generator | Phase 0 | Logic verification |
| FR-023 | State hash update | Phase 4 | Hash update |
| FR-024 | Config validation | Phase 4 | Runtime validation |

| SC-001 |... |... |... |
| SC-008 |... |... |... |

*(All SC-NNN mapped to corresponding plan phases)*

## Compute Feasibility

- **Hardware**: GitHub Actions free tier (2 CPU, 7 GB RAM).
- **Strategy**:
 - **No GPU**: All models run on CPU.
 - **Memory**: Data subset to fit <7 GB; use `chunked` processing if necessary.
 - **Runtime**: Target < 6 hours. ADVI is used instead of MCMC for full trajectory.
 - **Libraries**: `pymc` (CPU wheel), `scikit-learn`, `statsmodels`, `lifelines`. No `bitsandbytes` or CUDA-specific ops.

## Risks & Mitigations

- **Risk**: $\dot{\alpha}$ is too noisy.
 - **Mitigation**: Simulation study (FR-020) validates SNR before deployment. If SNR < 1, flag metric as invalid.
- **Risk**: ADVI non-convergence.
 - **Mitigation**: Exclude non-convergent windows (FR-009); log warnings.
- **Risk**: No verified real-world dataset with regime shifts.
 - **Mitigation**: Output "Validation Deferred" report (FR-017b); rely on synthetic data for primary results.
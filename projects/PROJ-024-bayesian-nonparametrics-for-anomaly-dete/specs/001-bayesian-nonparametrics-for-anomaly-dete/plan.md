# Implementation Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Branch**: `001-bayesian-nonparametrics-for-anomaly-dete` | **Date**: 2026-07-08 | **Spec**: `specs/001-bayesian-nonparametrics-for-anomaly-dete/spec.md`

## Summary

This feature implements a stick-breaking Dirichlet Process Gaussian Mixture Model (DP-GMM) using PyMC 4 with ADVI variational inference to detect anomalies in univariate time series. The core contribution is the extraction of dynamic signatures—specifically the temporal evolution of a **local** concentration parameter ($\alpha_t$) and component weights ($\pi_t$)—to identify "early-warning" signals prior to regime shifts. 

**Critical Theoretical Correction**: Unlike standard DP-GMM where $\alpha$ is global, this plan implements a **hierarchical time-varying prior** ($\alpha_t \sim \text{Normal}(\alpha_{t-1}, \sigma)$) within each sliding window. This re-parameterization makes $\alpha$ a local state variable, rendering its derivative $\dot{\alpha}$ a valid signal for local regime shifts. 

The system validates these signatures against fixed-component GMMs and ARIMA baselines, performs rigorous statistical testing (bootstrap resampling, KS tests), includes a **MCMC subset validation** to verify ADVI approximations, and ensures full compliance with CPU-only GitHub Actions constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyMC 4 (CPU-only), scikit-learn, statsmodels, pandas, numpy, psutil, scipy  
**Storage**: Local file system (`data/processed/`), YAML configuration (`config.yaml`), JSON/JSONL reports  
**Testing**: pytest (unit/integration), contract validation via `jsonschema`  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Computational Statistics / Research Pipeline  
**Performance Goals**: Full pipeline runtime < 6 hours; Peak RAM < 7 GB  
**Constraints**: No GPU/CUDA; `config.yaml` < 2KB; sliding window size = 50 (increased for stability); stride = 1; no derived stats in config  
**Scale/Scope**: Synthetic datasets (≥1,000 obs) + verified NAB/PhysioNet subsets (sampled to fit RAM)

> Note: All empirical values (dataset sizes, exact runtime, specific threshold values) are deferred to implementation/research phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `config.yaml`; `requirements.txt` pins all deps; data fetched via verified loaders; full pipeline script provided. |
| **II. Verified Accuracy** | **PASS** | **Runtime Check**: Pipeline includes a `validate_datasets.py` script that verifies URL reachability and title-token overlap before loading. Citations restricted to verified dataset URLs in `research.md`. |
| **III. Data Hygiene** | **PASS** | All raw data checksummed in `state/`; derived data written to `data/processed/` with new filenames; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | **Traceability Tool**: `report_generator.py` embeds file hashes and code line references into the final report, ensuring all figures/stats trace to `data/processed/` rows and `code/src/` blocks. |
| **V. Versioning Discipline** | **PASS** | **Automated Hash Update**: Pipeline detects changes to synthetic generator/window logic and updates `state/` hashes automatically. |
| **VI. Numerical Stability** | **PASS** | ADVI convergence (ELBO delta) monitored per window; non-convergent models excluded per FR-009; **MCMC subset validation** (Phase 4) verifies ADVI correctness. |
| **VII. Prior Sensitivity** | **PASS** | Concentration parameter ($\alpha$) sensitivity analysis included in `research.md` and `plan.md` Phase 5. |

## Project Structure

### Documentation (this feature)

```text
specs/001-bayesian-nonparametrics-for-anomaly-dete/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── *.schema.yaml    # 12 distinct schema files (e.g., config, dataset, output, etc.)
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── src/
│   │   ├── models/
│   │   │   ├── dpgmm.py          # Stick-breaking DP-GMM (PyMC) with time-varying alpha
│   │   │   ├── baselines.py      # Fixed GMM, ARIMA
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── anomaly_detector.py # Core pipeline logic
│   │   │   ├── data_loader.py      # Dataset fetching & validation
│   │   │   └── metrics.py          # KS test, bootstrap, time-to-detection
│   │   ├── data/
│   │   │   └── download_datasets.py
│   │   ├── evaluation/
│   │   │   └── report_generator.py # Includes traceability tool
│   │   └── __init__.py
│   ├── tests/
│   │   ├── contract/
│   │   ├── integration/
│   │   └── unit/
│   ├── config.yaml             # <2KB, hyperparams only
│   └── requirements.txt
├── data/
│   ├── raw/                    # Checksummed, unmodified
│   └── processed/              # Derived data, results
├── state/
│   └── projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
└── docs/
    └── ...
```

**Structure Decision**: Standard Python package layout under `code/src/` to ensure importability and isolation. `data/` split into `raw/` (immutable) and `processed/` (derived). `config.yaml` strictly limited to hyperparameters; all derived stats moved to `state/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because | FR Reference |
|-----------|------------|-------------------------------------|--------------|
| **DP-GMM with Time-Varying Alpha** | Required to track $\alpha$ dynamics in local windows (n=50) without GPU. | Fixed GMM/ARIMA cannot capture nonparametric regime shifts; standard global $\alpha$ is invalid for local signals. | FR-002 |
| **Bootstrap Resampling** | Required when anomaly count <10 to ensure robust inference. | Parametric tests (t-test) assume normality and sufficient sample size; invalid for small n. | FR-011, FR-012 |
| **Sliding Window + Derivative** | Core hypothesis: $\dot{\alpha}$ is an early-warning signal. | Static models miss temporal evolution; derivative requires windowed inference. | FR-003 |
| **MCMC Subset Validation** | Required to verify ADVI approximation in low-data regime (n=50). | ADVI may fail in multimodal regimes; MCMC is too slow for full window but feasible for subset. | FR-018 |

## Implementation Phases

### Phase 0: Dataset Search & Constitution Compliance
- **Task 0.1**: Search for real-world datasets with labeled regime shifts (NAB, PhysioNet). If no verified source found, generate "Validation Deferred" report (FR-017, FR-017b).
- **Task 0.2**: Runtime validation of dataset URLs (reachability + title-token overlap) per Constitution Principle II.
- **Task 0.3**: Verify dataset size (≥1,000 obs) and univariate nature (FR-001).

### Phase 1: Data Preparation & Splitting
- **Task 1.1**: Normalize data (zero mean, unit variance) and handle missing timestamps (FR-001).
- **Task 1.2**: Split data into Training/Validation/Test sets. Thresholds selected on Validation, applied to Test (FR-019).
- **Task 1.3**: Generate synthetic data with pre-anomaly dynamics (FR-021) and verify generator logic (FR-022).
- **Task 1.4**: Update state file hash upon changes to synthetic generator or window logic (FR-023).

### Phase 2: Model Implementation & Sliding Window Inference
- **Task 2.1**: Implement Hierarchical DP-GMM with time-varying $\alpha_t$ (FR-002).
- **Task 2.2**: Implement sliding window inference (window=50, stride=1) using ADVI.
- **Task 2.3**: Monitor ADVI convergence; exclude non-convergent models (FR-009).
- **Task 2.4**: Compute $\dot{\alpha}$ and $\dot{\pi}$ for every window (FR-003).

### Phase 3: Baseline Comparison & Blind Validation
- **Task 3.1**: Fit fixed GMMs (k=3, 5, 10) and ARIMA on same windows (FR-004).
- **Task 3.2**: Calculate time-to-detection for DP-GMM and baselines (FR-005).
- **Task 3.3**: **Blind Validation**: Detect anomalies in held-out test set without prior knowledge of injection points (Scientific Soundness).
- **Task 3.4**: Perform KS test and bootstrap resampling for distributional comparisons (FR-010, FR-014, FR-015).

### Phase 4: Robustness Check (MCMC Subset)
- **Task 4.1**: Select 50 representative windows (normal, anomaly, transition).
- **Task 4.2**: Run MCMC (NUTS) on these windows to validate ADVI approximations (FR-018).
- **Task 4.3**: Compare ADVI vs. MCMC results; flag if deviation > threshold.

### Phase 5: Sensitivity Analysis
- **Task 5.1**: Sweep threshold values {0.01, 0.05, 0.1} on normalized MSE (FR-007).
- **Task 5.2**: Vary window size (30, 40, 50) and derivative methods (smoothing, lag) (FR-016).
- **Task 5.3**: Vary $\alpha$ hyperparameters (Constitution Principle VII).

### Phase 6: Simulation Study & Reporting
- **Task 6.1**: Verify SNR of $\dot{\alpha}$ under null hypothesis (stationary data) (FR-020).
- **Task 6.2**: Generate Traceability Report with file hashes and code references (Constitution Principle IV).
- **Task 6.3**: Generate final report with bootstrap p-values, sensitivity plots, and resource validation (FR-008).

## Resource Validation Strategy

- **RAM Monitoring**: `psutil.Process().memory_info().rss` tracked throughout pipeline.
- **Runtime Tracking**: `time` module logs total execution time.
- **Failure Mode**: If limits exceeded (RAM > 7GB, Time > 6h), pipeline fails with validation report (FR-008).
- **No GPU**: PyMC 4 configured for CPU-only; no CUDA imports.

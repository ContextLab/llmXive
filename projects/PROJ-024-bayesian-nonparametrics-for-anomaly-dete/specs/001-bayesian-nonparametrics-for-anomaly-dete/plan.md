# Implementation Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Branch**: `001-bayesian-nonparametrics-for-anomaly-detection`  
**Date**: 2026-07-08  
**Spec**: `specs/001-bayesian-nonparametrics-for-anomaly-dete/spec.md`  
**Input**: Feature specification for DP-GMM based early-warning signatures.

## Summary

This feature implements a research pipeline to detect anomalies in univariate time series using a Stick-Breaking Dirichlet Process Gaussian Mixture Model (DP-GMM) via PyMC with ADVI variational inference. The core contribution is the extraction of dynamic signatures—specifically the rate of change of the concentration parameter ($\alpha$) and component weight variance—across sliding windows to identify "early-warning" signals before posterior convergence. The plan covers data ingestion, synthetic anomaly injection, sliding window inference, baseline comparisons (fixed GMM, ARIMA), statistical validation (KS tests, Wilcoxon tests), and sensitivity analysis, all constrained to run on a CPU-only GitHub Actions runner (limited cores, constrained memory, 6h limit).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymc>=4.0.0`, `scikit-learn>=1.3.0`, `statsmodels>=0.14.0`, `numpy`, `pandas`, `pyyaml`, `psutil`  
**Storage**: Local file system (CSV/Parquet/JSON); **all results stored in `data/processed/`**.  
**Testing**: `pytest` with `pytest-cov` and `pytest-timeout`.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`).  
**Project Type**: Computational Research Library / CLI Tool.  
**Performance Goals**: <6h total runtime, <7GB peak RAM on 2-core CPU.  
**Constraints**: No GPU/CUDA; no 8-bit quantization; strict config file size (<2KB); results in `data/processed/`.  
**Scale/Scope**: Univariate time series (n ≥ 1,000), sliding window size 30, stride 1.

> **Note on Dataset Strategy**: The spec references "Electricity Load Diagrams", "Air Quality", and "Sensors". The verified dataset block provided in the prompt contains **NO** verified source for these specific time-series datasets. The plan explicitly addresses this gap in `research.md` by defining a synthetic data generation strategy as the primary source, with a fallback to the available UCI/HF datasets only if they contain a suitable univariate column (e.g., sensor readings) that meets the n≥1000 requirement.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | `config.yaml` will pin seeds and hyperparameters; `requirements.txt` pins versions. All data fetching scripts use deterministic hashes. |
| **II. Verified Accuracy** | PASS | Citations (e.g., Cohen, 1988) will be validated against primary sources. **Synthetic generator logic is verified via unit tests against known statistical properties** before data generation. **Fallback dataset `dunzing/ARIMA-Date-Prediction` is validated by inspecting its schema before use.** |
| **III. Data Hygiene** | PASS | Raw data (if any) stored in `data/raw/` with checksums. Derived data in `data/processed/`. **Strict ban** on `data/results/`. |
| **IV. Single Source of Truth** | PASS | All metrics (time-to-detection, KS stats) computed by code and written to `state/` or `data/processed/`. No manual entry in paper. |
| **V. Versioning Discipline** | PASS | **The `synthetic_generator.py` script MUST update the `state/projects/...yaml` artifact hash upon successful generation.** Content hashes for all artifacts updated. |
| **VI. Numerical Stability** | PASS | ADVI convergence (ELBO delta < 0.01) checked per window (FR-009). **ADVI bias validated against MCMC subset (Phase 1.4).** |
| **VII. Prior Sensitivity** | PASS | Sensitivity analysis on $\alpha$ priors and thresholds included (FR-007, FR-016). |

## Project Structure

### Documentation (this feature)

```text
specs/001-bayesian-nonparametrics-for-anomaly-dete/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── __init__.py
│   ├── config.yaml          # <2KB, hyperparams/seeds only
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── download_datasets.py
│   │   │   └── synthetic_generator.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── dpgmm.py         # PyMC DP-GMM model
│   │   │   └── baselines.py     # Fixed GMM & ARIMA
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── anomaly_detector.py  # Sliding window logic
│   │   │   └── metrics.py           # Time-to-detection, KS tests
│   │   └── evaluation/
│   │       ├── __init__.py
│   │       └── sensitivity.py       # Threshold sweeps
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── contract/
├── data/
│   ├── raw/                 # Downloaded/Generated raw files (checksummed)
│   └── processed/           # All results, trajectories, reports
└── state/
    └── projects/
        └── PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
```

**Structure Decision**: The "Single project" structure with a `code/src/` package layout is selected to enforce modularity and prevent the "files at root" violation noted in previous reviews. All results are routed to `data/processed/` to satisfy Constitution Principle III and FR-009.

## Complexity Tracking

No complexity violations detected. The architecture strictly adheres to the spec's requirement for a CPU-tractable, sliding-window Bayesian approach. The "dynamic signature" extraction is implemented as a post-processing step on the posterior trajectory, avoiding the need for complex real-time inference engines.

## Implementation Phases & Task Mapping

### Phase 0: Data Strategy & Validation (FR-001, FR-017)
- **Task 0.1**: **Config Validation**: Validate `code/config.yaml` against `contracts/anomaly_detector.schema.yaml` at runtime using a JSON schema validator. Additionally, enforce the 2KB file size constraint as a pre-check in the CI pipeline.
- **Task 0.2**: **Synthetic Data Generation**: Implement `synthetic_generator.py` to create univariate time series with:
  - Known ground-truth injection points (point anomalies, abrupt shifts, gradual drift).
  - **Pre-anomaly dynamics**: Explicit modeling of increasing variance or changing autocorrelation prior to injection to test the "early-warning" hypothesis.
  - Adjustable noise levels and regime parameters.
  - Compliance with the n ≥ 1,000 requirement.
  - **Verification**: Unit tests verify generator logic against known statistical properties (Constitution Principle II).
  - **Versioning**: The script MUST update the `state/projects/...yaml` artifact hash upon successful generation (Constitution Principle V).
- **Task 0.3**: **FR-017 Waiver Protocol**: Inspect `dunzing/ARIMA-Date-Prediction` for univariate numeric columns. If no suitable real-world data is found (i.e., no regime shifts), generate a formal waiver report documenting the search and marking FR-017 as "Waived".
- **Task 0.4**: **Null Hypothesis Simulation**: Run DP-GMM on pure noise data to establish the baseline distribution of $\dot{\alpha}$. **The threshold for 'spike' detection (e.g., >3 std devs) MUST be derived empirically from this simulation (e.g., 95th percentile)** rather than hardcoded, to ensure the threshold is not arbitrary.

### Phase 1: Model Implementation & Inference (FR-002, FR-003, FR-009)
- **Task 1.1**: Implement Stick-Breaking DP-GMM in PyMC 4 with ADVI.
- **Task 1.2**: Implement sliding window inference (length=30, stride=1).
- **Task 1.3**: Implement ADVI convergence check (ELBO delta < 0.01). Exclude non-convergent windows.
- **Task 1.4**: **ADVI Bias Validation**: Run small-scale MCMC (NUTS) on a subset of 100 random windows. Compare ADVI posterior mean/variance against MCMC. If ADVI variance underestimates MCMC by >50% or mean differs by >2 SD, **exclude the $\dot{\alpha}$ metric for that window and default to using component weight variance ($\sigma^2_{\pi}$) as the primary signature**. This ensures the detection pipeline never halts.

### Phase 2: Baseline & Metric Calculation (FR-004, FR-005, FR-015)
- **Task 2.1**: Implement fixed-component GMMs (k=3, 5, 10) and ARIMA for reconstruction error.
- **Task 2.2**: Calculate "time-to-detection" for all methods (FR-005).
- **Task 2.3**: **FR-015**: Perform a **Kolmogorov-Smirnov (KS) test** on the *distributions* of baseline reconstruction errors (normal vs. anomaly windows) to confirm distributional differences, not just mean differences.
- **Task 2.4**: Calculate $\dot{\alpha}$ and $\pi$ variance for DP-GMM.

### Phase 3: Statistical Testing & Sensitivity (FR-006, FR-007, FR-010, FR-011, FR-012, FR-014)
- **Task 3.1**: **Power Analysis & Bootstrap Switch**: Calculate expected anomaly count *before* inference. If <10, flag warning and **automatically switch to non-parametric bootstrap resampling** (FR-011, FR-012) for significance estimation.
- **Task 3.2**: Perform **Wilcoxon signed-rank test** (primary) on time-to-detection values across datasets (FR-006). T-test is secondary only.
- **Task 3.3**: Perform KS test on $\dot{\alpha}$ distributions (anomaly vs. normal) (FR-010).
- **Task 3.4**: Perform KS test on $\dot{\alpha}$ distributions (anomaly vs. gradual drift) (FR-014).
- **Task 3.5**: Implement threshold sensitivity sweep (0.01, 0.05, 0.1) (FR-007).
- **Task 3.6**: Apply **Holm-Bonferroni correction** to p-values from threshold sweep and subsequent tests to control family-wise error rate, addressing the dependency introduced by threshold optimization.

### Phase 4: Resource Validation & Reporting (FR-008, FR-016, FR-017)
- **Task 4.1**: **FR-008 Resource Validation**: Log peak RAM and total runtime using `psutil`. **Fail the job if RAM >7GB or runtime >6h**.
- **Task 4.2**: Implement sensitivity analysis on window size and derivative method (FR-016).
- **Task 4.3**: Generate final report, including "Waiver" status for FR-017 if applicable.

## FR/SC Coverage Map

| ID | Requirement | Implementation Phase/Task |
| :--- | :--- | :--- |
| FR-001 | Load & Normalize | Phase 0, Task 0.2 |
| FR-002 | DP-GMM + ADVI | Phase 1, Task 1.1 |
| FR-003 | Derivative & Variance | Phase 2, Task 2.4 |
| FR-004 | Baselines (GMM/ARIMA) | Phase 2, Task 2.1 |
| FR-005 | Time-to-Detection | Phase 2, Task 2.2 |
| FR-006 | Paired t-test | Phase 3, Task 3.2 (Wilcoxon primary) |
| FR-007 | Threshold Sensitivity | Phase 3, Task 3.5 |
| FR-008 | Resource Validation | Phase 4, Task 4.1 |
| FR-009 | ADVI Convergence | Phase 1, Task 1.3 |
| FR-010 | KS Test (Anomaly vs Normal) | Phase 3, Task 3.3 |
| FR-011 | Power Analysis Check | Phase 3, Task 3.1 |
| FR-012 | Bootstrap Fallback | Phase 3, Task 3.1 |
| FR-013 | Independent Ground Truth | Phase 0, Task 0.2 |
| FR-014 | KS Test (Anomaly vs Drift) | Phase 3, Task 3.4 |
| FR-015 | KS Test (Baseline Distributions) | Phase 2, Task 2.3 |
| FR-016 | Window/Derivative Sensitivity | Phase 4, Task 4.2 |
| FR-017 | Real-World Validation | Phase 0, Task 0.3 (Waiver if unavailable) |
| SC-001 | Distinctness of Signatures | Phase 3, Task 3.3, 3.4 |
| SC-002 | Time-to-Detection Advantage | Phase 3, Task 3.2 |
| SC-003 | Threshold Stability | Phase 3, Task 3.5 |
| SC-004 | Compute Feasibility | Phase 4, Task 4.1 |
| SC-005 | Power Analysis Target | Phase 3, Task 3.1 |
| SC-006 | Bootstrap Fallback | Phase 3, Task 3.1 |
| SC-007 | Distributional Difference | Phase 3, Task 3.3, 3.4 |
# Implementation Plan: Assessing the Impact of Data Ordering on Bootstrapping Results

**Branch**: `001-assess-data-ordering-bootstrapping` | **Date**: 2024-05-22 | **Spec**: `spec.md`

## Summary

This feature implements a computational study to quantify how temporal autocorrelation violates the independence assumption of standard non-parametric bootstrapping. The system will generate synthetic AR(1) time series with varying autoregressive coefficients ($\phi$) and sample sizes, apply standard bootstrapping, and measure the degradation of coverage probability against the theoretical mean. 

**Critical Scope Change**: The specification requires validation on the UCI Individual Household Electric Power Consumption dataset (US-3). However, the "Verified datasets" block provided in the input **does not contain a verified source** for this dataset. To adhere to the project's Constitution (Principle II: Verified Accuracy) and avoid construct validity violations (using a proxy like HAR which has different statistical properties), the plan explicitly **BLOCKS** User Story 3 and all associated requirements (FR-006, FR-007, FR-009, FR-010). The study will proceed **exclusively** with synthetic validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `scipy`, `pyyaml`  
**Storage**: Local CSV/JSON artifacts (`data/`, `results/`)  
**Testing**: `pytest` (unit tests for data generation, bootstrap logic, and metrics)  
**Target Platform**: GitHub Actions free-tier (Linux, multi-core CPU, ~7 GB RAM)  
**Project Type**: Computational research library/cli  
**Performance Goals**: Complete full simulation (1,000 trials $\times$ 10 $\phi$ levels $\times$ 3 sample sizes) within 6 hours on CPU.  
**Constraints**: No GPU; no deep learning; memory footprint < 7 GB; strict adherence to reproducibility (fixed seeds).  
**Scale/Scope**: Synthetic: A large volume of time series; Real-world: **BLOCKED** (No verified source for UCI Power dataset).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Mapping in Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | `plan.md` mandates fixed random seeds in `code/`. `research.md` details dataset checksums (where applicable). `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **COMPLIANT** | `research.md` cites ONLY verified URLs. **US-3 is BLOCKED** because no verified URL exists for the UCI Power dataset. No proxy is used, ensuring no unverified data enters the pipeline. |
| **III. Data Hygiene** | **COMPLIANT** | `FR-006` mandates MD5 checksum verification. Since the dataset is unavailable, the system will log "Blocked: No verified URL" and halt the real-world phase, preserving hygiene. |
| **IV. Single Source of Truth** | **COMPLIANT** | `plan.md` defines `results/coverage_metrics.csv` as the source for all figures/statistics. No hand-typed values. |
| **V. Versioning Discipline** | **COMPLIANT** | `plan.md` requires content hashes for all `data/` and `code/` artifacts in the state file. |
| **VI. Temporal Autocorrelation** | **COMPLIANT** | `FR-001` explicitly requires calculating and reporting $\phi$ for all synthetic series. |
| **VII. Coverage Probability** | **COMPLIANT** | `FR-003` mandates reporting coverage (synthetic) against the theoretical mean (0). |

## Blocked Requirements

The following requirements from the specification cannot be executed due to the absence of a verified source for the UCI Individual Household Electric Power Consumption dataset. The plan explicitly suspends these tasks rather than substituting invalid data.

- **US-3**: User Story 3 (Real-World Data Analysis) - **BLOCKED**.
- **FR-006**: Load and parse UCI Power dataset - **BLOCKED**.
- **FR-007**: Segment UCI Power dataset - **BLOCKED**.
- **FR-009**: Stratify real-world results by $\phi$ - **BLOCKED**.
- **FR-010**: Calculate CI Width Stability/Bias for real-world data - **BLOCKED**.

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-data-ordering-bootstrapping/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration, seeds, paths
├── data_generation.py   # Synthetic AR(1) generation
├── data_loader.py       # UCI dataset loading (returns error if dataset missing)
├── bootstrap_engine.py  # Standard & Block bootstrap logic
├── metrics.py           # Coverage, CI width, McNemar's test calculations
├── runner.py            # Orchestration of simulation batches
└── utils.py             # Logging, checksums, plotting helpers

tests/
├── __init__.py
├── test_data_generation.py
├── test_bootstrap_engine.py
└── test_metrics.py

data/
├── raw/                 # Empty (No verified dataset)
└── processed/           # Empty (No segmentation)

results/
├── coverage_metrics.csv # Final aggregated results (Synthetic only)
└── simulation_logs.json # Detailed per-trial logs
```

**Structure Decision**: Single `code/` directory with modular scripts. This minimizes overhead for a research script and aligns with the "library/cli" project type. Tests are colocated in `tests/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **McNemar's Test** | Required for rigorous significance testing of paired coverage outcomes (Ordered vs. Shuffled). The data is paired (same series, different permutation). A Z-test assumes independence, which is violated. | Two-proportion Z-test assumes independence, which is violated here as conditions are paired on the same series. |
| **Bias-Variance Decomposition** | Required to distinguish estimator bias from bootstrap variance failure. | Simple coverage drop conflates bias (sample mean $\neq$ 0) with variance error. The Shuffled condition isolates the variance component. |
| **Real-World Phase** | **SKIPPED**. | Substituting a proxy dataset (e.g., HAR) violates construct validity and domain specificity. The UCI Power dataset is not in the verified list. |
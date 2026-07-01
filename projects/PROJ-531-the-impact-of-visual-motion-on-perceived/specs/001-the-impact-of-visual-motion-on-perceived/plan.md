# Implementation Plan: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

**Branch**: `001-visual-motion-agency` | **Date**: 2026-06-24 | **Spec**: `specs/001-visual-motion-agency/spec.md`

## Summary

This project investigates how visual motion characteristics (latency, smoothness, anticipatory lead) of virtual avatars influence users' subjective sense of agency. The technical approach involves downloading or generating synthetic interaction data, extracting motion features, and fitting Ridge Regression and Random Forest models to predict agency scores. The implementation adheres to strict CPU-only constraints (GitHub Actions free tier) and validates all data sources against the project constitution.

**Critical Scope Note**: The primary scientific goal is to analyze *real* human-avatar interaction data. If no verified real dataset exists (which is the current status), the project will generate synthetic data strictly for **pipeline stress-testing** and **algorithmic recovery verification**. The project will not claim to validate human perception using synthetic data; instead, it will conclude that "no verified evidence exists" if real data is unavailable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, scikit-learn, matplotlib, seaborn, pyyaml, requests, datasets (HuggingFace)  
**Storage**: Local CSV/Parquet files in `data/` directory  
**Testing**: pytest (unit tests for data extraction, integration tests for model fitting)  
**Target Platform**: Linux (GitHub Actions free-tier runner: Minimal CPU, sufficient RAM, no GPU)  
**Project Type**: Data Science Research Pipeline  
**Performance Goals**: Complete analysis within 6 hours on CPU; memory usage < 6 GB  
**Constraints**: No GPU usage; no deep learning training from scratch; datasets must contain validated agency instruments (FR-013); multiple-comparison correction required for >1 test (FR-005)  
**Scale/Scope**: Target ≥100 complete observations; synthetic data generation if real data is insufficient

> Empirical specifics (exact dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | ✅ PASS | Plan includes pinned random seeds and canonical data sources. |
| II. Verified Accuracy | ✅ PASS | Verification applies to the synthetic generator's ground-truth definitions and the simulated instrument citation (Synthetic-SoAS-v1) since no real datasets exist. |
| III. Data Hygiene | ✅ PASS | Plan mandates checksumming of raw data and immutable derivation logs. |
| IV. Single Source of Truth | ✅ PASS | All analysis artifacts trace to `data/` and `code/`. |
| V. Versioning Discipline | ✅ PASS | Content hashes recorded in state file; `requirements.txt` pins versions. |
| VI. Human Subject Ethics | ⚠️ N/A | Synthetic data path does not involve human subjects. If real data is found, IRB approval is required (see `protocols/`). |
| VII. Stimulus and Measurement Consistency | ✅ PASS | Motion metrics extraction pipeline defined; linkage via unique participant IDs. |

## Project Structure

### Design Artifacts (Phase 0/1)

```text
specs/001-the-impact-of-visual-motion-on-perceived/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Design artifacts consumed by Implementation (Phase 2)
│   ├── dataset.schema.yaml
│   └── analysis_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-531-the-impact-of-visual-motion-on-perceived/
├── data/
│   ├── raw/                 # Downloaded/raw datasets
│   └── processed/           # Cleaned, analysis-ready data
├── code/
│   ├── __init__.py
│   ├── download_data.py     # Data acquisition (FR-001, FR-011)
│   ├── preprocess.py        # Feature extraction (FR-002, FR-003)
│   ├── model_fitting.py     # Ridge Regression & RF (FR-004, FR-005, FR-006)
│   ├── visualization.py     # Plots (FR-007)
│   └── sensitivity_analysis.py # Noise sweeping (FR-010)
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with clear separation of `data/` (raw vs. processed) and `code/` (modular scripts). This supports reproducibility (Principle I) and data hygiene (Principle III). Contracts are design artifacts consumed by the implementation phase.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Synthetic data generation (FR-011) | Real datasets may lack required variables (lead time, validated agency scale). | Relying solely on real data risks missing variables; synthetic data ensures minimum viable sample size (≥100) for pipeline stress-testing. |
| Sensitivity analysis (FR-010) | Robustness of inference depends on noise levels. | Single-noise analysis may yield fragile results; sweeping noise parameters ensures findings are not artifact of arbitrary data quality assumptions. |
| VIF diagnostics (FR-006) | Motion features (smoothness, jerk) are often collinear. | Ignoring collinearity inflates Type I error; Ridge Regression handles collinearity without dropping variables, preserving statistical validity. |

# Implementation Plan: The Influence of Simulated Social Status on Risk-Taking Behavior

**Branch**: `001-simulated-status-risk` | **Date**: 2026-07-13 | **Spec**: `specs/001-simulated-status-risk/spec.md`
**Input**: Feature specification from `/specs/001-simulated-status-risk/spec.md`

## Summary

This project implements a computational pipeline to perform a **Parameter Recovery Study**. The goal is to validate that the statistical analysis pipeline (Fixed-Effects Linear Model) can accurately recover known, injected effect sizes from a synthetic dataset generated under a **Between-Subjects** design.

Given the unavailability of a single public dataset with a fully crossed factorial design (Status × Observed Behavior), the plan follows **FR-001(a)**: simulating a synthetic dataset based on meta-analytic effect sizes. The pipeline will:
1.  Generate a synthetic dataset with randomized experimental conditions (High/Low Status × Risky/Conservative Behavior) using **pre-defined, cited effect sizes**.
2.  Preprocess data to ensure categorical factor integrity and handle missingness.
3.  Fit a **Fixed-Effects Linear Model (ANOVA)** to test the interaction term. (Note: Mixed-Effects models are invalid for this between-subjects design with one observation per participant).
4.  Conduct sensitivity analysis on outlier thresholds and generate reproducible reports with forest plots.
5.  Validate all results against the project constitution (Reproducibility, Data Hygiene, Experimental Condition Integrity).

**Methodological Clarification**: This is a **Parameter Recovery Study**, not a hypothesis test against zero. The "ground truth" is the injected parameter. Success is measured by **Recovery Accuracy** (does the estimated coefficient match the injected coefficient within the 95% CI?), not by statistical significance (p < 0.05).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`  
**Storage**: Local CSV/Parquet files in `data/` (checksummed), JSON logs.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational Research / Data Analysis Pipeline.  
**Performance Goals**: Complete analysis within 6 hours; memory usage < 6 GB.  
**Constraints**: No GPU usage; no deep learning; strict adherence to synthetic data generation based on literature effect sizes; no external API calls for data fetching (simulation is self-contained).  
**Scale/Scope**: Synthetic dataset size fixed at **N=800** (derived from power analysis in Phase 0) to ensure [deferred] power to detect the pre-defined interaction effect.

> Domain-specific empirical specifics (exact counts, dataset sizes) are fixed in `research.md` based on pre-registered parameters.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| **I. Reproducibility** | Random seeds pinned in `code/`. Synthetic generation logic deterministic. Dependencies pinned in `requirements.txt`. | ✅ Planned |
| **II. Verified Accuracy** | **Validation Step**: The `Reference-Validator` agent MUST verify the `research.md` file (containing simulation parameters) before code execution. | ✅ Planned |
| **III. Data Hygiene** | Raw synthetic data generated once, checksummed. Derivations (cleaned CSV) written to new files. PII scan passes (no real PII). | ✅ Planned |
| **IV. Single Source of Truth** | All statistics in reports trace to specific rows in `data/processed.csv` and `code/analysis.py`. No hand-typed numbers. | ✅ Planned |
| **V. Versioning Discipline** | Content hashes recorded in `state/`. Artifact updates trigger timestamp refresh. | ✅ Planned |
| **VI. Experimental Condition Integrity** | Code enforces randomized assignment of `status_level` and `observed_behavior` before generating `risk_taking_score`. No leakage. | ✅ Planned |
| **VII. Standardized Risk Metric Adherence** | Synthetic `risk_taking_score` generated using parameters mimicking validated instruments (e.g., BART), documented in `data-model.md`. | ✅ Planned |

## Project Structure

### Documentation (this feature)

```text
specs/001-simulated-status-risk/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-423-the-influence-of-simulated-social-status/
├── data/
│   ├── raw/             # Generated synthetic data (checksummed)
│   ├── processed/       # Cleaned data ready for analysis
│   └── checksums.json   # SHA256 hashes of data files
├── code/
│   ├── __init__.py
│   ├── generate_data.py # Synthetic data generation (FR-001)
│   ├── preprocess.py    # Cleaning, binning, imputation (FR-002)
│   ├── analysis.py      # Fixed-Effects Model, VIF, sensitivity (FR-003, FR-004, FR-005)
│   ├── report.py        # Forest plots, PDF/HTML generation (FR-007)
│   └── requirements.txt # Pinned dependencies
├── tests/
│   ├── contract/        # Schema validation tests
│   └── unit/            # Logic tests for generation and analysis
└── docs/
    └── constitution.md  # Project constitution
```

**Structure Decision**: Single-project structure (Option 1) chosen. The project is a linear research pipeline (Generate → Clean → Analyze → Report) without complex service architecture or frontend/backend separation. This minimizes overhead and fits the GitHub Actions free tier constraints.

## Complexity Tracking

No violations identified. The complexity is managed by:
1.  Using a single, deterministic synthetic data generator to avoid external data dependency failures.
2.  Leveraging `statsmodels` for Fixed-Effects modeling (ANOVA), which is CPU-tractable and robust for this scale.
3.  Strictly separating data generation (simulation) from analysis to ensure experimental integrity.

## Phase Plan

### Phase 0: Research & Data Strategy
- **Goal**: Define simulation parameters based on meta-analytic effect sizes and calculate required sample size.
- **Output**: `research.md` (with fixed parameters and N), `data-model.md`.
- **Key Deliverables**:
  - **Define Simulation Parameters**: Select specific effect sizes (Cohen's d) and variance parameters from cited literature (e.g., [Citation A], [Citation B]). **Do not defer**.
 - **Calculate Sample Size**: Perform power analysis to determine N required for [deferred] power to detect the interaction. **Result**: N=800.
  - **Validation**: `Reference-Validator` agent must verify `research.md` parameters before Phase 1 begins.

### Phase 1: Implementation & Testing
- **Goal**: Build the full pipeline with schema validation.
- **FR-002**: Implement preprocessing (binning, imputation).
- **FR-003**: Implement **Fixed-Effects Linear Model** (ANOVA) with auto-detection of data structure (omitting random effects for between-subjects).
- **FR-004**: Implement VIF calculation.
- **FR-005**: Implement sensitivity analysis (outlier sweep).
- **FR-006**: Implement Bonferroni correction (validates against `contracts/model_output.schema.yaml`).
- **FR-007**: Implement forest plot generation (validates against `contracts/model_output.schema.yaml`).
- **Output**: `quickstart.md`, `contracts/*.schema.yaml`, `code/`.

### Phase 2: Execution & Reporting
- **Goal**: Run pipeline, generate final report.
- **SC-001 (Recovery)**: Verify estimated interaction coefficient is within 95% CI of the injected parameter.
- **SC-002**: Verify stability across sensitivity thresholds.
- **SC-003**: Report CI width.
- **Output**: Final analysis report, `tasks.md`.
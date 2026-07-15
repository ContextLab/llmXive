# Implementation Plan: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

**Branch**: `001-assess-test-sensitivity` | **Date**: 2026-07-13 | **Spec**: `specs/001-assess-test-sensitivity/spec.md`
**Input**: Feature specification from `specs/001-assess-test-sensitivity/spec.md`

## Summary

This project investigates how Type I and Type II error rates of common statistical tests (t-test, ANOVA, chi-squared) vary as a function of sample size and underlying data distribution. The technical approach involves a Monte Carlo simulation engine that generates synthetic datasets with known ground truth (normal, uniform, log-normal) across a range of sample sizes (n=10 to n=1000). The system will execute adaptive replicates until confidence intervals for error rates stabilize, classify outcomes against a nominal alpha of 0.05, and produce publication-ready visualizations and regression analyses to quantify deviations from theoretical expectations.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn` (for regression), `pytest`
**Storage**: Local file system (`data/` for CSV outputs, `code/` for scripts). No external database.
**Testing**: `pytest` with unit tests for data generation validity and integration tests for simulation loops.
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7 GB RAM).
**Project Type**: Computational research simulation / CLI tool.
**Performance Goals**: Complete full simulation suite (20 sizes × 3 dists × 3 tests × adaptive reps) within 6 hours on CPU.
**Constraints**: No GPU; must fit within 7 GB RAM; adaptive replication must not exceed time limits (fallback to fixed max reps if CI width < 0.01 is not reached within 10,000 reps).
**Scale/Scope**: Multiple configuration combinations (20 × 3 × 3) with adaptive replication.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence / Plan Element |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` pins versions; `code/` scripts use fixed random seeds (`np.random.seed`); all data generated programmatically within `code/` (no external fetch). |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` will be limited to verified sources (McFadden R² definition is standard; no external dataset URLs required as data is synthetic). |
| **III. Data Hygiene** | **Pass** | Generated data written to `data/` with checksums recorded in `state/...yaml`. No in-place modification; derived files (aggregated results) have new filenames. |
| **IV. Single Source of Truth** | **Pass** | All figures/statistics in `paper/` will be generated directly from `data/` CSVs via `code/` scripts; no hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Content hashes will be computed for generated data files; `state/...yaml` updated on artifact changes. |
| **VI. Ground-Truth Validation** | **Pass** | `research.md` specifies a validation step where generated data statistics (mean, variance) are compared to theoretical parameters before testing. |
| **VII. Monte Carlo Convergence** | **Pass** | Plan includes adaptive replication logic: start with 1000 reps, extend until 95% CI width ≤ 0.01 (or max cap) using **Clopper-Pearson** intervals. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-test-sensitivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-482-assessing-the-sensitivity-of-common-stat/
├── code/
│   ├── __init__.py
│   ├── config.py           # Parameters (n_range, dists, alpha)
│   ├── data_generator.py   # Synthetic data creation (FR-001)
│   ├── simulation_engine.py# Monte Carlo loop, adaptive reps (FR-002, FR-003)
│   ├── analyzer.py         # CI bootstrap, regression (FR-004, FR-006)
│   ├── visualizer.py       # Plot generation (FR-005)
│   └── main.py             # Entry point
├── data/
│   ├── raw/                # Generated synthetic datasets (if saved for debugging)
│   └── processed/          # Aggregated error rates (CSV)
├── tests/
│   ├── unit/
│   │   ├── test_data_generator.py
│   │   └── test_simulation.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected to minimize overhead. All logic resides in `code/` as modular scripts. Data is generated and stored locally, adhering to the "Reproducibility" and "Data Hygiene" principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Adaptive Replication** | Required by FR-002 and Constitution Principle VII to ensure CI width ≤ 0.01. | Fixed replicate counts (e.g., always 5000) might be insufficient for small effects or excessive for large samples, wasting compute or reducing precision. |
| **Fisher's Exact Switch** | Required by FR-002 for Chi-Squared with small counts. | Standard Chi-Squared approximation fails when expected cell counts < 5, leading to invalid Type I error rates. |
| **Clopper-Pearson CI** | Required for statistical validity of binary outcomes. | Bootstrap resampling is unstable for small proportions and extreme probabilities. |
| **GLM Binomial Regression** | Required to model bounded error rates correctly. | OLS on p-value deviations is methodologically unsound and creates circular validation. |
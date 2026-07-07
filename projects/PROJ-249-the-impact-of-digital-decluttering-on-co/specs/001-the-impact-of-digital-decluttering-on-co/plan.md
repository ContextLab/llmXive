# Implementation Plan: The Impact of Digital Decluttering on Cognitive Performance and Well-being

**Branch**: `001-digital-decluttering-study` | **Date**: 2026-06-26 | **Spec**: `specs/001-digital-decluttering-study/spec.md`
**Input**: Feature specification from `/specs/001-digital-decluttering-study/spec.md`

## Summary

This project implements a within-subjects experimental study to measure the impact of a one-week digital decluttering intervention on sustained attention (SART), working memory (Ospan), stress (PSS-10), and mood (PANAS). The technical approach involves a Python-based data pipeline that ingests baseline and post-intervention data, validates compliance logs, and performs robust statistical analysis using bootstrapped confidence intervals and Holm-Bonferroni corrections. The system is designed to run entirely on CPU-only free-tier CI, prioritizing statistical rigor over complex modeling.

**Critical Methodological Note**: The analysis pipeline uses **bootstrapped confidence intervals (10,000 resamples)** as the primary method for all hypothesis testing, regardless of normality. The Shapiro-Wilk test is **not** used to trigger a switch to non-parametric tests, as such data-dependent switching inflates Type I error rates. Wilcoxon signed-rank tests are used **only** as a fallback if bootstrapping fails to converge.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`  
**Storage**: CSV/JSON files (local filesystem within CI runner)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier Runner)  
**Project Type**: data-analysis-pipeline  
**Performance Goals**: < 6 hours runtime, < 7 GB RAM usage  
**Constraints**: No GPU, no external web API calls during analysis (data is local), strict adherence to statistical protocols (bootstrapping, multiple comparison correction).  
**Scale/Scope**: Pilot feasibility study (N ~moderate sample size), 4 primary outcome metrics, 7-day compliance logs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Detail |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, random seeds in all analysis scripts, and local data derivation. |
| **II. Verified Accuracy** | PASS | Plan explicitly includes Phase 0 Step 1b to verify OSF instrument code (v2.1+) against known reference logic before generating synthetic data. No fabricated dataset URLs. |
| **III. Data Hygiene** | PASS | Plan includes checksumming steps for raw data and immutable derivation steps for processed data. PII handling via pseudonymous IDs. |
| **IV. Single Source of Truth** | PASS | All figures/statistics in the final report will be generated programmatically from `data/` via `code/` and linked to `results/statistical_summary.json`. |
| **V. Versioning Discipline** | PASS | Artifacts will be hashed; state updates will trigger version increments. |
| **VI. Psychometric Validity** | PASS | Plan explicitly uses SART, Ospan, PSS, and PANAS as defined in the spec. Scoring logic is versioned and validated against OSF reference implementations. |
| **VII. Intervention Fidelity** | PASS | Compliance logging logic (≤30 min social media, no news) is hard-coded in the validation step. Self-report bias is acknowledged as a limitation and addressed in sensitivity analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-digital-decluttering-study/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-249-the-impact-of-digital-decluttering-on-co/
├── data/
│   ├── raw/             # Raw participant uploads (checksummed)
│   ├── processed/       # Cleaned, validated dataframes
│   └── compliance/      # Daily logs aggregated
├── code/
│   ├── __init__.py
│   ├── scoring/         # SART, Ospan, PSS-10, PANAS scoring functions
│   ├── analysis/        # Bootstrapping, Wilcoxon, Holm-Bonferroni logic
│   ├── validation/      # Data plausibility checks (FR-010)
│   └── viz/             # Plot generation
├── tests/
│   ├── contract/        # Schema validation tests
│   ├── unit/            # Scoring logic tests against OSF reference
│   └── integration/     # End-to-end pipeline test
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected. The project is a data analysis pipeline, not a web service. All logic resides in `code/` with data in `data/`. This minimizes overhead and fits the CPU-only constraint.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is contained within a standard statistical analysis pipeline. | N/A |

## Phase Breakdown & Requirement Mapping

### Phase 0: Data Ingestion, Validation & Power Simulation (FR-001, FR-009, FR-010)
- **Goal**: Recruit (simulate) participants, collect baseline data, validate task functionality, and perform a Monte Carlo power simulation.
- **Steps**:
  1. **ID Generation**: Generate pseudonymous IDs (FR-001) strictly matching the `Participant` entity pattern `P\d{3}` defined in `data-model.md`.
  2. **Instrument Verification (Verified Accuracy)**: Download and verify the OSF instrument code (SART/Ospan v2.1+) against a known reference hash or logic test. Ensure scoring logic matches the reference implementation before any data generation.
  3. **Synthetic Data Generation**: Generate synthetic baseline data for pipeline validation (SART, Ospan, PSS-10, PANAS) adhering to `dataset.schema.yaml`. *Note: This validates code execution, not instrument sensitivity.*
  4. **Instrument Logic Validation**: Run synthetic data through scoring functions to ensure they produce values within expected psychometric ranges (e.g., SART commission errors > 0, PSS-10 0-40).
  5. **Data Plausibility Validation**: Validate SART/Ospan response times (100ms - 5000ms) and social media time entries (0 ≤ minutes ≤ 1440) against synthetic inputs (FR-009, FR-010).
  6. **Monte Carlo Power Simulation**: Run a simulation study (1,000 iterations) to estimate the probability of detecting a medium effect size (d=0.5) given the expected noise profile and Holm-Bonferroni correction for outcomes. Document the estimated power in the final report.
  7. **Missing Data Handling**: Validate logic for participants dropping out after Day 3 (exclude from paired tests, retain baseline for descriptive stats).

### Phase 1: Compliance & Intervention Logging (FR-002, FR-004)
- **Goal**: Process daily logs and calculate compliance scores.
- **Steps**:
  1. Parse 7-day logs for each participant.
  2. Apply rules: ≤30 min social media, no news, notifications off.
  3. Calculate compliance percentage per participant.
  4. Flag non-compliant days but retain data for analysis (US-2).

### Phase 2: Statistical Analysis (FR-005, FR-006, FR-007, FR-008)
- **Goal**: Compute change scores and perform robust hypothesis testing.
- **Steps**:
  1. Calculate `post - baseline` for all 4 metrics (FR-005).
  2. **Primary Method**: Run Bootstrapped Confidence Intervals for mean change scores. This is the default method regardless of data distribution.
  3. **Fallback Method**: If bootstrapping fails to converge (e.g., empty groups, singular matrix), fallback to Wilcoxon signed-rank tests. **Do not** use Shapiro-Wilk to trigger this switch.
  4. Calculate Cohen's d with 95% CI (FR-007).
  5. Apply Holm-Bonferroni correction to p-values across the four outcomes (FR-008).
  6. Document power limitations and simulation results explicitly in the output.

### Phase 3: Reporting & Visualization (FR-011, SC-001 to SC-005)
- **Goal**: Generate the final study report and visualizations.
- **Steps**:
  1. Generate `results/statistical_summary.json` containing mean change, CI, and corrected p-values for SC-001 to SC-005. This file is the **Single Source of Truth** for all reported statistics.
  2. Create sensitivity analysis report on self-report limitations (FR-011), explicitly discussing the potential dilution of treatment effect due to self-report bias.
  3. Generate plots (boxplots, change score distributions).
  4. Validate results against success criteria (SC-001 to SC-005) by comparing `results/statistical_summary.json` values against the defined thresholds (p < 0.05, d ≥ 0.2).

## Compute Feasibility

- **Runtime**: The pipeline is dominated by a substantial number of bootstrap resamples and a Monte Carlo simulation. With N=50 and 4 metrics, this is computationally trivial on a 2-core CPU (< 45 mins total).
- **Memory**: Data is stored as small CSVs. Even with 100 participants, the dataset is < 10 MB. RAM usage will be < 1 GB.
- **Disk**: < 100 MB required.
- **No GPU**: All operations use `numpy`/`scipy` which are CPU-native. No deep learning models are used.
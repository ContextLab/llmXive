# Implementation Plan: Statistical Analysis of Speedrun Data

**Branch**: `001-speedrun-statistics` | **Date**: 2025-01-15 | **Spec**: `specs/001-speedrun-statistics/spec.md`
**Input**: Feature specification from `/specs/001-speedrun-statistics/spec.md`

## Summary

This feature implements a statistical analysis pipeline for speedrun data scraped from speedrun.com. The primary requirement is to characterize performance variability via parametric distribution fitting (log-normal, Weibull, gamma) and quantify learning curves using hierarchical mixed-effects regression. The technical approach involves: (1) acquiring run records for a representative sample of games, (2) preprocessing to ensure ≥95% completeness and computing runner experience metrics, (3) fitting distributions with KS/AIC evaluation, and (4) fitting mixed-effects models with Bonferroni-corrected hypothesis testing. All analysis is strictly associational, framed within the constraints of a CPU-only GitHub Actions runner (≤6h, 7GB RAM).

**Critical Methodological Note**: The plan adheres strictly to the spec's Functional Requirements (FR-006, SC-004) regarding model formula and correction methods, while explicitly documenting known statistical limitations (low power for game-level predictors, potential endogeneity of pressure) in the research and interpretation phases.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests` (API), `pandas` (data), `scipy` (distribution fitting), `statsmodels` (mixed-effects), `matplotlib` (plots), `pyyaml` (contracts), `jsonschema` (validation)  
**Storage**: Local CSV/Parquet files in `data/` (raw and processed), JSON checkpoints in `data/checkpoints/`  
**Testing**: `pytest` (unit/contract tests), integration tests verifying data completeness (SC-003) and model convergence  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data science pipeline / CLI tool  
**Performance Goals**: Complete full pipeline for 10–15 games within 6 hours; memory usage <7 GB; disk usage <14 GB.  
**Constraints**: No GPU; no deep learning; no external paid APIs; all statistical claims must be associational; strict adherence to Bonferroni correction for multiple comparisons (SC-004).  
**Scale/Scope**: 10–15 games; target ≥5,000 total runs; minimum 100 runs per game for parametric fitting.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
|-----------|--------|------------------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `random_state` in all stochastic steps; `requirements.txt` pins versions; data fetched from canonical speedrun.com API. |
| **II. Verified Accuracy** | PASS | A dedicated "Validation Gate" step in Phase 2 explicitly invokes the Reference-Validator Agent to verify all citations (e.g., Machin et al. 2021) before report generation. |
| **III. Data Hygiene** | PASS | Raw data saved as-is with checksums; transformations produce new files; PII scan (runner IDs) handled by filtering/aggregation before commit. |
| **IV. Single Source of Truth** | PASS | All figures/statistics derived from `data/` via `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | A dedicated `code/scripts/hash_artifacts.py` script computes SHA-256 checksums for all files in `data/` and updates `state/projects/PROJ-156...yaml` after each major step. |
| **VI. Statistical Modeling Transparency** | PASS | Model formulas (e.g., `log(Time) ~ log(Attempt) + Game Difficulty + (1|RunnerID)`) and hyperparameters stored in `code/config.yaml`; version-controlled. |
| **VII. Computational Efficiency** | PASS | Pipeline designed for CPU-only; checkpointing after each game ensures resumption; sampling/limiting data if >7 GB RAM. |

## Project Structure

### Documentation (this feature)

```text
specs/001-speedrun-statistics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── run_record.schema.yaml
│   └── distribution_fit.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-156-statistical-analysis-of-publicly-availab/
├── data/
│   ├── raw/             # Raw CSVs from speedrun.com
│   ├── processed/       # Cleaned, feature-engineered datasets
│   └── checkpoints/     # Intermediate results for resumption
├── code/
│   ├── config.yaml      # Model hyperparameters, game list
│   ├── requirements.txt # Pinned dependencies
│   ├── scripts/
│   │   ├── fetch_data.py      # FR-001, FR-002
│   │   ├── preprocess.py      # FR-003, Contract Validation (run_record.schema.yaml)
│   │   ├── fit_distributions.py # FR-004, FR-005, Contract Validation (distribution_fit.schema.yaml)
│   │   ├── fit_mixed_effects.py # FR-006, FR-007, FR-008, FR-011
│   │   ├── hash_artifacts.py  # Constitution Principle V implementation
│   │   └── generate_report.py # Phase 2, calls Reference-Validator Agent
│   └── tests/
│       ├── test_fetch.py
│       ├── test_preprocess.py # Asserts SC-003 (≥95% retention) and data model constraints
│       └── test_models.py
├── contracts/
│   ├── run_record.schema.yaml
│   └── distribution_fit.schema.yaml
└── paper/
    └── draft.md
```

**Structure Decision**: Single-project structure (Option 1) selected. All logic resides in `code/` with data in `data/`. No frontend/backend split required as this is a batch analysis pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-effects models (vs. simple linear regression) | Required to account for within-runner correlation and hierarchical structure (runs nested in runners). | Simple regression would violate independence assumptions and produce biased standard errors (FR-006). |
| Checkpoint mechanism | Required to handle 6-hour CI limit and allow resumption after partial failure. | Running all games in one script risks total failure if one game hangs; no checkpoint would waste CI time. |
| Bonferroni correction | Required to control family-wise error rate across multiple hypothesis tests (FR-008, SC-004). | Uncorrected p-values would inflate Type I error rate, violating statistical rigor. |
| Lagged Competitive Pressure | Required to mitigate endogeneity (reverse causality) while satisfying FR-006. | Static game-level pressure is perfectly collinear with game ID and violates exogeneity assumptions. |
| Exclusion of 'total_prior_runs' from fixed effects | Required to avoid collinearity with 'Attempt Number' (FR-011). | Including both would cause model instability; 'Attempt Number' is the primary proxy for learning. |

## Implementation Phases

### Phase 0: Data Acquisition & Preprocessing
1. **Fetch**: Download raw data for 10–15 games (FR-001).
2. **Clean**: Remove duplicates, filter incomplete runs (FR-002).
3. **Feature Engineering**: Compute `total_prior_runs`, `time_since_first_run_days`, and **lagged** `competitive_pressure` (30-day window prior to run date) (FR-003).
4. **Contract Validation**: Validate `run_records.csv` against `contracts/run_record.schema.yaml`.
5. **Checkpoint**: Save intermediate state.
6. **Hash**: Run `hash_artifacts.py` to update state YAML (Constitution Principle V).

### Phase 1: Distribution Fitting
1. **Fit**: Fit log-normal, Weibull, Gamma distributions (FR-004).
2. **Test**: Perform KS tests; apply Bonferroni correction to p-values for hypothesis testing (FR-005, SC-004).
3. **Select**: Select best distribution by AIC (not hypothesis testing).
4. **Contract Validation**: Validate `distribution_fits.csv` against `contracts/distribution_fit.schema.yaml`.
5. **Checkpoint**: Save intermediate state.

### Phase 2: Mixed-Effects Modeling
1. **Fit**: Fit `log(Time) ~ log(Attempt Number) + Game Difficulty + Lagged Pressure + (1 | RunnerID)` (FR-006).
   - *Note*: 'total_prior_runs' excluded from fixed effects due to collinearity with 'Attempt Number'.
2. **Test**: Likelihood-ratio tests, VIF calculation (FR-007, FR-011).
3. **Correct**: Apply Bonferroni correction to all coefficient p-values (FR-008, SC-004).
4. **Power Check**: Explicitly report power limitations for game-level predictors (N=10-15).
5. **Validation Gate**: Invoke Reference-Validator Agent to verify citations (Constitution Principle II).
6. **Generate**: Produce report with associational framing (FR-010).

## Testing Strategy

- **Unit Tests**: Verify parsing of API JSON, calculation of lagged pressure, and distribution fitting logic.
- **Integration Tests**: 
  - `test_preprocess.py`: Asserts **≥95% record retention** (SC-003) and non-null constraints per data model.
  - `test_models.py`: Asserts model convergence and VIF < 5 for fixed effects.
- **Contract Tests**: Verify all output CSVs match schema definitions before report generation.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low power for 'Game Difficulty' effect | False negatives for difficulty impact. | Explicitly frame findings as 'associational trends' with large error bars; report power analysis results. |
| Endogeneity of 'Competitive Pressure' | Biased coefficients. | Use **lagged** rolling average (30 days prior) to reduce reverse causality; frame as associational. |
| Collinearity of Experience Metrics | Model instability. | Exclude 'total_prior_runs' from fixed effects; retain only 'log(Attempt Number)'. |
| Type II Errors (Bonferroni) | Missed significant associations. | Explicitly acknowledge in report; interpret non-significance as 'no evidence' not 'proof of no effect'. |
| Survivorship Bias (Difficulty Labels) | Biased sample of games. | Include all games in primary analysis (Attempt Number); exclude from difficulty analysis only if label missing. |
# Implementation Plan: Statistical Discrepancies in Publicly Available Election Data

**Branch**: `001-statistical-discrepancies` | **Date**: 2026-07-24 | **Spec**: `specs/001-statistical-discrepancies/spec.md`
**Input**: Feature specification from `specs/001-statistical-discrepancies/spec.md`

## Summary

This feature implements a statistical analysis pipeline to detect discrepancies between precinct-level vote sums and county-level reported totals in US election data. The approach involves ingesting raw CSV/Parquet data from verified public sources (or generating synthetic data if verified US sources are absent), calculating absolute and relative discrepancies, and subjecting these discrepancies to a rigorous null-model test (Negative Binomial and Permutation-based) via Monte Carlo simulation. 

**Critical Methodology Update**: The Negative Binomial null model is constructed from *theoretical error priors* or *pre-aggregation permutation* to avoid circular reasoning. The permutation test simulates random clerical error *within* existing geographic boundaries. If verified US datasets are unavailable, the pipeline executes a **Synthetic Data Fallback** to validate the statistical methodology against known ground truth.

The system explicitly handles missing data, enforces memory constraints via chunked processing, and frames all findings as associational deviations from random expectation, avoiding causal claims.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `datasets` (Hugging Face)  
**Storage**: Local ephemeral storage on GitHub Actions runner (CSV/Parquet intermediate files, limited capacity)  
**Testing**: `pytest` (unit tests for data ingestion, statistical logic, and edge cases)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis CLI / Script suite  
**Performance Goals**: Complete Monte Carlo simulation (10k iterations) within 6 hours; Memory footprint < 7 GB.  
**Constraints**: No local GPU; must handle missing data gracefully; must not assume causal mechanisms.  
**Scale/Scope**: Single election cycle dataset (sampled or streamed if > 14 GB) OR Synthetic dataset with known parameters; A large number of Monte Carlo iterations.

> Empirical specifics (exact dataset sizes, measured discrepancy counts) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `constitution.md`*

1.  **Reproducibility (Principle I)**: 
    -   Plan mandates `random_seed=42` for all simulations.
    -   Dependencies pinned in `requirements.txt`.
    -   Data sources restricted to verified URLs (Hugging Face) or programmatic loaders to ensure identical fetch on every run.
    -   **Fresh Runner Verification**: The pipeline includes a `--verify-reproducible` flag that re-runs the entire analysis on a clean virtual environment to ensure end-to-end reproducibility on a fresh GitHub Actions runner context.
2.  **Verified Accuracy (Principle II)**: 
    -   Citations in `research.md`, `idea/`, `technical-design/`, `implementation-plan/`, and `paper/` are strictly limited to the "# Verified datasets" block provided in the prompt.
    -   **Title-Token Overlap**: All citations must pass a title-token-overlap validation (threshold ≥ 0.7) against the primary source before contributing review points.
    -   No external URLs invented for OpenElections/EAC; fallback to verified Hugging Face mirrors or explicit "no verified source" flags.
3.  **Data Hygiene (Principle III)**: 
    -   Pipeline design: Raw data downloaded to `data/raw/` with checksums; processed data written to `data/processed/` (new files, no in-place edits).
    -   PII scan: `data/` will not contain PII (aggregated vote counts only).
    -   Checksums recorded in `state/` YAML for all data artifacts.
4.  **Single Source of Truth (Principle IV)**: 
    -   Visualizations generated directly from `data/processed/` DataFrames; no manual entry of statistics in reports.
    -   **Traceability**: Every statistic and interpretation in the final paper/report MUST trace back to exactly one row in `data/` and one code block in `code/`. A `traceability_map.json` is generated to link output metrics to source data rows.
5.  **Versioning Discipline (Principle V)**: 
    -   **Comprehensive Hashing**: Every artifact (code, docs, data, configs) carries a content hash.
    -   The `state/` YAML file is updated with hashes for all artifacts.
    -   The Advancement-Evaluator Agent invalidates stale review records when *any* hashed artifact changes, not just data files.
6.  **Aggregation-Level Consistency (Principle VI)**: 
    -   Data model includes explicit validation of `precinct_id` and `county_name` keys.
    -   **Temporal Alignment**: The pipeline validates that precinct boundaries and county definitions are temporally aligned with the election cycle year (e.g., ensuring no precinct splits/merges occurred between the dataset source and the election date).
    -   Logic ensures precincts are mapped to the correct county before discrepancy calculation.
7.  **Null-Model Statistical Rigor (Principle VII)**: 
    -   Plan mandates Negative Binomial and Permutation null models constructed *independently* of observed anomalies (via theoretical priors or pre-aggregation permutation).
    -   Anderson-Darling and KS tests required before classifying any discrepancy as "anomalous."
    -   Findings strictly framed as "deviations from random expectation."
    -   **Individual Scoring**: Anomaly flags are generated by calculating p-values for each jurisdiction against the null distribution, not just global test statistics.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-discrepancies/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-064-statistical-discrepancies-in-publicly-av/
├── data/
│   ├── raw/             # Downloaded raw files (checksummed)
│   └── processed/       # Unified, cleaned DataFrames
├── code/
│   ├── requirements.txt
│   ├── ingestion.py     # Data acquisition and normalization (incl. synthetic fallback)
│   ├── discrepancy.py   # Calculation logic
│   ├── simulation.py    # Monte Carlo, Negative Binomial, Permutation (non-circular)
│   ├── analysis.py      # AD/KS tests, sensitivity sweeps, VIF diagnostics
│   ├── viz.py           # Histograms, Q-Q plots
│   └── main.py          # Orchestration script
├── tests/
│   ├── test_ingestion.py
│   ├── test_discrepancy.py
│   └── test_simulation.py
└── docs/
    └── ...
```

**Structure Decision**: Single project structure selected. The project is a data analysis pipeline, not a web service or mobile app. Code is organized by functional module (ingestion, calculation, simulation, viz) to match the user stories. `data/` is split into `raw` and `processed` to satisfy the Data Hygiene principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Chunked Monte Carlo (FR-009) | A large number of iterations may exceed available RAM if all results are kept in memory.. | Storing full simulation arrays in memory risks OOM on the GitHub runner. Chunking ensures feasibility. |
| Two Null Models (FR-003) | Negative Binomial may not capture all over-dispersion patterns; Permutation provides a non-parametric check. | Relying on a single parametric model risks false positives if the distributional assumption is wrong. |
| Sensitivity Sweep (FR-005) | Thresholds (0.5%) are arbitrary; robustness must be demonstrated. | A single threshold analysis cannot prove the anomaly is not an artifact of the chosen cutoff. |
| Synthetic Data Fallback | Verified US sources may be absent. | Without a fallback, the statistical methodology cannot be tested or validated, rendering the project non-executable. |
| Non-Circular Null Model | Fitting NB to observed data absorbs anomalies. | Using theoretical priors or pre-aggregation permutation ensures the null is independent of the signal. |

## Sensitivity Analysis Thresholds (FR-005)

The plan explicitly defines the sensitivity sweep thresholds as:
`{[deferred], [deferred], [deferred], [deferred]}`

This set satisfies FR-005 and replaces any `[deferred]` placeholders. The primary threshold for the main metric (SC-001) is fixed at **[deferred]**.

## Collinearity & Predictor Diagnostics (SC-006)

If the analysis is extended to include regression on covariates (e.g., population density, precinct size) to explore systematic bias:
1.  **VIF Calculation**: The Variance Inflation Factor (VIF) will be calculated for all predictors.
2.  **Threshold**: If VIF > 5, the plan will report the collinearity and describe the relationship descriptively.
3.  **No Independent Claims**: The plan will **not** claim independent predictive effects for collinear variables.
4.  **Scope**: If no regression is performed (pure goodness-of-fit), this step is skipped, and SC-006 is marked as "Not Applicable" in the final report.
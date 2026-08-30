# Implementation Plan: Detecting Statistical Power Drift in Replicated Studies

**Branch**: `001-detect-power-drift` | **Date**: 2026-07-30 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-detect-power-drift/spec.md`

## Summary

This feature implements a statistical pipeline to detect temporal drift in post-hoc statistical power within replication studies. The core approach involves: (1) ingesting replication metadata from verified OSF sources, (2) calculating post-hoc power using standard formulas (Cohen's *d*, odds ratio) with fixed $\alpha=0.05$, (3) calculating **residual power** (power residuals after regressing on N and d) to avoid tautology, (4) fitting a linear mixed-effects model (LMM) `residual_power ~ year + (1|field)` to isolate residual temporal trends, and (5) validating results via non-parametric permutation tests (shuffling year and inputs) and alpha-sensitivity sweeps. The implementation adheres to CPU-only constraints (max a minimal number of cores, limited RAM) and strictly avoids fabricating data or inventing constraints not present in the spec.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `statsmodels` (for LMM), `scipy`, `numpy`, `seaborn`, `matplotlib`, `pyyaml`, `datasets` (HuggingFace), `scikit-learn` (for stratified sampling).  
**Storage**: Local file system (`data/`, `results/`, `code/`). No external database.  
**Testing**: `pytest` (unit tests for power formulas, schema validation).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Data analysis pipeline / CLI script.  
**Performance Goals**: Complete end-to-end analysis (download, clean, model, permute, visualize) within the standard GitHub Actions free-tier limit.  
**Constraints**: CPU-only execution; no GPU; streaming data if dataset > 500MB; strict handling of missing data (log & skip, no crash); random seed pinning for reproducibility.  
**Scale/Scope**: Single dataset (OSF Reproducibility Project subset); A sufficient number of permutations (with a lower fallback count if timeout occurs); 1 LMM fit; alpha-sensitivity points.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and canonical OSF dataset loading. All results traceable to `data/`. **PASS**.
- **II. Verified Accuracy**: Citations in `research.md` restricted to verified URLs (OSF). No external claims without source. **PASS**.
- **III. Data Hygiene**: Raw data downloaded to `data/raw/` with checksums. Derivations (cleaned data, power estimates, residuals) saved to `data/derived/` with new filenames. **PASS**.
- **IV. Single Source of Truth**: All figures/statistics in paper generated from `results/*.json` or `data/derived/*.csv`. No hand-typed numbers. Mechanism: All visualizations are generated programmatically from `results/*.json` files, which are derived directly from `data/derived/`. No manual entry is permitted. **PASS**.
- **V. Versioning Discipline**: Artifacts (code, data, results) will carry content hashes in state file. **PASS**.
- **VI. Power Re-estimation Consistency**: Plan explicitly defines post-hoc power calculation using reported effect size and sample size, ignoring author-reported power. **PASS**.
- **VII. Temporal Drift Modeling Rigor**: Plan mandates LMM with `year` fixed effect + random intercepts on residual power, plus a large number of permutations (with documented fallback). **PASS**.

## Project Structure

### Documentation (this feature)

```text
specs/001-detect-power-drift/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-150-detecting-statistical-power-drift-in-rep/
├── code/
│   ├── __init__.py
│   ├── download_data.py      # Fetches OSF datasets, saves to data/raw/
│   ├── preprocess.py         # Cleans data, calculates power, residuals, logs warnings
│   ├── model_fit.py          # Fits LMM on residuals, runs LRT, saves lmm_final_summary.json
│   ├── robustness.py         # Permutation tests (year & input), sensitivity analysis
│   ├── aggregate.py          # DerSimonian-Laird cross-field aggregation
│   ├── visualize.py          # Generates residual power plots
│   └── requirements.txt      # Pinned dependencies
├── data/
│   ├── raw/                  # Downloaded parquet/CSV files (checksummed)
│   └── derived/
│       ├── cleaned_data.csv  # Filtered, power-calculated
│       └── power_estimates.csv (includes residual_power)
├── results/
│   ├── lmm_final_summary.json
│   ├── permutation_pvalue.json
│   ├── permutation_consistency.json
│   ├── sensitivity_report.json
│   └── plots/
│       └── residual_power_vs_year.png
├── contracts/
│   ├── dataset.schema.yaml
│   ├── lmm_summary.schema.yaml
│   ├── sensitivity_report.schema.yaml
│   └── ... (other schemas)
└── README.md
```

**Structure Decision**: Single-project structure (Option 1) selected. The analysis is a linear pipeline (download -> clean -> model -> validate -> visualize) best served by modular scripts in `code/` rather than a complex web service or multi-repo setup. This minimizes overhead and aligns with CPU-only CI constraints.

## Complexity Tracking

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Residual Power Modeling | Required to avoid tautology (regressing power on its own inputs). The spec requires adjusting for inputs, which is achieved by modeling the *residuals* of power after accounting for N and d. | Regressing `power ~ year + N + d` creates perfect multicollinearity and invalidates the `year` coefficient. |
| Mixed-Effects Model (vs. OLS) | Required by Spec (FR-002) and Constitution Principle VII to account for clustering by `field` and `original_study_id`. | OLS would ignore hierarchical structure, violating the "Temporal Drift Modeling Rigor" principle and inflating Type I error. |
| Permutation Test (10k iters) | Required by Spec (FR-004) and Constitution Principle VII to validate against model misspecification. | Fewer iterations would yield unstable empirical p-values, failing the "Robustness" acceptance criteria. Fallback to [deferred] is only for hard timeout. |
| Sensitivity Sweep | Required by Spec (FR-005) to ensure findings are not alpha-dependent. | Single alpha check (0.05) is insufficient to prove robustness per User Story 2. |
| Cross-Field Aggregation | Required by Spec (FR-006) to generalize findings. | Single-field analysis ignores heterogeneity across disciplines. |
| Input Permutation | Required by Spec (FR-007) to validate against input distribution changes. | Year-only permutation does not test if the drift is driven by input changes. |


## Phase Breakdown

### Phase 0: Data Ingestion & Validation
- **Goal**: Download verified OSF dataset, validate schema (year, effect_size, sample_size, field).
- **Output**: `data/raw/osf_replication.parquet` (checksummed).
- **Risk**: Dataset lacks required columns. **Mitigation**: Halt with error if schema mismatch.

### Phase 1: Preprocessing & Residual Calculation
- **Goal**: Clean data, calculate post-hoc power, then calculate `residual_power` (residuals of power ~ N + d).
- **Output**: `data/derived/power_estimates.csv` (includes `residual_power`).
- **Risk**: Missing data. **Mitigation**: Log and skip rows with missing N or effect_size.

### Phase 2: Primary Model (LMM)
- **Goal**: Fit `residual_power ~ year + (1|field)`. Perform LRT.
- **Output**: `results/lmm_final_summary.json`.
- **Risk**: Convergence failure. **Mitigation**: Simplify random effects (remove `original_study_id` if needed).

### Phase 3: Robustness Checks
- **Goal**: 
  1. Permutation Test (Year): Shuffle `year` labels (10k iters).
  2. Permutation Test (Input): Shuffle `effect_size` and `sample_size` (10k iters).
  3. Sensitivity Analysis: Sweep alpha across a range of low-to-moderate values..
- **Output**: `results/permutation_pvalue.json`, `results/sensitivity_report.json`.
- **Risk**: Timeout. **Mitigation**: Fallback to a sufficient number of permutations, log as "approximate".

### Phase 4: Cross-Field Aggregation (FR-006)
- **Goal**: Calculate field-specific drift slopes. Combine using DerSimonian-Laird inverse-variance weighting.
- **Output**: `results/aggregated_drift.json`.
- **Risk**: Heterogeneity too high. **Mitigation**: Report I-squared statistic; do not force aggregation if I-squared > 75%.

### Phase 5: Input Permutation Validation (FR-007)
- **Goal**: Generate null distribution of drift slopes by shuffling inputs (effect_size, sample_size) while holding year constant. Compare observed slope to null.
- **Output**: `results/input_permutation.json`.
- **Risk**: High variance in null distribution. **Mitigation**: Increase iterations if needed (within time budget).

### Phase 6: Visualization & Reporting
- **Goal**: Generate residual power vs. year plot. Compile final report.
- **Output**: `results/plots/residual_power_vs_year.png`, `results/final_report.md`.
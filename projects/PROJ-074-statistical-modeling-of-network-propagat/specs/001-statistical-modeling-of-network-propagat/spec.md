# Feature Specification: Bayesian Hierarchical Modeling of Misinformation Cascade Size

**Feature Branch**: `001-bayesian-misinformation-cascade`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Statistical Modeling of Network Propagation in Online Misinformation – develop Bayesian hierarchical models to quantify how network topology and user‑susceptibility features predict the size of misinformation cascades."  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑end Modeling Pipeline (Priority: P1)

A researcher wants to run a reproducible end‑to‑end pipeline that ingests raw cascade data, generates network‑and‑user features, fits a Bayesian hierarchical model, and outputs posterior summaries.

**Why this priority**: This story delivers the core scientific value – the ability to answer the research question with a single command, enabling rapid iteration and replication.

**Independent Test**: Execute the pipeline on a small benchmark dataset (e.g., a modest number of cascades) and verify that all output files (features CSV, model trace, posterior summary) are created and pass basic sanity checks.

**Acceptance Scenarios**:

1. **Given** the benchmark dataset is placed in `data/raw/`, **When** the command `run_pipeline.sh --data data/raw/ --out results/` finishes, **Then** a `features.csv`, `model_trace.nc`, and `posterior_summary.csv` exist in `results/` and contain no missing values.  
2. **Given** the pipeline completed successfully, **When** the researcher opens `posterior_summary.csv`, **Then** at least three predictors have a posterior probability > 0.95 of having a non‑zero effect on held‑out validation data.

---

### User Story 2 – Predictive Performance Evaluation (Priority: P2)

A researcher wants to assess how well the fitted model predicts cascade size on held‑out data and whether its prediction intervals are calibrated.

**Why this priority**: Validating predictive performance is essential before the model can be used for intervention planning.

**Independent Test**: Run cross‑validation with an appropriate number of folds on the benchmark dataset and compute coverage of the [deferred] posterior predictive intervals.

**Acceptance Scenarios**:

1. **Given** the cross‑validation script is executed, **When** the resulting `cv_metrics.json` is inspected, **Then** the coverage of the [deferred] intervals is measured against the nominal interval level (e.g., Intervals should have coverage rates approximately corresponding to their nominal level.).

---

### User Story 3 – Collinearity Diagnostics & Reporting (Priority: P3)

A researcher wants an automated report that flags high collinearity among predictors and provides variance‑inflation factors (VIFs).

**Why this priority**: The methodology panel requires explicit handling of predictor collinearity to avoid overstating independent effects.

**Independent Test**: After model fitting, the script `diagnostics.sh` produces `collinearity_report.txt`.

**Acceptance Scenarios**:

1. **Given** the model has been fitted, **When** `collinearity_report.txt` is opened, **Then** any predictor pair with Pearson |r| > 0.8 is listed together with its VIF, and the report advises whether to drop or combine variables.

---

### Edge Cases

- **What happens when a required variable (e.g., user‑susceptibility score) is missing from the input dataset?**  
  The pipeline aborts with a clear error message indicating the missing column and suggests the user verify the dataset schema.  

- **How does the system handle cascades larger than the RAM‑constrained limit (10 000 nodes)?**  
  Cascades exceeding the limit are logged and skipped; a summary `skipped_cascades.log` records their identifiers for later manual inspection.  

- **What if Hamiltonian Monte Carlo fails to converge within the 6‑hour budget?**  
  The training script detects divergent transitions > 5 % and automatically reduces the step size, re‑runs up to three times; if convergence still fails, it exits with a diagnostic report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest raw cascade files (edge list or JSON) from a user‑specified directory and validate that each file contains node identifiers, timestamps, and cascade label. (See US-1)  
- **FR-002**: System MUST compute the following network‑level features for every cascade: node degree distribution moments, clustering coefficient, betweenness centrality, and cascade depth. (See US-1)  
- **FR-003**: System MUST construct a user‑susceptibility score for each participant using historical sharing frequency; the score computation MUST be documented and reproducible. (See US-1)  
- **FR-004**: System MUST fit a Bayesian hierarchical model with cascade size as the outcome, the network and user features as fixed effects, and random intercepts for user ID and message ID. (See US-1)  
- **FR-005**: System MUST perform k-fold cross-validation, compute WAIC/LOO‑CV for model comparison, and output predictive‑interval coverage statistics. (See US-2)  
- **FR-006**: System MUST generate a collinearity diagnostics report that includes pairwise Pearson correlations, VIF values, and recommendations for handling high collinearity. (See US-3)  
- **FR-007**: System MUST log all major steps (data loading, feature extraction, sampling diagnostics, runtime) to a machine‑readable `pipeline.log`. (See US-1)  
- **FR-008**: System MUST respect hardware constraints: ≤ 7 GB RAM usage and ≤ 2 CPU cores during sampling; if limits are exceeded, the process aborts with an informative message. (See US-1)  
- **FR-009**: System MUST output model coefficients, posterior credible intervals, and [deferred] prediction intervals for each cascade in a CSV file. (See US-1)  
- **FR-010**: System MUST include a reproducibility manifest (software versions, random seeds, data hashes) in `manifest.json`. (See US-1)  

*Clarification markers*:

- **FR-003**: System MUST construct a user-susceptibility score for each participant using available historical activity metrics. When per-user historical sharing counts are unavailable in source datasets (e.g., PolitiFact), the system MUST compute a proxy susceptibility score from pre-cascade historical activity metrics (node degree ≥ 2 in the user's historical network, total shares in historical data ≥ 1). The score computation MUST be documented in `susceptibility_method.md` with the exact formula and thresholds used. Pre-cascade activity must be measured from data available before the cascade starts to avoid circularity with the outcome variable.  
- **FR-001**: System MUST ingest raw cascade files (edge list or JSON) from a user-specified directory and validate that each file contains node identifiers, timestamps, and cascade label. All timestamps MUST be normalized to UTC during ingestion, regardless of source dataset format. If timestamps are in local time, the system MUST convert them using timezone metadata or default to UTC with a warning logged to `pipeline.log`. Timestamp validation MUST reject files with mixed timezone formats without explicit conversion rules.  
- **FR-004**: System MUST fit a Bayesian hierarchical model with cascade size as the outcome, the network and user features as fixed effects, and random intercepts for user ID and message ID. When multiple platforms are combined, the system MUST include platform as an additional random intercept level to account for platform-specific variance (≥ 2 platforms). Single-platform analyses MAY omit the platform random effect. This follows standard multi-level modeling practice for heterogeneous data sources to prevent biased fixed-effect estimates.

### Key Entities

- **Cascade**: Represents a single misinformation diffusion event; key attributes – `cascade_id`, `node_list`, `edge_list`, `timestamps`, `size`.  
- **FeatureSet**: Tabular collection of computed network and user attributes for each cascade; columns include `degree_mean`, `clustering_coeff`, `betweenness_mean`, `susceptibility_score`, etc.  
- **ModelOutput**: Stores posterior samples, summary statistics, and predictive intervals; compatible with NetCDF or CSV export.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: At least three predictors achieve a posterior probability > 0.95 of having a non‑zero effect on held‑out validation data, with consistent effect direction across folds (reference: Bayesian credible‑interval criterion tied to predictive performance). (See US-1)  
- **SC-002**: The [deferred] posterior predictive intervals attain coverage measured against the nominal interval level (e.g., [deferred] intervals should have [deferred] coverage) on held‑out test data (reference: calibration benchmark). (See US-2)
- **SC-003**: WAIC of the final hierarchical model improves by [deferred] relative to a baseline linear regression model without random effects (reference: model‑comparison standard). (See US-2)  
- **SC-004**: Total wall‑clock time for fitting the model on the benchmark dataset does not exceed a reasonable timeframe. on a 2‑core, 7 GB RAM VM (reference: hardware budget). (See US-1)  
- **SC-005**: No predictor pair exhibits Pearson |r| > 0.8 without being flagged in the collinearity report (reference: collinearity diagnostic threshold). (See US-3)  
- **SC-006**: All output files pass schema validation (e.g., no missing cascade IDs, numeric columns within plausible ranges) as confirmed by an automated test suite. (See US-1)  

## Assumptions

- The public datasets (PolitiFact fact‑checking network, Stanford SNAP Twitter cascades) contain the necessary variables: node identifiers, timestamps, and enough historical activity to compute user‑susceptibility scores.  
- The Bayesian hierarchical model is observational; therefore, all findings are interpreted as associative, not causal.  
- The researcher has access to a Linux environment with Python 3.10, NumPyro/PyStan, NetworkX, and standard scientific‑Python stack installed.  
- Memory usage estimates assume that cascade trees larger than a predefined threshold are excluded; this threshold is sufficient to keep RAM within acceptable limits for the benchmark dataset.  
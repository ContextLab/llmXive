# Feature Specification: Bayesian Hierarchical Modeling of Misinformation Cascade Size

**Feature Branch**: `001-bayesian-misinformation-cascade`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “Statistical Modeling of Network Propagation in Online Misinformation – develop Bayesian hierarchical models to quantify how network topology and user‑susceptibility features predict the size of misinformation cascades.”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑end Modeling Pipeline (Priority: P1)

A researcher wants to run a reproducible end‑to‑end pipeline that ingests raw cascade data, generates network‑and‑user features, fits a Bayesian hierarchical model, and outputs posterior summaries.

**Why this priority**: This story delivers the core scientific value – the ability to answer the research question with a single command, enabling rapid iteration and replication.

**Independent Test**: Execute the pipeline on a small benchmark dataset (e.g., a modest number of cascades) and verify that all output files (features CSV, model trace, posterior summary) are created and pass basic sanity checks.

**Acceptance Scenarios**:

1. **Given** the benchmark dataset is placed in `data/raw/`, **When** the command `run_pipeline.sh --data data/raw/ --out results/` finishes, **Then** a `features.csv`, `model_trace.nc`, and `posterior_summary.csv` exist in `results/` and contain no missing values.  
2. **Given** the pipeline completed successfully, **When** the researcher opens `posterior_summary.csv`, **Then** at least three predictors have a posterior probability > 0.95 of having a non‑zero effect.

---

### User Story 2 – Predictive Performance Evaluation (Priority: P2)

A researcher wants to assess how well the fitted model predicts cascade size on held‑out data and whether its prediction intervals are calibrated.

**Why this priority**: Validating predictive performance is essential before the model can be used for intervention planning.

**Independent Test**: Run cross‑validation with an appropriate number of folds on the benchmark dataset and compute coverage of the [deferred] posterior predictive intervals.

**Acceptance Scenarios**:

1. **Given** the cross‑validation script is executed, **When** the resulting `cv_metrics.json` is inspected, **Then** the coverage of the [deferred] intervals lies between 0.85 and 0.90.

---

### User Story 3 – Collinearity Diagnostics & Reporting (Priority: P3)

A researcher wants an automated report that flags high collinearity among predictors and provides variance‑inflation factors (VIFs).

**Why this priority**: The methodology panel requires explicit handling of predictor collinearity to avoid overstating independent effects.

**Independent Test**: After model fitting, the script `diagnostics.sh` produces `collinearity_report.txt`.

**Acceptance Scenarios**:

1. **Given** the model has been fitted, **When** `collinearity_report.txt` is opened, **Then** any predictor pair with Pearson |r| > 0.8 is listed together with its VIF, and the report advises whether to drop or combine variables.

---

### Edge Cases

- **What happens when a required variable (e.g., user‑susceptibility score) is missing from the input dataset?**  
  The pipeline aborts with a clear error message indicating the missing column and suggests the user verify the dataset schema.  

- **How does the system handle cascades larger than the RAM‑constrained limit (10 000 nodes)?**  
  Cascades exceeding the limit are logged and skipped; a summary `skipped_cascades.log` records their identifiers for later manual inspection.  

- **What if Hamiltonian Monte Carlo fails to converge within the 6‑hour budget?**  
  The training script detects divergent transitions > 5 % and automatically reduces the step size, re‑runs up to three times; if convergence still fails, it exits with a diagnostic report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest raw cascade files (edge list or JSON) from a user‑specified directory and validate that each file contains node identifiers, timestamps, and cascade label.  
- **FR-002**: System MUST compute the following network‑level features for every cascade: node degree distribution moments, clustering coefficient, betweenness centrality, and cascade depth.  
- **FR-003**: System MUST construct a user‑susceptibility score for each participant using historical sharing frequency; the score computation MUST be documented and reproducible.  
- **FR-004**: System MUST fit a Bayesian hierarchical model with cascade size as the outcome, the network and user features as fixed effects, and random intercepts for user ID and message ID.  
- **FR-005**: System MUST perform 5‑fold cross‑validation, compute WAIC/LOO‑CV for model comparison, and output predictive‑interval coverage statistics.  
- **FR-006**: System MUST generate a collinearity diagnostics report that includes pairwise Pearson correlations, VIF values, and recommendations for handling high collinearity.  
- **FR-007**: System MUST log all major steps (data loading, feature extraction, sampling diagnostics, runtime) to a machine‑readable `pipeline.log`.  
- **FR-008**: System MUST respect hardware constraints: ≤ 7 GB RAM usage and ≤ 2 CPU cores during sampling; if limits are exceeded, the process aborts with an informative message.  
- **FR-009**: System MUST output model coefficients, posterior credible intervals, and [deferred] prediction intervals for each cascade in a CSV file.
- **FR-010**: System MUST include a reproducibility manifest (software versions, random seeds, data hashes) in `manifest.json`.

*Clarification markers*:

- **FR-003**: [NEEDS CLARIFICATION: does the PolitiFact fact‑checking dataset include per‑user historical sharing counts required for the susceptibility score?]  
- **FR-001**: [NEEDS CLARIFICATION: are cascade timestamps guaranteed to be in UTC across all source datasets?]  
- **FR-004**: [NEEDS CLARIFICATION: should the hierarchical random effects also include a level for platform (e.g., Twitter vs. Facebook) if multiple platforms are combined?]

### Key Entities

- **Cascade**: Represents a single misinformation diffusion event; key attributes – `cascade_id`, `node_list`, `edge_list`, `timestamps`, `size`.  
- **FeatureSet**: Tabular collection of computed network and user attributes for each cascade; columns include `degree_mean`, `clustering_coeff`, `betweenness_mean`, `susceptibility_score`, `sentiment_score`, etc.  
- **ModelOutput**: Stores posterior samples, summary statistics, and predictive intervals; compatible with NetCDF or CSV export.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least three predictors achieve a posterior probability > 0.95 of having a non‑zero effect (reference: Bayesian credible‑interval criterion).  
- **SC-002**: The [deferred] posterior predictive intervals attain coverage between 0.85 and 0.90 on held‑out test data (reference: calibration benchmark).
- **SC-03**: WAIC of the final hierarchical model improves by ≥ 5 % relative to a baseline linear regression model without random effects (reference: model‑comparison standard).  
- **SC-004**: Total wall‑clock time for fitting the model on the benchmark dataset does not exceed 6 hours on a 2‑core, 7 GB RAM VM (reference: hardware budget).  
- **SC-005**: No predictor pair exhibits Pearson |r| > 0.8 without being flagged in the collinearity report (reference: collinearity diagnostic threshold).  
- **SC-006**: All output files pass schema validation (e.g., no missing cascade IDs, numeric columns within plausible ranges) as confirmed by an automated test suite.  

## Assumptions

- The public datasets (PolitiFact fact‑checking network, Stanford SNAP Twitter cascades) contain the necessary variables: node identifiers, timestamps, and enough historical activity to compute user‑susceptibility scores.  
- Sentiment scores are derived using a validated lexicon‑based tool (e.g., VADER) whose validity for short social‑media messages is established in the literature.  
- The Bayesian hierarchical model is observational; therefore, all findings are interpreted as associative, not causal.  
- The researcher has access to a Linux environment with Python 3.10, NumPyro/PyStan, NetworkX, and standard scientific‑Python stack installed.  
- Memory usage estimates assume that cascade trees larger than 10 000 nodes are excluded; this threshold is sufficient to keep RAM under 7 GB for the benchmark dataset.  

---

# Feature Specification: The Impact of Predictive Coding Errors on Subjective Time Perception

**Feature Branch**: `001-predictive-coding-time-perception`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Does manipulating the predictability of sequential stimuli alter participants' duration estimates, and do larger prediction errors correlate with overestimation of elapsed time?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher downloads existing time perception datasets from OpenML and HuggingFace Datasets using dataset identifiers (OpenML dataset IDs or HuggingFace repository paths), filters them for studies using sequential stimuli with known predictability manipulations, and extracts duration estimates, stimulus timing, and condition labels into standardized CSV format. If explicit predictability metrics are missing, the researcher reconstructs them from raw stimulus sequences using a first-order Markov model to calculate surprisal.

**Why this priority**: Without valid data, no analysis can proceed. This is the foundational step that determines whether the research question can be answered at all.

**Independent Test**: Can be fully tested by executing the data download and preprocessing scripts and verifying that output CSV files contain the required columns (duration estimate, stimulus timing, condition label, participant ID, surprisal metric) with ≥100 valid rows.

**Acceptance Scenarios**:

1. **Given** the OpenML dataset IDs or HuggingFace repository paths are documented, **When** the download script executes, **Then** all specified datasets are retrieved and stored in `data/raw/` with checksums verified
2. **Given** raw dataset files exist, **When** the preprocessing script executes, **Then** standardized CSV files are generated in `data/processed/` containing duration estimates and surprisal metrics for ≥100 trials
3. **Given** a dataset lacks required variables (duration estimates OR raw stimulus sequences), **When** the filtering step runs, **Then** the dataset is excluded with a logged warning and the exclusion reason is documented in `data/README.md`
4. **Given** a dataset has raw sequences but no explicit metrics, **When** the preprocessing script executes, **Then** surprisal metrics are computed using a first-order Markov model and added to the output CSV

---

### User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

The researcher fits linear mixed-effects models with duration estimate as outcome, surprisal (continuous) as the fixed effect, and participant ID as a random intercept. The model MUST control for potential confounders (sequence length, stimulus modality). The researcher performs sensitivity analysis to determine the minimum detectable effect (MDE) for the observed sample size at [deferred] power.

**Why this priority**: This delivers the core research answer. Without valid statistical modeling, the hypothesis cannot be tested even if data exists.

**Independent Test**: Can be fully tested by running the analysis script on a sample dataset and verifying that model outputs include effect sizes (Cohen's d), 95% confidence intervals, p-values for the surprisal main effect, and the calculated MDE.

**Acceptance Scenarios**:

1. **Given** preprocessed data with duration estimates and surprisal metrics, **When** the statistical modeling script executes, **Then** linear mixed-effects models converge successfully and output includes fixed effect coefficients, standard errors, and participant random intercept variance
2. **Given** continuous surprisal metrics, **When** hypothesis testing runs, **Then** the primary analysis treats surprisal as a continuous predictor (not dichotomized)
3. **Given** any dataset sample size, **When** sensitivity analysis runs, **Then** the Minimum Detectable Effect (MDE) for [deferred] power is calculated and reported, regardless of whether the observed effect reaches it

---

### User Story 3 - Visualization and Reproducible Reporting (Priority: P3)

The researcher generates forest plots of condition effects and residual diagnostic plots, and stores all code and analysis scripts in `analysis/` with pinned requirements and a Dockerfile for environment consistency.

**Why this priority**: This enables peer review and replication. While not required for initial results, it is essential for scientific credibility and project completion.

**Independent Test**: Can be fully tested by executing the visualization script and verifying that output plots (forest plot, residual diagnostics) are generated in `figures/` and that the Dockerfile builds successfully.

**Acceptance Scenarios**:

1. **Given** statistical model outputs exist, **When** the visualization script executes, **Then** forest plots of condition effects and residual diagnostic plots are generated in `figures/` with ≥300 DPI resolution
2. **Given** analysis scripts are complete, **When** the Dockerfile builds, **Then** a reproducible environment is created that executes all analysis scripts without modification
3. **Given** the project is complete, **When** a reviewer runs the analysis from scratch, **Then** all results are reproduced within 6 hours on a CPU-only runner with ≤7 GB RAM

---

### Edge Cases

- What happens when a dataset lacks prediction error metrics (e.g., only has raw stimulus sequences without transition probabilities)? → The system SHALL compute surprisal from raw sequences using a first-order Markov model. If raw sequences are unavailable, the dataset is excluded with a documented reason in `data/README.md`.
- How does the system handle non-normal duration estimate distributions? → Wilcoxon signed-rank test is applied instead of paired t-tests, with normality verified via Shapiro-Wilk (α=0.05)
- What happens when the linear mixed-effects model fails to converge? → The model is re-fitted with simplified random effects structure (random intercept only) and the simplification is documented
- How does the system handle datasets exceeding 7 GB RAM? → Data is processed in chunks of ≤500 MB with streaming aggregation to stay within memory limits

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download datasets from OpenML and HuggingFace Datasets using explicit dataset identifiers (OpenML IDs or HuggingFace paths) documented in `data/README.md` (See US-1)
- **FR-002**: System MUST filter datasets to retain only studies using sequential stimuli with known predictability manipulations or raw stimulus sequences (See US-1)
- **FR-003**: System MUST compute 'surprisal' (negative log probability of the observed stimulus given the sequence history) for each trial, assuming a first-order Markov learner, if explicit metrics are missing (See US-1)
- **FR-004**: System MUST fit linear mixed-effects models with duration estimate as outcome, surprisal (continuous) as fixed effect, participant ID as random intercept, AND sequence length and stimulus modality as covariates (See US-2)
- **FR-005**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) when >1 hypothesis test is run (See US-2)
- **FR-006**: System MUST compute Cohen's d effect sizes with 95% confidence intervals for main effects (See US-2)
- **FR-007**: System MUST perform sensitivity analysis to calculate the Minimum Detectable Effect (MDE) for power=0.80 given the observed sample size and variance. If the observed effect is smaller than the MDE, the system MUST report this as a limitation (See US-2)
- **FR-008**: System MUST generate forest plots of condition effects and residual diagnostic plots using matplotlib/seaborn (See US-3)
- **FR-009**: System MUST parallelize bootstrap resampling across multiple CPU cores using joblib to complete within 6 hours (See US-3)

### Key Entities *(include if feature involves data)*

- **Trial**: Single stimulus presentation with attributes (stimulus sequence, surprisal metric, duration estimate, participant ID)
- **Participant**: Individual subject with attributes (participant ID, condition assignments, duration estimates across trials)
- **Dataset**: Source data collection with attributes (source URL, identifier, number of trials, number of participants, variable availability)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset variable coverage is measured against the requirement that EVERY predictor (surprisal), outcome (duration estimates), and covariate (stimulus timing) must be present (See US-1)
- **SC-002**: Model convergence rate is measured against the requirement that ≥90% of linear mixed-effects models (per-dataset model fits) must converge without simplification (See US-2)
- **SC-003**: Multiple-comparison correction is measured against the requirement that family-wise error rate is controlled at α≤0.05 when >1 hypothesis test is run (See US-2)
- **SC-004**: Computational feasibility is measured against the constraint of ≤6 hours total runtime on 2 CPU cores with ≤7 GB RAM (See US-3)
- **SC-005**: Sensitivity adequacy is measured against the requirement that the Minimum Detectable Effect (MDE) for [deferred] power is reported for every dataset analyzed (See US-2)
- **SC-006**: Reproducibility is measured against the requirement that a reviewer can reproduce all results from scratch within 6 hours on CPU-only infrastructure (See US-3)

---

## Assumptions

- **Assumption 1**: OpenML and HuggingFace Datasets contain at least one dataset with sequential stimuli and participant duration estimates. If explicit predictability metrics (transition probabilities or entropy) are missing, the system SHALL compute 'surprisal' algorithmically from raw stimulus sequences using a first-order Markov model (Shannon entropy of the transition). This computation is bounded to ≤5000 trials per dataset to maintain the 6-hour runtime constraint. If raw sequences are unavailable, the dataset is excluded with a logged reason in `data/README.md`. Note: Surprisal measures stimulus uncertainty, not the latent participant prediction error; the analysis tests the association between stimulus surprisal and duration estimates.
- **Assumption 2**: All time perception instruments used are validated (e.g., temporal bisection task with citable validation) — if the dataset uses non-validated measures, this is flagged in `data/README.md`
- **Assumption 3**: Surprisal metrics are computationally tractable on CPU within the 6-hour budget — if the sequence length or dataset size exceeds this, a sampling strategy (≤5000 trials) is applied
- **Assumption 4**: The analysis is observational (no random assignment to predictability conditions within participants); findings are framed as ASSOCIATIONAL, not causal (no moderation/mediation claims without identification strategy)
- **Assumption 5**: If surprisal metrics are definitionally related (e.g., bounded by sequence length), collinearity diagnostics (VIF≥5) are required and joint relationships are described descriptively rather than claiming independent predictive effects
- **Assumption 6**: No GPU/CUDA/accelerators are required; all methods use default precision CPU-only execution (load_in_8bit, bitsandbytes, device_map="cuda" are explicitly excluded)
- **Assumption 7**: If any decision cutoffs are introduced (e.g., high vs. low surprisal for secondary analysis), they carry a one-line justification naming community-standard basis AND require sensitivity analysis sweeping the cutoff over a range of low thresholds to report how false-positive/false-negative rates vary
- **Assumption 8**: The total dataset size after preprocessing fits within a manageable RAM footprint and disk storage capacity.; if not, additional sampling/subsetting is applied and documented in `data/README.md`
- **Assumption 9**: Data processing is performed in chunks of ≤500 MB to stay within 7 GB RAM limits (implementation constraint)
- **Assumption 10**: Bootstrap resampling is parallelized across 2 CPU cores to complete within 6 hours (implementation constraint)
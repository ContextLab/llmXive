# Feature Specification: The Impact of Predictive Coding Errors on Subjective Time Perception

**Feature Branch**: `001-predictive-coding-time-perception`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Does manipulating the predictability of sequential stimuli alter participants' duration estimates, and do larger prediction errors correlate with overestimation of elapsed time?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher downloads existing time perception datasets from OpenML and HuggingFace Datasets, filters them for studies using sequential stimuli with known predictability manipulations, and extracts duration estimates, stimulus timing, and condition labels into standardized CSV format.

**Why this priority**: Without valid data, no analysis can proceed. This is the foundational step that determines whether the research question can be answered at all.

**Independent Test**: Can be fully tested by executing the data download and preprocessing scripts and verifying that output CSV files contain the required columns (duration estimate, stimulus timing, condition label, participant ID) with ≥100 valid rows.

**Acceptance Scenarios**:

1. **Given** the OpenML and HuggingFace dataset DOIs are documented, **When** the download script executes, **Then** all specified datasets are retrieved and stored in `data/raw/` with checksums verified
2. **Given** raw dataset files exist, **When** the preprocessing script executes, **Then** standardized CSV files are generated in `data/processed/` containing duration estimates and predictability condition labels for ≥100 trials
3. **Given** a dataset lacks required variables (duration estimates OR predictability labels), **When** the filtering step runs, **Then** the dataset is excluded with a logged warning and the exclusion reason is documented in `data/README.md`

---

### User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

The researcher computes prediction error metrics (entropy, transition probability) for each trial, fits linear mixed-effects models with duration estimate as outcome and predictability level as fixed effect (participant ID as random intercept), and applies paired t-tests or Wilcoxon signed-rank tests comparing high vs. low predictability conditions.

**Why this priority**: This delivers the core research answer. Without valid statistical modeling, the hypothesis cannot be tested even if data exists.

**Independent Test**: Can be fully tested by running the analysis script on a sample dataset and verifying that model outputs include effect sizes (Cohen's d), 95% confidence intervals, and p-values for the predictability main effect.

**Acceptance Scenarios**:

1. **Given** preprocessed data with duration estimates and predictability labels, **When** the statistical modeling script executes, **Then** linear mixed-effects models converge successfully and output includes fixed effect coefficients, standard errors, and participant random intercept variance
2. **Given** high vs. low predictability condition labels, **When** hypothesis testing runs, **Then** paired t-tests (or Wilcoxon signed-rank for non-normal data) produce p-values with multiple-comparison correction applied
3. **Given** ≥30 participants per condition, **When** power analysis runs, **Then** post-hoc power ≥0.80 is confirmed or the limitation is documented

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

- What happens when a dataset lacks prediction error metrics (e.g., only has raw stimulus sequences without transition probabilities)? → The dataset is excluded with a documented reason in `data/README.md`
- How does the system handle non-normal duration estimate distributions? → Wilcoxon signed-rank test is applied instead of paired t-tests, with normality verified via Shapiro-Wilk (α=0.05)
- What happens when the linear mixed-effects model fails to converge? → The model is re-fitted with simplified random effects structure (random intercept only) and the simplification is documented
- How does the system handle datasets exceeding 7 GB RAM? → Data is processed in chunks of ≤500 MB with streaming aggregation to stay within memory limits

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download datasets from OpenML and HuggingFace Datasets using explicit DOIs documented in `data/README.md` (See US-1)
- **FR-002**: System MUST filter datasets to retain only studies using sequential stimuli with known predictability manipulations (e.g., transition probabilities, entropy) (See US-1)
- **FR-003**: System MUST compute prediction error metrics (entropy, transition probability) for each trial based on stimulus patterns (See US-2)
- **FR-004**: System MUST fit linear mixed-effects models with duration estimate as outcome, predictability level as fixed effect, and participant ID as random intercept (See US-2)
- **FR-005**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) when >1 hypothesis test is run (See US-2)
- **FR-006**: System MUST compute Cohen's d effect sizes with 95% confidence intervals for main effects (See US-2)
- **FR-007**: System MUST perform post-hoc power analysis with statsmodels.stats.power to assess whether sample sizes (N≥30 per condition) provide adequate power (≥0.80) (See US-2)
- **FR-008**: System MUST generate forest plots of condition effects and residual diagnostic plots using matplotlib/seaborn (See US-3)
- **FR-009**: System MUST process datasets in chunks ≤500 MB to stay within 7 GB RAM (See US-3)
- **FR-010**: System MUST parallelize bootstrap resampling across 2 CPU cores using joblib to complete within 6 hours (See US-3)

### Key Entities *(include if feature involves data)*

- **Trial**: Single stimulus presentation with attributes (stimulus sequence, predictability level, duration estimate, participant ID)
- **Participant**: Individual subject with attributes (participant ID, condition assignments, duration estimates across trials)
- **Dataset**: Source data collection with attributes (source URL, DOI, number of trials, number of participants, variable availability)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset variable coverage is measured against the requirement that EVERY predictor (predictability metrics), outcome (duration estimates), and covariate (stimulus timing) must be present (See US-1)
- **SC-002**: Model convergence rate is measured against the requirement that ≥90% of linear mixed-effects models must converge without simplification (See US-2)
- **SC-003**: Multiple-comparison correction is measured against the requirement that family-wise error rate is controlled at α≤0.05 when >1 hypothesis test is run (See US-2)
- **SC-004**: Computational feasibility is measured against the constraint of ≤6 hours total runtime on 2 CPU cores with ≤7 GB RAM (See US-3)
- **SC-005**: Power adequacy is measured against the requirement that post-hoc power ≥0.80 for N≥30 per condition (See US-2)
- **SC-006**: Reproducibility is measured against the requirement that a reviewer can reproduce all results from scratch within 6 hours on CPU-only infrastructure (See US-3)

---

## Assumptions

- **Assumption 1**: OpenML and HuggingFace Datasets contain at least one dataset with sequential stimuli, known predictability manipulations (transition probabilities or entropy), and participant duration estimates (if not, [NEEDS CLARIFICATION: does the target dataset contain prediction error metrics?])
- **Assumption 2**: All time perception instruments used are validated (e.g., temporal bisection task with citable validation) — if the dataset uses non-validated measures, this is flagged in `data/README.md`
- **Assumption 3**: Predictability metrics (entropy, transition probability) are computationally tractable on CPU within the 6-hour budget — if the sequence length or dataset size exceeds this, a sampling strategy (≤5000 trials) is applied
- **Assumption 4**: The analysis is observational (no random assignment to predictability conditions within participants); findings are framed as ASSOCIATIONAL, not causal (no moderation/mediation claims without identification strategy)
- **Assumption 5**: If predictability metrics are definitionally related (e.g., entropy bounded by sequence length), collinearity diagnostics (VIF≥5) are required and joint relationships are described descriptively rather than claiming independent predictive effects
- **Assumption 6**: No GPU/CUDA/accelerators are required; all methods use default precision CPU-only execution (load_in_8bit, bitsandbytes, device_map="cuda" are explicitly excluded)
- **Assumption 7**: If any decision cutoffs are introduced (e.g., high vs. low predictability threshold), they carry a one-line justification naming community-standard basis AND require sensitivity analysis sweeping the cutoff over {0.01, 0.05, 0.1} to report how false-positive/false-negative rates vary
- **Assumption 8**: The total dataset size after preprocessing fits within ~7 GB RAM / ~14 GB disk; if not, additional sampling/subsetting is applied and documented in `data/README.md`

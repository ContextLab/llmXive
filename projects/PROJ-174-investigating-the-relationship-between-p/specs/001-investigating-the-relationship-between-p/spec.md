# Feature Specification: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

**Feature Branch**: `001-pupil-dilation-cognitive-load`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "How does task‑evoked pupil dilation quantitatively track moment‑by‑moment cognitive load during visual‑search tasks, and can it serve as a real‑time, non‑invasive indicator of search difficulty?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Trial‑wise Pupil‑Load Correlations (Priority: P1)

A researcher wants to load a public eye‑tracking visual‑search dataset, extract pupil‑diameter features, compute trial‑wise load proxies (search time, target salience, fixation count), and obtain correlation statistics between pupil metrics and each load proxy.

**Why this priority**: Establishes the core empirical relationship that underpins the whole project; without these correlations the later modeling and classification steps have no foundation.

**Independent Test**: Run the preprocessing and feature‑extraction pipeline on a single dataset and verify that the output CSV contains the required columns and that Pearson‑r values are produced for each proxy.

**Acceptance Scenarios**:
1. **Given** a downloaded OpenNeuro visual‑search dataset, **When** the pipeline is executed, **Then** a results file reports Pearson‑r ≥ 0.0 for each of the three load proxies with corresponding p‑values.
2. **Given** a dataset missing the "target salience" column, **When** the pipeline reaches the load‑metric construction step, **Then** it logs a clear `WARNING: Target salience missing; skipping proxy` and skips that proxy while still completing the others.

---

### User Story 2 – Fit Linear Mixed‑Effects Model (Priority: P2)

A researcher wants to fit a linear mixed‑effects (LME) model that predicts a chosen pupil metric (e.g., peak dilation) from the three load proxies while accounting for subject‑level random intercepts, and to test the significance of each fixed effect.

**Why this priority**: Provides a statistically rigorous test of the unique contribution of each load predictor, addressing potential collinearity and subject variability.

**Independent Test**: Execute the LME fitting script on the pre‑processed data and verify that model summary output includes fixed‑effect coefficients, standard errors, and p‑values, and that a likelihood‑ratio test comparing nested models is reported.

**Acceptance Scenarios**:
1. **Given** the pre‑processed trial‑level CSV, **When** the LME script runs, **Then** it produces a model file where each fixed effect has a reported p‑value and the overall model fit passes a likelihood‑ratio test at α = 0.05.

---

### User Story 3 – Simulated Real‑Time Load Classification Prototype (Priority: P3)

A researcher wants to deploy a sliding‑window logistic‑regression classifier that updates every 200 ms using extracted pupil features, simulating real-time processing on historical data, and to evaluate its ability to distinguish high‑ vs. low‑load trials on a held‑out subset.

**Why this priority**: Demonstrates the practical utility of pupil‑based load estimation for adaptive interfaces, moving from offline analysis to a proof‑of‑concept for online load detection.

**Independent Test**: Run the classifier on a reserved test set and compute classification metrics; the test passes if the system successfully reports accuracy and AUC metrics.

**Acceptance Scenarios**:
1. **Given** a held‑out set of trials labeled by median split of load proxy, **When** the classifier processes the data, **Then** it outputs a confusion matrix with reported accuracy and ROC‑AUC values.

---

### Edge Cases

- **Missing pupil samples due to prolonged blink**: The pipeline must detect trials where > 30% of pupil samples are missing after interpolation and exclude them from analysis, logging the exclusion count.
- **Corrupted timestamps or non‑monotonic time series**: The preprocessing step must validate timestamp ordering; if violations are found, the affected trial is dropped with a warning.
- **Insufficient number of trials per subject (< 20)**: The LME fitting script must issue a note and either aggregate across subjects or abort with a clear message if a subject has < 20 trials, ensuring sufficient degrees of freedom for random intercept estimation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest raw eye‑tracking files (e.g., .edf, .csv) from OpenNeuro or OSF and convert them to a uniform CSV format containing `timestamp`, `x`, `y`, and `pupil_diameter`. *(See US-1)*
- **FR-002**: System MUST apply blink interpolation and a low‑pass filter (cut‑off ≤ 4 Hz) to the pupil‑diameter signal, preserving signal integrity for downstream analysis. *(See US-1)*
- **FR-003**: System MUST compute trial‑wise load proxies: (a) search time, (b) target salience (computed on-the-fly from stimulus metadata if not provided, using dispersion-based fixation detector logic), and (c) total fixation count. *(See US-1)*
- **FR-004**: System MUST calculate Pearson correlation coefficients (with two‑tailed p‑values) between each pupil metric (peak, mean, temporally quantized distribution) and each load proxy (distinguishing between stimulus properties like salience and behavioral measures like search time), and store the results in a summary CSV. *(See US-1)*
- **FR-005**: System MUST fit a linear mixed‑effects model `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)` using `statsmodels` or `lme4`‑compatible Python library, and output fixed‑effect estimates, standard errors, p‑values, and a likelihood‑ratio test for each predictor. *(See US-2)*
- **FR-006**: System MUST implement a sliding‑window logistic‑regression classifier that updates every 200 ms, using the three pupil features as inputs, and output a real‑time load probability per trial. *(See US-3)*
- **FR-007**: System MUST evaluate the classifier on a held‑out test set and report accuracy, precision, recall, and ROC‑AUC. *(See US-3)*
- **FR-008**: System MUST log all preprocessing exclusions (e.g., excessive blink loss, timestamp errors) and provide a final quality‑report CSV summarizing counts per exclusion type. *(See Edge Cases)*
- **FR-009**: System MUST perform a sensitivity analysis sweeping the classifier's decision probability threshold over the set {0.01, 0.05, 0.10} (standard range for pupillometry effect sizes) and report how accuracy and AUC vary. *(Methodological soundness – Threshold justification & sensitivity)*
- **FR-010**: System MUST apply a multiple‑comparison correction (Bonferroni) to the set of correlation tests (3 pupil metrics × 3 load proxies) and report adjusted p‑values. *(Methodological soundness – Multiplicity & power)*
- **FR-011**: System MUST validate the classifier against an independent ground truth (e.g., secondary task performance or subjective rating) if available; otherwise, it MUST explicitly document that the ground truth is derived from the search-time median split and report this limitation. *(Scientific soundness – Ground truth independence)*

### Key Entities

- **Dataset**: Represents a collection of eye‑tracking trials; key attributes include `subject_id`, `trial_id`, `timestamp`, `pupil_diameter`, `x`, `y`, `search_time`, `target_salience`, `fixation_count`.
- **ModelResult**: Stores outputs from the LME model and classifier evaluation, including coefficients, p‑values, accuracy, ROC‑AUC, and sensitivity‑analysis tables.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pearson correlation between peak pupil dilation and load proxies must be computed and reported with p‑values and significance status (significant or not) after Bonferroni correction. *(Supports US-1)*
- **SC-002**: In the linear mixed‑effects model, fixed‑effect estimates, standard errors, and p‑values must be reported for each predictor. *(Supports US-2)*
- **SC-003**: The real‑time classifier evaluation must report accuracy and ROC‑AUC metrics on the held‑out test set. *(Supports US-3)*
- **SC-004**: Sensitivity analysis must show that classification performance does not drop below a [deferred] relative decrease for any of the three threshold values, indicating stability of the chosen cutoff. *(Methodological soundness – Threshold justification & sensitivity)*
- **SC-005**: Whole pipeline (preprocessing → modeling → classification) must complete on a GitHub Actions free‑tier runner within 5 hours and consume ≤ 6 GB RAM, confirming compute feasibility. *(Compute feasibility)*

## Assumptions

- The OpenNeuro datasets (e.g., ds001734, ds002642) may contain **target salience** metadata; if absent, the pipeline will compute it on-the-fly as defined in FR-003.
- Pupil‑diameter measurements are recorded in millimeters and have been calibrated by the original experimenters; no additional hardware calibration is required.
- The chosen low‑pass filter (≤ 4 Hz) is sufficient to remove high‑frequency noise while preserving task‑evoked dilation dynamics (standard in pupillometry literature).
- Logistic regression with L2 regularization is an adequate model for real‑time classification; more complex models (e.g., deep nets) are excluded due to CPU‑only constraints.
- All statistical analyses assume **associational** inference because the datasets are observational; no causal language will be used in reporting.

---

*All functional requirements and success criteria explicitly cite the user story they serve, ensuring traceability for review.*
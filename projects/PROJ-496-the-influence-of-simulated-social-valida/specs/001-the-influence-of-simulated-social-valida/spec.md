# Feature Specification: The Influence of Simulated Social Validation on Neural Responses to Novel Information

**Feature Branch**: main‑feature‑sim‑social‑validation  
**Created**: 2026‑07‑06  
**Status**: Draft  
**Input**: User description: “How does simulated social validation (text‑based feedback) compare to real‑world social validation in eliciting neural responses (e.g., P300 amplitude) during social cognition tasks, and does this relationship vary with individual differences in social anxiety?”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Dataset Discovery & Eligibility Check (Priority: P1)

A researcher needs to locate a publicly available EEG dataset that contains (a) a social‑feedback manipulation (simulated vs. real validation) and (b) individual‑difference measures of social anxiety.

**Why this priority**: Without a suitable dataset the entire analysis cannot proceed; this is the gating step for the project.

**Independent Test**: Run the dataset‑search script on OpenNeuro/PhysioNet with the prescribed keywords and verify that the returned list includes at least one dataset meeting both criteria, OR identify two separate datasets (one simulated, one real) that can be combined via meta-analysis.

**Acceptance Scenarios**:

1. **Given** the search script is executed with keywords “social”, “feedback”, “validation”, “anxiety”, **When** the script finishes, **Then** it outputs a CSV file containing at least one entry whose metadata indicates (i) a social‑feedback task and (ii) a completed social‑anxiety questionnaire.
2. **Given** the script finds no single dataset meeting both criteria, **When** the researcher reviews the log, **Then** the script outputs a list of two separate eligible datasets (one for simulated, one for real validation) and flags them for meta-analytic combination.
3. **Given** the script finds no eligible datasets, **When** the researcher reviews the log, **Then** the script reports a clear “No eligible datasets found” message and suggests alternative keyword combinations or a new data collection plan.

### User Story 2 – EEG Pre‑processing & P300 Extraction (Priority: P2)

A researcher must preprocess the raw EEG files and extract P300 amplitude and latency for each trial, separately for simulated‑validation and real‑validation conditions.

**Why this priority**: Accurate ERP extraction is essential for valid statistical inference; errors here would invalidate downstream results.

**Independent Test**: Execute the preprocessing pipeline on a sample of 20 participants and confirm that (a) the number of retained epochs per condition meets the minimum trial count and (b) the resulting event-related potential amplitudes fall within the physiologically plausible range.

**Acceptance Scenarios**:

1. **Given** raw .edf files and a configuration file, **When** the pipeline runs, **Then** it produces a tidy CSV with columns `subject_id`, `condition`, `p300_amplitude`, `p300_latency` and logs the number of rejected epochs (< 20 % per condition).
2. **Given** an epoch where ocular artifacts were not removed, **When** the ICA step is applied, **Then** the pipeline flags the epoch and excludes it from the final CSV.

### User Story 3 – Statistical Modeling & Sensitivity Analysis (Priority: P3)

A researcher needs to fit a mixed‑effects regression testing (a) the main effect of validation type on P300 amplitude and (b) moderation by social‑anxiety scores, while controlling for multiple comparisons and reporting sensitivity to the artifact rejection thresholds.

**Why this priority**: This delivers the core empirical answer to the research question and satisfies methodological rigor requirements.

**Independent Test**: Run the analysis script on the full cleaned dataset and verify that (a) the model converges, (b) p‑values are corrected using the Holm‑Bonferroni method, and (c) a sensitivity sweep over artifact-rejection thresholds ranging from ±75 µV to ±150 µV is exported.

**Acceptance Scenarios**:

1. **Given** the CSV of P300 measures and anxiety scores, **When** the mixed‑effects model is executed, **Then** it outputs a table with fixed‑effect estimates, Holm‑adjusted p‑values, and Cohen’s d effect sizes for both main and interaction terms.
2. **Given** the sensitivity sweep, **When** the results are plotted, **Then** the figure shows that the direction and significance of the interaction remain stable across all three artifact-rejection thresholds.

### Edge Cases

- **Missing anxiety measure**: If a selected dataset lacks a validated social‑anxiety questionnaire, the pipeline aborts with a clear error and logs the dataset ID for manual review.  
- **Insufficient trials**: If any participant has < 30 valid trials in a condition, that participant is excluded and a warning is emitted indicating the number excluded.  
- **Artifact‑heavy recordings**: If > 40 % of epochs are rejected for a participant, the script flags the participant as “low‑quality data” and removes them from the final analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST search OpenNeuro and PhysioNet for EEG datasets using the keywords “social”, “feedback”, “validation”, and “anxiety”, and output a CSV of candidate datasets. If no single dataset contains both simulated and real validation conditions, the system MUST identify separate datasets for each condition to enable meta-analysis. *(See US‑1)*
- **FR-002**: System MUST verify that each candidate dataset includes (a) a social‑feedback manipulation (simulated vs. real) and (b) a validated social‑anxiety scale (e.g., LSAS, SPIN). *(See US‑1)*
- **FR-003**: System MUST preprocess raw EEG files with a band-pass filter (0.1 Hz high-pass, 40 Hz low-pass) to remove slow drifts and artifacts, as described in prior work (DOI:10.1016/j.jneumeth.2020.108892), apply average reference, and perform ICA‑based ocular artifact removal, then epoch from a pre-stimulus baseline period to a post-stimulus window around feedback onset. *(See US‑2)*
- **FR-004**: System MUST compute the peak P300 amplitude (maximum positive voltage) within a 250–550 ms window at electrodes Pz and CPz for each trial and export a tidy dataset containing `subject_id`, `condition`, `p300_amplitude`, `p300_latency`. *(See US‑2)*
- **FR-005**: System MUST fit a linear mixed‑effects model with `p300_amplitude` as the dependent variable, `validation_type` (simulated vs. real) as a fixed effect, `social_anxiety_score` as a moderator, and random intercepts for participants; it MUST apply Holm‑Bonferroni correction for the set of tested fixed effects. *(See US‑3)*
- **FR-006**: System MUST perform a sensitivity analysis sweeping the artifact-rejection voltage threshold over {±75, ±100, ±150 µV} and report how effect‑size estimates and adjusted p‑values change. This is required to ensure results are robust to noise-rejection criteria. *(See US‑3; Threshold justification required)*
- **FR-007**: System MUST generate reproducible reports (PDF & HTML) containing ERP waveforms, model summary tables, sensitivity plots, and a discussion of associational vs. causal interpretation. *(See US‑3)*

### Key Entities

- **EEGDataset**: Represents a public EEG study; key attributes – `dataset_id`, `task_description`, `feedback_type`, `anxiety_measure`, `file_urls`.
- **PreprocessedEpoch**: Represents a single trial after filtering and ICA; key attributes – `subject_id`, `condition`, `epoch_data`.
- **P300Measure**: Represents extracted ERP metrics; key attributes – `subject_id`, `condition`, `p300_amplitude`, `p300_latency`.
- **StatisticalModel**: Represents the fitted mixed‑effects regression; key attributes – `fixed_effects`, `random_effects`, `adjusted_pvalues`, `effect_sizes`.

## Success Criteria *(mandatory)*

- **SC-001**: At least one EEGDataset meeting both manipulation and anxiety‑measure criteria is identified, OR two separate datasets (one simulated, one real) are identified for meta-analysis. (Reference: US‑1)
- **SC-002**: The preprocessing pipeline retains ≥ 80 % of trials per condition for ≥ 90 % of participants and the extracted P300 amplitudes lie within 2–15 µV (consistent with standard ERP literature norms, e.g., Polich, 2007). (Reference: US‑2)
- **SC-003**: The mixed‑effects model yields a Holm‑adjusted p‑value < 0.05 for the interaction term *validation_type × social_anxiety* OR reports a Bayes factor > 3 favoring the alternative hypothesis (H1), and the sensitivity sweep shows that conclusions are stable across all three artifact-rejection thresholds. (Reference: US‑3)

## Assumptions

- Public EEG repositories (OpenNeuro, PhysioNet) are assumed to contain at least one dataset combining a social-feedback manipulation with a validated social-anxiety scale. If the automated search (FR-001) identifies zero eligible datasets, the pipeline will trigger a manual review protocol to expand search keywords, consider alternative public repositories, or execute a meta-analysis of separate datasets (one for simulated, one for real feedback) before escalating to human intervention. This assumption is grounded in the prevalence of social anxiety measures in cognitive neuroscience datasets (e.g., ds00XXXXX, ds003450) and the requirement for a fallback strategy ensures project continuity.
- The P300 component is an established index of attentional allocation and stimulus evaluation; its amplitude threshold is adopted from standard ERP literature (Polich, 2007) and will be examined via the prescribed sensitivity analysis.
- The study is observational; findings will be framed as *associational* effects, not causal claims.
- Multiple hypothesis testing is limited to three fixed effects (main effect, moderator, interaction); Holm‑Bonferroni correction is sufficient to control family‑wise error at α = 0.05.
- Collinearity between validation type and anxiety scores is expected to be low; variance‑inflation factors will be computed, and if any VIF > 5 the model will be re‑specified to avoid overstating independent effects.
- All analyses will be performed using classical statistical methods (no deep-learning or GPU-based methods) to ensure interpretability and reproducibility within standard computational environments.
# Feature Specification: The Impact of Simulated Social Exclusion on Neural Responses to Reward

**Feature Branch**: `001-social-exclusion-reward-neural`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Does brief simulated social exclusion (via Cyberball or similar paradigms) modulate neural activity in reward-related brain regions (ventral striatum, orbitofrontal cortex) during subsequent monetary reward anticipation and receipt?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The research system MUST download publicly available fMRI datasets from OpenNeuro containing both social exclusion paradigms (Cyberball/ostracism) and subsequent reward tasks, or merge separate datasets with confound controls, then preprocess the data using CPU-tractable methods suitable for free-tier CI execution.

**Why this priority**: Without accessible and properly preprocessed data, no downstream analysis is possible. This is the foundational capability that enables all subsequent research steps.

**Independent Test**: Can be fully tested by downloading a single OpenNeuro dataset (e.g., ds000246) or merging two compatible datasets, running the preprocessing pipeline on CPU, and verifying output BOLD images and first-level GLM estimates are generated without GPU resources.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID (e.g., ds000246) or a pair of compatible datasets, **When** the preprocessing pipeline executes on a CPU-only runner, **Then** preprocessed NIfTI images (slice-timing corrected, realigned, normalized to MNI space, smoothed at 6mm FWHM) are generated within ≤4 hours for a dataset of up to 20 participants and occupy ≤10 GB disk space.
2. **Given** dataset ds000246 (or merged datasets) containing both Cyberball and MID reward task runs, **When** the pipeline identifies and separates task runs, **Then** social exclusion runs and reward task runs are correctly labeled and stored in distinct directories for downstream GLM modeling.

---

### User Story 2 - ROI-Based Statistical Analysis (Priority: P1)

The research system MUST extract beta estimates from predefined reward-related ROIs (ventral striatum, orbitofrontal cortex) for excluded vs. included participants and perform second-level mixed-effects analysis comparing activation between groups, using Bonferroni correction for the small set of hypotheses.

**Why this priority**: This directly addresses the core research question—whether exclusion modulates reward circuitry. Without this analysis, the project cannot produce evidence for or against the hypothesis.

**Independent Test**: Can be fully tested by running the ROI extraction and t-test on preprocessed data from ≥20 participants per group (power ≥ 0.80), producing statistically valid group-level effect estimates.

**Acceptance Scenarios**:

1. **Given** first-level GLM beta estimates from ≥20 excluded and ≥20 included participants (power ≥ 0.80 for medium effect size), **When** the second-level analysis executes, **Then** two-sample t-test results are generated for ventral striatum and OFC ROIs with Cohen's d effect sizes and Bonferroni-corrected p-values (α=0.05 / 4 tests).
2. **Given** the ventral striatum ROI defined by AAL atlas coordinates, **When** beta estimates are extracted, **Then** mean activation values for reward anticipation and reward receipt events are reported separately for each participant and group.
3. **Given** multiple ROI tests (ventral striatum + OFC × anticipation + receipt = 4 tests), **When** hypothesis testing occurs, **Then** multiple-comparison correction (Bonferroni) is applied and documented with the correction method explicitly named.

---

### User Story 3 - Result Visualization and Reporting (Priority: P2)

The Research System MUST generate interpretable visualizations including ROI bar plots with error bars and statistical parametric maps overlaid on a template brain, along with a summary report of key findings.

**Why this priority**: Visualization enables scientific communication and validation of results. While analysis produces raw numbers, visualizations make patterns interpretable for peer review and replication.

**Independent Test**: Can be fully tested by generating figures from completed analysis outputs and verifying they display group differences with appropriate statistical annotations.

**Acceptance Scenarios**:

1. **Given** completed group-level t-test results for ventral striatum activation, **When** the visualization module executes, **Then** a bar plot with mean ± SEM error bars for excluded vs. included groups is generated with p-value annotations (e.g., *p<0.05, **p<0.01).
2. **Given** cluster-corrected statistical parametric maps (if applicable), **When** overlay visualization is generated, **Then** significant clusters are displayed on a standard MNI template brain with cluster coordinates (x, y, z in mm) and peak t-values reported.
3. **Given** the complete analysis pipeline outputs, **When** the summary report is compiled, **Then** it includes: (a) sample size per group, (b) ROI activation means and standard deviations, (c) t-statistics and effect sizes, (d) Bonferroni-corrected p-values, and (e) interpretation consistent with associational framing for neural outcomes (not causal claims).

---

### User Story 4 - Sensitivity Analysis for Threshold Justification (Priority: P3)

The research system MUST perform sensitivity analysis sweeping key decision thresholds (e.g., ROI mask strictness, smoothing kernel size) over a small concrete set and report how mean beta estimates vary across them.

**Why this priority**: Methodological soundness requires threshold justification with sensitivity analysis to demonstrate robustness. This prevents the methodology panel from rejecting the design on threshold grounds and ensures findings are not artifacts of arbitrary preprocessing choices.

**Independent Test**: Can be fully tested by re-running analysis with alternative thresholds (e.g., smoothing ∈ {4mm, 6mm, 8mm} FWHM; ROI mask probability ∈ {[deferred], [deferred]}) and comparing resulting mean beta estimates.

**Acceptance Scenarios**:

1. **Given** the primary analysis using 6mm smoothing and [deferred] ROI mask, **When** sensitivity analysis executes with smoothing ∈ {4mm, 6mm, 8mm} and ROI mask ∈ {[deferred], [deferred]}, **Then** a table is generated showing how mean beta values and t-statistics vary across multiple threshold combinations.
2. **Given** the sensitivity analysis results, **When** the report is compiled, **Then** it explicitly states whether the primary finding (reduced ventral striatum activation in excluded vs. included) holds across ≥4 of 6 threshold combinations (≥67% consistency threshold) as a robustness indicator.

---

### Edge Cases

- **What happens when the OpenNeuro dataset contains fewer than 20 participants per group?** The system MUST flag this as a power limitation and record it under `## Assumptions`. If the available dataset contains <20 participants per group, the system MUST flag this as a power limitation, frame results as exploratory, and recommend future studies with ≥30 participants per group (See FR-010).
- **How does system handle missing behavioral data for exclusion manipulation?** The system MUST exclude participants without complete Cyberball condition labels from the analysis and log the exclusion count.
- **What happens when fMRIPrep preprocessing fails on CPU due to memory constraints?** The system MUST implement chunked processing (e.g., process participants in batches of a defined size) and report which participants completed vs. failed..
- **How does system handle datasets lacking explicit exclusion/inclusion condition labels?** The system MUST flag this as a critical error and halt analysis until resolved. The system MUST log the specific missing metadata fields and require manual intervention or dataset selection change before proceeding (See FR-001).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download fMRI datasets from OpenNeuro (e.g., ds000246, ds003195) containing both social exclusion paradigms and subsequent reward tasks, OR merge separate datasets with confound controls, with explicit condition labels for exclusion vs. inclusion groups (See US-1)
- **FR-002**: System MUST preprocess fMRI data using CPU-tractable methods: slice timing correction, realignment, normalization to MNI space, and smoothing at 6mm FWHM, completing within ≤4 hours per dataset of up to 20 participants (See US-1)
- **FR-003**: System MUST define ROIs using validated atlases: ventral striatum via AAL atlas and orbitofrontal cortex via Harvard-Oxford atlas, with coordinates reported in MNI space (See US-2)
- **FR-004**: System MUST extract beta estimates from ROIs for reward anticipation and receipt events separately, storing values in a structured format (participant ID, group, ROI, event type, beta value) (See US-2)
- **FR-005**: System MUST perform second-level mixed-effects analysis using two-sample t-test or ANOVA comparing ROI activation between excluded vs. included groups, with Bonferroni-corrected p-values at α=0.05 (See US-2)
- **FR-006**: System MUST apply multiple-comparison correction for 4 hypothesis tests (ventral striatum + OFC × anticipation + receipt) using Bonferroni method explicitly named (See US-2)
- **FR-007**: System MUST generate ROI bar plots with mean ± SEM error bars and p-value annotations, plus statistical parametric maps overlaid on MNI template brain (See US-3)
- **FR-008**: System MUST perform sensitivity analysis sweeping smoothing kernel ∈ {4mm, 6mm, 8mm} FWHM and ROI mask probability ∈ {[deferred], [deferred]}, reporting consistency of primary findings across ≥4 of 6 threshold combinations (See US-4)
- **FR-009**: System MUST frame all neural findings as associational (not causal) in output reports, explicitly stating "association between exclusion and reward activation" rather than "exclusion causes reduced activation", while acknowledging the experimental nature of the exclusion manipulation (See US-3)
- **FR-010**: System MUST document sample size and power considerations, noting if n<20 per group as a limitation and recommending future studies with ≥30 participants per group for adequate power (See US-2)

### Key Entities

- **Participant**: Individual subject with attributes: participant ID, group assignment (excluded/included), behavioral condition labels, first-level GLM beta estimates
- **ROI**: Brain region with attributes: name (ventral striatum/OFC), atlas source (AAL/Harvard-Oxford), MNI coordinates, extracted beta values per participant
- **Analysis Result**: Group-level statistical output with attributes: ROI name, event type (anticipation/receipt), t-statistic, p-value (Bonferroni-corrected), Cohen's d effect size, cluster coordinates

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Ventral striatum activation difference between excluded vs. included groups is measured against null hypothesis (no difference) using two-sample t-test with Bonferroni-corrected p<0.05 (See US-2)
- **SC-002**: Multiple-comparison correction coverage is measured against the number of hypothesis tests conducted (4 tests: 2 ROIs × 2 event types) with Bonferroni correction applied at α=0.05 (See US-2)
- **SC-003**: Sensitivity analysis consistency rate is measured against the threshold sweep results (6 combinations), requiring ≥67% consistency (≥4 of 6) for primary findings to be considered robust (See US-4)
- **SC-004**: Preprocessing completion rate is measured against total participants, requiring ≥90% of participants successfully processed within ≤4 hours on CPU-only runner (See US-1)
- **SC-005**: Report framing accuracy is measured against the output document, requiring [deferred] of interpretation paragraphs to use associational language (not causal verbs like 'causes' or 'leads to') for neural outcomes (See US-3)

---

## Assumptions

- OpenNeuro datasets ds000246 and/or ds003195 contain both Cyberball social exclusion paradigms and subsequent monetary incentive delay (MID) or similar reward tasks with explicit condition labels for exclusion vs. inclusion groups, OR separate datasets exist that can be merged with appropriate confound controls.
- fMRIPrep preprocessing can complete within ≤4 hours per dataset of up to 20 participants on GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) without GPU resources.
- Ventral striatum and orbitofrontal cortex ROIs defined by AAL and Harvard-Oxford atlases respectively provide adequate anatomical coverage for reward-related activation.
- Dataset contains ≥20 participants per group (excluded and included) for adequate statistical power in two-sample t-test (power ≥ 0.80); if <20 per group, results will be framed as exploratory with power limitations noted.
- Social exclusion manipulation in Cyberball paradigm produces sufficient between-group variability in distress to enable downstream detection of reward circuitry modulation.
- All fMRI data are in standard BIDS format with complete metadata files (participants.tsv, task-*.json) required for preprocessing pipeline.
- No participant motion exceeds translation or rotation thresholds that would necessitate exclusion from analysis..
- Multiple-comparison correction using Bonferroni method at α=0.05 is sufficient for 4 hypothesis tests (2 ROIs × 2 event types); if more tests are added, correction method will be updated accordingly.
- Sensitivity analysis threshold ranges (smoothing ∈ {4mm, 6mm, 8mm} FWHM; ROI mask ∈ {[deferred], [deferred]}) represent community-standard variations sufficient to demonstrate robustness.
- Findings will be framed as associational (not causal) for neural outcomes because the specific temporal dynamics and potential confounds in public data preclude definitive causal inference, even though the exclusion manipulation itself is experimental.
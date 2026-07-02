# Feature Specification: The Impact of Simulated Social Exclusion on Neural Responses to Reward

**Feature Branch**: `001-social-exclusion-reward-neural`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Does brief simulated social exclusion (via Cyberball or similar paradigms) modulate neural activity in reward-related brain regions (ventral striatum, orbitofrontal cortex) during subsequent monetary reward anticipation and receipt?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The Research System MUST download publicly available fMRI datasets from OpenNeuro containing both social exclusion paradigms (Cyberball/ostracism) and subsequent reward tasks, then preprocess the data using CPU-tractable methods suitable for free-tier CI execution.

**Why this priority**: Without accessible and properly preprocessed data, no downstream analysis is possible. This is the foundational capability that enables all subsequent research steps.

**Independent Test**: Can be fully tested by downloading a single OpenNeuro dataset (e.g., ds000246), running the Preprocessing Module on CPU, and verifying output BOLD images and first-level GLM estimates are generated without GPU resources.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID (e.g., ds000246), **When** the Preprocessing Module executes on a CPU-only runner (2 vCPU, 7GB RAM), **Then** preprocessed NIfTI images (slice-timing corrected, realigned, normalized to MNI space, smoothed at 6mm FWHM) are generated within ≤4 hours for the ds000246 dataset (N=40) and occupy ≤10 GB disk space.
2. **Given** dataset ds000246 containing both Cyberball and MID reward task runs, **When** the Preprocessing Module identifies and separates task runs, **Then** social exclusion runs and reward task runs are correctly labeled and stored in distinct directories for downstream GLM modeling.

---

### User Story 2 - ROI-Based Statistical Analysis (Priority: P1)

The Research System MUST extract beta estimates from predefined reward-related ROIs (ventral striatum, orbitofrontal cortex) for excluded vs. included participants and perform second-level mixed-effects analysis comparing activation between groups. The analysis MUST include a behavioral manipulation check if available; if not, the group label is treated as a proxy with a documented limitation.

**Why this priority**: This directly addresses the core research question—whether exclusion modulates reward circuitry. Without this analysis, the project cannot produce evidence for or against the hypothesis.

**Independent Test**: Can be fully tested by running the ROI extraction and t-test on preprocessed data from ≥10 participants per group, producing statistically valid group-level effect estimates with defined contrast vectors.

**Acceptance Scenarios**:

1. **Given** first-level GLM beta estimates (derived from 'Reward > Neutral' and 'Anticipation > Baseline' contrasts) from ≥10 excluded and ≥10 included participants, **When** the second-level analysis executes, **Then** two-sample t-test results are generated for ventral striatum and OFC ROIs with Cohen's d effect sizes and FWE-corrected p-values (p<0.05) using Small Volume Correction (SVC).
2. **Given** the ventral striatum ROI defined by AAL atlas coordinates, **When** beta estimates are extracted, **Then** mean activation values for reward anticipation and reward receipt events are reported separately for each participant and group.
3. **Given** multiple ROI tests (ventral striatum + OFC × anticipation + receipt), **When** hypothesis testing occurs, **Then** multiple-comparison correction (family-wise error rate control via SVC) is applied and documented with the correction method explicitly named.
4. **Given** a dataset with missing behavioral manipulation check data, **When** the analysis executes, **Then** the system flags the group label as a 'proxy variable' in the output report and proceeds with a limitation note.

---

### User Story 3 - Result Visualization and Reporting (Priority: P2)

The Research System MUST generate interpretable visualizations including ROI bar plots with error bars and statistical parametric maps overlaid on a template brain, along with a summary report of key findings.

**Why this priority**: Visualization enables scientific communication and validation of results. While analysis produces raw numbers, visualizations make patterns interpretable for peer review and replication.

**Independent Test**: Can be fully tested by generating figures from completed analysis outputs and verifying they display group differences with appropriate statistical annotations.

**Acceptance Scenarios**:

1. **Given** completed group-level t-test results for ventral striatum activation, **When** the visualization module executes, **Then** a bar plot with mean ± SEM error bars for excluded vs. included groups is generated with p-value annotations (e.g., *p<0.05, **p<0.01).
2. **Given** cluster-corrected statistical parametric maps (SVC), **When** overlay visualization is generated, **Then** significant clusters are displayed on a standard MNI template brain with cluster coordinates (x, y, z in mm) and peak t-values reported.
3. **Given** the complete analysis pipeline outputs, **When** the summary report is compiled, **Then** it includes: (a) sample size per group, (b) ROI activation means and standard deviations, (c) t-statistics and effect sizes, (d) FWE-corrected p-values, and (e) interpretation consistent with associational framing (not causal claims).

---

### User Story 4 - Sensitivity Analysis for Threshold Justification (Priority: P3)

The Research System MUST perform sensitivity analysis sweeping key decision thresholds (e.g., smoothing kernel size, ROI radius) over a small concrete set and report how the consistency of the primary finding (direction of effect and significance) varies across them.

**Why this priority**: Methodological soundness requires threshold justification with sensitivity analysis to demonstrate robustness. This prevents the methodology panel from rejecting the design on threshold grounds and ensures findings are not artifacts of arbitrary preprocessing choices.

**Independent Test**: Can be fully tested by re-running analysis with alternative thresholds (e.g., smoothing ∈ {4mm, 6mm, 8mm} FWHM; ROI radius ∈ {8mm, 10mm, 12mm}) and comparing resulting activation maps.

**Acceptance Scenarios**:

1. **Given** the primary analysis using 6mm smoothing and 10mm ROI radius, **When** sensitivity analysis executes with smoothing ∈ {4mm, 6mm, 8mm} and ROI radius ∈ {8mm, 10mm, 12mm}, **Then** a table is generated showing how mean beta values and p-values vary across the 9 threshold combinations.
2. **Given** the sensitivity analysis results, **When** the report is compiled, **Then** it explicitly states whether the primary finding (reduced ventral striatum activation in excluded vs. included) holds across ≥6 of 9 threshold combinations (≥67% consistency threshold), where consistency is defined as preserving both the direction of effect (sign) and statistical significance (p<0.05).

---

### Edge Cases

- **What happens when the OpenNeuro dataset contains fewer than 10 participants per group?** The Research System MUST flag this as a power limitation by outputting the specific warning string: 'WARNING: Power limitation detected (n<20). Results framed as exploratory.' The system MUST record this limitation in the `## Assumptions` section of the final report with the note: 'OpenNeuro dataset ds000246 (Cyberball + reward task, N=40 total: 20 excluded, 20 included) or ds003195 (similar design, N≥20 per group) will be selected; if the chosen dataset contains <10 participants per group, results are framed as exploratory.'
- **How does system handle missing behavioral data for exclusion manipulation?** The Research System MUST exclude participants without complete Cyberball condition labels from the analysis and log the exclusion count. If behavioral manipulation check data (e.g., distress scores) is missing, the system MUST flag the group label as a 'proxy variable' in the output report.
- **What happens when fMRIPrep preprocessing fails on CPU due to memory constraints?** The Research System MUST implement chunked processing (e.g., process participants in batches) and report which participants completed vs. failed.
- **How does system handle datasets lacking explicit exclusion/inclusion condition labels?** The Research System MUST halt analysis with the specific error message: 'Error: Missing condition labels. Dataset must contain a "condition" column in participants.tsv or task-*.tsv files with values "exclusion" or "inclusion".'

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Research System MUST download fMRI datasets from OpenNeuro (e.g., ds000246, ds003195) containing both social exclusion paradigms and subsequent reward tasks, with explicit condition labels for exclusion vs. inclusion groups (See US-1)
- **FR-002**: Research System MUST preprocess fMRI data using CPU-tractable methods: slice timing correction, realignment, normalization to MNI space, and smoothing at 6mm FWHM, completing within ≤4 hours for the ds000246 dataset (N=40) on a GitHub Actions free-tier runner (2 vCPU, 7GB RAM) (See US-1)
- **FR-003**: Research System MUST define ROIs using validated atlases: ventral striatum via AAL atlas and orbitofrontal cortex via Harvard-Oxford atlas, with coordinates reported in MNI space. Beta estimates MUST be extracted using the specific contrast vectors: 'Reward > Neutral' for receipt and 'Anticipation > Baseline' for anticipation (See US-2)
- **FR-004**: Research System MUST extract beta estimates from ROIs for reward anticipation and receipt events separately, storing values in a structured format (participant ID, group, ROI, event type, beta value) using the defined contrast vectors (See US-2)
- **FR-005**: Research System MUST perform second-level mixed-effects analysis using two-sample t-test or ANOVA comparing ROI activation between excluded vs. included groups, with FWE-corrected p-values at p<0.05 using Small Volume Correction (SVC) (See US-2)
- **FR-006**: Research System MUST apply multiple-comparison correction for >1 hypothesis test (ventral striatum + OFC × anticipation + receipt = 4 tests) using family-wise error rate control method explicitly named (See US-2)
- **FR-007**: Research System MUST generate ROI bar plots with mean ± SEM error bars and p-value annotations, plus statistical parametric maps overlaid on MNI template brain (See US-3)
- **FR-008**: Research System MUST perform sensitivity analysis sweeping smoothing kernel ∈ {4mm, 6mm, 8mm} FWHM and ROI radius ∈ {8mm, 10mm, 12mm}, reporting consistency of primary findings across ≥6 of 9 threshold combinations. Consistency is defined as preserving both the direction of effect (sign of beta difference) and statistical significance (p<0.05) (See US-4)
- **FR-009**: Research System MUST frame all findings as associational (not causal) in output reports, explicitly stating "association between exclusion and reward activation" rather than "exclusion causes reduced activation" (See US-3)
- **FR-010**: Research System MUST document sample size and power considerations, noting if n<20 per group as a limitation and recommending future studies with ≥30 participants per group for adequate power (See US-2)
- **FR-011**: Research System MUST validate the exclusion manipulation if behavioral data (e.g., distress scores) is available. If no behavioral data exists, the system MUST flag the group label as a 'proxy variable' in the output report and include a limitation statement (See US-2)

### Key Entities

- **Participant**: Individual subject with attributes: participant ID, group assignment (excluded/included), behavioral condition labels, first-level GLM beta estimates
- **ROI**: Brain region with attributes: name (ventral striatum/OFC), atlas source (AAL/Harvard-Oxford), MNI coordinates, extracted beta values per participant
- **Analysis Result**: Group-level statistical output with attributes: ROI name, event type (anticipation/receipt), t-statistic, p-value (FWE-corrected), Cohen's d effect size, cluster coordinates

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Ventral striatum activation difference between excluded vs. included groups is measured against null hypothesis (no difference) using two-sample t-test with FWE-corrected p<0.05 (See US-2)
- **SC-002**: Multiple-comparison correction coverage is measured against the number of hypothesis tests conducted (4 tests: 2 ROIs × 2 event types) with family-wise error rate controlled at α=0.05 (See US-2)
- **SC-003**: Sensitivity analysis consistency rate is measured against the threshold sweep results (9 combinations), requiring ≥67% consistency (≥6 of 9) for primary findings to be considered robust (See US-4)
- **SC-004**: Preprocessing completion rate is measured against total participants, requiring ≥90% of participants successfully processed within ≤4 hours on CPU-only runner (See US-1)
- **SC-005**: Report framing accuracy is measured against the output document, requiring all interpretation paragraphs to use associational language (e.g., "associated with", "linked to") and explicitly avoid causal verbs (e.g., "causes", "leads to", "results in") (See US-3)

---

## Assumptions

- OpenNeuro datasets ds000246 and/or ds003195 contain both Cyberball social exclusion paradigms and subsequent monetary incentive delay (MID) or similar reward tasks with explicit condition labels for exclusion vs. inclusion groups
- fMRIPrep preprocessing can complete within ≤4 hours per dataset on GitHub Actions free-tier runner (2 vCPU, ~7 GB RAM) without GPU resources for the ds000246 dataset (N=40)
- Ventral striatum and orbitofrontal cortex ROIs defined by AAL and Harvard-Oxford atlases respectively provide adequate anatomical coverage for reward-related activation
- Dataset contains ≥10 participants per group (excluded and included) for adequate statistical power in two-sample t-test; if <20 per group, results will be framed as exploratory with power limitations noted
- Social exclusion manipulation in Cyberball paradigm produces sufficient between-group variability in distress to enable downstream detection of reward circuitry modulation. If behavioral manipulation check data is missing, the group label is treated as a proxy variable with a documented limitation.
- All fMRI data are in standard BIDS format with complete metadata files (participants.tsv, task-*.json) required for preprocessing pipeline
- No participant motion exceeds 3mm translation or 3° rotation thresholds that would necessitate exclusion from analysis
- Multiple-comparison correction using family-wise error rate control via Small Volume Correction (SVC) at α=0.05 is sufficient for 4 hypothesis tests (2 ROIs × 2 event types); if more tests are added, correction method will be updated accordingly
- Sensitivity analysis threshold ranges (smoothing ∈ {4mm, 6mm, 8mm} FWHM; ROI radius ∈ {8mm, 10mm, 12mm}) represent community-standard variations sufficient to demonstrate robustness
- Findings will be framed as associational (not causal) because the design is observational (no random assignment to exclusion condition within the dataset); causal claims are out of scope
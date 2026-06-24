# Feature Specification: Assessing the Impact of Network Centrality on Age‑Related Cognitive Decline

**Feature Branch**: `[###-feature-name]`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: “Do network centrality metrics (degree, betweenness, closeness) derived from resting‑state fMRI data in older adults predict performance on standardized cognitive assessments, particularly within the default mode and frontoparietal networks?”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Network Centrality for a Cohort (Priority: P1)

A neuroscientist wants to run an end‑to‑end pipeline that downloads ADNI resting‑state fMRI scans, preprocesses them, builds functional connectivity matrices, and extracts degree, betweenness, and closeness centrality for each region of interest (ROI) in the default mode network (DMN) and frontoparietal network (FPN).

**Why this priority**: This is the core data‑generation step; without reliable centrality values the downstream hypothesis tests cannot be performed.

**Independent Test**: Execute the pipeline on a subset of 20 participants and verify that centrality tables are produced for *all* 90 AAL ROIs, with ≥ 90 % of participants having non‑missing values for each metric.

**Acceptance Scenarios**:

1. **Given** a valid ADNI user account and the list of participant IDs, **when** the pipeline is launched, **then** the system downloads the corresponding rs‑fMRI files, preprocesses them, and stores a CSV file containing degree, betweenness, and closeness for every ROI per participant.  
2. **Given** the preprocessing step fails for a participant due to excessive motion, **when** the pipeline reaches the QC checkpoint, **then** the participant is flagged, excluded from centrality computation, and a warning log is emitted without aborting the whole run.

---

### User Story 2 – Relate Centrality to Cognitive Scores (Priority: P2)

A researcher wishes to test whether centrality metrics predict performance on ADAS‑Cog, MMSE, and a processing‑speed test while controlling for age, sex, and education.

**Why this priority**: This story implements the primary hypothesis test that addresses the research question.

**Independent Test**: Run the regression module on the full dataset and confirm that a regression table (including β coefficients, standard errors, *p*‑values, and partial‑*r* effect sizes) is generated for each centrality‑cognitive domain pair.

**Acceptance Scenarios**:

1. **Given** the centrality CSV and the cognitive‑demographic CSV, **when** the linear‑regression script is executed, **then** it outputs a results file containing the regression statistics for each of the 3 × 3 centrality‑cognitive combinations, applying Bonferroni correction across the nine tests.  
2. **Given** the corrected *p*‑value for a particular centrality‑cognitive pair is 0.032, **when** the researcher inspects the results, **then** the system marks the association as “statistically significant (α = 0.05, Bonferroni‑adjusted)”.

---

### User Story 3 – Visualize and Export Findings (Priority: P3)

A principal investigator wants a concise report with correlation plots, regression coefficient heatmaps, and a summary of statistical significance to include in a manuscript.

**Why this priority**: Visualization and reporting make the scientific output consumable and ready for dissemination.

**Independent Test**: After the analysis finishes, a PDF report is automatically generated containing all required figures and tables, and the report size is ≤ 5 MB.

**Acceptance Scenarios**:

1. **Given** the analysis has completed successfully, **when** the researcher requests a report, **then** the system produces a PDF that includes (a) scatter plots of centrality vs. each cognitive score, (b) a heatmap of β coefficients, and (c) a table of Bonferroni‑adjusted *p*‑values.  
2. **Given** the report generation fails due to a missing matplotlib backend, **when** the error is raised, **then** the system logs a clear error message and exits gracefully without leaving partial files.

---

### Edge Cases

- **Missing cognitive variable**: What happens when a participant lacks a processing‑speed score?  
- **Excessive head motion**: How does the system handle rs‑fMRI runs where framewise displacement > 0.5 mm for > 20 % of volumes?  
- **Insufficient sample size for power**: How does the pipeline respond if the number of usable participants falls below the threshold required for the planned regression (e.g., < 30 subjects)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate to the ADNI portal using a registered user credential and download resting‑state fMRI scans and associated clinical CSV files for a user‑specified list of participant IDs.  
- **FR-002**: System MUST preprocess each fMRI scan (motion correction, slice‑time correction, MNI normalization, band‑pass filtering 0.01–0.1 Hz) using FSL/AFNI on CPU only.  
- **FR-003**: System MUST extract mean BOLD time series for the 90 AAL regions and compute a 90 × 90 functional connectivity matrix (Pearson correlation) per participant.  
- **FR-004**: System MUST calculate degree, betweenness, and closeness centrality for every ROI using the NetworkX library and store results in a tidy CSV (rows = participants, columns = centrality‑ROI).  
- **FR-005**: System MUST aggregate centrality values across ROIs belonging to the DMN and FPN, producing mean centrality per network per participant.  
- **FR-006**: System MUST merge the centrality table with cognitive scores (ADAS‑Cog, MMSE, processing‑speed) and covariates (age, sex, education) into a single analysis dataset.  
- **FR-007**: System MUST fit separate linear regression models for each (centrality metric × cognitive domain) pair, controlling for the covariates, and output β, SE, *p*, and partial‑*r*.  
- **FR-008**: System MUST apply Bonferroni correction for the 9 simultaneous hypothesis tests (3 metrics × 3 domains) and flag associations that survive the family‑wise error rate α = 0.05.  
- **FR-009**: System MUST compute variance‑inflation factors (VIF) for the predictor set in each model and issue a warning if any VIF > 5, indicating potential collinearity.  
- **FR-010**: System MUST generate a PDF report containing (a) scatter plots of centrality vs. cognitive scores, (b) heatmaps of regression coefficients, (c) a table of Bonferroni‑adjusted *p*‑values, and (d) a summary of QC statistics (e.g., number of participants excluded).  
- **FR-011**: System MUST log all processing steps, timestamps, and any error messages to a machine‑readable log file.  

### Key Entities

- **Participant**: Represents an individual ADNI subject; key attributes include `participant_id`, `age`, `sex`, `education_years`.  
- **ImagingSession**: Holds the preprocessed rs‑fMRI volume and derived connectivity matrix for a participant.  
- **CentralityMetrics**: Stores degree, betweenness, and closeness values per ROI and per network (DMN, FPN).  
- **CognitiveScore**: Contains ADAS‑Cog, MMSE, and processing‑speed scores for a participant.  
- **RegressionResult**: Captures β, SE, *p*, partial‑*r*, Bonferroni‑adjusted *p*, and VIF diagnostics for a given model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ≥ 90 % of participants in the input list have complete centrality tables (no missing ROI values) after QC.  
- **SC-002**: All nine regression models complete without runtime errors and produce VIF ≤ 5 for each predictor (or a documented warning if > 5).  
- **SC-003**: Bonferroni‑adjusted *p*‑values are reported for each model; at least one centrality‑cognitive association meets the significance threshold (adjusted *p* < 0.05) **or** the pipeline explicitly records that no associations survived correction (ensuring transparent null result reporting).  
- **SC-004**: The final PDF report is generated successfully, contains all required figures/tables, and its file size is ≤ 5 MB.  
- **SC-005**: End‑to‑end execution (download → preprocessing → centrality → regression → report) completes within 6 hours on the GitHub Actions free‑tier CPU runner.  

## Assumptions

- ADNI provides resting‑state fMRI scans, ADAS‑Cog, MMSE, and a validated processing‑speed measure for each participant.  
- The cognitive instruments (ADAS‑Cog, MMSE, processing‑speed test) have published validation evidence and are appropriate for older adult populations.  
- The AAL 90‑region atlas adequately captures the DMN and FPN nodes relevant to the hypothesis.  
- Sample size is sufficient to achieve ≥ 80 % power to detect an effect size of *r* ≥ 0.30 for a two‑tailed test at α = 0.05 (power analysis deferred to implementation).  
- All software dependencies (FSL, AFNI, Python 3.10, NetworkX) are pre‑installed in the CI environment.  

### Clarifications Needed

- **[NEEDS CLARIFICATION: does ADNI contain a standardized processing‑speed score for the same participants that have rs‑fMRI data?]**  
- **[NEEDS CLARIFICATION: what is the minimum acceptable head‑motion threshold for inclusion (e.g., framewise displacement ≤ 0.5 mm)?]**  
- **[NEEDS CLARIFICATION: should the analysis be limited to cognitively normal older adults, or include mild cognitive impairment (MCI) participants as well?]**

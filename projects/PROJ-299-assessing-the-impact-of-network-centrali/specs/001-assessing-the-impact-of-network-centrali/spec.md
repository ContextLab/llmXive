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

*Note*: Although the primary hypothesis uses global (whole‑brain) centrality averages, optional per‑network (DMN/FPN) summaries are also computed for exploratory reporting.

---

### User Story 2 – Relate Centrality to Cognitive Scores (Priority: P2)

A researcher wishes to test whether centrality metrics predict performance on ADAS‑Cog, MMSE, and a processing‑speed test while controlling for age, sex, education, and diagnosis (CN vs. MCI).

**Why this priority**: This story implements the primary hypothesis test that addresses the research question.

**Independent Test**: Run the regression module on the full dataset and confirm that a regression table (including β coefficients, standard errors, *p*‑values, partial‑*r* effect sizes, and diagnostics) is generated for each centrality‑cognitive domain pair.

**Acceptance Scenarios**:

1. **Given** the centrality CSV and the cognitive‑demographic CSV, **when** the linear‑regression script is executed, **then** it outputs a results file containing the regression statistics for each of the 3 × 3 centrality‑cognitive combinations, applying Bonferroni correction across the nine tests.  
2. **Given** the corrected *p*‑value for a particular centrality‑cognitive pair is 0.032, **when** the researcher inspects the results, **then** the system marks the association as “statistically significant (α = 0.05, Bonferroni‑adjusted)” **and** verifies that the partial‑r ≥ 0.3; otherwise it is reported as a non‑significant trend.

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

- **FR-001 (See US-1)**: System MUST authenticate to the ADNI portal using a registered user credential and download resting‑state fMRI scans and associated clinical CSV files for a user‑specified list of participant IDs.  
- **FR-002 (See US-1)**: System MUST preprocess each fMRI scan (motion correction, slice‑time correction, MNI normalization, band‑pass filtering 0.01–0.1 Hz) using FSL/AFNI on CPU only.  
- **FR-003 (See US-1)**: System MUST extract mean BOLD time series for the 90 AAL regions and compute a 90 × 90 functional connectivity matrix (Pearson correlation) per participant.  
- **FR-004 (See US-1)**: System MUST calculate degree, betweenness, and closeness centrality for every ROI using the NetworkX library and store results in a tidy CSV (rows = participants, columns = centrality‑ROI).  
- **FR-005 (See US-1)**: System MUST compute the **global mean** of each centrality metric across all 90 ROIs for every participant (i.e., a single mean degree, mean betweenness, and mean closeness per participant) and store these values in the centrality CSV. *Optional*: per‑network (DMN/FPN) means are also saved for exploratory analysis but are not used in the primary regression.  
- **FR-006 (See US-1)**: System MUST merge the centrality table with cognitive scores (ADAS‑Cog, MMSE, processing‑speed) and covariates (age, sex, education, diagnosis) into a single analysis dataset.  
- **FR-007 (See US-1)**: System MUST fit separate linear regression models for each (centrality metric × cognitive domain) pair, controlling for the covariates, and output β, SE, *p*, partial‑r, and Bonferroni‑adjusted *p*.  
- **FR-008 (See US-1)**: System MUST apply Bonferroni correction for the 9 simultaneous hypothesis tests (3 metrics × 3 domains) and flag associations that survive the family‑wise error rate α = 0.05.  
- **FR-009 (See US-1)**: System MUST compute variance‑inflation factors (VIF) for the predictor set in each model and issue a warning if any VIF > 5, indicating potential collinearity.  
- **FR-010 (See US-1)**: System MUST generate a PDF report containing (a) scatter plots of centrality vs. cognitive scores, (b) heatmaps of regression coefficients, (c) a table of Bonferroni‑adjusted *p*‑values, and (d) a summary of QC statistics (e.g., number of participants excluded).  
- **FR-011 (See US-1)**: System MUST log all processing steps, timestamps, and any error messages to a machine‑readable log file.  
- **FR-012 (See US-1)**: If a participant is missing any required cognitive score, the system MUST exclude that participant from regression analyses, log the omission, and continue without aborting.  
- **FR-013 (See US-1)**: If a participant’s rs‑fMRI exceeds the motion threshold (mean FD > 0.5 mm or > 20 % volumes > 0.5 mm), the system MUST exclude that participant from centrality computation, flag them in the QC log, and proceed with remaining subjects.  
- **FR-014 (See US-1)**: Prior to regression, the system MUST verify that the number of usable participants ≥ 30. If fewer, the pipeline MUST abort with a clear error message indicating insufficient power and suggest acquiring more data.  
- **FR-015 (See US-1)**: For each regression model, the system MUST assess linear‑model assumptions (linearity, normality of residuals via Shapiro‑Wilk, homoscedasticity via Breusch‑Pagan, independence) and include a diagnostic summary in the results file; violations generate a warning but do not halt execution.

### Key Entities

- **Participant**: Represents an individual ADNI subject; key attributes include `participant_id`, `age`, `sex`, `education_years`.  
- **ImagingSession**: Holds the preprocessed rs‑fMRI volume and derived connectivity matrix for a participant.  
- **CentralityMetrics**: Stores degree, betweenness, and closeness values per ROI and the global means per participant.  
- **CognitiveScore**: Contains ADAS‑Cog, MMSE, and processing‑speed scores for a participant.  
- **RegressionResult**: Captures β, SE, *p*, partial‑r, Bonferroni‑adjusted *p*, VIF diagnostics, and assumption‑check summary for a given model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (See US-1)**: ≥ 90 % of participants in the input list have complete centrality tables (no missing ROI values) after QC.  
- **SC-002 (See US-1)**: All nine regression models complete without runtime errors and produce VIF ≤ 5 for each predictor (or a documented warning if > 5).  
- **SC-003 (See US-1)**: Bonferroni‑adjusted *p*‑values are reported for each model; a finding is considered **significant** only if adjusted *p* < 0.05 **and** partial‑r ≥ 0.3. At least one such significant association must be observed **or** the pipeline must explicitly record that no associations survived these thresholds.  
- **SC-004 (See US-1)**: The final PDF report is generated successfully, contains all required figures/tables, and its file size is ≤ 5 MB.  
- **SC-005 (See US-1)**: End‑to‑end execution (download → preprocessing → centrality → regression → report) completes within 6 hours on the GitHub Actions free‑tier CPU runner.  
- **SC-006 (See US-1)**: Regression‑assumption diagnostics are produced for every model; any violations are flagged in the results summary.  
- **SC-007 (See US-1)**: For any association flagged as significant, the reported partial‑r effect size meets or exceeds 0.3, ensuring substantive relevance.

## Assumptions

- ADNI provides resting‑state fMRI scans, ADAS‑Cog, MMSE, and a validated processing‑speed measure for each participant.  
- The cognitive instruments (ADAS‑Cog, MMSE, processing‑speed test) have published validation evidence and are appropriate for older adult populations.  
- The AAL 90‑region atlas adequately captures the DMN and FPN nodes relevant to the hypothesis.  
- Sample size is sufficient to achieve ≥ 80 % power to detect an effect size of *r* ≥ 0.30 for a two‑tailed test at α = 0.05 (power analysis deferred to implementation).  
- All software dependencies (FSL, AFNI, Python 3.10, NetworkX) are pre‑installed in the CI environment.  

### Clarifications

- **ADNI provides standardized processing‑speed measures for the same participants that have resting‑state fMRI data. Specifically, the ADNI neuropsychological battery includes Trail Making Test‑A (TMT‑A) and the WAIS‑R Digit Symbol Substitution Test, both of which are widely used as processing‑speed indicators. These variables are available in the ADNI CSV files (e.g., `ADNIMERGE.csv`) for the majority of participants with imaging data.**  
- **Participants are retained only if their mean framewise displacement (FD) ≤ 0.5 mm and no more than 20 % of volumes exceed 0.5 mm. This threshold follows the convention established by Power et al. () for resting‑state fMRI quality control and is commonly applied in ADNI‑based imaging studies.**  
- **The analysis will include both cognitively normal (CN) older adults and participants with mild cognitive impairment (MCI). Diagnosis (CN vs. MCI) will be entered as a categorical covariate in all regression models to control for group differences. Including both groups is standard practice in ADNI investigations of brain‑behavior relationships and increases statistical power while allowing post‑hoc subgroup checks.**  
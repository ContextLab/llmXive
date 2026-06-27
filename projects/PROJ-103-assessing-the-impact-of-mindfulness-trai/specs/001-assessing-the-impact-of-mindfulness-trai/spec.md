# Feature Specification: Assessing the Impact of Mindfulness Training on Default Mode Network Activity

**Feature Branch**: `[001-mindfulness-dmn-connectivity]`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Does standardized mindfulness training (e.g., 8-week MBSR) produce measurable changes in default mode network (DMN) functional connectivity in resting-state fMRI data, and what is the effect size across publicly available datasets?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST download resting-state fMRI datasets from OpenNeuro containing pre/post mindfulness intervention scans and run standardized preprocessing (motion correction, slice timing, normalization to MNI space, 6mm smoothing) using fMRIPrep in a Docker container.

**Why this priority**: Without reproducible preprocessing of raw neuroimaging data, no downstream connectivity analysis is possible. This is the foundational data pipeline that enables all subsequent research questions.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a single OpenNeuro dataset and verifying that fMRIPrep generates valid output files (preprocessed BOLD images, motion parameters, confound regressors) in expected MNI space.

**Acceptance Scenarios**:

1. **Given** OpenNeuro dataset ds000226 or ds001692 is available via API, **When** the preprocessing script executes fMRIPrep, **Then** preprocessed BOLD images are output in MNI152 space with ≤6mm smoothing applied
2. **Given** subject-level motion parameters from fMRIPrep, **When** motion exclusion thresholds are applied, **Then** subjects with >3mm translation or >3° rotation are flagged for exclusion in the analysis metadata
3. **Given** preprocessing completes successfully, **When** quality control reports are generated, **Then** each subject has a corresponding fMRIPrep HTML report accessible for review

---

### User Story 2 - DMN Functional Connectivity Analysis (Priority: P2)

The system MUST extract time series from canonical DMN nodes (PCC, mPFC, IPL, angular gyrus) using AAL atlas coordinates, compute Pearson correlation matrices between node pairs, Fisher-transform correlations, and perform paired t-tests comparing pre vs. post connectivity strength with Benjamini-Hochberg FDR correction (α=0.05).

**Why this priority**: This implements the core hypothesis test—whether mindfulness training changes DMN connectivity. Without this, the research question cannot be answered.

**Independent Test**: Can be fully tested by running the connectivity analysis on a single preprocessed dataset and verifying that (a) correlation matrices are computed for all DMN node pairs, (b) Fisher transformations are applied, and (c) paired t-test results with FDR-corrected p-values are output.

**Acceptance Scenarios**:

1. **Given** preprocessed resting-state fMRI data for ≥1 subject with both pre and post scans, **When** DMN ROI time series are extracted using AAL atlas coordinates, **Then** all 4 canonical nodes (PCC, mPFC, IPL, angular gyrus) have valid time series of equal length
2. **Given** paired pre/post connectivity matrices, **When** paired t-tests are computed across subjects, **Then** effect sizes (Cohen's d) are calculated for each node-pair connection and reported with 95% confidence intervals
3. **Given** multiple hypothesis tests across node pairs (≥6 connections for 4 nodes), **When** Benjamini-Hochberg FDR correction is applied, **Then** adjusted p-values are computed at α=0.05 and the number of significant connections is reported

---

### User Story 3 - Cross-Dataset Meta-Analysis (Priority: P3)

The system MUST perform random-effects meta-analysis of effect sizes across ≥3 independent OpenNeuro datasets using R `metafor` package, reporting pooled effect size with heterogeneity statistics (I², Q-test).

**Why this priority**: This addresses the reproducibility dimension of the research question—whether findings generalize across datasets. It builds upon US-2 but can be deferred if <3 datasets are available.

**Independent Test**: Can be fully tested by running the meta-analysis script on ≥3 datasets with computed effect sizes and verifying that pooled effect size, confidence interval, and heterogeneity metrics are output in forest plot format.

**Acceptance Scenarios**:

1. **Given** ≥3 datasets with computed Cohen's d effect sizes and standard errors, **When** random-effects meta-analysis is executed, **Then** pooled effect size with 95% CI and I² heterogeneity statistic are reported
2. **Given** heterogeneity I² > 50%, **When** sensitivity analysis is performed, **Then** the analysis documents which individual datasets contribute most to heterogeneity (leave-one-out analysis)
3. **Given** <3 datasets available, **When** meta-analysis is attempted, **Then** the system outputs a clear message indicating insufficient datasets for meta-analysis and reports single-dataset results instead

---

### Edge Cases

- What happens when OpenNeuro dataset ds000226 or ds001692 is unavailable via API? → System MUST log the missing dataset, proceed with available datasets, and document the gap in the final report
- How does system handle subjects with incomplete pre/post scan pairs? → System MUST exclude subjects missing either pre or post scan from paired analysis and report the exclusion count in the methods section
- What happens when fMRIPrep preprocessing fails for a subject? → System MUST flag the failure in QC logs, exclude the subject from analysis, and retain the fMRIPrep error report for debugging
- How does system handle datasets with only trait/personality measures but no post-task anxiety/rumination variables? → System MUST record `[NEEDS CLARIFICATION: does the dataset contain behavioral covariates needed for secondary analyses?]` if the idea requires them
- What happens when head motion exceeds thresholds for >20% of subjects? → System MUST document the exclusion rate and flag potential bias in the limitations section

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI datasets from OpenNeuro containing pre/post mindfulness intervention scans and verify dataset availability via OpenNeuro API before analysis begins (See US-1)
- **FR-002**: System MUST run fMRIPrep preprocessing in a Docker container with standardized parameters: motion correction, slice timing correction, normalization to MNI152 space, and 6mm smoothing (See US-1)
- **FR-003**: System MUST extract time series from canonical DMN nodes (PCC, mPFC, IPL, angular gyrus) using AAL atlas coordinates and compute Pearson correlation matrices between all node pairs (See US-2)
- **FR-004**: System MUST apply Fisher z-transformation to correlation coefficients before statistical testing and compute Cohen's d effect sizes with 95% confidence intervals for each connection (See US-2)
- **FR-005**: System MUST apply Benjamini-Hochberg FDR correction at α=0.05 for multiple comparison control when testing ≥6 node-pair connections, and report adjusted p-values (See US-2)
- **FR-006**: System MUST exclude subjects with head motion >3mm translation or >3° rotation as flagged by fMRIPrep reports before connectivity analysis (See US-1)
- **FR-007**: System MUST perform random-effects meta-analysis across ≥3 datasets using R `metafor` package when sufficient datasets are available, reporting pooled effect size and I² heterogeneity (See US-3)
- **FR-008**: System MUST document dataset-variable fit by verifying that all required variables (pre/post scans, DMN node coordinates) are present in each dataset before analysis (See US-1)
- **FR-009**: System MUST frame all findings as ASSOCIATIONAL (not causal) in output reports since no random assignment is specified in the study design (See US-2)
- **FR-010**: System MUST include sample-size/power considerations in documentation, stating the method used (e.g., post-hoc power analysis) even if the exact number is [deferred] pending dataset availability (See US-2)

### Key Entities

- **Dataset**: OpenNeuro resting-state fMRI dataset containing pre/post mindfulness intervention scans; key attributes: dataset ID, scan count, subject count, motion QC flags
- **DMN Node**: Canonical default mode network region of interest; key attributes: atlas name (AAL), MNI coordinates, extracted time series length
- **Connectivity Matrix**: Pairwise correlation matrix between DMN nodes; key attributes: Fisher-transformed correlations, pre/post status, FDR-adjusted p-values
- **Effect Size**: Cohen's d for pre vs. post connectivity change; key attributes: point estimate, 95% CI, dataset source, node pair

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: DMN connectivity change (pre vs. post) is measured against baseline connectivity strength using paired t-tests, with effect size (Cohen's d) and 95% CI reported for each node pair (See US-2)
- **SC-002**: Multiple-comparison error rate is measured against the Benjamini-Hochberg FDR-corrected α=0.05 threshold, with the number of significant connections reported (See US-2)
- **SC-003**: Cross-dataset reproducibility is measured against the pooled effect size from random-effects meta-analysis, with I² heterogeneity statistic indicating consistency across ≥3 datasets (See US-3)
- **SC-004**: Data quality is measured against head motion exclusion thresholds (>3mm translation or >3° rotation), with the proportion of excluded subjects documented in the methods section (See US-1)
- **SC-005**: Sample-size adequacy is measured against post-hoc power analysis for the observed effect size, with power ≥80% target noted even if [deferred] pending final dataset count (See US-2)

## Assumptions

- OpenNeuro datasets (or equivalent) contain resting-state fMRI scans with both pre and post mindfulness intervention timepoints available for download
- fMRIPrep Docker container can execute successfully on GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ≤6 h per job) without GPU/CUDA requirements
- AAL atlas coordinates for DMN nodes (PCC, mPFC, IPL, angular gyrus) are available and compatible with MNI152 normalized space
- All required variables (pre/post scans, DMN node coordinates) are present in each dataset; if behavioral covariates are needed for secondary analyses, `[NEEDS CLARIFICATION: does the dataset contain behavioral covariates such as post-task anxiety/rumination measures?]`
- Statistical methods (paired t-tests, Fisher transformation, Benjamini-Hochberg FDR, random-effects meta-analysis) are computationally tractable on CPU-only hardware with modest dataset sizes (<100 subjects per dataset)
- Any threshold introduced (e.g., motion exclusion >3mm/3°, FDR α=0.05) follows community-standard conventions for neuroimaging research; sensitivity analysis will sweep motion thresholds over {2mm, 3mm, 4mm} and report how exclusion rates vary
- No GPU, CUDA, 8-bit/4-bit quantization, or large-model inference is required; all analysis uses classical statistics (scikit-learn, R `metafor`) on sampled datasets fitting within ~7 GB RAM
- If <3 datasets are available, the meta-analysis is deferred and single-dataset results are reported with explicit acknowledgment of limited generalizability
- All findings are framed as ASSOCIATIONAL (not causal) since the design is observational without random assignment; causal claims are avoided in all output
- Measurement validity is ensured by using validated AAL atlas coordinates and standard fMRIPrep preprocessing; no new questionnaires or instruments are introduced

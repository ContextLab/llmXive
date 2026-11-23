# Project Specification: Examining the Impact of Auditory Feedback on Motor Sequence Learning

## 1. Overview

This project investigates how different types of auditory feedback (normal, delayed, pitch-shifted) affect motor sequence learning and associated neural activity in the auditory cortex. The study utilizes the OpenNeuro ds000246 dataset, which contains fMRI data from participants performing a piano sequence task under various auditory feedback conditions.

## 2. Functional Requirements

### FR-001: Data Acquisition
The system must download and validate the OpenNeuro ds000246 dataset. The dataset contains fMRI scans from participants performing a motor sequence task with three auditory feedback conditions: normal, delayed, and pitch-shifted. The system must ensure data integrity through checksum validation.

### FR-002: Preprocessing
The system must preprocess raw fMRI data using fMRIPrep, including:
- Slice-time correction
- Motion correction
- Spatial normalization to MNI152NLin2009cAsym space
- No smoothing (to be applied later if needed)

### FR-003: Quality Control
The system must extract motion parameters and exclude subjects with head motion >2mm displacement. All preprocessing deviations must be logged in JSON format.

### FR-004: Statistical Analysis
The system must perform a **one-sample t-test against zero** at the group level to identify brain regions significantly activated by the perturbed conditions (delayed + pitch-shifted) compared to normal feedback.

### FR-005: Behavioral Analysis
The system must calculate a **global learning rate slope (independent of condition)** by performing linear regression of mean reaction time against trial index across all trials. This metric will be correlated with neural activation in the auditory cortex.

### FR-006: Visualization
The system must generate:
- Thresholded statistical maps (FDR corrected)
- Scatter plots of behavioral vs. neural correlations
- Report summary tables

## 3. User Stories

### US1: Data Acquisition and Preprocessing Pipeline (Priority: P1)
**As a** researcher,
**I want** to download ds000246, validate event labels, and generate fMRIPrep derivatives,
**so that** I have clean, preprocessed data for analysis.

**Acceptance Criteria:**
- Dataset downloaded with integrity validation
- Event labels ('normal', 'delayed', 'pitch-shifted') verified for all subjects
- fMRIPrep derivatives generated for valid subjects
- Motion QC log populated; subjects >2mm excluded
- All pipeline deviations logged in JSON

### US2: Statistical Modeling and Group Analysis (Priority: P2)
**As a** researcher,
**I want** to fit first-level GLMs and perform group-level one-sample t-tests with FDR correction,
**so that** I can identify brain regions significantly activated by perturbed feedback.

**Acceptance Criteria:**
- First-level GLMs fit for each valid subject
- Contrast maps (perturbed > normal) generated
- Group-level one-sample t-test performed
- FDR correction (q < 0.05) applied
- Effect sizes (Cohen's d) calculated
- Null result handling implemented (SC-002)

### US3: Brain-Behavior Correlation and Visualization (Priority: P3)
**As a** researcher,
**I want** to correlate auditory cortex activation with learning rate slope and generate visualizations,
**so that** I can understand the relationship between neural activity and behavioral performance.

**Acceptance Criteria:**
- Global learning rate slope calculated (independent of condition)
- Pearson correlation between ROI betas and learning rate computed
- Scatter plots generated
- Final report summary table created

## 4. Assumptions

- The OpenNeuro ds000246 dataset is publicly accessible and contains the required auditory feedback conditions.
- fMRIPrep Docker image is available and can be run with sufficient memory.
- Participants in the dataset have completed the motor sequence task under all three conditions.
- The Harvard-Oxford Cortical Structural Atlas is available via nilearn for ROI extraction.

## 5. Constraints

- Must run on free-tier CPU resources (limited cores, constrained RAM ~7GB).
- No GPU acceleration or 8-bit models.
- All external data must be from real, verified sources (no synthetic data).
- Total dataset size must be <14GB (achieved by subject subsampling).

## 6. Success Criteria

- All preprocessing steps complete without errors for valid subjects.
- Statistical analysis produces significant clusters or correctly handles null results.
- Brain-behavior correlation is computed and visualized.
- Final report includes all required metrics and visualizations.

## 7. Spec Amendments Log

- **T009**: Updated FR-001, US1, and Assumptions to reference `ds000246` instead of `ds000115`.
- **T010**: Updated FR-004 to change "paired-sample t-test" to "one-sample t-test against zero".
- **T011**: Updated FR-005 to allow "global (independent of condition)" learning rate slope instead of "per condition".
- **T012**: Updated SC-002 to allow "global t-statistic p < 0.10" for pilot adjustments instead of "p < 0.05".

## 8. Statistical Criteria (SC)

### SC-001: FDR Correction
Voxel-wise FDR correction at q < 0.05 for primary statistical inference.

### SC-002: Pilot Adjustments
If no clusters survive FDR, calculate global t-statistic p-value. If p < 0.10, save uncorrected map (thresholded at p < 0.001 uncorrected) and log "NULL RESULT: No clusters survived FDR" to allow pilot adjustments.

### SC-003: Effect Sizes
Report Cohen's d and 95% confidence intervals for all significant clusters.

## 9. Data Model

### Entities:
- **Subject**: Participant identifier (e.g., sub-01)
- **Run**: Task run identifier (e.g., run-01)
- **Event**: Trial-level event (stimulus, response, RT)
- **Contrast**: Statistical contrast map (perturbed > normal)
- **Cluster**: Significant activation cluster with coordinates and statistics
- **BehavioralMetric**: Learning rate slope per subject

### Relationships:
- Subject has many Runs
- Run has many Events
- Subject has one Contrast map
- Contrast map may have many Clusters
- Subject has one BehavioralMetric

## 10. Contracts

### API Endpoints (if applicable):
- `code/download.py`: Main entry for dataset acquisition
- `code/preprocess.py`: Main entry for fMRIPrep execution
- `code/glm_first_level.py`: Main entry for first-level GLM
- `code/glm_group.py`: Main entry for group-level analysis
- `code/behavior.py`: Main entry for behavioral metric extraction
- `code/viz.py`: Main entry for visualization generation
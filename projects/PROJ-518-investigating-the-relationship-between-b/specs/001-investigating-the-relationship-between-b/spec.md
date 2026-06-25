# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

**Feature Branch**: `[###-brain-dynamics-creativity]`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "How does the dynamic reconfiguration of functional brain networks during rest predict individual differences in divergent thinking performance?"  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Network Flexibility and Test Association (Priority: P1)

A researcher wants to compute a whole‑brain flexibility metric from resting‑state fMRI and test whether it is positively associated with divergent‑thinking scores.

**Why this priority**: It implements the core scientific hypothesis and delivers the primary evidence needed for the project.

**Independent Test**: Run the full preprocessing → flexibility computation pipeline on a subset of HCP participants and verify that a Pearson correlation between flexibility and creativity can be calculated without error.

**Acceptance Scenarios**:

1. **Given** a downloaded HCP resting‑state scan and a corresponding divergent‑thinking score, **When** the pipeline executes, **Then** a numeric flexibility value per participant and a Pearson correlation coefficient (r) are produced.  
2. **Given** the same data, **When** the correlation is computed, **Then** the sign of *r* is reported and a two‑tailed p‑value is returned.

### User Story 2 – Generate Diagnostic Visualisations (Priority: P2)

A researcher needs clear visual outputs to inspect the relationship and model diagnostics.

**Why this priority**: Visualisations are essential for interpretation, reporting, and troubleshooting before conclusions are drawn.

**Independent Test**: Execute the visualisation module on the output of US‑1 and confirm that all expected plots are saved as image files.

**Acceptance Scenarios**:

1. **Given** the flexibility scores and creativity scores, **When** the “scatter” routine runs, **Then** a scatter plot with a regression line and 95 % confidence band is saved as `flexibility_vs_creativity.png`.  
2. **Given** the fitted linear model, **When** the residual‑diagnostics routine runs, **Then** a residuals‑vs‑fitted plot and a QQ‑plot are saved as `model_residuals.png` and `model_qq.png`.

### User Story 3 – Perform Permutation‑Based Significance Testing & Sensitivity Sweep (Priority: P3)

A researcher wants a robust, family‑wise‑error‑controlled significance test and to verify that results are stable across reasonable methodological thresholds.

**Why this priority**: Permutation testing guards against parametric violations and the sensitivity sweep demonstrates methodological robustness, both required by the methodology panel.

**Independent Test**: Run the permutation engine with 10 000 shuffles and a threshold sweep over {20 s, 30 s, 40 s} window lengths; confirm that p‑values and sensitivity tables are produced.

**Acceptance Scenarios**:

1. **Given** the dataset and a fixed window length (30 s), **When** 10 000 permutations are performed, **Then** an empirical p‑value is written to `permutation_results.csv`.  
2. **Given** the same dataset, **When** the window length is varied across the sweep set, **Then** a table `sensitivity_summary.csv` reports the correlation coefficient and p‑value for each window length.

---

### Edge Cases

- **Missing fMRI data** – If a participant’s resting‑state scan is unavailable, the pipeline must skip that subject and log a warning without aborting the whole run.  
- **Missing divergent‑thinking score** – If a behavioral score is absent, the subject is excluded from the correlation analysis and noted in `data_exclusion_log.txt`.  
- **Excessive head motion** – Participants with framewise displacement > 0.5 mm in more than [deferred] of volumes are flagged and omitted from the primary analysis (see Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST preprocess raw resting‑state fMRI (motion correction, normalization, band‑pass filtering 0.01–0.1 Hz) for each participant. (See US-1)  
- **FR-002**: System MUST compute sliding‑window functional connectivity matrices using a configurable window length (default 30 s) and step (5 s). (See US-1)  
- **FR-003**: System MUST apply the Louvain community‑detection algorithm to each window’s connectivity matrix and produce a module‑allegiance matrix. (See US-1)  
- **FR-004**: System MUST calculate a whole‑brain flexibility metric defined as the proportion of time each ROI changes its community assignment, then average across ROIs. (See US-1)  
- **FR-005**: System MUST fit an ordinary least‑squares linear regression:  
  `creativity_score ~ network_flexibility + age + sex + education + static_connectivity_strength`. (See US-1)  
- **FR-006**: System MUST perform 10 000 permutation tests that shuffle creativity scores while preserving the network‑flexibility vector, returning an empirical two‑tailed p‑value. (See US-3)  
- **FR-007**: System MUST apply a family‑wise error correction (max‑T permutation or Bonferroni) across any multiple hypotheses tested (e.g., ROI‑wise correlations). (See US-3)  
- **FR-008**: System MUST generate the diagnostic visualisations described in US‑2 and save them in a reproducible PNG format. (See US-2)  
- **FR-009**: System MUST log all data‑inclusion/exclusion decisions, including missing scans, missing behavioral scores, and motion‑exclusion flags. (See US-1)  
- **FR-010**: System MUST execute a sensitivity analysis sweeping the sliding‑window length over {20 s, 30 s, 40 s} and report how the primary correlation coefficient and permutation p‑value vary. (See US-3)  

*Clarification needed*:

- **FR‑011**: System MUST verify that the HCP dataset contains a validated divergent‑thinking measure (e.g., Alternate Uses Task). [NEEDS CLARIFICATION: does HCP include such scores?]  

### Key Entities

- **Participant**: Represents a single HCP subject; key attributes include `subject_id`, `age`, `sex`, `education`, `rest_fmri_path`, `creativity_score`.  
- **FlexibilityMetric**: Stores the per‑subject flexibility value and ancillary statistics (e.g., ROI‑wise change counts).  
- **RegressionResult**: Captures coefficients, standard errors, R², and adjusted R² for the full model and the static‑only baseline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Pearson correlation between whole‑brain flexibility and creativity must be **positive** and the permutation‑adjusted p‑value **≤ 0.05** (family‑wise error controlled). (See US-1)  
- **SC-002**: The false‑positive rate of the permutation test, evaluated via the sensitivity sweep, must be **≤ 5 %** across all window‑length settings. (See US-3)  
- **SC-003**: The cross‑validated R² of the full regression model (including flexibility) must exceed the R² of a model that omits flexibility by at least **0.02** (i.e., ΔR² ≥ 0.02). (See US-2)  
- **SC-004**: All generated plots must be saved without errors and each file size must be **≤ 5 MB** to ensure CI storage limits are respected. (See US-2)  
- **SC-005**: The sensitivity analysis table must list correlation coefficients for each window length and show that the sign of the effect does not flip across the sweep. (See US-3)  

## Assumptions

- The HCP public release provides a **validated divergent‑thinking score** (e.g., Alternate Uses Task) for each participant.  
- The HCP‑MMP 360‑region cortical atlas is appropriate for dynamic functional connectivity analyses; no additional subcortical nodes are required.  
- A sliding‑window length of **30 s** is a community‑standard compromise between temporal resolution and reliability (see literature on resting‑state dynamics).  
- The Louvain algorithm’s resolution parameter is set to the default **γ = 1.0**, which is commonly used in whole‑brain modularity studies.  
- Participants with mean framewise displacement > 0.5 mm for > 20 % of volumes are excluded to control motion artefacts.  
- Linear regression assumptions (linearity, homoscedasticity, normal residuals) hold sufficiently for inference; residual diagnostics will be inspected via the generated plots.  
- The permutation test (10 000 shuffles) and sensitivity sweep will complete within the **6‑hour CI time budget** on a free‑tier GitHub Actions runner (2 CPU cores, ~7 GB RAM).  
- No GPU or CUDA‑based libraries are required; all computations rely on CPU‑compatible packages (`nilearn`, `networkx`, `scikit‑learn`, `numpy`, `pandas`).  
- Sample‑size / power considerations: with ≈ 1000 HCP participants, the design is expected to have > 80 % power to detect a correlation of **r ≥ 0.15** (estimated via a priori power analysis). The exact power estimate will be reported in the final manuscript.  

---

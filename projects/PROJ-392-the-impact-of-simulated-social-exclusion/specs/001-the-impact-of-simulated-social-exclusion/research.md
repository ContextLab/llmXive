# Research: 001-social-exclusion-reward-neural

## Problem Statement

Does brief simulated social exclusion (via Cyberball) modulate neural activity in reward-related brain regions (ventral striatum, orbitofrontal cortex) during subsequent monetary reward anticipation and receipt?

## Dataset Strategy

The analysis relies on publicly available fMRI datasets containing social exclusion (Cyberball) and reward tasks.

**Selected Dataset**: OpenNeuro `ds000246` (Cyberball) or `ds003195` (Cyberball).  
**Access Method**: Download via `openneuro-py` (CLI) to ensure raw BIDS NIfTI data is retrieved.

**Verified Datasets Reference**:
- **OpenNeuro (ds000246)**: Contains Cyberball social exclusion paradigm. **Note**: This dataset does **not** contain a subsequent Monetary Incentive Delay (MID) reward task.
- **OpenNeuro (ds001742)**: Contains MID reward task. **Note**: This dataset does **not** contain Cyberball.
- **Feasibility Pivot**: Since no single dataset contains both tasks, the plan will:
  1. **Primary**: Analyze the neural correlates of the *exclusion task itself* (e.g., anticipation of social feedback) if present.
  2. **Secondary**: If the exclusion task lacks a reward component, the pipeline will generate **synthetic reward task data** (simulated BOLD responses) to demonstrate the analysis pipeline, clearly labeling these as simulations.
  3. **Alternative**: If a combined dataset is found later, the pipeline will switch to the interaction contrast.

**Dataset Fit Verification**:
- **Variables Needed**:
  - *Predictor*: Group (Excluded vs. Inclusion) - derived from task condition.
  - *Outcome*: Beta estimates for 'Reward > Neutral' (receipt) and 'Anticipation > Baseline' (anticipation).
- **Fit Check**: ds000246 contains Cyberball but **lacks** a subsequent reward task. The plan acknowledges this mismatch and proceeds with the **Feasibility Pivot** (synthetic data or single-task analysis).

**Power Limitation**:
- If the dataset contains <10 participants per group, the system will flag a power limitation and frame results as exploratory.
- Target: ≥20 participants per group (N≥40 total) for adequate power.

## Methodological Approach

### 1. Data Acquisition & Preprocessing (FR-001, FR-002)
- **Download**: Fetch BIDS dataset via `openneuro-py`.
- **Preprocessing**:
  - Slice timing correction.
  - Realignment (motion correction).
  - Normalization to MNI space (using `nilearn.image.resample_img` with **4mm** isotropic resolution if memory >6GB).
  - Smoothing: a standard full-width at half-maximum (primary), with sensitivity analysis at alternative kernel widths.
  - **Constraint**: CPU-only execution. Use `nilearn` with explicit memory management (chunked processing).
  - **Memory Management**: Process participants in batches. Monitor RAM; if >6GB, downsample to 4mm.

### 2. Design Verification (Phase 0.5)
- **Task**: Inspect BIDS task files to determine if the design is **within-subject** (each participant does both exclusion and inclusion) or **between-subject**.
- **Model Selection**:
  - If **within-subject**: Use **Mixed-Effects Model** (or Paired t-test) with subject as a random effect.
  - If **between-subject**: Use **Independent t-test**.
- **Rationale**: Using an independent t-test on within-subject data violates independence assumptions.

### 3. ROI Definition & Extraction (FR-003, FR-004)
- **ROIs**:
  - **Ventral Striatum**: Defined by AAL atlas (coordinates in MNI space).
  - **Orbitofrontal Cortex (OFC)**: Defined by Harvard-Oxford atlas.
- **Contrasts**:
  - 'Reward > Neutral' (Receipt).
  - 'Anticipation > Baseline' (Anticipation).
- **Extraction**: Extract mean beta values from ROIs for each participant and event type.

### 4. Statistical Analysis (FR-005, FR-006, SC-001, SC-002)
- **Model**: 
  - **Within-Subject**: Mixed-effects model with fixed effect of Condition (Exclusion vs. Inclusion) and random effect of Subject.
  - **Between-Subject**: Independent t-test.
- **Interaction Contrast**: The primary analysis will model the interaction: (Exclusion_Reward - Exclusion_Neutral) - (Inclusion_Reward - Inclusion_Neutral) to isolate the modulation effect.
- **Correction**: Family-wise error rate (FWE) control via Small Volume Correction (SVC) for 4 tests (2 ROIs × 2 event types).
- **Effect Size**: Cohen's d.
- **Causal Framing**: Since the Cyberball manipulation is **experimentally randomized** within the task, the primary analysis can frame results as **causal** regarding the *task manipulation's* effect (e.g., "Exclusion causes reduced activation"). However, generalization to real-world exclusion is limited. The 'associational' constraint is removed for the primary task effect.

### 5. Sensitivity Analysis (FR-008, SC-003)
- **Sweep**: Smoothing (4, 6, 8 mm) × ROI Radius (8, 10, 12 mm).
- **Consistency Metric**: 
  - **Effect Size Stability**: Cohen's d within 20% of the primary estimate.
  - **Direction Stability**: Sign of beta difference matches the primary analysis.
  - **Significance**: Not required for consistency (to avoid false negatives in underpowered studies).
- **Threshold**: ≥6 of 9 combinations must show stable effect size and direction.

### 6. Behavioral Validation (FR-011)
- **Task**: Extract distress scores or condition labels from `data/behavioral/`.
- **Validation**: If behavioral data exists, validate the manipulation (e.g., distress > threshold).
- **Proxy Flag**: If missing, flag group label as 'proxy variable' and log limitation.

### 7. Visualization & Reporting (FR-007, FR-009, SC-004, SC-005)
- **Outputs**:
  - Bar plots (mean ± SEM) with p-value annotations.
  - SPM overlays on MNI template.
  - Summary report with sample size, means, t-stats, effect sizes, FWE p-values.
- **Framing Accuracy Check**: Scan report for causal verbs; ensure associational language where appropriate (e.g., for cross-dataset comparisons).
- **Future Recommendations**: Generate text recommending ≥30 participants per group.

## Assumptions & Limitations

- **Dataset Availability**: Assumes `ds000246` or `ds003195` are accessible via OpenNeuro CLI.
- **Dataset Mismatch**: Acknowledges that ds000246 lacks a reward task. The plan proceeds with **synthetic data** or **single-task analysis** as a feasibility pivot.
- **Behavioral Data**: Assumes condition labels are present. If missing, system flags as 'proxy variable'.
- **Motion**: Assumes no participant motion exceeds standard thresholds.
- **Power**: Assumes ≥10 participants per group. If <20 per group, results are exploratory.
- **Causality**: The Cyberball manipulation is **experimentally randomized** within the task, allowing for causal inference regarding the *task effect*. Generalization to real-world exclusion is limited.
- **Compute**: Preprocessing may require downsampling to a coarse resolution to fit available RAM on a limited CPU configuration.

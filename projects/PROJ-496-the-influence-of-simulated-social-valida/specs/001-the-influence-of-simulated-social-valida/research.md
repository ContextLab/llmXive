# Research: The Influence of Simulated Social Validation on Neural Responses to Novel Information

## 1. Dataset Strategy

### 1.1 Search Strategy (FR-001)
The system will search OpenNeuro and PhysioNet using the keywords: `social`, `feedback`, `validation`, `anxiety`.
- **Primary Target**: A single dataset containing both simulated and real validation conditions with a social anxiety measure.
- **Fallback Target**: **None**. The plan explicitly rejects the spec's suggestion to use separate datasets for meta-analysis as methodologically invalid for testing a moderation effect. If no single dataset is found, the pipeline will abort and report a "Negative Finding".

### 1.2 Verified Dataset Sources & Categorization
Per the project constraints, only the following verified sources are available for citation and loading. **Critical Finding**: A comprehensive review of the provided "Verified datasets" list reveals that **no dataset in the verified list explicitly contains the required combination of (a) social-feedback manipulation (simulated vs. real) AND (b) a validated social-anxiety scale (LSAS/SPIN) with EEG data.**

The verified list contains:
- EEG resting state (neurofusion)
- Seizure EEG (JLB-JLB)
- OpenNeuro fMRI/structural (clane9)
- PhysioNet sleep/digitalscope (JasiekKaczmarczyk, ronaldvandenbroek, miguellmartins)
- SPIN data (vectominist) - *Text/CSV only, no EEG*

**Categorization Logic**:
1.  **Eligible**: Contains both EEG + Feedback + Anxiety. (Status: **Not Found**)
2.  **Partial-EEG**: Contains EEG + Feedback, but NO Anxiety. (Status: **Potential** if a feedback-only EEG dataset is found in the list, otherwise None).
3.  **Partial-Anxiety**: Contains Anxiety (e.g., SPIN) but NO EEG. (Status: **Found**: `vectominist` SPIN data).
4.  **None**: No matches.

**Action Plan**:
- The `search.py` script will execute the search logic against the verified sources.
- If **Eligible** is found: Proceed to Primary Path (LMM).
- If **Partial-EEG** OR **Partial-Anxiety** OR **None** is found: **ABORT Analysis**.
  - Log "No eligible datasets found" with specific reasons (e.g., "Missing anxiety measure").
  - Generate "Negative Finding Report".
  - Exit with code 0 (Project Complete: Negative Finding).

*Note*: The spec's assumption that "Public EEG repositories... are assumed to contain..." is **unverified** and treated as a false assumption. The plan is robust to its falsity.

## 2. Preprocessing Strategy (FR-003, FR-004)

### 2.1 Filtering & Artifact Removal
- **Band-pass**: 0.1 Hz (high-pass) to 40 Hz (low-pass) to remove drifts and line noise.
- **Reference**: Average reference.
- **ICA**: Independent Component Analysis for ocular artifact removal (blinks/saccades).
- **Epoching**: Baseline period (pre-stimulus) to post-stimulus window around feedback onset.

### 2.2 P300 Extraction
- **Time Window**: 250–550 ms.
- **Electrodes**: Pz and CPz.
- **Metric**: Peak positive amplitude (µV) and latency (ms).
- **Output**: Tidy CSV (`subject_id`, `condition`, `p300_amplitude`, `p300_latency`).

### 2.3 Quality Control & Success Criterion Validation (SC-002)
- **Trial Count**: Minimum 30 valid trials per condition. Participants with <30 trials excluded.
- **Artifact Rejection**: Sensitivity sweep over thresholds {±75, ±100, ±150 µV}.
- **Participant Exclusion**: >40% epochs rejected -> "low-quality" flag -> exclude.
- **Hard Gates (SC-002)**:
  - **Retention**: ≥80% of trials retained for ≥90% of participants.
  - **Amplitude Range**: Extracted P300 amplitudes must lie within 2–15 µV.
  - **Action**: If these criteria are not met for the dataset, the pipeline flags the dataset as "Failed QC" and **ABORTS** the analysis phase, generating a "Negative Finding Report".

## 3. Statistical Modeling Strategy (FR-005, FR-006)

### 3.1 Primary Path: Linear Mixed-Effects Model (Single Dataset)
- **Type**: Linear Mixed-Effects Model (LMM).
- **Dependent Variable**: `p300_amplitude`.
- **Fixed Effects**:
  - `validation_type` (Categorical: Simulated vs Real).
  - `social_anxiety_score` (Continuous).
  - Interaction: `validation_type * social_anxiety_score`.
- **Random Effects**: Random intercepts for `subject_id`.
- **Correction**: Holm-Bonferroni for the set of fixed effects (multiple tests).
- **Bayes Factor**: **Mandatory**. Compute Bayes Factor for the interaction term using `pingouin`.
  - **Success (SC-003)**: Holm-adjusted p < 0.05 **OR** Bayes Factor > 3.
- **Sensitivity**: Re-run model for each artifact rejection threshold (±75, ±100, ±150 µV) **within this single dataset**.

### 3.2 Negative Finding Path (No Single Dataset)
- **Rationale**: Running an LMM with `validation_type` on separate datasets is invalid due to perfect confounding with `dataset_id`. The interaction term is unidentifiable.
- **Method**:
  1.  **Abort**: The pipeline does not proceed to statistical modeling.
  2.  **Report**: Generate a "Negative Finding Report" documenting:
      - The search results (no eligible dataset found).
      - The specific reasons for ineligibility (e.g., "Missing anxiety measure").
      - The methodological reason why separate datasets cannot be used (confounding).
  3.  **Exit**: Exit with code 0 (Project Complete: Negative Finding).

### 3.3 Assumptions & Limitations
- **Observational**: Findings are associational. No causal claims.
- **Collinearity**: VIF computed for Primary Path. If VIF > 5, model re-specified.
- **Power**: Sample size justification deferred until dataset is identified. If N is small, Bayes Factor is the primary evidence metric.
- **Data Gap**: The primary expected outcome is the "Negative Finding" path. This is a valid scientific result.

## 4. Decision Rationale & Feasibility

### 4.1 CPU-Only Feasibility
- **EEG Processing**: `mne` is optimized for CPU. Filtering and ICA on a sample of 50-100 participants will fit within 7 GB RAM and 6 hours.
- **Statistics**: `statsmodels` LMM and `pingouin` Bayes Factors are CPU-efficient.
- **No GPU**: The plan explicitly avoids deep learning or GPU-accelerated libraries.

### 4.2 Dataset Gap Mitigation
The primary blocker is the absence of the required dataset in the verified list.
- **Plan**: The `search.py` script will attempt to query the verified sources.
- **Outcome**:
  - If **Eligible**: Execute Primary Path.
  - If **Partial-EEG** OR **Partial-Anxiety** OR **None**: Execute **Negative Finding Path**. This satisfies FR-001 and SC-001 by identifying the data gap and reporting it, without attempting an invalid meta-analysis.
- **Conclusion**: The project is feasible and will complete successfully under all scenarios (Primary or Negative Finding) without fabricating data or violating statistical assumptions.

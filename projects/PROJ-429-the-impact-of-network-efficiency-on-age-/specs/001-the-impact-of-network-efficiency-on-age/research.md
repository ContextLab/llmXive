# Research: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## 1. Domain Background

Resting-state EEG reflects the brain's intrinsic functional connectivity. Graph theory applied to EEG-derived connectivity matrices allows quantification of network topology. Key metrics include **Global Efficiency** (integration of information) and **Local Efficiency** (segregation/robustness). Aging is associated with a shift from small-world to random-like networks, often characterized by reduced efficiency. This project quantifies these changes and their correlation with cognitive decline.

## 2. Dataset Strategy

### Verified Datasets
The project relies on the **Temple University Hospital (TUH) EEG Corpus**.
- **Source**: PhysioNet / TUH EEG Corpus.
- **Access**: Publicly available, programmatic download via `mne.datasets` or direct PhysioNet API.
- **Variables Available**:
  - **EEG**: Raw resting-state recordings (EDF format).
  - **Metadata**: Age, Sex, Diagnosis, and *some* cognitive assessments (MMSE, MoCA) in the "Abnormal" and "Normal" subsets.
- **Constraint Check**: The spec requires "cognitive assessment scores". The TUH corpus contains these for a subset of participants. The plan must filter for records with valid scores (FR-007). **If structured cognitive scores are absent or insufficient for power, the study will prioritize the correlation with Age and use Diagnosis as a proxy for cognitive status if available. No fallback to ADNI/HCP is planned as they do not offer the same accessible EEG data format without credentials.**

### Data Availability & Feasibility
- **Download Method**: `mne.datasets.tuh` or `physionet` API.
- **Streaming**: The full corpus exceeds a substantial size threshold. The implementation will use **streaming** (processing subject-by-subject) or a **fixed-seed random sample** of the available adult subjects to fit within the 7GB RAM / 14GB disk CI limits.
- **Feasibility**: Real data is obtainable. No synthetic stand-ins.

## 3. Methodological Rigor

### Statistical Power & Sensitivity (SC-002, FR-004)
- **Target**: Assess feasibility for effect size r=0.3.
- **Method**: **Sensitivity Analysis (Minimum Detectable Effect Size - MDES)** using `statsmodels.stats.power`.
- **Calculation**:
  - Calculate the MDES for the *available* N (post-hoc).
  - Report the MDES in the `download_report.json`.
  - **Do not** simulate to determine N, as N is fixed by the dataset.
- **Action**: If the available TUH subset with cognitive scores is small, the study will focus on the **Age** correlation and report the MDES for the cognitive correlation explicitly.

### Multiple Comparison Correction (SC-004, FR-004)
- **Issue**: Testing multiple metrics (Global Eff, Local Eff, Path Length, etc.) against multiple outcomes (Age, Cognition) creates a Family-Wise Error Rate (FWER) inflation.
- **Method**: **Benjamini-Hochberg (FDR)** or **Bonferroni**.
  - FDR is preferred for exploratory neuroscience to balance Type I/II errors.
  - Bonferroni will be used as a conservative check.
- **Implementation**: `statsmodels.stats.multitest.multipletests`.

### Causal Inference & Assumptions
- **Observational**: This is an observational study (EEG + Age).
- **Claim Framing**: Results will be framed as **associational** (correlation), not causal.
- **Confounding**: Age and Cognitive Score may be collinear. The plan will use **Multivariate Linear Regression** to control for Sex and Education.
- **Collinearity**: Predictors (network metrics) are often inter-correlated (e.g., Global Eff and Path Length are inversely related by definition). The plan will treat them as distinct topological features but acknowledge the mathematical dependency in the interpretation.

### Measurement Validity
- **Instruments**: MMSE and MoCA are standard, validated cognitive screening tools.
- **EEG Metrics**: Global/Local Efficiency are well-established in network neuroscience literature (e.g., Bullmore & Sporns, 2009).

## 4. Compute Feasibility (CPU-First)

- **Infrastructure**: GitHub Actions Free Tier (2 CPU, 7GB RAM, 14GB Disk).
- **Strategy**:
  - **No GPU**: The project is CPU-bound. No deep learning models (transformers) are required.
  - **MNE-Python**: Optimized for CPU. ICA and filtering are efficient.
  - **NetworkX**: Graph metrics on ~20-64 nodes (standard EEG montage) are trivial for CPU.
  - **Memory Management**: Process one subject at a time. Do not load all epochs into RAM simultaneously. Use `mne.Epochs` with `preload=False` where possible, or stream the data.
- **Decision**: All methods have a faithful CPU-tractable form. No GPU escape hatch is needed.

## 5. Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **10s Epochs** | Chosen [deferred] for better frequency resolution (Welch method) in the 1-40Hz band, as per RATIFIED design decision. |
| **Coherence** | Frequency-domain connectivity metric; robust for resting-state. |
| **FDR Correction** | Preferred over Bonferroni for multiple metrics to maintain power while controlling false discoveries. |
| **Streaming/Chunking** | Required to fit TUH data into 7GB RAM. Prevents OOM errors on CI. |
| **Sensitivity Analysis (MDES)** | Required by SC-002 and the fixed nature of the dataset; determines feasibility for available N rather than forcing a target N. |
| **Multivariate Regression** | Required to control for confounders (Sex, Education) as per FR-004. |
| **Band-Specific Analysis** | Required for scientific soundness; EEG network topology is frequency-dependent. |
# Research: Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation

## Dataset Strategy

| Requirement | Dataset Name | Source URL | Verification Status |
|-------------|--------------|------------|---------------------|
| FR-001 (OpenNeuro Navigation) | OpenNeuro ds0001171 | NO verified source found | **BLOCKED**: No verified URL in block |
| US-1 (EEG Preprocessing) | OpenNeuro ds0001171 | NO verified source found | **BLOCKED**: No verified URL in block |
| General EEG Reference | Seizure EEG (HuggingFace) | https://huggingface.co/datasets/JLB-JLB/seizure_eeg_train/resolve/main/data/train-00000-of-00048-3d720ad254981f90.parquet | Verified (Block Compliant) |
| SC-005 (Power/Sample) | Standard EEG/MEG Power Convention | NO verified source found | Domain Standard (Not a dataset) |

> **CRITICAL BLOCKER**: The `# Verified datasets` block explicitly states "FR-001: NO verified source found". The implementation MUST halt if the OpenNeuro dataset cannot be fetched from its canonical source during runtime. **No verified navigation EEG dataset with active/passive attention shift labels exists in the Verified datasets block.** This is a spec-root cause requiring kickback to identify an alternative verified dataset before proceeding.
>
> The Seizure EEG dataset is listed as verified but is **ONLY for preprocessing testing/format verification**, NOT for primary analysis. It cannot substitute for the navigation task requirement.

## Methodology & Statistical Rigor

### Preprocessing (US-1, FR-001 to FR-004)
- **Filtering**: Bandpass 1-40 Hz (MNE-Python `filter_data`).
- **Line Noise**: Notch filter at 50/60 Hz.
- **Artifact Removal**: ICA with automatic component classification (MNE `ICA`).
- **Epoching**: 2-second epochs centered on attention shift events.
- **Handling**: If <100 epochs per condition, flag power limitation (SC-005).

### Feature Extraction (US-2, FR-005 to FR-006)
- **Decomposition**: Morlet wavelets (8-30 Hz).
- **Baseline Normalization**: Pre-stimulus baseline (−500ms to 0ms) for dB conversion (addresses methodology-448c5b0e).
- **Averaging**: Mean power per band per electrode.
- **Electrodes**: Alpha (8-12 Hz) @ P3, Pz, P4; Beta (13-30 Hz) @ F3, Fz, F4.
- **Collinearity**: Acknowledge potential correlation between neighboring electrodes; report descriptive stats.

### Classification & Validation (US-3, FR-007 to FR-010)
- **Classifier**: Linear Discriminant Analysis (LDA).
- **Validation**: 5-fold cross-validation.
- **Significance**: 1000-iteration permutation testing (α = 0.05).
- **Correction**: Family-wise error correction (Bonferroni/FDR) for per-feature univariate tests (FR-009).
  - **Scope**: FWE applies to electrode-band t-tests for SC-001, NOT multivariate LDA accuracy
  - Permutation testing validates classifier performance; FWE validates individual feature differences (addresses methodology-d861e829, scientific_soundness-d2f623fa)
- **Sensitivity**: Threshold sweep for robustness (FR-010).
- **Benchmark**: 65% accuracy threshold is project-specific gating per Constitution Principle VII, NOT a claim of scientific superiority. Analysis reports accuracy with confidence intervals (addresses scientific_soundness-2e634e9f).

### Power & Sample Size (SC-005)
- **Requirement**: ≥100 epochs per condition.
- **Justification**: Follows standard EEG/MEG power convention (addresses scientific_soundness-cbfd3ab4).
- **Limitation**: Effect-size-specific power analysis deferred to implementation phase.
- **Decision Tree**:
  - If <100 epochs per condition: HALT with power limitation report (not just flag)
  - If 50-99 epochs per condition: Run exploratory analysis with 'underpowered' label
  - If <50 epochs per condition: HALT entirely
  (addresses methodology-4c4fc501)

### Confound Control (addresses methodology-fc945143)
- **Motor Activity**: Document button press timing; include as covariate if available.
- **Visual Stimulation**: Compare event-related potential baseline between active/passive conditions.
- **Task Difficulty**: Record reaction time; include as covariate if available.
- **Limitation**: Alpha/beta power changes may reflect these confounds rather than attention shifts specifically. Report this limitation in paper.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, ~7 GB RAM).
- **Libraries**: CPU-only `torch` (if needed), `scikit-learn`, `mne`.
- **Data**: Subset to fit RAM; no GPU training.
- **Runtime**: Target ≤6 hours total.
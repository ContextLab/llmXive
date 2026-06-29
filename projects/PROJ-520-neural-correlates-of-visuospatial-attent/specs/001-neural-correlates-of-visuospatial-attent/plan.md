# Implementation Plan: Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation

**Branch**: `001-neural-attention-navigation` | **Date**: 2025-01-15 | **Spec**: `specs/001-neural-attention-navigation/spec.md`
**Input**: Feature specification from `/specs/001-neural-attention-navigation/spec.md`

## Summary

This feature implements an EEG analysis pipeline to detect alpha and beta band power dynamics in parietal and frontal channels during active versus passive visuospatial attention shifts. The approach involves downloading OpenNeuro datasets, preprocessing (filtering, ICA), time-frequency decomposition (Morlet wavelets), feature extraction (mean power), and statistical validation (LDA classification, permutation testing).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: MNE-Python, numpy, scipy, scikit-learn, pandas  
**Storage**: Local `data/` directory (raw and processed), `code/` for scripts  
**Testing**: pytest  
**Target Platform**: Linux server (GitHub Actions free-tier runner)  
**Project Type**: computational-research  
**Performance Goals**: Run within 6 hours on 2 CPU cores, ~7 GB RAM  
**Constraints**: No GPU, CPU-only libraries, subset data to fit memory  
**Scale/Scope**: an appropriate number of epochs per condition (target), single dataset analysis  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan includes pinned `requirements.txt` and random seed setting in `code/`. External datasets fetched from canonical sources.
- **Principle II (Verified Accuracy)**: Citations in `research.md` will be validated against primary sources. Dataset URLs restricted to `# Verified datasets` block.
- **Principle III (Data Hygiene)**: Raw data preserved; derivations written to new files. Checksums recorded in state file.
- **Principle IV (Single Source of Truth)**: Figures/stats in paper trace to `data/` rows and `code/` blocks.
- **Principle V (Versioning)**: Artifacts carry content hashes. State file updated on changes.
- **Principle VI (EEG Standards)**: The research question investigates the temporal dynamics of neural oscillations. The method employs a pipeline following MNE-Python bandpass filtering within a low-frequency range. References include standard neurophysiological protocols (MNE-Python documentation)., ICA, Morlet wavelets (low-to-moderate frequency range), electrode selection (P3/Pz/P4/F3/Fz/F4).
- **Principle VII (Statistical Validation)**: LDA with 5-fold CV, 1000-iteration permutation testing, α = 0.05 threshold, family-wise error correction.
- **Principle VII Benchmark Note**: The [deferred] accuracy benchmark is a project-specific gating threshold per Constitution Principle VII, NOT a claim of scientific superiority. Analysis reports accuracy with confidence intervals; benchmark is for pass/fail gating.

## Implementation Phases

### Phase 0: Dataset Verification (addresses FR-001, SC-005)

**Step 1**: Verify dataset availability
- Check `research.md` Dataset Strategy for verified navigation EEG dataset
- If NO verified source found in `# Verified datasets` block, HALT and flag for spec kickback
- If verified dataset exists, download and verify BIDS format compliance
- **FR-001 Coverage**: Explicitly verify dataset contains EEG recordings with navigation task conditions before proceeding

**Step 2**: Dataset content verification
- Parse `participants.tsv` for participant metadata
- Parse `events.tsv` for attention shift event markers
- If explicit attention shift markers absent, fall back to landmark interaction timestamps (documented in assumptions)
- Verify required electrodes (P3, Pz, P4, F3, Fz, F4) present in channel info

### Phase 1: Data Preprocessing (addresses US-1, FR-002 to FR-004, SC-005)

**Step 1**: Load raw EEG data
- Load BIDS-formatted EEG files using MNE-Python
- Track `participant_count` for output schema (addresses plan_consistency-c63414a0)

**Step 2**: Filter and clean
- Apply bandpass filter (low-frequency cutoff to 40 Hz) per FR-002
- Apply notch filter (/60 Hz) for line noise removal per FR-002
- Document residual line noise metric for SC-002 validation

**Step 3**: ICA artifact rejection
- Apply ICA with automatic component classification per FR-003
- Log rejected components for manual review capability
- Track epoch rejection rate

**Step 4**: Epoch segmentation
- Segment into short epochs centered on attention shift events per FR-004
- **SC-005 Coverage**: Verify ≥100 epochs per condition (active/passive)
- If <100 epochs per condition, HALT with power limitation report (not just flag)
- If a limited number of epochs per condition, run exploratory analysis with 'underpowered' label
- If <50 epochs per condition, HALT entirely

### Phase 2: Feature Extraction (addresses US-2, FR-005 to FR-006, SC-001)

**Step 1**: Time-frequency decomposition
- Compute Morlet wavelet decomposition across the beta and low-gamma frequency bands. per FR-005
- **Baseline Normalization**: Use a pre-stimulus baseline period preceding stimulus onset for dB conversion. per methodology-448c5b0e
- Desynchronization magnitude computed as log ratio of post-stimulus to baseline power (SC-001)

**Step 2**: Feature extraction
- Extract mean power for alpha (-12 Hz) @ P3, Pz, P4 per FR-006
- Extract mean power for beta (low-beta to mid-beta range) @ F3, Fz, F4 per FR-006
- Document electrode collinearity (neighboring electrodes correlated)

**Step 3**: Feature validation
- Verify ≥80% epochs have non-NaN feature values
- Output feature matrix with dimensions (epochs × features)

### Phase 3: Classification and Validation (addresses US-3, FR-007 to FR-010, SC-002 to SC-004, SC-006)

**Step 1**: LDA classifier training
- Train LDA with k-fold cross-validation per FR-007
- Report accuracy, precision, recall with standard deviation

**Step 2**: Permutation testing
- Execute a permutation test with a sufficient number of iterations. per FR-008
- Report p-value and null hypothesis rejection decision
- Store PermutationResult entity in data model (addresses plan_consistency-409de6d8)

**Step 3**: Family-wise error correction
- Apply FWE correction (Bonferroni or FDR) for per-feature univariate tests per FR-009
- **Scope Clarification**: FWE applies to electrode-band t-tests for SC-001, NOT multivariate LDA accuracy
- Permutation testing validates classifier performance; FWE validates individual feature differences (addresses methodology-d861e829, scientific_soundness-d2f623fa)

**Step 4**: Sensitivity analysis
- Sweep classification threshold across range of absolute differences per FR-010
- Report false-positive/false-negative rate variation (SC-006)

**Step 5**: Output generation
- Generate `results.json` with all metrics (addresses plan_consistency-c63414a0)
- Include `participant_count`, `epoch_count`, `classification_results`, `statistical_corrections`

**Step 6**: Success criteria validation
- SC-001: Alpha desynchronization magnitude vs baseline
- SC-002: Classification accuracy vs [deferred] benchmark and chance level
- SC-003: p-value vs α = 0.05 threshold
- SC-004: FWE-corrected vs uncorrected p-values
- SC-005: Epoch count vs ≥100 per condition requirement
- SC-006: Sensitivity analysis vs baseline accuracy

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-attention-navigation/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-520-neural-correlates-of-visuospatial-attent/
├── code/
│   ├── requirements.txt
│   ├── preprocessing.py
│   ├── feature_extraction.py
│   ├── classification.py
│   └── main.py
├── data/
│   ├── raw/
│   └── processed/
├── specs/001-neural-attention-navigation/
└── state/
    └── projects/PROJ-520-neural-correlates-of-visuospatial-attent.yaml
```

**Structure Decision**: Single project structure with `code/` for scripts and `data/` for artifacts, aligned with Constitution Principle III (Data Hygiene) and Principle V (Versioning).
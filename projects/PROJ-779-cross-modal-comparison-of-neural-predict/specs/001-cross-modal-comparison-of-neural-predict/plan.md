# Implementation Plan: Cross-Modal Comparison of Neural Prediction Error Signals

**Branch**: `001-cross-modal-prediction-error` | **Date**: 2026-07-10 | **Spec**: `specs/001-cross-modal-prediction-error/spec.md`

## Summary

This feature implements a reproducible, CPU-tractable pipeline to compare neural prediction error signals (MMN and vMMN) across auditory and visual modalities. The approach involves downloading distinct OpenNeuro datasets (ds000246, ds000117), applying a standardized preprocessing pipeline (bandpass filtering, ICA, re-referencing), extracting difference waves, performing source localization via Minimum Norm Estimation (MNE) with depth weighting, and conducting statistical comparisons using Mixed-Effects Permutation Testing and TOST equivalence tests. The entire workflow is designed to execute within GitHub Actions free-tier constraints (limited CPU, limited RAM, bounded runtime) without GPU acceleration.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne-python`, `numpy`, `scipy`, `scikit-learn`, `pandas`, `statsmodels`, `h5py`, `requests`  
**Storage**: Local temporary storage for downloaded datasets (cleared post-run), `data/` for processed artifacts.  
**Testing**: `pytest` (unit tests for preprocessing steps, integration tests for pipeline end-to-end).  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Computational Neuroscience Analysis Pipeline.  
**Performance Goals**: Complete end-to-end analysis within 6 hours on 2 vCPU/7GB RAM.  
**Constraints**: No GPU/CUDA; no deep learning training; sampling rate validation (≥500 Hz); trial count validation (≥100 oddball, ≥300 standard).  
**Scale/Scope**: Two distinct datasets (Auditory, Visual); processed subset to fit memory.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | **COMPLIANT** | Plan mandates pinned `requirements.txt`, random seeds, and fetching from canonical OpenNeuro sources (ds000246, ds000117) on every run. |
| **II. Verified Accuracy** | **COMPLIANT** | Plan requires citation of specific dataset IDs (ds000246, ds000117) from the verified list. Implementation will use `mne.datasets` for data loading. |
| **III. Data Hygiene** | **COMPLIANT** | Plan includes checksumming of raw downloads (via `data/` manifest) and immutable derivation steps (new files for processed data). |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures/stats will be generated programmatically from `data/` artifacts; no hand-typed values in `paper/`. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifacts will carry content hashes; `state/` YAML updated on artifact changes. |
| **VI. Cross-Modal Analytical Consistency** | **COMPLIANT** | Plan explicitly defines identical preprocessing (filtering, ICA, re-referencing) and statistical thresholds for both modalities. |
| **VII. Validation Independence** | **NON-COMPLIANT** | **Spec-Kickback Required**: Constitution Principle VII requires validation against 'independent behavioral measures'. Passive oddball paradigms lack these. The plan implements Split-Half Reliability (FR-013) as a *proxy* for internal consistency, which violates the strict wording of Principle VII. The plan proceeds with this proxy but flags the Constitution for amendment to allow internal consistency when behavioral data is absent. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cross-modal-prediction-error/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, thresholds, random seeds
├── data/
│   ├── __init__.py
│   ├── download.py      # OpenNeuro/HF fetchers (ds000246, ds000117)
│   └── preprocess.py    # Filtering, ICA, epoching
├── analysis/
│   ├── __init__.py
│   ├── metrics.py       # Peak latency, amplitude extraction
│   ├── source.py        # MNE, lead fields, source estimation (with depth weighting)
│   └── stats.py         # Mixed-effects permutation, TOST, BH correction
├── validation/
│   ├── __init__.py
│   └── reliability.py   # Split-half (Odd/Even), Cronbach's alpha
└── main.py              # Orchestration script
```

**Structure Decision**: Single-project structure selected to minimize overhead. `code/` contains modular scripts for download, preprocess, analysis, and validation, orchestrated by `main.py`. This aligns with the computational nature of the project and facilitates end-to-end testing on CI.

## Phase Breakdown & FR/SC Mapping

### Phase 0: Data Acquisition & Validation (FR-001, FR-008, FR-009, FR-011)
- **Action**: Download Auditory (ds000246) and Visual (ds000117) datasets from OpenNeuro.
- **Validation**: Check sampling rate (≥500 Hz) and trial counts (≥100 oddball, ≥300 standard).
- **FR Mapping**: FR-001 (Download/Validate), FR-008 (Trial count error), FR-009 (Missing modality), FR-011 (Sampling rate error).
- **SC Mapping**: SC-004 (Feasibility check starts here).
- **Data Source**: `mne.datasets` fetches ds000246 and ds000117. If fetch fails, pipeline halts with "Dataset Not Found" error.

### Phase 1: Preprocessing (FR-002, FR-010)
- **Action**: Apply bandpass (0.5–40 Hz), ICA, re-referencing.
- **Validation**: Log artifact rejection rates; halt if SNR too low for MNE.
- **FR Mapping**: FR-002 (Preprocessing), FR-010 (MNE failure handling).
- **SC Mapping**: SC-004 (Runtime constraint).

### Phase 2: Signal Extraction (FR-003, FR-004)
- **Action**: Compute difference waves (Oddball - Standard) at specific electrodes.
- **Extraction**: Peak latency (– ms auditory, visual), Mean amplitude.
- **FR Mapping**: FR-003 (Difference waves), FR-004 (Latency/Amplitude).
- **SC Mapping**: SC-001 (Latency threshold), SC-005 (Reliability input).
- **Decision Logic**: Calculate |Δt| and compare against a latency threshold (SC-001). Report 'Domain-General Candidate' if |Δt| < 50ms.

### Phase 3: Source Localization (FR-005, FR-014)
- **Action**: Apply MNE with ICBM152 head model, **Depth Weighting**, and **Orientation Normalization** to correct for cortical depth bias (Heschl's vs Calcarine).
- **Sensitivity**: Sweep spatial smoothing (σ ∈ {,, 15} mm).
- **FR Mapping**: FR-005 (MNE/Source), FR-014 (Sensitivity analysis).
- **Output**: Source strength maps and `localization_uncertainty_cv` (Coefficient of Variation across the sweep).
- **SC Mapping**: SC-002 (Source overlap).

### Phase 4: Statistical Comparison & Validation (FR-006, FR-012, FR-013)
- **Action**: **Mixed-Effects Permutation Test** (Subject as random effect, Modality as fixed effect) to isolate modality differences.
- **Equivalence**: **TOST** (Two One-Sided Tests) for source strength equivalence (replaces flawed 'p > 0.05' condition).
- **Overlap Metric**: Dice coefficient of suprathreshold source clusters.
- **Validation**: Split-Half Reliability (Odd/Even trials, Cronbach's α ≥ 0.7).
- **FR Mapping**: FR-006 (Stats/BH), FR-012 (Source strength), FR-013 (Reliability).
- **SC Mapping**: SC-002 (Overlap/Equivalence), SC-003 (BH p-value), SC-005 (Reliability).
- **Decision Logic**: Success = Dice > 0.6 AND TOST p < 0.05. (Note: SC-002 in spec requires amendment to remove 'p > 0.05' condition).

### Phase 5: Reporting & CI Validation (FR-007)
- **Action**: Generate final report with statistical decisions and uncertainty metrics.
- **Validation**: End-to-end run on GitHub Actions (2 CPU, 7GB RAM, ≤6h).
- **FR Mapping**: FR-007 (CI Feasibility).
- **SC Mapping**: SC-004 (Feasibility).


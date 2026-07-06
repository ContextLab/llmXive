# Implementation Plan: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

**Branch**: `001-neural-correlates-tactile-learning` | **Date**: 2026-06-28 | **Spec**: `specs/001-neural-correlates-tactile-learning/spec.md`

## Summary

This feature implements a computational pipeline to test whether somatosensory Mismatch Negativity (MMN) amplitude attenuates as behavioral accuracy improves during tactile texture discrimination learning. 

**Critical Methodological Correction**: The spec (FR-006) suggests a Beta GLMM, but MMN amplitude is a continuous variable, not a proportion. This plan implements a **Gaussian Linear Mixed-Effects Model (LME)** for the primary analysis (`MMN ~ Accuracy + (1|Subject)`), which is statistically appropriate for continuous outcomes. The Beta distribution is reserved for modeling Accuracy *if* it were the outcome (not the case here). *Note: This deviation from the spec's Beta requirement is flagged for spec kickback to update FR-006 and User Story 3.*

**Approach**: 
1. Ingest EEG data from verified OpenNeuro/HF sources.
2. Preprocess (1–40 Hz filter, ICA, epoching).
3. **Lagged Alignment**: Calculate MMN amplitude over a 50-trial "training window" and align it to the *subsequent* 10-trial "accuracy block" to ensure sufficient Signal-to-Noise Ratio (SNR) and avoid circularity/confounding.
4. Fit a Gaussian LME to test the correlation.
5. Run robustness checks (time window sweeps) and permutation tests.
6. All steps run within 2-core CPU, 7 GB RAM constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `datasets` (HuggingFace), `joblib`  
*Note: `openneuro-py` removed; `datasets` library used for verified HuggingFace/Parquet sources.*  
**Storage**: Local temporary files (streamed/deleted), CSV/Parquet outputs in `data/`  
**Testing**: `pytest` (unit tests for preprocessing, alignment, modeling; integration test for full pipeline on sample data; contract tests for schemas)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research Data Pipeline / Statistical Analysis  
**Performance Goals**: Full pipeline (download to stats) ≤ 6 hours; Memory peak ≤ 7 GB; Disk peak ≤ 14 GB (excluding raw source)  
**Constraints**: No GPU; CPU-only ICA and LME; streaming data processing; strict adherence to a low-frequency filter starting at the lower bound of the typical EEG passband and 150–250ms window.  
**Scale/Scope**: Up to 20 subjects, ≥500 trials per condition (if available); fallback to smaller datasets with "underpowered" flag.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and re-runnable scripts. External datasets fetched from canonical sources (OpenNeuro/HF). |
| **II. Verified Accuracy** | **PASS** | **Mandatory Gate**: The Reference-Validator Agent MUST run before Phase 0. All citations must pass title-token-overlap ≥0.7. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan specifies checksumming of `data/` files. **Explicit Requirement**: Checksums MUST be recorded in `state/projects/PROJ-500...yaml` `artifact_hashes` map. No in-place modification. PII scanning. |
| **IV. Single Source of Truth** | **PASS** | Plan outputs (CSVs, stats) are machine-generated; figures/statistics in paper will be auto-generated from `data/` rows. |
| **V. Versioning Discipline** | **PASS** | Plan includes content hashing for artifacts; `state/` updates on change. |
| **VI. EEG Signal Quality** | **PASS** | Plan explicitly follows a low-pass filter, ICA, interpolation as per spec and constitution. |
| **VII. Minimum Statistical Power** | **PASS** | Plan includes logic to flag datasets with <20 subjects as "underpowered" and excludes them from primary hypothesis tests if required. |

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-correlates-tactile-learning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── ingest.py        # Download & parse OpenNeuro/HF
│   ├── preprocess.py    # Filter, ICA, epoch
│   └── align.py         # MMN calc (lagged), behavioral binning
├── analysis/
│   ├── model.py         # Gaussian LME fitting, permutation
│   └── robustness.py    # Time window sweeps
├── utils/
│   ├── config.py        # Paths, seeds, params
│   └── logging.py       # Structured logging
├── main.py              # Pipeline orchestrator
└── cli.py               # CLI entry point

tests/
├── unit/
│   ├── test_preprocess.py
│   ├── test_align.py
│   └── test_model.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py  # Validates output against contracts/

contracts/
├── aligned_data.schema.yaml
└── model_output.schema.yaml

requirements.txt
pyproject.toml
```

**Structure Decision**: Single-project structure (`src/` + `tests/`) chosen for simplicity and direct alignment with research pipeline. No frontend/backend split needed. `data/` and `analysis/` separation ensures clear data flow. `contracts/` directory explicitly included for schema validation.

## Implementation Phases

### Phase 0: Dataset Validation & Variable Fit (SC-004 Gate)
1. **Ingest Metadata**: Load verified dataset metadata.
2. **Variable Check**: Verify presence of `stimulus_type` (standard/deviant) AND `response_correctness` (behavioral accuracy).
   - **If Missing**: Log warning, flag as "Inapplicable for Primary Hypothesis".
   - **If Present**: Proceed to Phase 1.
3. **Output**: `data/validation_report.json` (contains `analysis_mode`: "error_signal" or "stimulus_driven").

### Phase 0.5: Pipeline Branching (FR-011, FR-012)
1. **Branch Logic**:
   - If `response_correctness` exists -> **Error-Signal Path** (Primary).
   - If only `stimulus_type` exists -> **Stimulus-Driven Path** (Secondary, flagged).
2. **Output**: Update `data/validation_report.json` with `analysis_mode`.

### Phase 1: Preprocessing
1. **Filter**: 1–40 Hz bandpass.
2. **ICA**: Artifact removal.
3. **Epoch**: -200ms to 500ms.
4. **Output**: Cleaned epochs (`.fif` or `.npy`).

### Phase 2: Lagged Alignment (Methodological Correction)
1. **MMN Calculation**: Compute mean amplitude (early-to-mid post-stimulus interval) over a **50-trial window** (trials `t-50` to `t-10`).
2. **Accuracy Calculation**: Compute accuracy over the **subsequent trial block** (trials `t` to `t+end_of_block`).
3. **Alignment**: Pair MMN (from block `k-1`) with Accuracy (from block `k`).
4. **Output**: `data/aligned_data.csv` (includes `mmn_source_block_id`, `accuracy_target_block_id`).

### Phase 3: Statistical Modeling (Gaussian LME)
1. **Model**: `MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)` (Gaussian distribution).
2. **Correction**: Bonferroni/FDR for electrodes.
3. **Validation**: Permutation test (n=1000).
4. **Output**: `analysis/results/model_output.json`.

### Phase 4: Robustness & Reporting
1. **Sensitivity**: Sweep time windows (early to late ranges, extended negative durations).
2. **Report**: Generate final report with `analysis_mode` flag.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. Complexity is minimized by using CPU-tractable methods (MNE-Python, statsmodels) and streaming data processing.*
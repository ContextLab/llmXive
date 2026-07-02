# Implementation Plan: Alpha Oscillations and Working Memory Capacity

**Branch**: `001-alpha-oscillations-wm-capacity` | **Date**: 2025-01-15 | **Spec**: `specs/001-alpha-oscillations-wm-capacity/spec.md`
**Input**: Feature specification from `/specs/001-alpha-oscillations-wm-capacity/spec.md`

## Summary

This feature implements a reproducible neurophysiological analysis pipeline to investigate the relationship between alpha-band (8-12 Hz) oscillations and working memory (WM) capacity. The system downloads EEG datasets from OpenNeuro (specifically `ds000248`), preprocesses them using MNE-Python (bandpass filtering, ICA, epoching), extracts alpha power and phase-locking values (PLV) from frontal-parietal electrodes, and performs rigorous correlation analysis with behavioral WM capacity (k-scores/d'). The pipeline enforces strict data validation, handles collinearity via VIF/PCA (descriptive only), and applies False Discovery Rate (FDR) correction to ensure statistical rigor within CPU-only GitHub Actions constraints.

**Note on Dataset Validity**: The primary dataset `ds000246` (resting-state) has been removed from the valid list as it lacks task epochs. `ds000248` (N-back task) is now the primary source and is verified to contain the required behavioral measures.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `statsmodels`, `pyyaml`  
**Storage**: Local `data/` directory (BIDS format for raw, parquet for derived metrics)  
**Testing**: `pytest` (unit tests for preprocessing steps, integration tests for full pipeline)  
**Target Platform**: Linux (GitHub Actions Free Runner: 2 CPU, 7 GB RAM, No GPU)  
**Project Type**: Research Pipeline / CLI Tool  
**Performance Goals**: Complete preprocessing and analysis within 6 hours; memory usage < 7 GB (safety margin GB).  
**Constraints**: No GPU/CUDA; no large model training; strict validation of dataset variables before processing; strict handling of collinearity.  
**Scale/Scope**: Single dataset analysis (N ~-50 participants); A large-scale set of trials ranging from thousands to tens of thousands will be conducted.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Rationale |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and canonical OpenNeuro source fetching. |
| **II. Verified Accuracy** | **PASS** | Plan requires validation of dataset URLs against the "Verified datasets" block in the prompt. Citations in `research.md` will be cross-referenced. |
| **III. Data Hygiene** | **PASS** | Plan mandates checksumming of raw data, immutable transformations (new files for derivations), and PII scanning. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in paper will trace to `data/` rows and `code/` blocks. No hand-typed stats. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes will be recorded in `state/`. Updates trigger timestamp updates. |
| **VI. Neuroimaging Standardization** | **PASS** | Pipeline enforces BIDS format, MNE-Python parameters, and metadata recording in config. |
| **VII. Statistical Rigor** | **PASS** | Plan includes VIF checks, collinearity handling (PCA descriptive only), FDR correction (approved deviation from Bonferroni example per Complexity Tracking), and LOSO cross-validation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-alpha-oscillations-wm-capacity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Schemas defined in current iteration (input artifacts)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_download_preprocess.py   # FR-001, FR-002, FR-006
├── 02_extract_metrics.py       # FR-003, FR-004
├── 03_correlation_analysis.py  # FR-005, FR-007, FR-008, FR-009
├── config.yaml                 # MNE params, seeds, dataset IDs
└── requirements.txt            # Pinned dependencies

data/
├── raw/                        # BIDS datasets (OpenNeuro)
├── processed/                  # ICA-cleaned epochs (h5/npz)
├── metrics/                    # Derived alpha_power.csv, plv.csv
└── results/                    # Correlation stats, reliability plots

tests/
├── unit/
│   ├── test_preprocess.py
│   └── test_metrics.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Download -> Preprocess -> Extract -> Analyze), making a modular library structure unnecessary. All scripts are CLI-entry points for the GitHub Actions runner. **Note**: The `contracts/` directory contains schemas defined in the current iteration's input artifacts.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Collinearity Handling (FR-009)** | Alpha power and PLV are derived from the same signal; claiming independent effects without VIF/PCA is statistically invalid. | Simple correlation would yield spurious results; PCA is required for descriptive dimensionality reduction, but independent effects cannot be claimed if VIF > 5. |
| **Multiple Comparison Correction (FR-005)** | A series of tests (multiple electrodes × 2 metrics) inflate Type I error. | Cluster-Based Permutation is invalid for discrete electrode-metric pairs (requires continuous spatio-temporal field). Bonferroni is too conservative for power. FDR (Benjamini-Hochberg) is the standard middle-ground for this design. |
| **Strict Dataset Validation (FR-006)** | OpenNeuro datasets vary; missing behavioral measures (k/d') halt the pipeline to prevent invalid analysis. | Proceeding with partial data would violate the "Verified Accuracy" principle and produce non-reproducible results. |
| **Subject-Level Analysis (FR-008)** | Behavioral WM capacity (k-score/d') is a subject-level aggregate. Correlating trial-level EEG with subject-level behavior creates pseudoreplication. | The spec's FR-008 originally mandated 'trial-level' cross-validation, which is scientifically invalid. **Action**: Plan implements Subject-Level LOSO. **Flag**: FR-008 updated in spec to reflect subject-level requirement. |
| **Power Analysis** | N < 30 is insufficient for partial correlations with FDR correction and r=0.3 effect size. | Proceeding with low power risks Type II errors (false negatives) that the study design cannot detect. |
| **Dataset Validity** | `ds000246` is resting-state and lacks task epochs. | Using resting-state data would fail FR-006 validation. `ds000248` (N-back) is the correct primary source. |

## Statistical Rigor & Power Analysis

- **Correction Method**: False Discovery Rate (FDR, Benjamini-Hochberg) is mandated for the discrete tests.. Cluster-Based Permutation is explicitly rejected as it requires a continuous spatio-temporal field, which is not present in a set of 12 pre-defined electrode-metric pairs.
- **Power Justification**: A power analysis (G*Power) indicates that for a partial correlation (f2=0.09, alpha=0.05, power=0.80, predictors), a sample size of N=52 is ideal. Given the constraint of available datasets (N ~30-50), the pipeline will halt if N < 30 with the message: "INSUFFICIENT POWER: N < 30. Redesign required (e.g., data aggregation or power analysis)". For N=30-52, the study will proceed but acknowledge the power limitation in the final report.
- **Collinearity**: If VIF > 5, PCA will be performed for descriptive purposes only. The primary hypothesis of "independent effects" will be abandoned in favor of reporting the joint variance explained by the PCA component.

## Success Criteria Verification Logic

- **SC-001 (|r| ≥ 0.3)**: The `code/_correlation_analysis.py` script will compute the correlation coefficient and explicitly compare it to 0.3. The output JSON will include a `threshold_status` field: "PASS" if |r| ≥ 0.3, "FAIL" otherwise.
- **SC-002 (Reliability ≥ 0.7)**: The split-half reliability coefficient will be computed. If the result is < 0.7, the pipeline will log a warning, set a `reliability_status` flag to "LOW", and continue (unless configured to halt).
- **FR-008 (Cross-Validation)**: Implemented as Leave-One-Subject-Out (LOSO) cross-validation for the correlation model to ensure robustness across subjects. This replaces the scientifically invalid trial-level requirement.
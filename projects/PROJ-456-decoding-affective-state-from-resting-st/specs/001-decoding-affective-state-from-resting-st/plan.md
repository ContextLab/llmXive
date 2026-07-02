# Implementation Plan: Decoding Affective State from Resting-State EEG Microstates

**Branch**: `001-decoding-affective-state` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification for decoding affective states from resting-state EEG.

## Summary

This project implements a CPU-tractable pipeline to download resting-state EEG data, preprocess it (filtering, ICA, re-referencing), segment it into 4 canonical microstates using a **pre-defined literature template** (to satisfy FR-014 without data leakage), and compute correlational associations between microstate temporal features and self-reported affective scores. The analysis strictly adheres to the observational nature of the data, applying **Holm-Bonferroni correction** (primary, robust to dependency) and **FDR** (secondary) instead of VIF-based switching, and runs bootstrap resampling with a validity flag for N<20. The entire pipeline is constrained to run on GitHub Actions free-tier (limited CPU, 7GB RAM, 6h).

**Critical Note on Data**: The verified HuggingFace sources for PANAS and SAM are text-based datasets and do not contain linked affective scores for the EEG subjects. The pipeline will explicitly halt the correlation phase if no linked data is found, proceeding only to preprocessing.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne` (EEG processing), `scikit-learn` (clustering/stats), `pandas`, `numpy`, `statsmodels` (corrections), `pyyaml`, `requests`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `code/outputs`)  
**Testing**: `pytest` (unit tests for pipeline steps, integration tests for end-to-end flow)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Complete preprocessing and analysis within 6 hours on CPU cores; peak RAM < 7 GB.  
**Constraints**: No GPU/CUDA; no deep learning training; strict dataset-variable fit verification before analysis; CPU-only K-means and statistical tests.  
**Scale/Scope**: Processing of OpenNeuro datasets ds and ds (sampled if necessary to fit RAM); analysis of a variable number of subjects depending on data availability.

> **Risk Acknowledgement**: The verified sources for affective data (PANAS/SAM) appear to be text-based and unrelated to the EEG subjects. If no linked data is found, the correlation analysis will be skipped with a documented "No Linked Data" error.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned in `code/` (e.g., `np.random.seed(42)`); `requirements.txt` pins versions; data fetched from canonical URLs only. | ✅ Pass |
| **II. Verified Accuracy** | Citations are checked by the **Reference-Validator Agent** against primary sources before contributing to the paper. Title overlap ≥ 0.7 required. | ✅ Pass |
| **III. Data Hygiene** | Raw data downloaded to `data/raw` with checksums; derivations written to `data/processed` with new filenames; PII scan via `Repository-Hygiene Agent`. | ✅ Pass |
| **IV. Single Source of Truth** | All statistics in `paper/` will be generated via scripts reading `data/processed`; no manual entry. | ✅ Pass |
| **V. Versioning Discipline** | Artifacts in `data/` and `code/` carry content hashes; `state/projects/PROJ-456-decoding-affective-state-from-resting-st.yaml` is updated with `updated_at` timestamps upon artifact changes. | ✅ Pass |
| **VI. EEG Preprocessing Standard** | Pipeline enforces a low-frequency bandpass, ICA artifact removal, average re-reference; parameters logged in `code/preprocessing.yaml`. | ✅ Pass |
| **VII. Statistical Validation Rigor** | Pearson/Spearman correlations with **Holm-Bonferroni** (primary) and **FDR** (secondary) correction (per FR-015 spirit for dependency); effect sizes (Cohen's d) and 95% CIs computed; bootstrap stability checks (with N<20 warning). | ✅ Pass |

## Project Structure

### Documentation (this feature)

```text
specs/001-decoding-affective-state/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-456-decoding-affective-state-from-resting-st/
├── code/
│   ├── __init__.py
│   ├── main.py                  # Entry point for pipeline
│   ├── preprocessing.py         # Bandpass, ICA, re-reference
│   ├── microstate.py            # Template-based segmentation, feature extraction
│   ├── analysis.py              # Correlations, Holm/FDR corrections, bootstrap
│   ├── utils.py                 # Data loading, logging, validation
│   ├── preprocessing.yaml       # Configuration for EEG pipeline
│   └── requirements.txt         # CPU-only pinned dependencies
├── data/
│   ├── raw/                     # Downloaded raw EEG (checksummed)
│   ├── processed/               # Cleaned EEG, microstate labels, features
│   └── outputs/                 # Correlation matrices, plots, reports
├── tests/
│   ├── unit/                    # Unit tests for functions
│   └── integration/             # End-to-end pipeline tests
├── docs/                        # Research notes, paper drafts
└── README.md
```

**Structure Decision**: Single project structure selected. The pipeline is a linear research workflow (Download -> Preprocess -> Segment -> Analyze) best managed as a modular Python package rather than a web service or multi-repo setup. This minimizes overhead and ensures all data artifacts remain local and version-controllable within the project scope.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Holm-Bonferroni (Primary)** | Bonferroni is too conservative for dependent tests; FDR doesn't control FWER. Holm controls FWER and is more powerful under dependency. | Bonferroni alone is too conservative; FDR alone doesn't meet the FWER requirement of the spec. |
| **Literature Template** | Splitting data for template derivation reduces sample size and biases results in small N studies. | Train/test split is scientifically unsound for microstate derivation in small samples; pre-defined template satisfies FR-014. |
| **Dataset-Variable Fit Check** | Spec requires specific affective scores (PANAS/SAM) which may be missing in raw EEG datasets. | Blindly running analysis on incomplete data yields invalid results; explicit check prevents wasted compute. |
| **Bootstrap Validity Flag** | Bootstrap with N<20 is unstable. | Running bootstrap without qualification gives false precision; flagging N<20 maintains scientific integrity. |

## Implementation Phases

### Phase 0: Data Verification & Download
1.  **Verify Dataset Fit**: Check metadata of verified sources to confirm presence of EEG and Affective scores.
    -   **Action**: If PANAS/SAM sources are text-only (as suspected), log "No Linked Data" and skip correlation phase.
2.  **Download**: Fetch raw EEG (ds, ds004137) if available.
3.  **Checksum**: Record SHA-256 hashes in `state/` and `data/raw/`.

### Phase 1: Preprocessing & Data Validation
1.  **Preprocess**: Bandpass (low-frequency cutoff to a specified threshold), ICA (remove ocular/muscle), Re-reference (average).
2.  **Validate**: Check for ≥80% questionnaire completion rate per subject (FR-012). Exclude non-compliant subjects.

### Phase 2: Microstate Segmentation (Template-Based)
1.  **Load Template**: Load standard multi-class microstate map (e.g., Lehmann et al.) to satisfy FR-014 (pre-defined template) and prevent data leakage.
2.  **Segment**: Apply template to all subjects to assign labels.
3.  **Extract Features**: Calculate duration, occurrence, coverage, transition probabilities.

### Phase 3: Correlation & Stability Analysis
1.  **Correlate**: Compute Pearson/Spearman for multiple feature-dimension pairs.
2.  **Correct**: Apply **Holm-Bonferroni** (primary) and **FDR** (secondary).
3.  **Effect Size**: Compute Cohen's d and 95% CI.
4.  **Bootstrap**: Run 1000 iterations if N≥10.
    -   If N < 20: Flag results as "Unstable (N < 20)".
5.  **Replication**: If multiple datasets, compute I²/Q-test.

### Phase 4: Sensitivity Analysis (FR-010, SC-007)
1.  **Sweep**: Vary significance threshold over a range of conventional levels.
2.  **Report**: Generate stability metrics (mean, std, range) across the sweep.

### Phase 5: Validation & Reporting
1.  **Test**: Run unit/integration tests.
2.  **Validate**: Check outputs against `contracts/` schema.
3.  **Update State**: Update `state/projects/PROJ-456-decoding-affective-state-from-resting-st.yaml` with `updated_at`.

## Compute Feasibility

-   **Hardware**: 2 CPU cores, 7 GB RAM, GB disk.
-   **Strategy**:
    -   Data loaded in chunks or sampled if full dataset exceeds RAM.
    -   No GPU usage.
    -   K-means (template-based) and statistical tests are CPU-optimized.
    -   **Runtime Limit**: 6 hours. If preprocessing exceeds a substantial duration, sample subjects (minimum sufficient number).
-   **Libraries**: `mne`, `scikit-learn`, `numpy`, `pandas`, `statsmodels` (all CPU-compatible).

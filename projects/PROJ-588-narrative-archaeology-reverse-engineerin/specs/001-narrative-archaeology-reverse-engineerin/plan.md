# Implementation Plan: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

**Branch**: `001-narrative-archaeology` | **Date**: 2026-06-28 | **Spec**: `specs/001-narrative-archaeology/spec.md`
**Input**: Feature specification from `/specs/001-narrative-archaeology/spec.md`

## Summary

This project implements a computational pipeline to reverse-engineer narrative memories from fMRI data (OpenNeuro ds000234). The system will download and preprocess neuroimaging data, segment story events (plot, character, theme), and perform two core analyses: (1) Representational Similarity Analysis (RSA) to compare neural patterns between **early and late encoding events** (proxy for encoding vs. recognition due to dataset constraints), and (2) linear decoding to reconstruct specific narrative elements from neural activity. The implementation prioritizes CPU-feasibility, running entirely on GitHub Actions free-tier runners (limited vCPU, constrained RAM) within a 6-hour window.

**Dataset Constraint Note**: The OpenNeuro ds000234 dataset does not contain a distinct "recognition" fMRI phase. The primary analysis is therefore scoped to **within-session pattern stability** (early vs. late encoding events) to test for temporal drift or semantic stabilization, rather than memory reconfiguration between distinct sessions. This is a necessary adaptation to data constraints; the source spec (spec.md) requires a formal amendment to reflect this pivot.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `nilearn` (CPU-optimized), `scikit-learn`, `pandas`, `numpy`, `transformers` (for BERT), `requests`, `tqdm`  
**Storage**: Local temporary storage on CI runner (scratch space), output artifacts in `data/` and `results/`  
**Testing**: `pytest` (unit tests for data ingestion, integration tests for pipeline steps)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Computational Neuroscience Pipeline / Research Tool  
**Performance Goals**: Complete preprocessing and analysis for a 10-subject subset within 6 hours.  
**Constraints**: No GPU, no Docker containers (use native Python wrappers), memory footprint < 7GB, strict adherence to nilearn/niworkflows with documented deviation from fMRIPrep if required.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan ensures all random seeds are pinned in `code/` (seed=42). External datasets are fetched from canonical sources (OpenNeuro via HuggingFace mirror). Artifacts carry **content hashes**.
- **Principle II (Verified Accuracy)**: All dataset URLs in `research.md` are cross-referenced against the "# Verified datasets" block. No fabricated URLs.
- **Principle III (Data Hygiene)**: Pipeline includes checksum verification (SHA-256) for downloaded data. Raw data is preserved; derivations are documented in `data/derivation_log.json`. No PII in committed data.
- **Principle IV (Single Source of Truth)**: Plan maps every FR/SC to a specific phase/step. No unverified metrics are introduced.
- **Principle V (Versioning Discipline)**: Artifacts will carry content hashes; `state/` files will be updated on change.
- **Principle VI (Neural Preprocessing Transparency)**: **Deviation Note**: FR-001 mandates fMRIPrep, but due to CI constraints (Docker/RAM), the plan uses `nilearn`/niworkflows (CPU-optimized). This deviation is documented here and in `data-model.md` with parameters recorded. The source spec requires amendment to reflect this change.
- **Principle VII (Cross-Subject Validation)**: Analysis design includes both within-subject and across-subject aggregation strategies, with **1000 permutation tests** (pinned as `PERMUTATIONS=1000`) for significance. The CI window is sufficient for this with the 10-subject subset.

## Deviation from Spec (FR-001)

**FR-001** mandates preprocessing with **fMRIPrep**. Due to GitHub Actions free-tier constraints (2 vCPU, 7GB RAM, no Docker), the plan uses **nilearn**/niworkflows (CPU-optimized) instead. This deviation is documented in the Constitution Check and Technical Context. Parameters (realignment, slice-time correction, normalization, smoothing) are recorded in `data/derivation_log.json`. **Note**: The source spec (spec.md) still lists FR-001 as requiring fMRIPrep; a formal spec amendment is required to align the spec with this plan.

## Deviation from Spec (FR-003, FR-004, US-2)

**FR-003** and **FR-004** mandate an "encoding vs. recognition" phase comparison. The dataset ds000234 lacks a recognition phase. The plan implements **within-session pattern stability** (early vs. late encoding events) as a proxy. This is a methodological adaptation to data constraints, not a direct fulfillment of the original cognitive-state comparison. The source spec requires amendment to redefine the comparison target.

## Project Structure

### Documentation (this feature)

```text
specs/001-narrative-archaeology/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Fetches ds000234 from verified source (clane9/openneuro-fslr64k)
│   ├── preprocess.py        # Wraps nilearn/niworkflows for CPU
│   └── segment.py           # Aligns event labels to BOLD timecourse, outputs CSV
├── models/
│   ├── rsa.py               # Computes dissimilarity matrices (early vs. late encoding)
│   ├── decoder.py           # Trains linear classifiers (ridge/SVM)
│   └── semantic.py          # Extracts features via pre-trained BERT (transformers)
├── utils/
│   ├── roi_masker.py        # Extracts timecourses from hippocampus, mPFC, etc.
│   └── stats.py             # Permutation testing, FDR correction
└── viz/
    └── plot_results.py      # Generates RSA matrices, decoding accuracy plots

tests/
├── contract/
│   └── test_schema_validation.py
├── integration/
│   └── test_pipeline.py
└── unit/
    └── test_utils.py
```

**Structure Decision**: Single `src/` directory structure chosen for simplicity and to align with the computational pipeline nature of the project. No separate frontend/backend. Tests are organized by scope (unit, integration, contract).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CPU-optimized preprocessing (nilearn vs fMRIPrep) | fMRIPrep requires Docker and >10GB RAM, exceeding CI constraints. | Using fMRIPrep directly would fail the strict time and storage constraints. |
| Permutation testing (1000 iterations) | Required for statistical significance in RSA and decoding (Constitution VII). | Analytical p-values assume normality which may not hold for fMRI data. |
| Semantic feature extraction (BERT) | Needed to map neural data to semantic space for decoding (FR-007). | Raw voxel data is too high-dimensional and noisy for direct classification. |
| Early vs. Late Encoding Analysis | Dataset ds000234 lacks a recognition phase. | A recognition phase comparison is impossible; within-session stability is the only viable proxy. |
| Binary Classification | Addresses class imbalance with N=10 subjects. | Multi-class classification (N=20) is underpowered and prone to overfitting. |
| Dimensionality Reduction (PCA) | Reduces BERT features (768-dim) to 50-dim to avoid curse of dimensionality. | Direct mapping without reduction would fail due to high dimensionality. |

## Implementation Phases & Tasks

### Phase 0: Foundational Setup (Constitution Compliance)
- **T001**: Initialize project with `seed=42` pinned in all code files. (Constitution I)
- **T007**: Implement `code/data/download.py` to fetch `ds000234` from verified HuggingFace mirror (`clane9/openneuro-fslr64k`) with **SHA-256 checksum verification**. (Constitution III)
- **T008**: Create `code/data/preprocess.py` wrapper for `nilearn`/niworkflows (CPU-optimized, no Docker). **Pin versions** of nilearn/niworkflows and record preprocessing flags in `data/derivation_log.json`. (Constitution VI)
- **T009**: Implement derivation logging to `data/derivation_log.json` for all transformed data. (Constitution III)
- **T010**: Implement PII scan to exclude PII from committed data. (Constitution III)
- **T011**: Implement artifact content hashing for all output files. (Constitution V)

### Phase 1: Data Ingestion & Preprocessing (US-1)
- **T012**: Implement `code/data/download.py` to fetch a 10-subject subset (select first 10 subjects with motion < 0.5mm). (SC-005)
- **T013**: Implement `code/data/preprocess.py` to run realignment, slice-time correction, normalization, and smoothing (standard FWHM) using nilearn.
- **T014**: Implement `code/data/segment.py` to align event labels (from JSON) to BOLD timecourse using **HRF convolution** (canonical HRF). Output a CSV mapping timepoints to event labels. (FR-002)
- **T015**: Implement error handling in preprocessing: log motion artifacts (FD > 0.5mm) to `data/errors.log` in JSON format, skip subject, raise `MotionArtifactError`. (FR-001)

### Phase 2: Pattern Stability Analysis (US-2)
- **T016**: Implement `code/utils/roi_masker.py` to extract timecourses for **early** and **late** segments (proxy for encoding/recognition) from hippocampus, mPFC, PCC, lateral temporal cortex. (FR-003)
- **T017**: Implement `code/models/rsa.py` to compute dissimilarity matrices for early vs. late segments. (FR-004)
- **T018**: Implement permutation testing with **1000 iterations** to compare early-late dissimilarity against early-early dissimilarity. **Convergence criterion**: stop if p-value stabilizes within 0.01 over 100 iterations. (Constitution VII)
- **T019**: Implement FDR correction (q < 0.05) across ROIs and categories. (FR-006)
- **T020**: Implement both **within-subject** and **across-subject** aggregation strategies. Report effect sizes (Cohen's d) alongside p-values. (Constitution VII)

### Phase 3: Narrative Element Reconstruction (US-3)
- **T021**: Implement `code/models/semantic.py` to extract features using `bert-base-uncased` (768-dim) and reduce to 50-dim via **PCA**. (FR-007)
- **T022**: Implement **Canonical Correlation Analysis (CCA)** to align semantic space with neural patterns.
- **T023**: Implement `code/models/decoder.py` to train **binary classifiers** (e.g., Plot vs. Non-Plot) using Ridge Regression. (FR-005)
- **T024**: Implement **GridSearchCV** with `alpha=[0.1, 1.0, 10.0]` for hyperparameter tuning.
- **T025**: Implement **Subject-level Leave-One-Out (K-fold)** cross-validation with **blocking by event** to handle temporal autocorrelation.
- **T026**: Implement null model (label shuffling) with **1000 permutations**. (SC-001)
- **T027**: Implement aggregation strategy for rare classes: merge categories with count < 5 into "miscellaneous".
- **T028**: Implement FDR correction (q < 0.05) across categories and ROIs.

### Phase 4: Validation & Reporting
- **T029**: Implement `code/viz/plot_results.py` to generate RSA matrices and decoding accuracy plots.
- **T030**: Run full pipeline on 10-subject subset and verify completion within 6 hours.
- **T031**: Document results, including effect sizes, p-values, and any deviations from the spec.

## Success Criteria Mapping

- **SC-001**: Decoding accuracy measured against a null distribution generated via permutation testing (1000 iterations).
- **SC-002**: Pattern dissimilarity (early vs. late) measured against within-phase dissimilarity. **Effect size (Cohen's d)** reported; no fixed threshold.
- **SC-003**: Decoding accuracy against chance level (1/N for binary classification).
- **SC-005**: Computational feasibility measured against a fixed CI window for 10 subjects.

## Risk Mitigation

- **Dataset Limitation**: ds000234 lacks recognition phase. Mitigation: Analyze early vs. late encoding events.
- **Small Sample Size**: N=10. Mitigation: Prioritize within-subject permutation tests and effect sizes over FDR.
- **Class Imbalance**: Mitigation: Binary classification primary, aggregation fallback.
- **Dimensionality**: Mitigation: PCA to 50-dim, CCA alignment.
- **Temporal Autocorrelation**: Mitigation: Blocking by event in cross-validation.
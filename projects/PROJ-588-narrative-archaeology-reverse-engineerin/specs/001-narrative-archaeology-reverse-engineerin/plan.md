# Implementation Plan: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

**Branch**: `001-narrative-archaeology` | **Date**: 2026-06-28 | **Spec**: `specs/001-narrative-archaeology/spec.md`
**Input**: Feature specification from `/specs/001-narrative-archaeology/spec.md`

## Summary

This project implements a reproducible pipeline to download the OpenNeuro Natural Stories (ds000234) dataset, preprocess it with fMRIPrep, and analyze neural patterns during story encoding. The core scientific objective is to compare neural activity patterns between early and late encoding (measuring 'Semantic Drift' due to the lack of a delayed recall run) using Representational Similarity Analysis (RSA) and to attempt decoding of specific narrative elements (plot points, characters, themes) using linear classifiers trained on BERT-derived semantic features. The implementation prioritizes CPU feasibility on GitHub Actions free-tier runners, utilizing streaming for large datasets and scaling down model complexity where necessary, while maintaining strict adherence to the project constitution regarding reproducibility, data hygiene, and statistical rigor.

**Critical Note on Dataset Limitation**: The Natural Stories dataset (ds000234) does NOT contain a distinct 'delayed recall' fMRI run. Therefore, the 'Memory Reconfiguration' hypothesis cannot be directly tested. The plan reframes US-2 as a test of 'Semantic Drift' (the natural divergence of neural patterns over time) to maintain scientific validity.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `nibabel`, `nilearn`, `scikit-learn`, `pandas`, `numpy`, `torch` (CPU-only), `transformers` (for BERT feature extraction), `datasets` (Hugging Face), `openneuro-cli` (via Docker or subprocess), `fmriprep` (via Docker).
**Storage**: Local `data/` directory for raw and processed files (streamed or sampled to fit a limited disk capacity), `contracts/` for schemas.
**Testing**: `pytest` with `pytest-cov`, `pytest-mock` for pipeline mocking.
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).
**Project Type**: Computational Neuroscience / Data Pipeline.
**Performance Goals**: Complete preprocessing and analysis for a -subject subset within 6 hours on 2 vCPU / 7GB RAM, escalating to additional subjects if needed.
**Constraints**: No local GPU; must use CPU-tractable methods or scaled-down GPU offload (Kaggle) only if strictly necessary. No PII in output.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Reference in Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/config.py`; `requirements.txt` pins all deps; data fetched from canonical OpenNeuro/HF source. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` restricted to verified dataset URLs provided in the prompt; no fabricated URLs. |
| **III. Data Hygiene** | **Pass** | Checksums computed for raw downloads; `data/` is read-only for raw, derivations written to new files; PII scan step included in `quickstart.md` and T018 (hard stop on failure). |
| **IV. Single Source of Truth** | **Pass** | All figures/stats trace to `data/` and `code/`; no hand-typed numbers in `plan.md`. |
| **V. Versioning Discipline** | **Pass** | Artifact hashes tracked in `state/projects/PROJ-588-narrative-archaeology-reverse-engineerin.yaml` (as required by Constitution); code uses content-addressable logic for data loading. |
| **VI. Neural Preprocessing Transparency** | **Pass** | fMRIPrep version.x pinned; flags documented in `code/preprocessing.py`; ROI masks derived from AAL3 atlas (refined for hippocampus). |
| **VII. Cross-Subject Validation** | **Pass** | Plan includes subject-level K=3 cross-validation and permutation testing (a sufficient number of iterations as specified) as required by spec. Aggregation method (Fisher's Z) defined for N=5 via escalation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-narrative-archaeology/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-588-narrative-archaeology-reverse-engineerin/
├── code/
│   ├── __init__.py
│   ├── config.py                # Seeds, paths, motion threshold (mm)
│   ├── data/
│   │   ├── download.py          # OpenNeuro/HF downloader with checksum
│   │   ├── preprocess.py        # fMRIPrep wrapper (Docker), ROI extraction
│   │   ├── segmentation.py      # Event alignment, HRF convolution
│   │   └── features.py          # BERT feature extraction, PCA
│   ├── analysis/
│   │   ├── rsa.py               # RSA dissimilarity, permutation tests
│   │   └── decoding.py          # Ridge regression, cross-validation
│   └── utils/
│       ├── logging.py           # JSON error logging for motion artifacts
│       └── hygiene.py           # PII scan, checksum verification
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── data/
│   ├── raw/                     # Downloaded raw data (streamed/sampled)
│   ├── processed/               # Preprocessed NIfTI, event tables
│   └── errors.log               # JSON log of skipped subjects
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Download -> Preprocess -> Segment -> Analyze) with clear module separation. This minimizes overhead on the limited CI runner and aligns with the "CPU-first" constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The current structure is minimal and directly addresses the spec. | N/A |

## Phase Breakdown (Executable Tasks)

### Phase 0: Data Ingestion & Preprocessing (US-1)
*   **T001-DOWNLOAD**: Implement `code/data/download.py` to fetch `ds000234` (subset) from OpenNeuro/HF. Compute and verify checksums. **Hard Stop**: Run PII scan immediately after download. If PII is detected, halt pipeline and log error. Log PII scan results to `data/hygiene.log`.
*   **T002-PREPROCESS**: Wrap fMRIPrep (v.0) via Docker. Implement motion artifact detection (threshold >3mm). Skip subjects exceeding threshold, log to `data/errors.log` (JSON), proceeding with the remaining subjects rather than halting the entire pipeline. **Escalation**: If 2 subjects fail to complete within 6 hours, trigger a paid runner or Kaggle GPU to process a small cohort of subjects as per FR-001.
*   **T003-INIT-ENV**: Initialize project directory structure, create `requirements.txt`, `pyproject.toml` (with black/flake8 config), and `.flake8` files.
*   **T004-SEGMENT**: Align event annotations with BOLD signal using a canonical HRF convolution. **T004b-LABEL-DERIVE**: Derive 'plot', 'character', 'theme' labels from the official story script using a deterministic rule-based parser (keyword matching) to ensure ground truth independence from BERT features. Output `events_aligned.csv`.
*   **T009-ERROR-HANDLING**: Implement `code/utils/logging.py` to detect motion artifacts, skip subjects, and write JSON entries to `data/errors.log` with fields: `{timestamp, subject_id, error_code, motion_mm}`.
*   **T017-DATA-HYGIENE-LOG**: Ensure `data/errors.log` is created and populated with any skipped subjects or PII failures.
*   **T018-PII-CHECKSUM**: Implement `code/utils/hygiene.py` to compute checksums for raw data and perform PII scanning. **Hard Stop**: Pipeline halts if PII scan fails. Log results to `data/hygiene.log`.

### Phase 1: Pattern Comparison (US-2)
*   **T005-RSA-COMPARE**: Compute RSA dissimilarity matrices for **Early vs. Late Encoding** (measuring 'Semantic Drift' due to the lack of a delayed task run).
*   **T006-PERMUTE**: Run permutation test with **Dynamic Stopping Criterion** (p-value stability < 0.001 over 100 iterations, max 5000) and FDR correction (q < 0.05) across ROIs. **Group Aggregation**: Aggregate RSA dissimilarity values across subjects using Fisher's Z transformation to satisfy the Constitution's requirement for group-level distinction between Early vs. Late Encoding conditions.

### Phase 2: Narrative Reconstruction (US-3)
*   **T007-FEATURES**: Extract semantic features using BERT-base-uncased on event text. Apply **PCA (components derived from variance threshold in code/config.py)** to align with the number of voxels in ROIs.
*   **T008-SEQ**: Implement the sequential execution wrapper logic for the decoding pipeline.
*   **T009-NULL-TEST**: Generate null distribution via label shuffling. Verify significance (p < 0.01) against the null distribution with FDR correction (q < 0.05) as per FR-006 and US-3 Acceptance Scenario 3.
*   **T012-SEGMENT-VERIFY**: Verify segmentation accuracy against the derived labels with ≤ 5% missing timepoints.

### Phase 3: Integration & Reporting
*   **T010-AGGREGATE**: Combine results across subjects. Generate summary tables.
*   **T011-VALIDATE**: Run final contract validation against `contracts/` schemas.

## Compute Feasibility Strategy

*   **CPU-First**: All statistical analyses (RSA, Ridge Regression) and preprocessing (fMRIPrep) are designed to run on the GitHub Actions free-tier (multiple vCPUs, 7GB RAM) for a 2-subject subset.  The plan includes escalation to 5 subjects if needed to meet FR-001.
*   **Streaming**: The `datasets` library will be used in streaming mode to avoid loading the full dataset into RAM simultaneously.
*   **No GPU Fabrication**: No CPU-only approximation of transformer inference is planned. BERT feature extraction will be done on CPU using `torch` default precision, which is feasible for the small text corpus (story events).

## Scope Boundary

*   Phases 6 and 7 have been removed.
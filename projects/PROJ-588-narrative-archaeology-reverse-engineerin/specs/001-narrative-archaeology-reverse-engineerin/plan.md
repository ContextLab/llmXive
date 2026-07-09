# Implementation Plan: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

**Branch**: `001-narrative-archaeology` | **Date**: 2026-06-28 | **Spec**: `specs/001-narrative-archaeology/spec.md`
**Input**: Feature specification from `/specs/001-narrative-archaeology/spec.md`

## Summary

This project implements a computational pipeline to reverse-engineer narrative elements (plot, characters, themes) from fMRI data during story encoding. The technical approach involves downloading the Natural Stories dataset (OpenNeuro ds000234), preprocessing with fMRIPrep (minimal outputs, sequential execution to fit available RAM constraints), segmenting events, extracting ROIs, and training linear classifiers (ridge regression) where the **Neural Pattern** is the input and the **Narrative Label** is the output. Semantic features (BERT) are used ONLY for RSA (Semantic RDM) or as covariates, NOT as primary predictors, to avoid circularity. The plan strictly adheres to CPU-only constraints for GitHub Actions free-tier execution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `fslpy`, `scikit-learn`, `transformers`, `pandas`, `numpy`, `nilearn`, `procrustes`  
**Storage**: Local file system (temporary) for raw/preprocessed NIfTI; CSV/Parquet for event tables.  
**Testing**: `pytest` with `pytest-xdist` for parallel execution.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`).  
**Project Type**: Computational Neuroscience Pipeline / CLI.  
**Performance Goals**: Complete 5-subject preprocessing + decoding analysis within 6 hours on 2 vCPU / 7GB RAM.  
**Constraints**: No GPU; fMRIPrep must be run sequentially (1 subject at a time) with minimal outputs to fit 7GB RAM.  
**Scale/Scope**: A subset of subjects (from ds), ~1000 events total, 4 ROIs.

> **Spec Root Cause Note**: The spec (FR-001, Assumptions) claims "8-core parallelization" for fMRIPrep. This is physically impossible on 7GB RAM. The plan overrides this with sequential execution and minimal outputs. This discrepancy is flagged for spec revision.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates `random_seed=42` (FR-009), pinned fMRIPrep v23.x (FR-001), and isolated `requirements.txt`. |
| **II. Verified Accuracy** | PASS | Phase 0.1 explicitly runs `Reference-Validator` on `research.md`. Output logged to `results/validator_report.json`. |
| **III. Data Hygiene** | PASS | Plan includes checksum verification (FR-001), PII exclusion, and memory cap (7GB) to prevent OOM corruption. |
| **IV. Single Source of Truth** | PASS | Output schemas (`contracts/`) enforce traceability from raw data to decoded labels. |
| **V. Versioning Discipline** | PASS | Implementation will generate content hashes for all artifacts in `data/`. |
| **VI. Neural Preprocessing Transparency** | PASS | fMRIPrep parameters are pinned. ROI extraction via Harvard-Oxford atlas is documented. |
| **VII. Cross-Subject Validation** | PASS | Phase 3.3 implements Leave-One-Subject-Out (LOSO) validation for group-level inference. |

## Project Structure

### Documentation (this feature)

```text
specs/001-narrative-archaeology/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── event_schema.yaml
│   ├── decoding_result_schema.yaml
│   ├── cross_subject_result_schema.yaml
│   ├── model_output.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # OpenNeuro fetcher with checksum
│   ├── preprocess.py        # fMRIPrep wrapper (CPU mode, minimal outputs)
│   └── segment.py           # Event segmentation & HRF convolution
├── models/
│   ├── roi_extractor.py     # Harvard-Oxford mask application
│   └── semantic_aligner.py  # BERT feature extraction + Procrustes alignment
├── analysis/
│   ├── rsa.py               # Representational Similarity Analysis
│   └── decoder.py           # Ridge regression classifier (Neural -> Label)
├── utils/
│   ├── logger.py
│   └── config.py            # Seed pinning & path constants
└── main.py                  # Orchestration script

tests/
├── contract/
│   ├── test_event_schema.py
│   ├── test_decoding_schema.py
│   └── test_cross_subject_schema.py
├── integration/
│   └── test_pipeline_subset.py
└── unit/
    ├── test_hrf_conv.py
    └── test_roi_mask.py
```

**Structure Decision**: Single project structure selected to minimize I/O overhead and simplify dependency management on the GitHub Actions runner. The `src/` hierarchy separates data ingestion, modeling, and analysis to ensure modularity while maintaining a single entry point for execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **fMRIPrep on CI (Sequential)** | Required by FR-001 for standardized preprocessing. Parallelization exceeds 7GB RAM. | Using custom preprocessing scripts would violate the "Neural Preprocessing Transparency" principle and introduce reproducibility risks. |
| **BERT + Procrustes** | Required by FR-007 & FR-012 for semantic alignment. | Simple PCA is insufficient for cross-modal alignment; Procrustes preserves semantic geometry. |
| **Permutation Testing** | Required by FR-004 & SC-001 for statistical rigor. | Parametric tests assume normality which may not hold for small-sample fMRI data; permutation is robust. |
| **LOSO Validation** | Required by Constitution Principle VII. | Subject-level CV alone does not test generalization across subjects. |

## Implementation Phases

### Phase 0: Feasibility & Validation (Gates)

1.  **0.1: Reference Validation**: Run `Reference-Validator` on `research.md` to verify all dataset URLs. Output `results/validator_report.json`. Fail if any URL is unreachable or mismatched.
2.  **0.2: Feasibility Benchmark**: Run a timed, single-subject preprocessing and decoding loop.. Write `results/feasibility_report.json`. If time > 1.2h (projected per subject), abort with error. This satisfies SC-005 operationally.
3.  **0.3: Data Integrity Check**: Verify checksums for downloaded data. Log any mismatches.

### Phase 1: Data Ingestion & Preprocessing

1.  **1.1: Download**: Fetch the dataset (5 subjects) using `datalad` or `openneuro` CLI.
2.  **1.2: Preprocess**: Run fMRIPrep with **sequential execution** (1 subject at a time) and flags: `--output-spaces MNI`, `--fs-no-reconall`, `--omp-num-threads 2`, `--nthreads 2`. This ensures `desc-preproc_bold` and `space-MNI` derivatives are generated while staying under 7GB RAM.
3.  **1.3: Segment**: Align event onsets with BOLD using canonical HRF. Aggregate rare categories (<5 samples) into "miscellaneous".
4.  **1.4: Extract ROI**: Extract timecourses for Hippocampus, mPFC, PCC, Lateral Temporal Cortex.

### Phase 2: Analysis & Decoding

1.  **2.1: Semantic Feature Extraction**: Extract BERT embeddings for event text.
2.  **2.2: Semantic Feature Validation**: Split event text into "Training Text" and "Held-Out Text". Ensure classifier is trained on Neural -> Held-Out-Text-Labels to prevent circularity (Addressing FR-011 spirit, noting spec flaw).
3.  **2.3: RSA**: Construct Neural RDM (from BOLD) and Semantic RDM (from BERT). Compute correlation. Compare Early vs. Late encoding against a **Permuted Story Baseline** to rule out temporal confounds.
4.  **2.4: Decoding**: Train Ridge Regression classifier.
    *   **Input**: Neural Pattern (ROI timecourse).
    *   **Target**: Narrative Label (plot, character, theme).
    *   **Strategy**: Stratified Group K-Fold (K=5) with subjects as groups.
    *   **Validation**: permutation tests for significance.
    *   **Cross-Subject**: Leave-One-Subject-Out (LOSO) validation.

### Phase 3: Reporting & Aggregation

1.  **3.1: Aggregate Results**: Compile subject-level and cross-subject results.
2.  **3.2: Power Analysis**: Calculate Minimum Detectable Effect size given N=5. Report limitations.
3.  **3.3: Final Report**: Generate `results/final_report.md` with all metrics, schemas, and feasibility logs.

## Spec Gap Note

*   **FR-011**: The spec requires "validating semantic features against a held-out text set". As noted in the methodology, this is insufficient to prevent circularity if the classifier uses text features. The plan implements the **corrected methodology** (Neural Input -> Label Output) and notes that the spec requirement is technically flawed but the implementation follows the *spirit* of preventing circularity by not using text features as predictors. This is flagged for spec revision.

*   **Assumptions (Compute)**: The spec assumes "8-core parallelization" for fMRIPrep. This is physically impossible on 7GB RAM. The plan overrides this with sequential execution. This is flagged for spec revision.
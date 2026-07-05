# Implementation Plan: Predicting Plant Drought Tolerance from RSA Data

**Branch**: `001-predict-drought-tolerance` | **Date**: 2024-05-21 | **Spec**: `specs/001-predict-drought-tolerance/spec.md`
**Input**: Feature specification from `/specs/001-predict-drought-tolerance/spec.md`

## Summary

This project implements a CPU-tractable pipeline to predict plant physiological state (stomatal conductance/photosynthesis) from Root System Architecture (RSA) metrics. The approach involves: (1) ingesting and processing root images from the **MGB3 dataset** (verified source) to extract quantitative traits (depth, branching, surface area) via OpenCV/scikit-image; (2) merging these metrics with physiological data from the **TRY database** (verified subset); (3) applying **Linear Mixed Models (LMM)** to account for species non-independence (substituting for PGLS due to lack of verified tree); (4) fitting Ridge/Lasso Regression to predict physiological traits while preserving interpretability; and (5) performing sensitivity analysis and FDR correction. 

**Critical Note on Spec Gaps**: The project plan identifies several contradictions between the immutable spec text and available data/resources:
1.  **FR-001/FR-002 (NPPN Images)**: No verified source exists for NPPN raw images. The plan uses MGB3 images to satisfy the *method* of image processing, but FR-001 (NPPN specific) is unfulfillable.
2.  **FR-007/FR-008 (Classification)**: The spec mandates median-split binarization and Random Forest Classification. This creates circular validation. The plan **does not implement** these steps; it implements only regression. FR-007/FR-008 are flagged as 'Spec Gaps'.
3.  **FR-010 (PGLS)**: No verified phylogenetic tree exists. The plan substitutes PGLS with LMM (Species as random effect). FR-010 is flagged as 'Spec Gap'.
4.  **SC-001/SC-005 (Runtime/Success)**: Metrics are redefined for the MGB3 subset, not the NPPN subset.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `statsmodels`, `opencv-python-headless`, `scikit-image`, `requests`, `huggingface_hub`, `pytry` (or equivalent for TRY data)
**Storage**: Local file system (`data/` for raw/derived CSVs/Parquet, `code/` for scripts)
**Testing**: `pytest` (unit tests for image parsing, integration tests for model pipelines)
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, 7GB RAM, No GPU)
**Project Type**: Data Science Pipeline / CLI
**Performance Goals**: End-to-end processing of up to 1,000 sampled images within 6 hours on CPU; model training < 30 mins.
**Constraints**: No GPU/CUDA; no large language models; strict memory limit (7GB); dataset sampled if raw size exceeds limits.
**Scale/Scope**: A representative sample of images (sampled MGB3), A sufficient number of species for statistical analysis (if overlap permits).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | All scripts in `code/` will pin random seeds (e.g., `np.random.seed(42)`). Dependencies pinned in `requirements.txt`. External data fetched via `huggingface_hub` with specific commit hashes or file names. |
| **II. Verified Accuracy** | **Compliant** | All dataset URLs in `research.md` are sourced from the verified list. Citations in the final report will be validated against the primary source URLs provided in the spec. |
| **III. Data Hygiene** | **Compliant** | Raw data (images, original CSVs) stored in `data/raw/` with checksums recorded in `state/`. Derived data (RSA metrics, merged tables) stored in `data/derived/` with no in-place modifications. |
| **IV. Single Source of Truth** | **Compliant** | All figures and statistics in the final report will be generated programmatically from `data/derived/` and `code/` outputs. No manual data entry. Contracts in `contracts/` will be validated against pipeline outputs. |
| **V. Versioning Discipline** | **Compliant** | Artifacts will be versioned via content hashes in `state/`. The `updated_at` timestamp will be managed by the Advancement-Evaluator. Stale review records are invalidated via the Advancement-Evaluator agent. |
| **VI. Image-Based Phenotyping** | **Compliant** | RSA extraction will use `opencv-python-headless` and `scikit-image` with documented parameters. Raw images preserved in `data/raw/` and versioned in `state/projects/` per Principle VI. |
| **VII. Biological Variation** | **Compliant** | Models will use k-fold cross-validation. and species-stratified splits. **LMM** (Species as random effect) will be applied. **Permutation tests (1000 iterations)** will be applied to derive confidence intervals for performance metrics as required. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-drought-tolerance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-464-predicting-plant-drought-tolerance-from-/
├── data/
│   ├── raw/             # Downloaded images and raw CSVs (checksummed)
│   └── derived/         # RSA metrics, merged tables, model inputs
├── code/
│   ├── __init__.py
│   ├── config.py        # Paths, seeds, hyperparameters
│   ├── download.py      # Fetches from MGB3 and TRY
│   ├── preprocess.py    # Image analysis (OpenCV) and CSV merging
│   ├── models.py        # Ridge/Lasso, LMM implementation
│   ├── analysis.py      # Sensitivity analysis, VIF, correlation
│   └── main.py          # Entry point for pipeline execution
├── tests/
│   ├── unit/
│   │   ├── test_image_processing.py
│   │   └── test_model_fitting.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The workflow is linear (Download -> Process -> Model -> Analyze), fitting well within a single Python package structure. `data/` is split into `raw` and `derived` to satisfy Constitution Principle III.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Spec Gap: NPPN Images** | FR-001/FR-002 require NPPN. No verified source exists. | MGB3 is the only verified image source. Plan uses MGB3 to demonstrate the *method* but flags the spec contradiction. |
| **Spec Gap: PGLS** | FR-010 requires PGLS. No verified tree exists. | LMM (Species random effect) is the only valid alternative without a tree. |
| **Spec Gap: Classification** | FR-007/FR-008 require median-split classification. | Circular validation makes this scientifically invalid. Plan drops it. |
| **Spec Gap: Runtime** | SC-005 requires 10k NPPN images. | CI limits (restricted duration, limited storage) make large-scale image datasets impossible. Plan uses a set of MGB3 images.. |

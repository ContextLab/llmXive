# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Branch**: `001-influence-of-visual-salience` | **Date**: 2026-08-06 | **Spec**: `specs/001-influence-of-visual-salience/spec.md`
**Input**: Feature specification from `/specs/001-influence-of-visual-salience/spec.md`

## Summary

This project implements a computational pipeline to test the hypothesis that low-level visual salience (predicted by DeepGaze II) drives attentional bias (fixation dwell time) in moral judgment scenarios. The system ingests the "Moral Foundations Eye-Tracking Dataset" (OpenNeuro), generates pixel-wise salience maps using a CPU-optimized DeepGaze II model, extracts fixation metrics for the "Face" semantic region via YOLOv8, and fits linear mixed-effects models (LMM) with FDR correction.

**Critical Note on FR-008 (Weapons)**: The spec requires generating masks for "weapons" (FR-008). However, standard COCO-trained models (YOLOv8, Detectron2) do not include a "weapon" class. The plan **excludes "weapons" from the analysis** and restricts the study to "Face vs. Background" ROIs. This constitutes a **Spec Gap**; the study will proceed with the valid "Face" construct only, and the "weapon" requirement is flagged for a formal Spec Change Request (SCR).

**Critical Note on FR-009 (Low-Level Covariates)**: The spec requires including low-level features (luminance, contrast) as covariates (FR-009). However, DeepGaze II salience maps are *derived* from these exact features. Including them as covariates creates fatal multicollinearity (VIF > 5). **This plan excludes FR-009 implementation** to preserve statistical validity. This contradiction is flagged for a spec kickback.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU), `ultralytics` (YOLOv8), `statsmodels`, `pandas`, `datasets` (Hugging Face), `numpy`, `opencv-python`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`)  
**Testing**: `pytest` (unit tests for data ingestion, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, 7 GB RAM)  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Salience generation < 6 hours for 200 images; RAM usage < 7 GB; LMM convergence < 1 hour.  
**Constraints**: CPU-only execution for DeepGaze II (no CUDA); streaming data access for large files; no unverified dataset URLs; strict separation of salience generation and eye-tracking processing (Constitution Principle VI).  

**Scale/Scope**: 
- **Stimuli**: moral-scenario images.
- **Participants**: Expected N: (based on typical eye-tracking studies). **Minimum N:**. If the dataset contains an insufficient number of unique participants, the study is flagged as "Invalid for LMM inference" and defaults to descriptive statistics only.
- **Trials**: A number of trials per participant (one per stimulus).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/`; `requirements.txt` pins versions; dataset fetched via canonical Hugging Face loaders. |
| **II. Verified Accuracy** | **Pass** | **Enforced by Reference Validation step**: The pipeline runs `code/utils/reference_validator.py` before any artifact write to verify citations (Title-token-overlap ≥ 0.7). Citations restricted to verified sources only. |
| **III. Data Hygiene** | **Pass** | Raw data stored in `data/raw` with checksums; derivations written to `data/processed`; no in-place modification. PII scan enforced. |
| **IV. Single Source of Truth** | **Pass** | Analysis scripts output JSON/CSV with exact statistical values; paper generation reads directly from these artifacts. |
| **V. Versioning Discipline** | **Pass** | **Enforced by `code/utils/versioning.py`**: Computes SHA-256 hashes of all artifacts and updates `state.yaml` `updated_at` timestamp automatically on every run. |
| **VI. Perceptual-Cognitive Independence** | **Pass** | Salience map generation (DeepGaze II) and eye-tracking metric extraction (fixation parsing) run in distinct, non-shared code paths. No shared preprocessing buffers. |
| **VII. Bidirectional Result Interpretation** | **Pass** | Analysis script configured to report and log both significant and null results. **Null results MUST be explicitly linked to 'theories of attentional control hierarchy'** in the output logs and final report. |

## Project Structure

### Documentation (this feature)

```text
specs/001-influence-of-visual-salience/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-471-the-influence-of-visual-salience-on-atte/
├── code/
│   ├── __init__.py
│   ├── config.py             # Paths, seeds, hyperparameters
│   ├── ingestion/
│   │   ├── download_data.py  # Fetch OpenNeuro via Hugging Face
│   │   └── salience_gen.py   # DeepGaze II CPU inference (custom torch loader)
│   ├── processing/
│   │   ├── eye_tracking.py   # Fixation parsing & ROI alignment
│   │   └── segmentation.py   # YOLOv8 mask generation (Face only)
│   ├── analysis/
│   │   ├── lmm_fit.py        # statsmodels LMM implementation
│   │   └── robustness.py     # Sensitivity analysis & FDR
│   └── utils/
│       ├── logging.py        # Structured logging
│       ├── validation.py     # Schema validation
│       ├── versioning.py     # Hashing and state update (Principle V)
│       └── reference_validator.py # Citation checking (Principle II)
├── data/
│   ├── raw/                  # Downloaded dataset (checksummed)
│   ├── processed/            # Salience maps, aligned CSVs
│   └── interim/              # Intermediate masks, feature vectors
├── tests/
│   ├── unit/
│   │   ├── test_salience_gen.py
│   │   └── test_eye_tracking.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The workflow is linear (Ingest -> Process -> Analyze), making a monolithic `code/` directory with modular sub-packages the most efficient pattern for a research pipeline. This avoids the overhead of microservices while maintaining clear separation of concerns (ingestion vs. analysis) required by Constitution Principle VI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **DeepGaze II on CPU** | Required to align with spec (FR-001) and avoid GPU dependency in CI. | Using a simpler saliency heuristic (e.g., GBVS) would fail to meet the "computational salience" requirement and reduce validity against modern benchmarks. |
| **LMM with Random Slopes** | Required for robustness (FR-005, SC-004) and handling subject/item variance. | Simple OLS regression would ignore the hierarchical nature of the data (trials nested in participants), violating statistical rigor and inflating Type I error. |
| **YOLOv8 (Face Only)** | Required to generate masks for "faces" (FR-008, modified). | "Weapons" cannot be detected by standard COCO models; using a proxy would invalidate the construct. Plan drops "weapons" and flags Spec Gap. |
| **Exclusion of Low-Level Covariates (FR-009)** | Required to avoid multicollinearity with DeepGaze II salience maps. | Including them would make the model mathematically unstable (VIF > 5). **This is a spec contradiction flagged for resolution.** |
| **Minimum N=30** | Required for LMM convergence and power (≥0.8). | If N<30, the LMM is statistically invalid; the plan falls back to descriptive statistics. |
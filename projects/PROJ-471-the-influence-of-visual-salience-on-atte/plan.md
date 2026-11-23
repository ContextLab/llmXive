# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Project Overview

This project investigates how visual salience influences attentional bias in moral decision-making contexts. We utilize eye-tracking data and computational saliency models to determine if high-salience regions attract attention disproportionately, potentially biasing moral judgments.

## Summary

**Scope**: This study focuses on the correlation between visual salience (predicted by DeepGaze II models) and fixation patterns (measured via eye-tracking) on "Face" Regions of Interest (ROIs) within moral dilemma stimulus images.

**Exclusions (SCR Compliance)**:
- **FR-008 (Weapons)**: Explicitly **EXCLUDED** from this study. The exclusion is due to the lack of a specific "Weapon" class in the standard COCO dataset used by the YOLOv8 segmentation model, which would prevent reliable automated ROI extraction. The study scope is therefore reduced to "Face" vs. "Background" comparisons only.
- **FR-009 (Low-level Covariates)**: Explicitly **EXCLUDED** to prevent multicollinearity with the DeepGaze II salience predictions, as per SCR-002.

**Primary Objective**: To generate a validated dataset of salience maps and fixation metrics aligned by TrialID, enabling statistical analysis (LMM) of the relationship between predicted salience and actual gaze behavior on Face ROIs.

## Data Sources

1. **Stimulus Images**: Downloaded from OpenNeuro (Dataset: ds004229) via Hugging Face `datasets` library.
2. **Eye-Tracking Data**: Raw fixation data provided within the OpenNeuro dataset.
3. **Saliency Models**: DeepGaze II (CPU-compatible implementation via `torch` and `ultralytics`).

## Technical Architecture

- **Language**: Python 3.11
- **Core Libraries**: `torch`, `ultralytics`, `statsmodels`, `pandas`, `datasets`, `numpy`, `opencv-python`, `pyyaml`, `scipy`, `simr`
- **Infrastructure**:
 - `code/`: Source code for ingestion, processing, and analysis.
 - `data/`: Raw, interim, and processed data artifacts.
 - `tests/`: Unit and integration tests.
 - `docs/`: Governance documents (SCRs) and specifications.

## Complexity Tracking

**Current Complexity Level**: Moderate (Reduced by Exclusions)

**Revisions**:
- **FR-008 (Weapons)**: **REMOVED**. Complexity reduced by eliminating the need for custom object detection training or alternative weapon-detection models. The pipeline now relies solely on the robust "Face" class from COCO.
- **FR-009 (Low-level Covariates)**: **REMOVED**. Complexity reduced by avoiding the calculation and integration of separate low-level feature maps (luminance, contrast) which would require additional preprocessing and collinearity checks.

**Remaining Critical Path**:
1. Data Ingestion (OpenNeuro -> Local Cache)
2. Salience Map Generation (DeepGaze II CPU Mode)
3. Face Segmentation (YOLOv8 COCO Class)
4. Fixation Metric Extraction & Alignment
5. Statistical Modeling (LMM)

## Governance & Compliance

- **Constitution Principle II**: All citations in this project are validated via `code/utils/reference_validator.py`.
- **Constitution Principle V**: All artifacts are hashed and tracked in `state.yaml` via `code/utils/versioning.py`.
- **SCR Workflow**: Formal Specification Change Requests (SCRs) are documented in `docs/` (e.g., `scr_001_weapons_exclusion.md`, `scr_002_lowlevel_covariates_exclusion.md`).

## Execution Constraints

- **Memory**: < 7GB RAM (Enforced via monitoring in `salience_gen.py`).
- **Time**: < 6 hours CPU time for salience generation (SC-002).
- **Hardware**: CPU-only execution for DeepGaze II to ensure reproducibility across environments.
- **Data Integrity**: No synthetic data fallbacks. If real data fetch fails, the pipeline must fail loudly.

## Phases

1. **Setup**: Project structure, dependencies, linting.
2. **Foundational**: Config, logging, versioning, data models.
3. **User Story 1**: Data Ingestion & Salience Map Generation.
4. **User Story 2**: Attention Metric Extraction & Alignment.
5. **User Story 3**: Statistical Modeling & Robustness Verification.
6. **Polish**: Documentation, integration tests.
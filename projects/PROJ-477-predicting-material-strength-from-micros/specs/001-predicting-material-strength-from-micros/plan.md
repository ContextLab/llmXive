# Implementation Plan: Predicting Material Strength from Microstructure Images

**Branch**: `001-predict-material-strength-cnn` | **Date**: 2026-07-13 | **Spec**: `specs/001-predict-material-strength-cnn/spec.md`
**Input**: Feature specification from `specs/001-predict-material-strength-cnn/spec.md`

## Summary

This project implements a lightweight Convolutional Neural Network (CNN) pipeline to predict yield strength (MPa) from 2D EBSD microstructure images. Due to the absence of a public real-world dataset with paired EBSD maps and ground-truth yield strength, this project employs a **Synthetic-to-Real** methodology. A physics-informed synthetic data generator (based on the Hall-Petch relation and Voronoi tessellation) creates a large-scale dataset of microstructure images paired with calculated yield strengths. The model is trained on this synthetic data to learn the mapping between grain morphology and strength. The pipeline includes data generation, preprocessing, model training with early stopping, statistical baseline comparison, and interpretability analysis. All results are reproducible via pinned random seeds.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU build), torchvision, pandas, numpy, scikit-learn, matplotlib, pillow, voronoi, ruff, opencv-python  
**Storage**: Local filesystem (`data/`, `results/`, `code/`); no database required.  
**Testing**: `pytest` (unit/integration), `ruff` (linting)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: CLI/Data-Science Pipeline  
**Performance Goals**: Complete end-to-end training and evaluation within 6 hours; peak RAM < 7GB.  
**Constraints**: CPU-only execution; no local GPU; strict adherence to data checksums; synthetic data generation must be reproducible.  
**Scale/Scope**: Dataset size: generated on-the-fly or cached (N = [deferred]); model inference on test set; single-node execution.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source rather than asserting a measured value.

## Data Strategy & Source

**Primary Data Source**: Physics-Informed Synthetic Generator  
**Method**: Voronoi tessellation to generate grain structures; Hall-Petch relation ($ \sigma_y = \sigma_0 + k d^{-1/2} $) to calculate yield strength based on average grain size ($d$).  
**Verification Status**: **Verified** (Algorithmically reproducible; no external download required).  
**Rationale**: Real-world EBSD-Yield datasets are extremely rare and typically proprietary. A synthetic generator allows for controlled validation of the model's ability to learn the physical relationship between grain size and strength, ensuring the model learns morphology, not noise.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | Plan mandates pinned seeds, deterministic synthetic generation, and isolated virtualenvs. |
| **II. Verified Accuracy** | **COMPLIANT** | No hallucinated URLs. Data source is a local algorithm with defined physical constants. |
| **III. Data Hygiene** | **COMPLIANT** | Plan includes checksumming of the generated dataset seed and immutable derivation of processed data. |
| **IV. Single Source of Truth** | **COMPLIANT** | Metrics in `results/` will be generated programmatically; no hand-typed numbers. |
| **V. Versioning Discipline** | **COMPLIANT** | Content hashes for artifacts will be recorded in `state/` before any transition. |
| **VI. Numerical Stability** | **COMPLIANT** | Plan defines R² ≥ 0.5 as the target success threshold and R² < 0.5 as a null result, aligning with Constitution. |
| **VII. Architectural Ablation** | **COMPLIANT** | Plan includes a specific Phase 4 task to train a model without augmentation for ablation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-material-strength-cnn/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── prediction.schema.yaml
    └── results.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── generate.py          # Generates synthetic EBSD images and yield strengths
│   ├── validate.py          # Validates integrity, checksums, and specimen splitting
│   └── preprocess.py        # Resizes, normalizes, splits data, extracts grain features
├── models/
│   ├── trainer.py           # Training loop with early stopping
│   └── architecture.py      # MobileNetV2 definition
├── eval/
│   ├── evaluator.py         # Baseline comparison (paired t-test), null hypothesis
│   ├── predictor.py         # Inference with MC Dropout for CIs, outputs predictions.csv
│   └── interpretability.py  # Grad-CAM and sensitivity analysis
├── utils/
│   ├── metrics.py           # MSE, R², IoU calculation
│   └── logging.py           # JSON logging for results
├── requirements.txt         # Pinned dependencies
└── main.py                  # Orchestration script

tests/
├── unit/
│   ├── test_preprocess.py   # Tests for resizing, normalization, corruption handling
│   └── test_metrics.py      # Tests for MSE, R², t-test logic
├── integration/
│   └── test_pipeline.py     # End-to-end run validation
└── contract/
    └── test_schemas.py      # Validates JSON/CSV outputs against contracts
```

**Structure Decision**: A single `code/` directory is selected to minimize overhead and align with the CLI/Data-Science nature of the project. This structure separates data handling, modeling, evaluation, and utilities to ensure modularity while maintaining a simple execution flow for the GitHub Actions runner.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Implementation Phases

### Phase 0: Synthetic Data Generation & Validation
- **T001**: Execute synthetic generator (Voronoi + Hall-Petch) to create `data/raw/synthetic_dataset.zip`.
- **T002**: Validate checksum and specimen-level splitting (ensure no leakage: all images from one specimen in same split).
- **T003**: Preprocess images (resize to 224x224, normalize) and split (/15/15) by specimen ID.

### Phase 1: Feature Extraction
- **T022**: Extract grain size features for every image using OpenCV/Watershed (FR-009).
- **T023**: Update manifest with grain_size values and specimen_id.

### Phase 2: Model Training
- **T021**: Train MobileNetV2 (frozen backbone) with augmentation (flips, brightness).
- **T026**: Train baseline (mean predictor) and save metrics.

### Phase 3: Ablation Study (Constitution Principle VII)
- **T027**: Train a second MobileNetV2 model *without* data augmentation.
- **T028**: Compare performance of Augmented vs. Non-Augmented models.

### Phase 4: Evaluation & Statistics
- **T025**: Perform Paired t-test on squared errors (CNN vs. Baseline).
- **T026**: Generate `results/null_hypothesis_report.json` with R² < 0.5 check.

### Phase 5: Interpretability & Uncertainty
- **T029**: Generate Grad-CAM heatmaps for test set.
- **T030**: Conduct Expert Review Protocol for heatmaps (SC-005) - *Note: Validated against synthetic ground-truth grain boundaries*.
- **T031**: Perform Sensitivity Analysis (median threshold sweep ±5%, ±10%, ±15%).
- **T032**: Generate Confidence Intervals via MC Dropout and output `results/predictions.csv` (FR-008).

### Phase 6: Final Reporting
- **T039**: Assemble final performance report and artifacts.
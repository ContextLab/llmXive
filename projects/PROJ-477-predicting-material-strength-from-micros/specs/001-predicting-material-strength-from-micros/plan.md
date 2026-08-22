# Implementation Plan: Predicting Material Strength from Microstructure Images

**Branch**: `001-predict-material-strength-cnn` | **Date**: 2024-10-27 | **Spec**: `specs/001-predicting-material-strength-cnn/spec.md`
**Input**: Feature specification from `/specs/001-predicting-material-strength-cnn/spec.md`

## Summary

This feature implements a reproducible pipeline to predict material yield strength from 2D **synthetic** EBSD microstructure images using a lightweight Convolutional Neural Network (CNN). The approach leverages transfer learning (frozen MobileNetV/ResNet-18 backbone) to operate within strict CPU-only constraints (multiple cores, 7GB RAM) on GitHub Actions. The plan explicitly reframes the hypothesis to validate predictive capability on *synthetic* microstructure morphology (using the verified `Rxzh/ebsd-synthetic` dataset) and acknowledges that generalization to real-world EBSD is future work. It ensures statistical rigor by comparing CNN performance against a naive mean predictor using a **paired t-test** on the difference of squared errors, applying Bonferroni correction for architecture comparisons, and defining a Minimum Effect Size of Interest (MESI) of R² = 0.2 (per Constitution VI).

## Technical Context

**Language/Version**: Python version

The specific value to remove/generalize: 'version'

Rewritten passage:  
**Primary Dependencies**: PyTorch (CPU-only), `torchvision`, `scikit-learn`, `pandas`, `numpy`, `albumentations` (for augmentation), `pyyaml`, `matplotlib`  
**Storage**: Local file system (`data/` for raw/processed, `models/` for checkpoints, `results/` for reports)  
**Testing**: `pytest` (unit/integration), `ruff` (linting)  
**Target Platform**: Linux (GitHub Actions Free Tier: Limited vCPU, ~7GB RAM)  
**Project Type**: Research Pipeline / CLI  
**Performance Goals**: End-to-end training and evaluation within 6 hours; Peak RAM < 7GB  
**Constraints**: No local GPU; Data must be open/directly downloadable; No synthetic data generation (must use verified source); Strict adherence to FR-001 through FR-009.  
**Scale/Scope**: Dataset size: a verified corpus of images (N=2,697); Model parameters in the low-millions range (frozen backbone).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` pins versions; Random seeds set in `code/`; Data fetched from canonical HuggingFace URL (`Rxzh/ebsd-synthetic`). |
| **II. Verified Accuracy** | **Pass** | All dataset URLs cited only from the `# Verified datasets` block; Hypothesis scope explicitly limited to *synthetic* morphology to match data modality. |
| **III. Data Hygiene** | **Pass** | Checksums recorded in `state/`; Raw data preserved; Transformations output new files (e.g., `data/processed/`). |
| **IV. Single Source of Truth** | **Pass** | Metrics in `results/` trace to specific code blocks; No hand-typed numbers in `paper/`. |
| **V. Versioning** | **Pass** | Artifacts tracked via content hashes; `state/` updated on change. |
| **VI. Numerical Stability** | **Pass** | MSE/R² calculated on held-out test set; Null threshold (R² < 0.2) defined; **Paired t-test** (not single-sample) used for significance; MESI (R²=0.2) defined. |
| **VII. Architectural Ablation** | **Pass** | Plan includes explicit `train_ablation.py` script (T007) for 'no-augmentation' run and Grad-CAM visualization. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-material-strength-cnn/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download.py          # Downloads and verifies checksum of EBSD dataset
│   ├── preprocess.py        # Resizes to 224x224, normalizes, splits (train/val/test)
│   ├── validate.py          # Validates image-strength pairs (FR-001, US-1)
│   └── extract_features.py  # Extracts grain size features (FR-009)
├── models/
│   ├── backbone.py          # Defines MobileNetV2/ResNet-18 with frozen weights
│   ├── train.py             # Training loop with augmentation and early stopping (FR-002, FR-003)
│   └── train_ablation.py    # Training loop WITHOUT augmentation (Constitution VII)
├── eval/
│   ├── baseline.py          # Naive mean predictor (FR-004)
│   ├── metrics.py           # MSE, R², paired t-test calculation (FR-004, FR-005)
│   ├── interpret.py         # Grad-CAM generation (FR-006)
│   └── sensitivity.py       # Threshold sweep analysis (FR-007, FR-008)
├── utils/
│   ├── io.py                # Logging, manifest handling
│   └── config.py            # Hyperparameters, paths
├── tests/
│   ├── unit/
│   │   ├── test_data.py     # Tests for corrupted data, aspect ratios (T037)
│   │   └── test_metrics.py
│   └── integration/
│       └── test_pipeline.py # End-to-end run (T039)
└── requirements.txt

data/
├── raw/                     # Unmodified downloaded zip
├── processed/               # 224x224 images, manifest.csv
└── features/                # Extracted grain features (FR-009)

results/
├── model_checkpoint.pt
├── performance_report.json
├── null_hypothesis_report.json
├── interpretability_report.json
├── predictions.csv          # With confidence intervals and baseline
└── sensitivity_analysis.csv
```

**Structure Decision**: Single project structure selected to minimize overhead. `code/` is organized by functional stage (data, models, eval) to match the computational ordering requirements (download -> preprocess -> train -> evaluate).

## Complexity Tracking

No complexity violations identified. The plan strictly adheres to CPU constraints by using frozen backbones and streaming/efficient batch loading. The data source contradiction is resolved by explicitly reframing the hypothesis to match the synthetic dataset.

## Execution Phases

### Phase 1: Setup & Validation (Foundational)
- **T001**: Initialize project structure, `requirements.txt`, and CI config.
- **T002**: Implement `download.py` and `validate.py` (US-1).
- **T003**: Implement `preprocess.py` (US-1).
- **T004**: Implement `extract_features.py` (FR-009). *Explicitly extracts grain size features for every image in the test set.*
- **T005**: Implement `backbone.py` (MobileNetV2 frozen).

### Phase 2: Model & Baseline (Core)
- **T006**: Implement `train.py` (US-2, FR-002, FR-003).
- **T007**: Implement `train_ablation.py` (Constitution VII). *Trains a model without data augmentation.*
- **T008**: Implement `baseline.py` (Naive mean predictor).

### Phase 3: Evaluation & Interpretation (Analysis)
- **T009**: Implement `metrics.py` (Paired t-test, FR-005). *Calculates MSE, R², and performs paired t-test on squared errors.*
- **T010**: Implement `interpret.py` (Grad-CAM, FR-006).
- **T011**: Implement `sensitivity.py` (FR-007, FR-008).
- **T012**: Run end-to-end pipeline and generate reports. *Executes full pipeline to generate all required artifacts.*

### Phase 4: Testing & Polish
- **T013**: Write unit tests for data validation and metrics. *Includes tests for corrupted data and extreme aspect ratios.*
- **T014**: Run `ruff check --fix` and generate `results/lint_report.log`. *Ensures code quality.*
- **T015**: Run memory stress test and generate `results/memory_profile.json`. *Verifies peak RAM < 7GB.*
- **T016**: Final documentation update.

### Phase 5: Data Source Correction (Integrated)
- **T017**: Confirm synthetic dataset usage and hypothesis scope (Integrated into Phase 1).
- **T018**: Verify grain size correlation metric for interpretability (Integrated into Phase 3).

### Phase 6: Reporting
- **T019**: Generate final performance and null hypothesis reports.
- **T020**: Archive artifacts and update `state/`.

### Phase 7: Cleanup
- **T021**: Remove temporary files and verify checksums.
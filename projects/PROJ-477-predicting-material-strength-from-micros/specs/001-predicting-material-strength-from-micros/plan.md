# Implementation Plan: Predicting Material Strength from Microstructure Images

**Branch**: `001-predict-material-strength-cnn` | **Date**: 2026-07-13 | **Spec**: `specs/001-predict-material-strength-cnn/spec.md`
**Input**: Feature specification from `/specs/001-predict-material-strength-cnn/spec.md`

## Summary

This plan implements a reproducible pipeline to predict material yield strength from 2D EBSD microstructure images using a lightweight CNN (MobileNetV2). The approach prioritizes CPU-first execution on GitHub Actions free-tier runners, utilizing a verified public dataset or a synthetic generation fallback. The pipeline includes rigorous data validation, a naive statistical baseline for comparison, and interpretability analysis via Grad-CAM. All results are measured against the spec's success criteria (R², MSE, statistical significance) using dynamic computation, never fabricated metrics.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU-only build), `torchvision`, `datasets` (HuggingFace), `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `shap` (fallback), `pyyaml`, `pymatgen` (for synthetic generation fallback)  
**Storage**: Local filesystem (`data/`, `results/`, `code/`)  
**Testing**: `pytest` (unit tests for data loading, metric calculation)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, ~7GB RAM)  
**Project Type**: Computational Research / Machine Learning Pipeline  
**Performance Goals**: Complete training and evaluation within 6 hours on CPU; memory usage < 6GB.  
**Constraints**: No GPU access by default; dataset must be streamable or fit in RAM; no fabricated metrics.  
**Scale/Scope**: Dataset size ~2,697 images (source: verified synthetic generation or public dataset); model training on a single CPU core.

## Constitution Check

*Gates determined based on constitution file*

- **I. Reproducibility**: PINNED. All random seeds set in `code/config.py`. Dataset source fixed to verified HuggingFace ID or local generation script.
- **II. Verified Accuracy**: PINNED. All citations (e.g., dataset source) verified against the provided "Verified datasets" block or replaced with a verified fallback. No external URLs invented.
- **III. Data Hygiene**: PINNED. `data/raw/` contains the original zip or generated data; `data/processed/` contains derived artifacts. Checksums recorded in `state/...yaml`.
- **IV. Single Source of Truth**: PINNED. All metrics in `results/metrics.json` derived from `code/evaluation.py`. No hand-typed numbers in `plan.md`.
- **V. Versioning Discipline**: PINNED. Artifacts hashed; `updated_at` managed by the agent workflow.
- **VI. Numerical Stability**: PINNED. Metrics calculated via `sklearn.metrics` (MSE, R²). Null threshold defined as R² < 0.2.
- **VII. Architectural Ablation**: PINNED. Plan includes ablation (no augmentation, frozen vs. fine-tuned backbone) and Grad-CAM/SHAP visualization.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-material-strength-cnn/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameters
├── data/
│   ├── __init__.py
│   ├── loader.py        # Dataset download, unzip, validation (T042 logic), BatchLoader class
│   ├── preprocess.py    # Resize, normalize, split (FR-001)
│   ├── augment.py       # Data augmentation transforms (FR-003)
│   └── generate.py      # Synthetic data generation fallback (if download fails)
├── models/
│   ├── __init__.py
│   ├── backbone.py      # MobileNetV2 with frozen/fine-tuned weights (FR-002)
│   └── head.py          # Regression head
├── training/
│   ├── __init__.py
│   ├── train.py         # Training loop, early stopping (US-2)
│   └── baseline.py      # Naive mean predictor (US-2)
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py       # MSE, R², paired t-test (FR-004, FR-005)
│   └── interpretability.py # Grad-CAM, SHAP, sensitivity analysis (FR-006, FR-007)
├── utils/
│   ├── __init__.py
│   ├── logging_config.py # Logger to results/metrics.log and metrics.json (T007 fix)
│   └── validation.py     # Data integrity checks (T042 fix)
├── main.py              # Orchestration script
└── requirements.txt     # Pinned dependencies

tests/
├── test_loader.py
├── test_metrics.py
└── test_validation.py

results/
├── metrics.json         # Final metrics (T007 output)
├── metrics.log          # Training logs (T007 output)
├── validation_report.json # Data validation report (T042 output)
├── plots/               # Grad-CAM heatmaps, sensitivity curves
├── expert_review_report.md # Fallback for SC-005 (T030)
└── models/              # Saved checkpoints
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pipeline. `code/` is modularized by function (data, model, training, evaluation) to facilitate independent testing and debugging. `results/` is distinct from `data/` to ensure raw data is never overwritten.

## Complexity Tracking

No violations found. The plan strictly adheres to the spec and constitution.

## Phases

### Phase 0: Data Acquisition and Validation (FR-001, T042)
1.  **Download**: Attempt to fetch dataset from verified HuggingFace ID (e.g., `materials/ebsd-synthetic`).
2.  **Fallback**: If download fails, execute `code/data/generate.py` to create a synthetic dataset of ~2,700 EBSD images with paired yield strength values using Voronoi tessellation.
3.  **Validate**: Run `code/utils/validation.py` to check for:
    *   Missing image-metadata pairs.
    *   Invalid pixel depths (reject non-8-bit or normalize to 8-bit).
    *   NaN values in yield strength.
    *   **Output**: `results/validation_report.json` (T042). Exit code 1 if `invalid_ratio` > 0.01 (status="FAIL").
4.  **Extract Features**: Extract grain size features for every image (FR-009) and store in manifest.
5.  **Preprocess**: Resize to 224x224, normalize, split into train/val/test (80/10/10).

### Phase 1: Baseline and Model Training (FR-002, FR-003, US-2)
1.  **Baseline**: Implement naive mean predictor (constant value = training set mean).
2.  **Model**: Initialize MobileNetV2 with frozen ImageNet weights; train only the final regression head.
3.  **Augmentation**: Apply random rotation, flip, brightness (FR-003).
4.  **Training**: Run for max 50 epochs with early stopping (patience=5).
5.  **Ablation**: 
    *   Train a second model **without augmentation** (same epochs/early stopping criteria).
    *   Train a third model with **fine-tuned backbone** (low learning rate) to compare against frozen backbone (Constitution Principle VII).

### Phase 2: Evaluation and Interpretability (FR-004, FR-005, FR-006, FR-007, US-3)
1.  **Metrics**: Calculate MSE and R² for CNN and Baseline on test set.
2.  **Significance**: Perform **paired t-test** (α=0.05) on squared errors of CNN vs. Baseline (FR-005).
3.  **Interpretability**: Generate Grad-CAM heatmaps for test samples (FR-006). If manual annotations are missing, generate `expert_review_report.md` (SC-005 fallback).
4.  **Sensitivity**: Sweep thresholds based on **actual ground-truth yield strengths** (e.g., quartiles) and report FPR/FNR (FR-007).
5.  **Uncertainty**: Calculate prediction confidence intervals using **validation set residuals** (FR-008).

### Phase 3: Reporting (SC-001 to SC-005)
1.  **Consolidate**: Aggregate all metrics into `results/metrics.json`.
2.  **Verify**: Ensure all results trace back to `code/` and `data/`.
3.  **Finalize**: Generate summary report. If R² < 0.2, explicitly conclude "insufficient signal" per Constitution Principle VI.

## Implementation Details

### T042: Validation Report
The `code/utils/validation.py` script will:
- Count total images, valid pairs, and invalid pairs.
- Calculate `invalid_ratio`.
- Write `results/validation_report.json` with schema: `{total_images, valid_pairs, invalid_pairs, invalid_ratio, status, errors}`.
- Exit with code 1 if `status` is "FAIL" (invalid_ratio > 0.01).

### T007: Logging Configuration
The `code/utils/logging_config.py` will:
- Implement `get_logger()` that initializes a logger writing to `results/metrics.log` and `results/metrics.json`.
- Ensure `metrics.json` is updated with a valid JSON structure after each run.

### T030: Interpretability Fallback
If manual annotations are missing for IoU calculation:
- The system will generate a `expert_review_report.md` with qualitative descriptions of the Grad-CAM heatmaps.
- This satisfies the "OR" condition in SC-005.

### T032: Confidence Intervals
- Residuals (errors) will be calculated **only** on the validation set.
- The distribution of these residuals (e.g., the lower and upper percentiles) will be applied to test set predictions to form 95% CIs.

### T005: Batch Loading
- A custom `BatchLoader` class in `code/data/loader.py` will handle on-the-fly augmentation.
- It will implement memory-efficient loading to prevent OOM errors on the 7GB RAM limit.

### Fabricated Metrics
- All metrics (MSE, R², t-stat) will be computed dynamically from the actual model outputs.
- No hardcoded values or simulated results will be used.

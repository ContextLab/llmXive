# Implementation Plan: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

**Branch**: `001-predict-stiffness-cnn` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-stiffness-cnn/spec.md`

## Summary

This project implements a pipeline to generate synthetic 2D grayscale microstructure images with varying void/inclusion densities, compute their effective elastic stiffness tensors using FFT-based numerical homogenization, and train a shallow Convolutional Neural Network (CNN) to predict stiffness from images. The goal is to create a surrogate model that captures spatial correlations in stiffness, adhering to strict CPU-only constraints (GitHub Actions free tier) and achieving a Mean Absolute Error (MAE) ≤ 5% relative to numerical ground truth.

**Critical Methodological Update**: To ensure the model learns spatial topology rather than just volume fraction, the data generation strategy explicitly decouples density from topology via stratified sampling. The ground truth is generated via FFT-based numerical homogenization, necessitating an amendment to Constitution Principle VI (see Constitution Check). Statistical analysis uses One-way ANOVA instead of paired t-tests to correctly handle independent groups.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only), `scikit-image`, `scipy`, `numpy`, `pandas`, `pytest`, `scikit-learn`  
**Storage**: Local filesystem (generated data under `data/`, models under `code/models/`)  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple vCPU, ~7 GB RAM, no GPU)  
**Project Type**: Computational research / Machine Learning pipeline  
**Performance Goals**: Full pipeline (generation + training + eval) ≤ 6 hours; MAE ≤ 5% on test set  
**Constraints**: CPU-only execution; no CUDA; dataset size ≥ 2,000 samples; 256x256 image resolution  
**Scale/Scope**: synthetic images; k-fold cross-validation

The specific value to remove/generalize: 'k'

Rewritten passage:
k-fold cross-validation; statistical analysis on density bins  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned random seeds, isolated `requirements.txt`, and end-to-end script execution. |
| **II. Verified Accuracy** | **PASS** | No external citations for datasets (synthetic generation). FFT method is implemented locally; no external URL required. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of generated data and immutable derivation logs. |
| **IV. Single Source of Truth** | **PASS** | All metrics in reports will be derived directly from `code/` output; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; state file updated on change. |
| **VI. Synthetic Ground-Truth Validation** | **AMENDED** | **Amendment Required**: The original Principle VI mandated "analytical homogenization formulas". This plan requires "FFT-based numerical homogenization" to capture spatial topology effects (scientific validity). The plan proceeds with FFT; the Constitution file `constitution.md` will be amended in the next commit to reflect this necessary change. The current check status is "PASS" *conditional* on this amendment being accepted. |
| **VII. Generalization Boundary Disclosure** | **PASS** | Plan includes specific binning by density and error analysis for out-of-distribution cases. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-stiffness-cnn/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model-output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data_generation/
│   ├── __init__.py
│   ├── generate_microstructures.py  # FR-001 (Stratified)
│   └── compute_stiffness.py         # FR-002 (FFT)
├── training/
│   ├── __init__.py
│   ├── model.py                     # FR-003 (Shallow CNN)
│   ├── train.py                     # FR-004, FR-005
│   └── kfold_utils.py
├── evaluation/
│   ├── __init__.py
│   ├── evaluate.py                  # FR-006, FR-007 (ANOVA), FR-008
│   └── stats_utils.py
├── utils/
│   ├── fft_homogenization.py        # Core solver
│   └── metrics.py
├── main.py                          # Orchestration script
└── requirements.txt                 # Pinned dependencies

data/
├── raw/                             # Generated images & metadata
└── processed/                       # Preprocessed batches

tests/
├── unit/
│   ├── test_generation.py
│   ├── test_homogenization.py
│   └── test_model.py
├── contract/
│   ├── test_dataset_schema.py
│   └── test_output_schema.py
└── integration/
    └── test_full_pipeline.py
```

**Structure Decision**: Single-project structure selected to minimize overhead and simplify data flow between generation, training, and evaluation. All code resides under `code/` with clear submodules for separation of concerns.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **FFT-based Homogenization** | Required to capture spatial topology effects (FR-002) | Analytical Voigt-Reuss-Hill bounds decouple stiffness from topology, making the CNN task trivial and scientifically invalid. |
| **Shallow CNN** | Must run within 6 hours on 2-core CPU (FR-004) | Deeper networks or large architectures would exceed runtime limits on free-tier runners. |
| **K-fold Cross-Validation** | Required to assess stability (FR-005) | Simple train/test split is insufficient to validate model robustness against microstructural variability. |
| **Stratified Sampling** | Required to decouple density from topology (Methodology) | Random sampling risks a dataset where density dominates, allowing the model to ignore spatial features. |

## Methodology Updates

### 1. Stratified Data Generation (Addressing Methodology-32d77a10, Methodology-36e0b5bd)
- **Strategy**: Generate samples by first fixing inclusion density (e.g., [deferred], [deferred], [deferred]) and then varying the spatial topology (e.g., cluster size, connectivity) within each density bin.
- **Goal**: Ensure the model cannot simply predict stiffness from density alone; it must learn the spatial arrangement.
- **Validation**: Verify that for a fixed density, the stiffness tensor varies significantly across different topologies.

### 2. Architectural Ablation (Addressing Methodology-8050db58)
- **Strategy**: Before full training, run a small-scale ablation study (a representative subset of samples, a limited number of epochs) comparing shallow vs. deep CNNs to verify that the 3-layer model has sufficient receptive field for the generated microstructures.
- **Goal**: Prevent Type II error (missing learnable relationships due to underpowered architecture).
- **Decision**: If the 3-layer model fails to capture correlations in the ablation, the architecture will be adjusted (if CPU time permits) or the limitation will be explicitly documented.

### 3. Statistical Analysis Correction (Addressing Methodology-c5f059c9, Scientific-Soundness-149a7389)
- **Correction**: Replaced "paired t-tests" with "One-way ANOVA" (followed by Tukey HSD post-hoc tests) to compare error distributions across independent density bins.
- **Rationale**: Paired t-tests require matched pairs; density bins contain independent microstructures. ANOVA is the correct test for comparing means across multiple independent groups.

## Computational Feasibility

| Constraint | Mitigation Strategy |
|------------|---------------------|
| **No GPU** | Use CPU-only `torch`; avoid CUDA-specific operations. |
| **≤6 Hours** | Limit epochs to a sufficient number for convergence.; use batch size 32; optimize FFT solver. |
| **~7 GB RAM** | Stream data in batches; avoid loading entire dataset into memory. |
| **~ GB Disk** | Compress generated images; clean intermediate files. |

## Assumptions & Limitations

- **Synthetic Representativeness**: Generated microstructures approximate real polymer microstructures sufficiently for surrogate training.
- **FFT Accuracy**: FFT-based homogenization provides accurate ground truth for 2D cases.
- **Topological Learnability**: Spatial arrangement of inclusions is learnable by a shallow CNN (verified via ablation).
- **Runtime Stability**: GitHub Actions runners are stable enough for 6-hour jobs without preemption.
- **Constitution Amendment**: Principle VI is amended to allow FFT-based homogenization.

## References

- **FFT Homogenization**: Custom implementation based on standard numerical methods (no external URL cited).
- **Synthetic Generation**: `scikit-image` documentation (standard library).
- **CNN Architecture**: Standard shallow CNN designs for regression tasks.
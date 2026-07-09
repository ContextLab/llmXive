# Implementation Plan: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

**Branch**: `001-predict-stiffness-cnn` | **Date**: 2026-06-28 | **Spec**: `spec.md`

## Summary

This project implements a CPU-optimized surrogate model to predict the effective elastic stiffness tensors of 2D microstructures from grayscale images. The approach involves generating a synthetic dataset of 2,000+ microstructures with randomized void/inclusion topologies, calculating ground-truth stiffness via FFT-based numerical homogenization, and training a shallow Convolutional Neural Network (CNN) using PyTorch on CPU. The pipeline includes k-fold cross-validation, statistical analysis of prediction errors across density bins, and rigorous validation against the project's success criteria (MAE ≤ 5%, runtime ≤ 6 hours).

**Critical Governance Note**: This project requires an immediate amendment to Constitution Principle VI (currently mandating analytical homogenization) to permit FFT-based numerical homogenization. This amendment is the first actionable task (Phase 0) and is a strict prerequisite for data generation.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: PyTorch (CPU-only), scikit-image, scipy, numpy, pandas, scikit-learn, pyfftw (optional, fallback to scipy.fft)  
**Storage**: Local file system (images as PNG/TIFF, metadata as CSV/JSON)  
**Testing**: pytest (unit tests for homogenization, integration tests for training pipeline)  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7 GB RAM, no GPU)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Full pipeline (data gen + training + eval) ≤ 6 hours; MAE ≤ 5% on test set  
**Constraints**: No GPU usage; memory usage < 7 GB; dataset size ≤ 14 GB; no external API calls for data  
**Scale/Scope**: 2,000 synthetic images (128x128 pixels to fit runtime), 5-fold cross-validation, 50 epochs max

> **Note on Constraints**: The dataset size and model depth are constrained by the 6-hour runtime and 7 GB RAM limits of the free-tier runner. To ensure feasibility, the image resolution is set to 128x128 pixels, as 256x256 FFT homogenization on 2-core CPU exceeds the 2-hour data generation budget.

## Constitution Check

**Status**: **GATE FAILED - REQUIRES IMMEDIATE AMENDMENT**

The current `constitution.md` (Principle VI) mandates "analytical homogenization formulas" (Voigt-Reuss-Hill) for synthetic ground truth. However, the spec explicitly requires **FFT-based numerical homogenization** to capture spatial topology dependencies, as analytical bounds are topology-independent and render the CNN task trivial.

**Action Required**:
1.  **Amendment Task (Task 0.1)**: A specific task has been added to Phase 0 to formally amend `constitution.md` Principle VI to allow "FFT-based numerical homogenization" for this project, citing the scientific necessity of topology-dependent ground truth.
2.  **Execution**: No data generation or training will commence until this amendment is committed and the state files are updated.

**Revised Principle VI (Proposed)**:
> "The project generates labels using FFT-based numerical homogenization. The validity of the surrogate model depends on the accuracy of these numerical solutions for the specific microstructure topology. The methodology MUST document the range of validity for the numerical homogenization method used."

## Implementation Plan

### Phase 0: Governance & Constitution Amendment (Prerequisite)
*Goal: Align project governance with scientific requirements before code execution.*
- **Task 0.1**: Draft and commit `docs/constitution_amendment_proposal.md` justifying the shift from analytical to FFT-based homogenization.
- **Task 0.2**: Update `constitution.md` to reflect the new Principle VI.
- **Task 0.3**: Update `state/projects/.../artifact_hashes` and `updated_at` timestamp to record the governance change.
- **Gate**: Proceed to Phase 1 only after `constitution.md` is updated.

### Phase 1: Data Generation & Ground Truth (FR-001, FR-002)
*Goal: Create a synthetic dataset with topology-dependent labels.*
- **Task 1.1**: Implement `generate_microstructures.py` using `scikit-image`.
  - **Topological Diversity Strategy**: Use **Latin Hypercube Sampling (LHS)** to vary volume fraction (density) and spatial correlation length (topology) **independently**. This ensures that for every density bin, there is a wide variance in clustering and percolation properties, preventing the model from learning only density-stiffness correlations.
  - **Resolution**: 128x128 pixels (to ensure FFT homogenization completes within the 2-hour time budget on 2-core CPU).
 - **Quantity**: [deferred] images.
- **Task 1.2**: Implement `homogenize.py` using `scipy.fft`.
  - **Ground Truth Definition**: Calculate the *exact* numerical stiffness tensor for each image. **Crucially**, the CNN is trained on this specific numerical value, NOT on the fact that it falls within Voigt-Reuss-Hill (VRH) bounds. VRH is used *only* to filter invalid simulation runs (e.g., numerical instability).
  - **Plausibility Filter**: Check if results fall within VRH bounds. If an FFT run fails or falls outside bounds, the image is flagged and excluded from training.
- **Task 1.3**: Validate dataset.
  - **Topology Validation**: Perform a statistical test to verify topology dependence. Specifically, calculate the **partial correlation coefficient** between the `topology_metric` and `stiffness_tensor` components, **holding density constant**. A significant partial correlation confirms the dataset captures topology-stiffness relationships.
  - Verify variance in stiffness correlates with spatial topology, not just density.
  - Confirm dataset size and file integrity.

### Phase 2: Model Training & Cross-Validation (FR-003, FR-004, FR-005)
*Goal: Train a shallow CNN within CPU constraints.*
- **Task 2.1**: Implement `cnn.py` (Shallow CNN: 2-3 Conv layers, Global Average Pooling).
- **Task 2.2**: Implement `train.py` (PyTorch CPU mode, Adam, Batch size, 50 epochs).
- **Task 2.3**: Implement `cross_validate.py` (5-fold).
  - **Stratification**: Folds will be stratified by both inclusion density AND topological features (e.g., clustering coefficient) to ensure the model learns topology-stiffness relationships.
- **Task 2.4**: Save model artifacts and training logs.

### Phase 3: Evaluation & Statistical Analysis (FR-006, FR-007, FR-008)
*Goal: Quantify performance and generalization.*
- **Task 3.1**: Compute metrics (MSE, R2, MAE) on held-out test set.
- **Task 3.2**: Bin test data by density and perform paired t-tests (FR-007).
- **Task 3.3**: Flag outliers (MAE > 5%) and analyze OOD performance (FR-008).
- **Task 3.4**: Generate final reports and visualizations.

## Power Analysis & Sample Size Justification

**Concern**: Is [deferred] samples sufficient for a 6-component tensor regression on 128x128 images?

**Statistical Justification**:
1.  **Effect Size Assumption**: Based on preliminary literature, the variance in stiffness due to topology (at fixed density) is expected to be moderate (Cohen's f² ≈ small to medium effect size).
2.  **Regression Complexity**: The model predicts multiple continuous outputs. We treat this as 6 separate regression problems for sample size estimation.
3. **Precision Requirement**: We require a 95% Confidence Interval (CI) width for the Mean Absolute Error (MAE) of ≤ 0.02 ([deferred] of the stiffness range).
4.  **Calculation**:
    - Assuming a standard deviation (σ) of the MAE of a moderate magnitude (based on preliminary noise estimates).
    - To achieve a CI width of 0.02 with 95% confidence (Z=1.96):
      $$ N = \left( \frac{Z \cdot \sigma}{\text{Margin of Error}} \right)^2 = \left( \frac{1.96 \cdot 0.05}{0.02} \right)^2 \approx 240 $$
    - However, this is for a simple mean. For a regression model with $p$ parameters (shallow CNN ~500 parameters), the effective degrees of freedom are reduced. A rule of thumb for regression is $N \ge c \cdot p$ for stable estimates, where $c$ represents a sufficiently large multiplier, suggesting $N \ge 5000$.
 - **Feasibility Constraint**: Given the 6-hour runtime limit, we cannot generate [deferred] samples. We prioritize **relative trend analysis** (generalization across density bins) over absolute precision of the MAE.
    - **Revised Justification**: We select $N=2,000$ as the maximum feasible sample size that allows for 50 epochs of training on a 2-core CPU within 6 hours. This sample size provides sufficient power (>0.8) to detect **large** effect sizes (f² > 0.25) in the generalization analysis (SC-002), which is the primary scientific goal. The absolute MAE precision will be reported with its confidence interval; if the interval is wide, the conclusion will be framed as "The 2D topology-stiffness relationship requires more data for precise quantification," which is a valid scientific finding.

**Mitigation**:
1.  **Shallow Architecture**: The CNN is intentionally shallow (2-3 layers) to reduce the parameter count and prevent overfitting on small data.
2.  **Focus on Relative Performance**: The primary scientific metric is the *trend* of error across density bins (generalization), not the absolute precision of the 6 components.
3.  **Post-hoc Analysis**: A power analysis will be performed on the MAE variance post-training. If variance is too high, the conclusion will be framed as "The 2D topology-stiffness relationship is not learnable with <2,000 samples on CPU," which is a valid scientific finding.

## Runtime Budget & Fallback Strategy

**Total Budget**: 6 hours (GitHub Actions free tier).
**Allocation**:
- **Data Generation (FFT)**: 2.0 hours max. (Bottleneck: 128x128 FFT).
 - **Per-Image Estimate**: [deferred] per image on 2-core CPU (conservative estimate for 128x128).
 - **Total**: [deferred] images * 30s = 60,000s [deferred]. **Correction**: 30s is too high for 128x128. Re-estimating: [deferred]/image for 128x128. Total = 5.5 hours.
  - **Revised Strategy**: To ensure the 2-hour budget is met, we will use **128x128 resolution** and **optimize the FFT solver** (using `scipy.fft` with `workers=2`). If this still exceeds 2 hours, we will reduce the sample size to **500 images** for the 128x128 run, or fallback to **64x64** resolution.
- **Training (50 epochs)**: 3.0 hours max.
- **Evaluation & Reporting**: 1.0 hour max.

**Fallback Strategy**:
- If FFT generation exceeds 2.0 hours:
  1.  Reduce image resolution to **x64**.
  2.  Reduce dataset size to a manageable subset of images.
  3.  Document the reduction in `research.md` as a constraint-induced limitation.
- This ensures the pipeline completes within the 6-hour limit even on slower runner instances.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-stiffness-cnn/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-506-predicting-material-stiffness-from-micro/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── generate_microstructures.py  # FR-001: Synthetic data generation
│   │   └── homogenize.py                # FR-002: FFT-based stiffness calculation
│   ├── models/
│   │   ├── __init__.py
│   │   └── cnn.py                       # FR-003: Shallow CNN definition
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py                     # FR-004: CPU training loop
│   │   └── cross_validate.py            # FR-005: K-fold CV
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py                   # FR-006: MSE, R2, MAE
│   │   └── statistical_analysis.py      # FR-007, FR-008: T-tests, outlier flagging
│   └── utils/
│       ├── __init__.py
│       └── config.py                    # Hyperparameters, seeds
├── data/
│   ├── raw/                             # Generated images (128x128)
│   ├── processed/                       # Metadata CSV, training splits
│   └── models/                          # Saved model weights
├── tests/
│   ├── unit/
│   │   ├── test_homogenization.py
│   │   └── test_cnn.py
│   └── integration/
│       └── test_full_pipeline.py
├── docs/
│   └── constitution_amendment_proposal.md # Formal amendment proposal for Principle VI (Phase 0)
└── requirements.txt
```

**Structure Decision**: A modular CLI structure is selected to separate data generation, model training, and evaluation. This ensures reproducibility and allows independent testing of each component (Constitution Principle I). The `code/` directory is pinned to `projects/PROJ-506...` to maintain a single source of truth.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| FFT-based Homogenization | Required to capture spatial topology dependencies (Spec Assumption). | Analytical bounds (Voigt-Reuss-Hill) are topology-independent, making the CNN task trivial and scientifically invalid. |
| Shallow CNN (CPU-only) | Must run within 6 hours on 2-core CPU (Spec Constraint). | Deep CNNs or GPU-based models would exceed runtime limits and violate the "free-tier" constraint. |
| K-Fold Cross-Validation | Required to assess model stability (FR-005, SC-005). | Simple train/test split is insufficient to guarantee stability across microstructural patterns. |
| Constitution Amendment | Required to align governance with scientific method. | Proceeding without amendment violates the project's legal constraints (Principle VI). |
| 128x128 Resolution | Required to fit [deferred] images into 2-hour FFT budget on 2-core CPU. | 256x256 resolution would take >10 hours for generation, violating the 6-hour total runtime. |

### Topological Diversity Strategy (Addressing Scientific Soundness)

To ensure the CNN learns topology-stiffness correlations and not just density-stiffness correlations:
1.  **Latin Hypercube Sampling (LHS)**: The data generation script will use LHS to sample pairs of (volume fraction, spatial correlation length) from a 2D hypercube. This guarantees that the two variables are **uncorrelated** in the generated dataset.
2.  **Stratified Sampling**: The dataset will be constructed to ensure that for every density bin, there is a wide variance in clustering and percolation properties.
3.  **Validation**: We will verify that the stiffness tensor variance within a single density bin is significant and correlated with the spatial arrangement metrics (via partial correlation), not just noise.

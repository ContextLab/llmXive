# Evaluation Integrity & Blindness Constraint

## Purpose
This document details the "Blindness" constraint enforced in the evaluation pipeline to ensure the independence of metric computation from the generative model's internal mechanics.

## The Constraint
The evaluation module (`code/pipeline/evaluate.py`) must be **blind** to the model that generated the video frames. It treats the video as a black box.

### Prohibited Actions
1. **Importing Internal Symbols**: The module must not import `dit_attention`, `latent_space`, `DreamXBackbone`, or any other internal component of the generative model.
2. **Accessing Latent States**: No access to intermediate feature maps or attention weights during metric calculation.
3. **Coupled Logic**: The logic for SfM, Procrustes alignment, and MAE calculation must not depend on the specific architecture of the generator.

### Allowed Inputs
The evaluation functions accept only:
- `numpy.ndarray`: Video frames (H, W, C).
- `numpy.ndarray`: 4x4 Camera Extrinsic Matrices (Ground Truth).

## Enforcement Mechanism
A static analysis tool (`code/pipeline/static_analysis_check.py`) is included in the CI pipeline to verify this constraint.
- It scans `code/pipeline/evaluate.py` for forbidden imports.
- It fails the build if any internal model symbols are detected.

## Rationale
This separation ensures that the metrics (MAE, Scale Drift, Convergence) are objective measures of 3D consistency, independent of the specific generative method. It allows for fair comparison between DreamX-Lite and other models without bias from shared internal states.

## Compliance
- **T018**: Static analysis check implemented.
- **T019**: Refactored function signatures to accept only frames and extrinsics.
- **T020**: This documentation and docstrings added to enforce the constraint.
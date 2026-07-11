# Implementation Plan: llmXive follow-up: extending "SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diff"

**Branch**: `001-symbolic-geometric-priors` | **Date**: 2026-07-11 | **Spec**: `specs/001-symbolic-geometric-priors/spec.md`
**Input**: Feature specification from `/specs/001-symbolic-geometric-priors/spec.md`

## Summary

This project investigates the extent to which the geometric consistency of SANA-WM's minute-scale video generation depends on learned semantic priors versus architectural inductive biases. The approach involves replacing the standard text-to-image encoder with a deterministic symbolic function mapping kinematic rules to camera condition vectors. The system will generate a substantial set of synthetic 6-DoF trajectories, produce video using NVFP4 quantized weights on a CPU-only environment (with a verified fallback to Stable Video Diffusion XT if SANA-WM is unavailable), and evaluate geometric consistency via COLMAP pose estimation against ground truth. **Critical Methodology**: A mandatory 'Baseline Calibration' phase identifies the optimal text prompt for the learned baseline to ensure a fair comparison. **Critical Alignment**: All pose comparisons use Procrustes scale alignment to resolve the relative/absolute scale mismatch. **Critical Statistics**: A Permutation Test on Censored Data is used to handle trajectory failures (capped errors) without violating statistical assumptions, ensuring failures are counted as maximum error rather than excluded.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `scikit-learn`, `torch` (CPU-only), `transformers` (modified), `opencv-python`, `colmap` (binary wrapper), `pyyaml`, `bitsandbytes` (for quantization verification)  
**Storage**: Local filesystem (`data/synthetic/`, `data/generated/`, `data/results/`)  
**Testing**: `pytest` (unit tests for trajectory generation, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions Free Tier: `ubuntu-latest`, 2 CPU, 7GB RAM, No GPU). **CI Configuration**: `CUDA_VISIBLE_DEVICES=""` and `export TORCH_USE_CUDA_DSA=0` explicitly set to enforce CPU-only execution per Constitution Principle VII.  
**Project Type**: Computational Research / Scientific Simulation  
**Performance Goals**: Complete 500 trajectory generations and evaluations within 6 hours (subject to Pilot Phase validation); memory footprint < 7GB.  
**Constraints**: No GPU/CUDA; NVFP4 quantization required (or fallback to verified CPU-tractable model); strict CPU-only execution; symbolic encoder must bypass all learned embedding layers.  
**Scale/Scope**: A set of synthetic trajectories, each with a short duration (HD resolution, fallback lower resolution/10s), paired t-test (or permutation test).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`; `requirements.txt` pins all dependencies; data fetched from verified sources only. |
| **II. Verified Accuracy** | **Compliant** | **Blocking Gate**: The `Reference-Validator Agent` is executed as a pre-flight check in `main.py` before Phase 0 starts. If any citation is invalid, the pipeline aborts. |
| **III. Data Hygiene** | **Compliant** | Synthetic data generated via code (checksummed); no modification of raw artifacts; derived metrics stored in new files. |
| **IV. Single Source of Truth** | **Compliant** | All metrics trace to `data/results/` JSON; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | **Compliant** | **Post-Processing Hook**: `main.py` includes a `post_process()` function that computes content hashes for all artifacts in `data/` and `code/`, then updates `state/projects/PROJ-822-llmxive-follow-up-extending-sana-wm-effi.yaml` with `updated_at` and `artifact_hashes`. |
| **VI. Symbolic Control Fidelity** | **Compliant** | `code/symbolic_encoder.py` implements hard-coded kinematic mapping; text-embedding layers explicitly bypassed. |
| **VII. Low-Compute Quantization** | **Compliant** | Pipeline enforces NVFP4 weights (or verified fallback); execution restricted to CPU; memory checks enforced at runtime. |

## Project Structure

### Documentation (this feature)

```text
specs/001-symbolic-geometric-priors/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schemas stored here)
│   ├── geometric_metric.schema.yaml
│   ├── statistical_test_result.schema.yaml
│   └── synthetic_trajectory.schema.yaml
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
projects/PROJ-822-llmxive-follow-up-extending-sana-wm-effi/code/
├── __init__.py
├── config.py            # Global config, seeds, paths
├── data/
│   ├── __init__.py
│   ├── trajectory_generator.py  # FR-001: Kinematic equations
│   └── symbolic_encoder.py      # FR-002: Hard-coded mapping
├── model/
│   ├── __init__.py
│   ├── sana_wm_loader.py        # FR-003: NVFP4 CPU loader (or fallback to SVD-XT)
│   └── inference_loop.py        # Generation logic
├── evaluation/
│   ├── __init__.py
│   ├── pose_estimator.py        # FR-004, FR-007: COLMAP wrapper (AKAZE, exhaustive, a high inlier threshold)
│   ├── metrics.py               # FR-004, FR-005: Euclidean, SSIM, Procrustes alignment
│   └── stats.py                 # FR-005, FR-006: Permutation Test (censored data)
├── main.py              # Orchestration script (includes Performance Monitoring & Hashing)
└── requirements.txt     # Pinned dependencies

tests/
├── unit/
│   ├── test_trajectory.py
│   └── test_symbolic_encoder.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py  # Imports schemas from specs/.../contracts/ via relative path (Single Source of Truth)
```

**Structure Decision**: Single project structure selected to minimize overhead for a research simulation. Separation of `data`, `model`, and `evaluation` ensures modularity for testing the specific hypothesis components (generation, inference, evaluation). **Contracts are stored in `specs/.../contracts/` and imported by `tests/contract/` via relative path to ensure a Single Source of Truth.**

## Phases & Methodology

### Phase 0: Pilot & Feasibility (Critical Path)
1.  **Model Selection**: Verify availability of SANA-WM NVFP4 weights. If unavailable, **load Stable Video Diffusion XT** (verified fallback) from HuggingFace.
2.  **Pilot Run (N=10)**: Generate multiple trajectories. Measure actual inference time and memory usage.
3.  **Feasibility Check**:
    - If projected time for N=500 > 6 hours: **Dynamic Fallback** to 10s duration or 360p resolution.
    - If memory > 7GB: **Dynamic Fallback** to lower resolution or smaller model.
4.  **Validation Gate**: Run `Reference-Validator` on all model citations. Abort if invalid.

### Phase 0.5: Baseline Calibration (New)
1.  **Prompt Search**: For a small set of trajectories (N=5), iterate over candidate text prompts (e.g., "camera moves at {velocity} m/s", "motion: {velocity}", etc.) to find the one that minimizes the geometric error against the ground truth.
2.  **Selection**: Select the "Calibrated Prompt" that yields the lowest error.
3.  **Fixation**: Use this **single** Calibrated Prompt for all N=500 baseline runs to ensure the comparison isolates the encoder architecture, not prompt translation quality.

### Phase 1: Data Generation & Inference
1.  **Synthetic Generation**: Generate a sufficient number of trajectories to ensure robust statistical analysis. (FR-001) with **3D Perlin Noise textures** (temporally coherent) for COLMAP feature tracking.
2.  **Symbolic Inference**: Generate videos using symbolic encoder (FR-002).
3.  **Baseline Inference**: Generate videos using learned baseline with the **Calibrated Prompt** (from Phase 0.5).
4.  **Performance Monitoring** (SC-004, SC-005): Log `wall_clock_time` and `peak_memory` for every sequence. **Abort** if projected total time exceeds 6 hours.
5.  **Configuration Enforcement** (FR-007): Generate `colmap_config.yaml` with exact parameters (AKAZE, exhaustive, 0.8 inlier) and pass it to the COLMAP binary.

### Phase 2: Evaluation & Analysis
1.  **Pose Estimation**: Run COLMAP on generated videos.
2.  **Procrustes Alignment**: Apply Procrustes scale alignment to align COLMAP relative poses to ground-truth absolute poses (resolves scale mismatch).
3.  **Metric Calculation**: Compute Euclidean error and SSIM.
    - **Failure Handling**: If >50% frames invalid, mark trajectory as "Failed" and assign **Capped Maximum Error** (100m).
4.  **Statistical Workflow** (FR-006):
    - Compute distribution of error differences.
    - **Check Failure Rate**: If failure rate > 5%, use **Permutation Test on Censored Data**. Otherwise, use Paired T-Test.
    - Execute **exactly one** aggregate hypothesis test.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **NVFP4 Quantization / SVD-XT Fallback** | Required by Constitution Principle VII and Spec FR-003 to fit 7GB RAM. | FP32 would exceed the available RAM on the target runner, causing OOM failure. |
| **Baseline Calibration** | Required to remove the 'translation confound' in the learned baseline. | Using a generic prompt would measure prompt quality, not encoder bias. |
| **Procrustes Alignment** | Required to resolve scale mismatch between COLMAP (relative) and Ground Truth (absolute). | Direct Euclidean comparison is mathematically invalid. |
| **Permutation Test** | Required to handle censored data (capped errors) without violating normality assumptions. | Standard t-test is invalid for distributions with discrete capped values. |
| **3D Perlin Noise** | Required to ensure temporally consistent features for COLMAP. | Static noise or random noise lacks temporal coherence, causing tracking failure. |
| **Dynamic Fallback** | Required to ensure the experiment completes within 6 hours. | Fixed parameters risk exceeding the time budget (Type II error). |
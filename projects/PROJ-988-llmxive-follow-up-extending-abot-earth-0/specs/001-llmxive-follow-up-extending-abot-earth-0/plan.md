# Implementation Plan: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

**Branch**: `001-generative-3d-earth-fidelity` | **Date**: 2026-07-12 | **Spec**: `specs/001-generative-3d-earth-fidelity/spec.md`
**Input**: Feature specification from `/specs/001-generative-3d-earth-fidelity/spec.md`

## Summary

This project investigates the limits of generative 3D Gaussian Splatting (3DGS) in recovering geometric and textural fidelity from degraded satellite imagery (low resolution, cloud occlusion, temporal staleness). The core approach involves a controlled synthetic degradation pipeline using Sentinel-2 imagery aligned with OpenTopography LiDAR ground truth, followed by CPU-optimized 3D reconstruction and inpainting using a distilled diffusion prior (ONNX Runtime). The final phase quantifies recovery via Projected PSNR/SSIM (for non-temporal modes) and Chamfer Distance, identifying the critical Normalized Noise Fraction (NNF) threshold where restoration fails.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `onnxruntime`, `scikit-learn`, `opencv-python`, `pandas`, `numpy`, `pyyaml`, `tqdm`, `matplotlib`, `seaborn`, `bayesian_changepoint_detection`  
**Storage**: Local file system (`data/` for raw/processed assets, `data/interim/` for aligned pairs)  
**Testing**: `pytest` (unit tests for degradation logic, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions free-tier runner: multi-core CPU, ample RAM

The research question remains: [Research Question]
The method remains: [Method]
The references remain: [References])  
**Project Type**: Computational research pipeline  
**Performance Goals**: Single scene processing < 45 mins; Peak RAM < 6.5 GB; Total 500-sample run < 6 hours (via distributed jobs)  
**Constraints**: No CUDA/GPU; No 8-bit/4-bit quantization requiring CUDA kernels; Strict adherence to -core/7GB RAM limits.  
**Scale/Scope**: synthetic scenes (distributed); patches of varying sizes per scene; degradation modes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Plan Element |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and checksummed `data/` (FR-002, FR-006). |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset citations to verified sources: Microsoft Planetary Computer (Sentinel-2) and USGS 3DEP/NYC Open Data (LiDAR). |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming step for raw downloads; raw data preserved, derivations written to new files (Data Model). |
| **IV. Single Source of Truth** | **PASS** | Metrics (P-PSNR, Chamfer) generated solely by `code/` scripts; paper figures trace to `data/` CSVs. |
| **V. Versioning Discipline** | **PASS** | Plan includes explicit step to generate SHA256 hashes in `data/manifest.json` and update `state/` file. |
| **VI. Degradation-Threshold Validity** | **PASS** | Core objective is identifying the NNF threshold where p-value > 0.05 via Segmented Regression (FR-005, SC-002). |
| **VII. CPU-Bound Execution Integrity** | **PASS** | Plan explicitly excludes CUDA, uses ONNX Runtime (INT/LCM), and targets -core/7GB RAM limits (FR-003, SC-003). |

## Project Structure

### Documentation (this feature)

```text
specs/001-generative-3d-earth-fidelity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (AUTHORITATIVE DEFINITIONS)
    ├── degraded_scene.schema.yaml
    ├── reconstructed_scene.schema.yaml
    ├── ground_truth_lidar.schema.yaml
    └── fidelity_metrics.schema.yaml
```
*Note: The schemas in `contracts/` are the authoritative definitions for the entities described in `data-model.md`.*

### Source Code (repository root)

```text
projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/
├── code/
│   ├── requirements.txt
│   ├── 01_data_curation.py          # FR-001: Download & Align
│   ├── 02_degradation_pipeline.py   # FR-002: Synthetic Degradation
│   ├── 02b_validate_masks.py        # FR-006: Synthetic Mask Validation
│   ├── 03_3dgs_cpu_inference.py     # FR-003: 3DGS + Inpainting (CPU)
│   ├── 04_metrics_evaluation.py     # FR-004: P-PSNR, SSIM, Chamfer
│   ├── 05_threshold_analysis.py     # FR-005: Segmented Regression, Bayesian CP
│   └── lib/
│       ├── alignment.py
│       ├── degradation.py
│       ├── cpu_3dgs_wrapper.py
│       └── metrics.py
├── data/
│   ├── raw/                         # Downloaded Sentinel-2, LiDAR
│   ├── processed/                   # Aligned pairs, degraded scenes
│   └── results/                     # Metrics CSVs, plots, manifest.json
└── tests/
    ├── unit/
    │   ├── test_degradation.py
    │   └── test_metrics.py
    └── integration/
        └── test_full_pipeline.py
```

**Structure Decision**: Single project structure selected to minimize I/O overhead on the free-tier runner. All scripts reside in `code/` to ensure reproducibility and easy virtualenv isolation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Synthetic Degradation Pipeline** | Essential to control SNR and NNF variables independently to find the "critical threshold" (SC-002). | Using only real clouded images would introduce uncontrolled variables (cloud type, texture loss) making threshold identification impossible. |
| **CPU-Optimized 3DGS** | Required by Constitution Principle VII and GitHub Actions free-tier constraints. | GPU-accelerated 3DGS is faster but violates the "Compute feasibility" constraint, rendering the project non-runnable in CI. |
| **Segmented Regression & Bayesian CP** | Required to identify the specific threshold where significance is lost (SC-002). | Simple mean comparison or global t-test would fail to detect the specific failure point (threshold) where significance is lost. |

## Phase Execution Order

1.  **Data Curation**: Download Sentinel-2 (Microsoft Planetary Computer) and LiDAR (USGS 3DEP/NYC), align coordinates (FR-001).
2.  **Mask Validation**: Validate synthetic masks against real masks (FR-006).
3.  **Degradation**: Apply synthetic masks and downscaling (FR-002).
4.  **Generation**: Run CPU 3DGS and Inpainting (FR-003).
5.  **Evaluation**: Compute metrics against LiDAR (FR-004).
6.  **Analysis**: Segmented regression and Bayesian Change Point Detection (FR-005).

**Execution Strategy**:
- **CI Demo Run**: Process representative scenes (subset) to demonstrate the pipeline and identify the threshold trend within the 6-hour CI window.
- **Distributed Full Run**: The full sample dataset is executed via a GitHub Actions matrix strategy (e.g., A subset of jobs from the samples) or local execution, with results aggregated in `data/results/metrics.csv`. SC-003 measures feasibility of the *pipeline* within constraints, not the completion of 500 samples in a single job.

## Compute Feasibility & Resource Management

- **Hardware**: GitHub Actions Free Tier (multi-core CPU, ample RAM).
- **Memory Strategy**:
  - Process scenes sequentially (batch size = 1).
  - Use `mmap` for large point clouds.
  - **Diffusion Model**: Use `Stable Diffusion 1.5` via `ONNX Runtime` with `INT8` quantization or `Latent Consistency Model (LCM)` to ensure CPU compatibility and fit within 7GB RAM.
- **Time Strategy**:
  - Target moderate duration per scene.
  - **CI Demo**: 50 scenes (approx. A substantial total duration will be allocated., parallelized via matrix or reduced to scenes for strict 6h limit).
  - **Full Run**: Distributed across multiple jobs.

## Risks & Mitigation

- **Risk**: LiDAR data not available for selected urban tiles.
  - *Mitigation*: Script checks availability; uses `city_list.txt` (NYC, LA, Chicago) to ensure access; logs exclusion.
- **Risk**: CPU 3DGS too slow.
  - *Mitigation*: Use simplified 3DGS (fewer primitives) or reduce scene size.
- **Risk**: Temporal mismatch (LiDAR vs Image > 12 months).
  - *Mitigation*: Filter dataset; flag confounded samples; exclude from primary threshold calculation.
- **Risk**: Synthetic masks do not match real clouds.
  - *Mitigation*: FR-006 validation step; if similarity < 0.8, switch to real mask dataset or limit conclusions.
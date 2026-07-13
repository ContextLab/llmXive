# Implementation Plan: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

**Branch**: `001-generative-3d-earth-fidelity` | **Date**: 2026-07-12 | **Spec**: `specs/001-generative-3d-earth-fidelity/spec.md`
**Input**: Feature specification from `/specs/001-generative-3d-earth-fidelity/spec.md`

## Summary

This project investigates the limits of recovering geometric and textural fidelity from degraded satellite imagery (low-resolution, cloud-contaminated, temporally stale) using a generative 3D Gaussian Splatting (3DGS) pipeline enhanced by a CPU-optimized diffusion prior. The implementation focuses on a controlled experimental setup: downloading a representative sample of urban Sentinel-2 tiles, aligning them with OpenTopography LiDAR, applying reproducible synthetic degradations, and measuring recovery via P-PSNR, P-SSIM, and Chamfer Distance. The core constraint is strict adherence to GitHub Actions free-tier limits (CPU-only, ≤7GB RAM, ≤6h runtime), necessitating the use of quantized ONNX models and sampled data patches (100m²) rather than full 1km² scenes for the heavy generation steps.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only wheel), `onnxruntime`, `scikit-learn`, `pandas`, `numpy`, `opencv-python`, `open3d` (for LiDAR processing), `datasets` (HuggingFace), `seaborn`/`matplotlib`, `memory_profiler`, `psutil`, `statsmodels` (for LMM).  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`). No external database.  
**Testing**: `pytest` (unit tests for degradation logic, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Process 100m² patch within 45 mins (CPU), peak RAM < 6.5 GB.  
**Constraints**: No CUDA/GPU usage; no large model fine-tuning; all random seeds pinned; synthetic cloud masks must be validated against real statistics.  
**Scale/Scope**: A representative subset for dataset curation; A sufficient number of samples for the full generation/evaluation pipeline (power-justified); Variable-sized patches extracted from 1km² tiles.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required / Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds in `code/` and canonical data sources (Sentinel-2, OpenTopography). |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` restricted to the "Verified datasets" block. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming raw data and writing derivations to new files. PII scan in `code/` setup. |
| **IV. Single Source of Truth** | **PASS** | Metrics will be stored in `data/results/metrics.csv`; paper figures will be generated directly from this file. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be recorded for all artifacts in `state/` upon generation. |
| **VI. Degradation-Threshold Validity** | **PASS** | Plan explicitly includes a "Threshold Analysis" phase to identify the critical NNF where recovery fails (SC-002). NNF is now defined by input parameters, not ground truth. |
| **VII. CPU-Bound Execution Integrity** | **PASS** | Plan restricts to ONNX Runtime and CPU-only torch. No CUDA calls. Memory limits enforced via profiling. |

## Project Structure

### Documentation (this feature)

```text
specs/001-generative-3d-earth-fidelity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/code/
├── data/
│   ├── download_sentinel.py       # FR-001: Download & Align
│   ├── synthesize_degradation.py  # FR-002: Synthetic Degradation
│   └── validate_masks.py          # FR-006: Validate masks
├── model/
│   ├── load_onnx_diffusion.py     # FR-003: CPU-Optimized Inpainting
│   └── run_3dgs_baseline.py       # FR-003: Baseline 3DGS
├── pipeline/
│   └── run_full_experiment.py     # FR-003, FR-005: Orchestrates Degradation → Baseline → Inpainting → Metrics
├── analysis/
│   ├── compute_metrics.py         # FR-004: P-PSNR, P-SSIM, Chamfer, GDS
│   ├── statistical_tests.py       # FR-005: Wilcoxon, LMM, NNF sweep
│   └── plot_thresholds.py         # SC-002: Performance drop-off curve
├── utils/
│   ├── logger.py                  # Performance logging (SC-003) with memory_profiler
│   └── config.py                  # Seed management, paths
├── tests/
│   ├── test_degradation.py
│   └── test_pipeline_flow.py
└── requirements.txt
```

**Structure Decision**: Selected a modular CLI structure (`code/pipeline/`) to explicitly address the "Consumer before Producer" concern. The `run_full_experiment.py` script acts as the central orchestrator, ensuring the flow `degraded input → baseline 3DGS → render interface → inpainted 3DGS → metrics` is executed atomically per sample, rather than as disconnected tasks. Performance logging is integrated into this pipeline to satisfy SC-003.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Full 3DGS + Inpainting Pipeline** | Required to measure *recovery* (SC-001) and *thresholds* (SC-002). | Running only baseline or only inpainting would not allow comparison or threshold detection. |
| **Synthetic Degradation Engine** | Required for controlled, reproducible experiments (US-1). | Using only real degraded data lacks ground truth alignment and controlled variable isolation. |
| **CPU-Only ONNX Optimization** | Required by Constitution Principle VII and GitHub Actions constraints. | Standard GPU-based 3DGS/diffusion would fail on the target runner (OOM or timeout). |
| **Explicit Performance Instrumentation** | Required by SC-003 to measure feasibility. | Relying on CI logs is insufficient for per-sample granularity and statistical analysis. |
| **Geometric Divergence Score (GDS)** | Required to distinguish recovery from hallucination (Scientific Soundness). | Texture-geometry consistency is insufficient to detect geometric hallucinations. |

## Phases & Tasks

### Phase 0: Data Curation & Alignment (FR-001)
*   **T001**: Download a representative set of Sentinel-2 tiles and corresponding OpenTopography LiDAR.
*   **T002**: Align image and LiDAR coordinate systems. Exclude samples with >2m error.
*   **T003**: Extract m² patches from 1km² tiles.

### Phase 1: Synthetic Degradation (FR-002)
*   **T011**: Apply programmable degradation masks (low-res, cloud, temporal).
*   **T012**: Calculate **Normalized Noise Fraction (NNF)** as a weighted sum of degradation parameters (cloud_opacity, downscale_factor, blur_sigma). *NNF is independent of ground truth.*
*   **T013**: Validate synthetic masks against real cloud statistics (FR-006).

### Phase 2: CPU-Optimized Generation & Orchestration (FR-003, SC-001, SC-003)
*   **T021**: **Baseline 3DGS**: Generate baseline `.ply` from degraded image.
*   **T022**: **Render Interface**: Render 512x512 RGB and Depth maps from Baseline `.ply` using fixed camera intrinsics (f=1024, c=256) and 8 fixed poses. *This is the defined data interface.*
*   **T023**: **Inpainting Restoration**: Inpainting model consumes rendered maps to generate Inpainted `.ply`.
*   **T024**: **Performance Instrumentation**: Wrap T021/T023 with `memory_profiler` and `psutil`. Log `peak_ram_mb`, `wall_clock_time`, and `status` (success/oom) to `data/results/performance_log.csv`. Handle `MemoryError` by logging `ERR_OOM_CPU` and retrying with smaller batch.
*   **T025**: **End-to-End Pipeline Orchestration**: Execute T021 → T022 → T023 sequentially per sample. Ensure the output of T021 is directly passed as input to T022, and T022 to T023, within a single atomic script execution to guarantee data flow integrity.
*   **T026**: **Performance Data Producer**: Explicitly write the captured metrics from T024 to `data/results/performance_log.csv` for every sample processed in T025. This task ensures SC-003 data is generated.

### Phase 3: Fidelity Quantification & Threshold Analysis (FR-004, FR-005, SC-002, SC-004)
*   **T031**: Compute P-PSNR, P-SSIM, Chamfer Distance (vs LiDAR), and **Geometric Divergence Score (GDS)** (Baseline vs Inpainted geometry).
*   **T032**: **Statistical Testing**:
    *   Primary: **Wilcoxon signed-rank test** on improvement (Inpainted - Baseline) to handle heteroscedasticity and non-normal differences.
    *   Secondary: **Linear Mixed-Effects (LMM)** model with `scene_complexity` as random effect to account for varying urban densities.
 * **Power Analysis**: N=50 targets [deferred] power for Cohen's d=0.4 (Wilcoxon). If exclusions reduce N < 35, report achieved power.
*   **T033**: **Threshold Sweep**: Sweep NNF (independent variable) to find critical threshold where p-value > 0.05.
*   **T034**: Plot "Performance Drop-off Curve" and "Recovery vs. Hallucination" (GDS vs. Improvement).

## Statistical Rigor & Assumptions

### Statistical Assumptions
*   **Independence**: Samples are spatially distinct.
*   **Normality**: Rejected for difference scores; using non-parametric Wilcoxon.
*   **Heteroscedasticity**: Addressed via Wilcoxon and LMM.
* **Power**: N=50 justified for d=0.4 (Wilcoxon). Exclusion rate modeled at [deferred].

### Computational Feasibility (CPU-Only)
*   **Model Choice**: Distilled, quantized diffusion model (ONNX).
*   **Data Subsampling**: 100m² patches.
*   **No GPU**: Strictly forbidden. `torch.set_num_threads(2)`.

### Limitations
*   **Generalizability**: Urban environments only.
*   **Dataset Availability**: If OpenTopography lacks coverage, N is reduced, and power is re-calculated.
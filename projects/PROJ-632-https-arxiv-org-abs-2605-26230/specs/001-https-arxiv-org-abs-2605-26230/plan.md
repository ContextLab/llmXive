# Implementation Plan: Reproduce & Validate Geometry-Aware Representation Denoising (GARD)

**Branch**: `001-reproduce-gard` | **Date**: 2024-05-21 | **Spec**: `specs/001-reproduce-gard/spec.md`
**Input**: Feature specification from `/specs/001-reproduce-gard/spec.md`

## Summary

This plan executes the reproduction and validation of the "Geometry-Aware Representation Denoising (GARD)" framework (arXiv:2605.26230). The primary technical approach involves vendoring the provided GARD codebase, configuring a CPU-only Python environment compatible with the GitHub Actions free tier (limited vCPU and RAM), and running the inference pipeline on a sample degraded multi-view dataset. The plan prioritizes robust error handling for missing datasets and GPU dependencies, ensuring the pipeline produces valid 3D geometry (`.ply`/`.obj`) and restored RGB images (`.png`) within 6 hours. Crucially, the plan addresses the scientific validity of the reproduction by defining a **Gaussian Blur Baseline** and **Blind Metrics** (NIQE, LPIPS) to distinguish true denoising from simple blurring or hallucination. The validation logic has been corrected to avoid circular reasoning: success is defined by the output having better perceptual quality than the blur baseline, rather than just being similar to the noisy input.

## Technical Context

**Language/Version**: Python 3.10 (verified compatibility with standard PyTorch CPU wheels)
**Primary Dependencies**: PyTorch (CPU-only build), Open3D (for geometry), Pillow/Pandas (for image/data), NumPy, `scikit-image` (for NIQE/LPIPS), `lpips` (library).
**Storage**: Local filesystem (`data/`, `outputs/`), no external database.
**Testing**: `pytest` (for unit tests), **Real-Call Integration Tests** (atomic pipeline validation).
**Target Platform**: Linux (GitHub Actions runner), CPU-only.
**Project Type**: Research Reproduction / CLI Tool.
**Performance Goals**: Complete inference on sample dataset < 6 hours; RAM usage < 7GB.
**Constraints**: No GPU/CUDA; no `load_in_8bit`; strict memory limits; graceful failure on missing data.
**Scale/Scope**: Single sample dataset run; generation of geometry file and restored image.

> **Dataset Fit Note**: The spec requires "multi-view images with simulated or real degradation" conforming to the DA3 benchmark format. The verified dataset list contains a `da3-giant-blind-spots` metadata CSV and tokenized data, but **no verified source for the actual image files** (pixels) required for 3D reconstruction. The plan explicitly handles this by requiring the user to provide the raw pixels in `data/da_sample`. If the dataset is missing or lacks image files, the system MUST trigger a **Scientific Null** error (distinct from a generic pipeline error), explicitly stating that the validation of the model's claims is impossible without the raw data.

## Spec Compliance Check (SSoT)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This section explicitly maps every Functional Requirement (FR) and Success Criterion (SC) to a concrete plan step.

| Requirement | Plan Step / Implementation | Validation Method |
| :--- | :--- | :--- |
| **FR-001** (CPU Execution) | Environment setup enforces `torch.device('cpu')`; pre-flight scan for CUDA calls. | `test_cpu_only.py` checks for `cuda` imports. |
| **FR-002** (Generate Artifacts) | Pipeline writes `.ply` and `.png` to `outputs/`. | `test_artifacts.py` checks file existence. |
| **FR-003** (Missing Dataset) | Pre-flight check validates `data/da3_sample` against `gard_input.schema.yaml`. | `test_missing_data.py` triggers `FileNotFoundError` with specific message. |
| **FR-004** (Time Limit) | Batch processing logic; timeout watchdog in `src/run_gard.py`. | CI job timeout set to 6h; logs monitored. |
| **FR-005** (Loadable Outputs) | Post-processing validation using `open3d` and `PIL`. | `test_loadability.py` attempts to load files. |
| **SC-001** (Zero Exit Code) | Pipeline exits 0 only if all validation steps pass. | CI exit code check. |
| **SC-002** (Loadable Files) | Explicit load test in `test_artifacts.py`. | `open3d.io.read_point_cloud()` success. |
| **SC-003** (Report Fidelity) | `reproduction_report.md` generated with specific comparison to paper figures. | Manual review of report content. |
| **SC-004** (GPU Failure) | Pre-flight scan aborts if `torch.cuda` is required. | `test_gpu_abort.py` simulates GPU call. |
| **SC-005** (Memory Safety) | Batch processing; OOM catch block with diagnostic. | CI logs checked for OOM. |

## Project Structure

### Documentation (this feature)

```text
specs/001-reproduce-gard/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-632-https-arxiv-org-abs-2605-26230/
├── external/
│   └── GARD/            # Vendored code (read-only)
├── data/
│   └── da3_sample/      # Input dataset (MUST conform to gard_input.schema.yaml)
├── outputs/
│   ├── geometry/        # .ply, .obj files
│   └── images/          # .png restored images
├── src/
│   ├── run_gard.py      # Main entry point wrapper
│   ├── validators.py    # Output validation logic (LPIPS, NIQE, Loadability)
│   └── config.py        # Configuration loading
├── tests/
│   ├── test_entry_point.py
│   ├── test_artifacts.py
│   ├── test_missing_data.py
│   ├── test_cpu_only.py
│   ├── test_gpu_abort.py
│   └── test_integration_real_call.py  # Atomic pipeline test
├── requirements.txt     # CPU-pinned dependencies
└── reproduction_report.md # Final output artifact
```

**Structure Decision**: The vendored `external/GARD` is kept isolated. A thin wrapper layer (`src/`) is introduced to enforce the CPU-only environment, manage file paths, and validate outputs against the spec's success criteria. This avoids modifying the original research code while adding necessary production guards.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Custom Wrapper Layer | The vendored code likely assumes GPU and specific paths. | Direct execution would fail on CPU runners or crash on missing files without the `FR-003` graceful error handling required by the spec. |
| Output Validators | `SC-002` requires loadable files. | Simple file existence checks are insufficient; MeshLab/ImageIO load tests are needed to confirm artifact integrity. |
| Blind Metrics (LPIPS/NIQE) | Ground truth is unavailable. | Simple variance reduction is a tautology; LPIPS/NIQE provide a perceptual baseline against blurring. |
| Control Baseline (Gaussian Blur) | To distinguish denoising from blurring. | Without a control, a "smoothed" output cannot be distinguished from a "denoised" output. |

## Validation Strategy

### Real-Call Integration Tests
To satisfy **SC-001** and **SC-002**, the plan mandates a **Real-Call Integration Test** (`test_integration_real_call.py`). This is a single atomic test case that:
1.  Loads the dataset from `data/da3_sample` (validating against `gard_input.schema.yaml`).
2.  Executes the full GARD inference pipeline.
3.  Validates the generated artifacts (loadability, non-empty).
4.  Computes blind metrics (LPIPS, NIQE) against the **Gaussian Blur Baseline** (not the noisy input).
5.  Generates the `reproduction_report.md`.

**Failure Modes**:
-   **Missing Data**: Triggers `FR-003` with a "Scientific Null" error message.
-   **GPU Detected**: Triggers `SC-004` with a specific "GPU/CUDA not available" error.
-   **OOM**: Triggers a diagnostic error with memory stats.

### Scientific Validity Controls (Corrected Logic)
-   **Blurring Control**: The pipeline generates a Gaussian-blurred version of the input images to serve as a "worst-case smoothing" baseline.
-   **Metric Comparison**:
    -   **NIQE (Natural Image Quality Evaluator)**: Compares `NIQE(Output)` vs `NIQE(Blur)`. A lower NIQE indicates a more natural image. Success is defined as `NIQE(Output) < NIQE(Blur)`.
    -   **LPIPS (Learned Perceptual Image Patch Similarity)**: Compares `LPIPS(Output, Blur)`. This measures how perceptually distinct the output is from the over-smoothed blur. A higher distance (or distinct feature map) suggests the model preserved details that the blur removed.
    -   **Decision Logic**:
        -   **Success**: `NIQE(Output) < NIQE(Blur)` AND `LPIPS(Output, Blur)` indicates significant structural difference (not just noise).
        -   **Failure (Over-Smoothing)**: `NIQE(Output) >= NIQE(Blur)` (Output is as blurry or worse than the Gaussian baseline).
        -   **Failure (No Denoising)**: `LPIPS(Output, Input)` is near zero (Output is identical to noisy input).
    -   **Rationale**: This avoids the circular logic of comparing output to the noisy input. Instead, it validates that the output is perceptually superior to a known blurring operation.

## Constitution Check

*Note: No specific constitution was supplied for this project. The plan adheres to general scientific rigor principles: avoiding circular validation, defining clear baselines, and ensuring reproducibility.*

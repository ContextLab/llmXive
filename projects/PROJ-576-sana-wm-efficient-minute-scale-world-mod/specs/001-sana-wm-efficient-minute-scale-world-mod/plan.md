# Implementation Plan: Reproduce & Validate SANA-WM

**Branch**: `576-reproduce-validate-sana-wm` | **Date**: 2024-05-22 | **Spec**: `specs/576-reproduce-validate-sana-wm/spec.md`
**Input**: Feature specification from `specs/576-reproduce-validate-sana-wm/spec.md`

## Summary

This feature reproduces the SANA-WM (Efficient Minute-Scale World Modeling) inference pipeline using the vendored `external/Sana` codebase. The primary technical approach involves configuring the existing Python inference scripts to run in CPU-only mode, handling large model weights within the GB RAM constraint via memory-efficient loading, and validating 6-DoF camera trajectory adherence using **Automated Pose Drift Error** (SfM-based) rather than visual inspection.

**Critical Scope Note**: This phase is a **Feasibility & Artifact Generation** run. It validates that the code runs on CPU and produces a video. It **does not** scientifically validate the "minute-scale efficiency" claim, as the hardware constraints (2 vCPU, 7 GB RAM) prevent full s generation. The "minute-scale" efficiency claim is formally **deferred** to a future phase. The 6-DoF adherence (SC-002) is now measured via **Automated Pose Drift Error** (reprojection metric), resolving the scientific rigor gap identified in previous reviews.

## Technical Context

**Language/Version**: Python 3.10+ (matching `external/Sana` requirements)  
**Primary Dependencies**: `torch` (CPU-only build), `diffusers`, `transformers`, `opencv-python`, `numpy`, `accelerate` (CPU config), `colmap` (or alternative SfM tool for pose estimation)  
**Storage**: Local filesystem (`external/Sana`, `output/`, `assets/`)  
**Testing**: `pytest` (for contract validation and script exit codes)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free tier)  
**Project Type**: CLI / Research Reproduction  
**Performance Goals**: Complete -second generation within 4 hours; Peak RAM < 7 GB  
**Constraints**: No GPU/CUDA; No model training; Must handle OOM gracefully; Must validate camera poses via contract.  
**Scale/Scope**: Single video generation run (duration, resolution), trajectory validation runs (Feasibility only).

> **Dataset Note**: The plan relies on the **vendored demo data** (`external/Sana/asset/sana_wm/*.npy`) mentioned in the spec's User Scenarios for inference. The verified JSONL files are for training and are not used.

## Constitution Check

*Gates determined based on project constitution (assumed standard scientific rigor):*

1.  **Reproducibility**: The plan mandates running the *exact* code in `external/Sana` with specific flags.
2.  **Resource Honesty**: The plan explicitly acknowledges the CPU limitation and defers "minute-scale" generation.
3.  **Data Integrity**: The plan requires validating input `.npy` files via a schema conversion step (see FR-006) against `contracts/CameraPose.schema.yaml`.
4.  **Metric Transparency**: All runtime metrics are logged to JSON.
5.  **Scientific Rigor**: The plan now uses an **Automated Pose Drift Error** metric (SfM-based) for SC-002, ensuring quantitative validation of the 6-DoF claim.

## Project Structure

### Documentation (this feature)

```text
specs/576-reproduce-validate-sana-wm/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── Sana/
    ├── diffusion/
    │   └── longsana/
    │       └── pipeline/
    │           └── sana_inference_pipeline.py
    ├── asset/
    │   └── sana_wm/
    │       ├── demo_0_pose.npy
    │       └── demo_0_intrinsics.npy
    └── requirements.txt

tests/
└── integration/
    └── test_sana_wm_inference.py

output/
└── videos/
    └── [generated_video.mp4]
```

**Structure Decision**: The plan utilizes the existing vendored structure (`external/Sana`) as the primary execution environment. No new source modules are created; the implementation relies on the CLI entry points defined in the submodule. Test scripts are added in `tests/integration/` to orchestrate the validation runs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CPU-only Inference on Diffusion Transformer | The spec explicitly requires validation on a CPU-only runner (US-1, US-3). | GPU inference is impossible on the target CI environment. |
| Frame-skipping / Resolution reduction | The limited RAM and time constraints make full 60s generation infeasible. | Running the full minute-scale generation would result in OOM or timeout, failing the "reproduction" goal entirely. |
| Numpy-to-JSON Conversion for Validation | The `CameraPose` contract is a JSON schema, but input is `.npy`. | Direct `.npy` validation against a JSON schema is impossible; conversion is required to enforce the data model. |
| SfM-based Pose Estimation | SC-002 requires quantitative validation of 6-DoF adherence, not visual inspection. | Visual inspection is subjective and non-reproducible, failing the scientific rigor requirement. |

## Mapping to Requirements

- **FR-001 (Load Model)**: Phase 1 will configure `torch` and `accelerate` to load weights into CPU memory.
- **FR-002 (CPU Flags)**: Phase 1 will enforce `CUDA_VISIBLE_DEVICES=""` and `device="cpu"` in the pipeline config.
- **FR-003 (Pose Input)**: Phase 2 will inject `demo_0_pose.npy` into the inference pipeline arguments.
- **FR-004 (Video Output)**: Phase 2 will verify `.mp4` generation.
- **FR-005 (Metrics)**: Phase 2 will wrap the execution in a timer/memory profiler, outputting `metrics.json`.
- **FR-006 (Pose Validation)**: Phase 2 includes a pre-check script that **loads the `.npy` file, converts it to a JSON representation, and validates it against `contracts/CameraPose.schema.yaml`** before generation.

- **SC-001 (Success Rate)**: Measured by exit code 0 in `test_sana_wm_inference.py`.
- **SC-002 (Camera Adherence)**: Measured by **Automated Pose Drift Error** (reprojection error between input pose and SfM-estimated pose). Target: ≤ 5% drift in 4/5 videos. This is calculated by the `validate_pose_drift.py` script, replacing manual review.
- **SC-003 (RAM < 7GB)**: Measured by `psutil` logging in `metrics.json`.
- **SC-004 (Time < 4h)**: Measured by wall-clock timer in `metrics.json`. **Note**: Validates feasibility only; minute-scale claim is deferred.
- **SC-005 (Artifact Valid)**: Measured by file existence and non-zero size check.

## Phases

### Phase 0: Research & Feasibility (Completed in `research.md`)
- Analyze `external/Sana` codebase for CPU compatibility.
- Identify memory bottlenecks in the diffusion transformer.
- Confirm availability of demo `.npy` files.
- **Identify Gap**: Define the Automated Pose Drift Error metric (SfM-based) to replace visual inspection.

### Phase 1: Data Model & Contracts
- Define the `InferenceConfig` schema.
- Define the `MetricsReport` schema.
- Define the `CameraPose` schema (JSON representation of `.npy` metadata).
- **Validation Logic**: Implement the `.npy` -> JSON -> Schema validation pipeline using `contracts/CameraPose.schema.yaml`. The plan explicitly uses this schema as the source of truth for input validation.

### Phase 2: Implementation & Validation
- Implement the CLI wrapper script to handle CPU flags and memory profiling.
- Implement the `test_sana_wm_inference.py` suite.
- Implement the SfM-based pose estimation script to calculate drift error.
- Execute multiple trajectory validation runs to address the research question using the established method (Author et al., Year)..
- **Automated Metric**: Calculate and log the Pose Drift Error for each run using the `contracts/CameraPose.schema.yaml` validated input and the generated video.

### Phase 3: Reporting
- Aggregate `metrics.json` files.
- Generate the final validation report including Pose Drift Error results.
- **Gap Report**: Document the "Minute-Scale Efficiency" claim as deferred to a future phase.

## Scientific Rigor & Spec Alignment Notes

1.  **SC-002 (Camera Adherence)**: The spec now defines success as **Automated Pose Drift Error**. The plan implements this metric using SfM to ensure quantitative, reproducible validation of the 6-DoF claim.
2.  **Efficiency Claim**: The 4-second run is a **Feasibility Proxy**. It does not validate the "minute-scale" claim. The plan explicitly states this limitation and defers the full validation.
3.  **Data Model Consistency**: FR-006 is satisfied by converting the `.npy` input to a JSON structure that matches `contracts/CameraPose.schema.yaml` before validation, ensuring the data model is enforced.
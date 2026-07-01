# Implementation Plan: LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing

**Branch**: `807-liveedit-real-time-diffusion-bas` | **Date**: 2024-05-22 | **Spec**: [link]
**Input**: Feature specification from `/specs/807-liveedit-real-time-diffusion-bas/spec.md`

## Summary

This feature implements the reproduction and validation of the "LiveEdit" paper (Paper #408) within a constrained CPU-only CI environment. The primary technical approach involves adapting the vendored `author-kit` submodule to run inference on CPU, implementing chunked video processing to satisfy 7GB RAM limits, and establishing an automated benchmarking suite. 

**CRITICAL METHODOLOGICAL SHIFT**: The plan explicitly rejects absolute hardware comparisons (CPU vs. GPU) and absolute static thresholds (e.g., a specific PSNR value) as scientifically invalid for this context. Validation relies **exclusively** on **Relative Metrics** (Distilled vs. Baseline on the same CPU hardware). 

**SPEC CONFLICT WARNING**: The project's `spec.md` Success Criteria (SC-002, SC-003) mandate absolute thresholds (±20% of 12.66 FPS, ≥30dB PSNR) that contradict this revised methodology. The implementation will enforce the scientifically valid relative metrics but will **flag these SCs as 'Spec-Root Cause' blocking gaps** in the final report, as the plan cannot satisfy contradictory requirements without a spec update.

## Technical Context

**Language/Version**: Python 3.10 (compatible with `author-kit` standard)  
**Primary Dependencies**: `torch` (CPU-only build), `diffusers`, `transformers`, `opencv-python`, `numpy`, `pandas`, `pytest`  
**Storage**: Local filesystem (temporary artifacts in `external/author-kit/tmp`, final outputs in `results/`)  
**Testing**: `pytest` with contract validation against generated JSON logs and video existence checks  
**Target Platform**: GitHub Actions Free Tier (Ubuntu, 2 vCPU, ~7 GB RAM, No GPU)  
**Project Type**: Computational Research / Validation Pipeline  
**Performance Goals**: End-to-end execution < 6 hours; Relative Speedup (Distilled/Baseline) ≥ 1.0; Background Stability Degradation < 5%; Flicker Score < 3x Noise Floor.  
**Constraints**: No CUDA/GPU; Max limited RAM (requires chunked processing); Max GB Disk; No external model downloads during CI (weights must be vendored or pre-cached).

> **Dataset/Model Note**: The "dataset" is the vendored sample video/mask pairs within the `author-kit` submodule. No external dataset download is required per Assumption in spec.

## Constitution Check

*GATE: Must pass before Phase 0 research. This check explicitly maps to the project's FR-030 Constitution principles.*

*   **Principle I (SSoT - Single Source of Truth)**: The plan adheres strictly to the `spec.md` requirements (FR-001 to FR-005) but **flags** Success Criteria SC-002 and SC-003 as contradictory to the scientifically valid methodology (Relative vs. Absolute). The plan will not silently satisfy the absolute thresholds; it will satisfy the relative ones and report the conflict.
*   **Principle II (No Silent Fallbacks)**: The plan mandates explicit error handling for missing masks and corrupted weights (Edge Cases). The system will NOT silently fallback to a "no-op" or degraded mode; it will abort with a specific "Missing Mask" or "Model Integrity Failed" error code, ensuring the researcher is aware of the failure.
*   **Principle III (Real-Call Testing)**: The validation pipeline executes the *actual* `author-kit` inference code on real sample data, not mocks or synthetic stubs. The benchmarking scripts measure real wall-clock time and pixel-level differences on the generated artifacts.
*   **Principle IV (Data Integrity)**: The plan includes a specific "Chunk Boundary Artifact Test" to ensure data integrity across processing seams, preventing temporal corruption that would invalidate the "stable background" claim.

## Spec Conflict Resolution (Blocking Gaps)

The following Success Criteria in `spec.md` are identified as **blocking gaps** due to scientific invalidity. The plan implements the *correct* relative methodology but cannot satisfy the *incorrect* absolute requirements without a spec update.

| Spec ID | Requirement | Conflict | Plan Action | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SC-002** | "Inference speed... within ±20% of 12.66 FPS" | **Category Error**: Comparing CPU FPS to likely GPU paper claim is invalid. | Implement Relative Speedup (Distilled/Baseline on CPU). Log absolute CPU FPS as "Feasibility Metric" only. Flag SC-002 as **BLOCKED**. | **Spec-Root Cause** |
| **SC-003** | "Background preservation... ≥ 30 dB" | **Arbitrary Threshold**: 30dB is meaningless without a baseline. | Implement Relative Degradation (Distilled vs. Baseline). Flag SC-003 as **BLOCKED**. | **Spec-Root Cause** |
| **SC-004** | "No visible flickering... verified by automated analysis" | **Missing Metric**: Spec lacks definition for "flicker". | Implement Noise Floor Calibration + Flicker Score (< 3σ). | **Implemented** |
| **N/A** | **Chunk Boundary Artifact** | **Missing SC**: No Success Criterion exists for chunk seams. | Implement Chunk Boundary Score (< 1.5x Global Variance). Flag as **BLOCKED** (No SC). | **Spec-Root Cause** |

## Project Structure

### Documentation (this feature)

```text
specs/807-liveedit-real-time-diffusion-bas/
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
└── author-kit/          # Vendored submodule (read-only for execution)
    ├── src/
    ├── models/
    └── samples/         # Input video/mask pairs

src/
├── liveedit/
│   ├── __init__.py
│   ├── runner.py        # Orchestrates chunked inference
│   ├── benchmark.py     # Calculates FPS, PSNR, SSIM, Noise Floor, Flicker
│   └── validators.py    # Checks for missing masks, corrupted weights
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/        # Validates output schemas

results/
├── videos/              # Generated output clips
└── metrics/             # JSON logs of benchmark results
```

**Structure Decision**: A single `src/liveedit` module wraps the `author-kit` logic to inject CPU-specific configurations and memory management (chunking) without modifying the vendored submodule. This isolates the adaptation logic from the research code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Chunked Video Processing | Required to fit 720p video into 7GB RAM on CPU | Loading full video into memory causes OOM on large inputs. |
| CPU-Only Diffusion | Target environment has no GPU | GPU-based inference is impossible on GitHub Actions free tier. |
| Relative Metric Comparison | Required for scientific validity (CPU vs GPU) | Absolute FPS comparison across hardware is a category error. |
| Automated Frame-Diff | Required for SC-004 (flicker detection) | Manual inspection is not scalable or reproducible. |
| Noise Floor Calibration | Required to define flicker threshold scientifically | Static threshold is arbitrary and prone to false positives. |

## Phase Plan

### Phase 0: Research & Feasibility Verification
*   **Objective**: Confirm `author-kit` can load on CPU, identify memory bottlenecks, and verify the "Chunk Boundary" logic.
*   **Steps**:
    1.  Analyze `author-kit` requirements.txt and model loading logic.
    2.  Verify `torch` CPU build compatibility with `diffusers`.
    3.  Identify specific variables required for the "three-stage distillation" and "AR-oriented mask cache" to ensure the code path exists.
    4.  **FR-001, FR-005**: Validate that input video loading can be intercepted for chunking.
    5.  **Chunk Boundary Test (New)**: Run a minimal 2-chunk inference on a static video to verify no seam artifacts are introduced by the chunking logic itself. Calculate the "Chunk Boundary Score".
    6.  **SC-001**: Estimate runtime for a 5-second clip on CPU to ensure <6h feasibility.
    7.  **Noise Floor Calibration**: Process a static video to establish the pipeline's inherent noise floor (σ_noise).

### Phase 1: Data Model & Interface Design
*   **Objective**: Define the data contracts for inputs, outputs, and metrics, including the new relative metrics.
*   **Steps**:
    1.  **FR-002**: Define the output directory structure for videos and logs.
    2.  **FR-003**: Design the JSON schema for benchmark results (FPS, relative speedup, baseline PSNR, noise floor, flicker score).
    3.  **FR-004**: Define the frame-difference metric logic for background stability (Output vs. Baseline).
    4.  **Validate Contracts**: Verify that `contracts/benchmark_result.schema.yaml` and `contracts/output_manifest.schema.yaml` (already defined in data-model.md) match the data model.
    5.  **SC-003**: Establish the threshold logic for relative PSNR degradation.

### Phase 2: Implementation (Orchestrator & Validation)
*   **Objective**: Build the runner, benchmark, and validator scripts.
*   **Steps**:
    1.  Implement `src/liveedit/runner.py` with chunked video loading logic.
    2.  Implement `src/liveedit/validators.py` to check for missing masks (Edge Case) and corrupted weights (Edge Case). **Traceability**: This step addresses the Spec Edge Cases and SC-005 (OOM/Integrity) by ensuring the system fails gracefully rather than crashing, but specifically links SC-005 to OOM handling and Edge Cases to Integrity/Masks.
    3.  Implement `src/liveedit/benchmark.py` to calculate:
        *   FPS (for both Distilled and Baseline).
        *   **Relative Speedup** (Distilled FPS / Baseline FPS).
        *   **Background Stability** (Distilled Output PSNR vs. Baseline Output PSNR).
        *   **Flicker Score** (Output variance / Noise Floor).
        *   **Chunk Boundary Score** (Boundary difference / Global Variance).
    4.  **FR-001, FR-002**: Ensure the runner executes the `author-kit` inference and saves artifacts.
    5.  **FR-003, FR-004**: Ensure metrics are logged and background stability is measured.
    6.  **Edge Cases**: Implement graceful failure modes for OOM and missing inputs.

### Phase 3: Integration & Testing
*   **Objective**: Run the full pipeline on CI and validate against Success Criteria.
*   **Steps**:
    1.  Configure GitHub Actions workflow (CPU-only, 7GB RAM limit).
    2.  Execute `src/liveedit/runner.py` on sample data (Distilled) and baseline data.
    3.  **SC-001**: Verify completion within 6 hours.
    4.  **SC-002 (Blocked)**: Verify Relative Speedup ≥ 1.0. Log absolute CPU FPS as "Feasibility Metric". Report SC-002 as **FAIL** (Spec Conflict) if absolute threshold is not met, but **PASS** on relative metric.
    5.  **SC-003 (Blocked)**: Verify Background Stability degradation < 5% (Distilled vs Baseline). Report SC-003 as **FAIL** (Spec Conflict) if absolute 30dB is not met, but **PASS** on relative metric.
    6.  **SC-004**: Verify Flicker Score < 3x Noise Floor.
    7.  **SC-005**: Verify no OOM or disk limit exceeded.
    8.  **New**: Verify Chunk Boundary Score < 1.5. Report as **FAIL** (Spec Gap) if no SC exists, but **PASS** on metric.
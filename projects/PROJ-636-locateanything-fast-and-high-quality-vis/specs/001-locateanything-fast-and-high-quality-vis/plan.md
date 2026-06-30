# Implementation Plan: Reproduce & Validate LocateAnything (Eagle)

**Branch**: `636-reproduce-locateanything` | **Date**: 2023-10-27 | **Spec**: `specs/636-reproduce-locateanything/spec.md`

## Summary

This project reproduces the "LocateAnything: Fast and High-Quality Vision-Language Grounding with Parallel Box Decoding" implementation vendored in `external/Eagle`. The primary goal is to validate the core "Parallel Box Decoding" (PBD) mechanism's *correctness* and the evaluation pipeline on a CPU-only, free-tier GitHub Actions runner (2 CPU, 7GB RAM). 

**Critical Constraint**: The original paper likely relies on GPU parallelism and large models (7B+). This plan adapts the reproduction to CPU constraints by:
1. Using **GGUF quantization** (via `llama-cpp-python`) to ensure the model fits in 7GB RAM.
2. Implementing a **CPU-Native Serial Fallback** for PBD if CUDA kernels are detected or fail, allowing verification of box generation correctness and measurement of relative speedup (PBD time vs. Serial time).
3. Using **Synthetic Ground Truth** (programmatically injected boxes) for IoU calculation, as verified real-world bounding box datasets are unavailable in the provided list.

## Technical Context

**Language/Version**: Python 3.10+ (targeting standard CI environment)  
**Primary Dependencies**: `llama-cpp-python` (CPU-optimized), `transformers`, `Pillow`, `pandas`, `pytest`, `numpy`  
**Storage**: Local filesystem (temporary artifacts), GitHub Actions ephemeral storage (~14GB)  
**Testing**: `pytest` (for contract validation), shell scripts (for execution flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Research / Reproduction  
**Performance Goals**: Inference < 60s/image (CPU, quantized), Evaluation subset < 15 mins, RAM < 7GB peak.  
**Constraints**: NO GPU, NO CUDA, NO `bitsandbytes`, NO float32 loading for 7B+ models.  
**Scale/Scope**: Single model inference (quantized), small benchmark subset (50 images) with Synthetic Ground Truth.

> **Note**: If the `external/Eagle` code strictly requires CUDA kernels for PBD, the plan will execute a "CPU-Serial Fallback" (iterative decoding implemented in Python/NumPy) to verify box generation correctness. The "Parallel Speedup" claim will be measured as the ratio of Serial Time / PBD Time (if PBD runs) or marked as "Unmeasurable" if PBD fails completely.

## Constitution Check

*This plan references the project's `constitution.md` file (FR-030).*

**Constitution Missing Handling**:
The `constitution.md` file is currently missing from the project root.
- The plan does **NOT** halt.
- It proceeds using "Standard Scientific Integrity Principles" (Transparency, Feasibility, Reproducibility) as a default.
- The `reproduction_report.md` will explicitly note: "Constitution file missing; default principles applied."
- Future iterations must supply `constitution.md` to satisfy FR-030.

## Project Structure

### Documentation (this feature)

```text
specs/636-reproduce-locateanything/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── inference_result.schema.yaml
│   └── evaluation_metric.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
external/
└── Eagle/               # Vendored model code

src/
├── inference/
│   ├── run_smoke_test.py      # FR-001, US-1 (CPU/GGUF, Serial Fallback)
│   └── utils.py               # CPU device handling, memory logging
├── evaluation/
│   ├── run_subset_eval.py     # FR-003, US-2 (Synthetic GT)
│   └── metrics.py             # IoU calculation (Synthetic GT)
├── reporting/
│   └── generate_report.py     # FR-005, US-3
└── config/
    └── settings.yaml          # Dataset paths, batch size, model config

tests/
├── contract/
│   ├── test_inference_schema.py
│   └── test_evaluation_schema.py
└── integration/
    └── test_end_to_end.py

contracts/
├── inference_result.schema.yaml
└── evaluation_metric.schema.yaml
```

**Structure Decision**: The `src/` directory is used to isolate the reproduction logic from the vendored `external/Eagle` code, ensuring the main codebase remains clean and the reproduction scripts can be version-controlled independently. The `contracts/` directory holds the schemas for validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| GGUF Quantization | Float/16 OOMs on 7GB RAM for 7B+ models. | Using float32 guarantees failure; GGUF is the only CPU-tractable path. |
| CPU-Serial Fallback | PBD may rely on CUDA kernels. | Ignoring PBD would fail the "correctness" test; serial fallback validates logic and provides a baseline for speedup comparison. |
| Synthetic Ground Truth | No verified real-world GT dataset available. | Using embedding-only datasets for IoU is scientifically invalid; Synthetic GT allows pipeline validation. |

## Phased Plan

### Phase 0: Research & Feasibility (Week 1)
*Goal: Confirm dataset availability (Ground Truth) and model compatibility with CPU-only constraints.*

- **Step 0.1**: Verify `external/Eagle` submodule integrity and check for `.gguf` or `.safetensors` files.
- **Step 0.2**: Analyze `external/Eagle` code for GPU-specific dependencies. Plan a CPU-Serial Fallback strategy if PBD relies on CUDA.
- **Step 0.3**: Validate access to verified datasets containing **bounding box annotations** (Ground Truth). 
    - *If no verified dataset with boxes exists*: Plan switches to "Synthetic Ground Truth" mode (injecting known boxes into images).
- **Step 0.4**: Draft `research.md` with dataset strategy and compute feasibility analysis.

### Phase 1: Data Model & Contracts (Week 1)
*Goal: Define the data structures for inference and evaluation.*

- **Step 1.1**: Define `InferenceResult` schema (image_id, prompt, predicted_boxes, time, memory, status, pbd_serial_overhead_ms).
- **Step 1.2**: Define `EvaluationMetric` schema (benchmark, subset_size, mean_iou, throughput, memory_limit_pass, validation_mode, ground_truth_source).
- **Step 1.3**: Generate `contracts/*.schema.yaml` files.
- **Step 1.4**: Create `data-model.md` and `quickstart.md`.

### Phase 2: Implementation (Week 2)
*Goal: Build the scripts for inference, evaluation, and reporting.*

- **Step 2.1**: Implement `run_smoke_test.py` (FR-001, FR-002).
    - Load model with `device="cpu"` (GGUF).
    - Execute PBD (or CPU-Serial Fallback) on sample image.
    - **Mandatory**: Run a **Serial Baseline** (iterative decoding) to measure `pbd_serial_overhead_ms` (Serial Time - PBD Time). If PBD fails, this becomes the primary correctness check.
    - Log memory/time.
    - Validate output JSON.
- **Step 2.2**: Implement `run_subset_eval.py` (FR-003, US-2).
    - Load verified dataset subset (or Synthetic GT if real GT missing).
    - Run batch inference (batch_size=1).
    - Calculate IoU **only if** Ground Truth is available (Real or Synthetic); otherwise, log `validation_mode: 'pipeline_only'`.
    - Handle missing images (FR-005): Log `status: "error"` and `error_message` to `InferenceResult` (aligning with data model).
- **Step 2.3**: Implement `generate_report.py` (FR-004, US-3).
    - Aggregate logs.
    - Compare against paper claims (SC-001, SC-004) with explicit caveats on CPU vs. GPU and sample size.
    - Compare model output against a **Trivial Baseline** (random box) for relative quality.
    - Generate `reproduction_report.md`.

### Phase 3: Verification & Reporting (Week 2)
*Goal: Run the full pipeline and validate against success criteria.*

- **Step 3.1**: Execute end-to-end pipeline on GitHub Actions.
    - **Step 3.1.1**: **Memory Threshold Validation**: Parse logs, verify `peak_memory_mb` < 7000 MB. Record Pass/Fail for SC-003. Set `memory_limit_pass` in schema.
- **Step 3.2**: Validate outputs against `contracts/*.schema.yaml`.
- **Step 3.3**: Review `reproduction_report.md` for completeness and explicit limitations.
- **Step 3.4**: Finalize `plan.md` and close the feature.

## FR/SC Coverage Map

| ID | Type | Target Phase/Step | Notes |
|----|------|-------------------|-------|
| FR-001 | Functional | Step 2.1 | CPU-only loading (GGUF), no bitsandbytes. |
| FR-002 | Functional | Step 2.1 | PBD (or Serial) execution, JSON output. |
| FR-003 | Functional | Step 2.2 | IoU calculation (Synthetic GT) or GT-Missing flag. |
| FR-004 | Functional | Step 2.1, 2.2 | Memory/Time logging. |
| FR-005 | Functional | Step 2.2 | Graceful handling of missing images (status: error, error_message populated). |
| SC-001 | Success | Step 3.3 | Compare throughput vs. paper (with CPU caveat). |
| SC-002 | Success | Step 3.3 | Compare IoU vs. Trivial Baseline (Relative Quality). Absolute accuracy marked "Unverified". |
| SC-003 | Success | Step 3.1.1 | Explicit memory validation step (threshold 7000 MB). |
| SC-004 | Success | Step 3.3 | Pass/Fail status on claims (with caveats). |

## Compute Feasibility Strategy

- **Hardware**: GitHub Actions free-tier (2 CPU, 7GB RAM).
- **Model**: **Mandatory GGUF Quantization** (e.g., `q4_0`) via `llama-cpp-python`. 
    - *Constraint*: Float32/16 is **prohibited** for 7B+ models due to OOM.
- **Data**: Subset to 50 images with Synthetic Ground Truth.
- **Batching**: Batch size = 1 to prevent OOM.
- **Timeout**: Scripts must complete within 6 hours.
- **Fallback**: If the model fails to load on CPU, the plan logs "Hardware Incompatible" and halts.
- **PBD Strategy**: If PBD fails on CPU, execute CPU-Serial Fallback (iterative loop) and measure time difference against Serial Baseline.

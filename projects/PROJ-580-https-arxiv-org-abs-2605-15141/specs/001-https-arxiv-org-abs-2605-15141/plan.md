# Implementation Plan: Causal Forcing++ Reproduction & Validation

**Branch**: `580-reproduce-causal-for-validation` | **Date**: 2025-05-23 | **Spec**: `specs/580-reproduce-causal-forcing-validation/spec.md`
**Input**: Feature specification from `/specs/580-reproduce-causal-forcing-validation/spec.md`

## Summary

Reproduce and validate the "Causal Forcing++" implementation vendored at `external/Causal-Forcing`. The primary requirement is to ensure the codebase initializes correctly, executes a lightweight inference pass (generating a video artifact), and performs a single training step (verifying loss computation and checkpoint saving) within the constraints of a free-tier GitHub Actions runner (CPU-only, limited RAM, 6h limit). The technical approach involves initializing git submodules, installing dependencies, configuring the `wan_t2v_1_3B` model for CPU execution with aggressive memory management, and running minimal synthetic test cases to satisfy FR-001 through FR-005.

## Technical Context

**Language/Version**: Python (required by `wan`/`diffusers` ecosystem).  
**Primary Dependencies**: PyTorch (CPU-only build), `wan` (vendored), `transformers`, `diffusers`, `accelerate`, `av` (ffmpeg-python), `numpy`, `jsonschema`.  
**Storage**: Local filesystem for temporary artifacts (`.mp4`, `.pt`). No persistent database.  
**Testing**: `pytest` for unit validation; shell scripts for integration (inference/training loops).  
**Target Platform**: Linux (Ubuntu 22.04) on GitHub Actions free-tier (2 vCPU, 7GB RAM).  
**Project Type**: Research validation / CI pipeline.  
**Performance Goals**: Inference < 15 mins (for 16 frames, 2 steps); Training step < 30 mins (5 steps). Total job < 6h.  
**Constraints**: NO GPU/CUDA. Must handle missing weights gracefully or fail fast with specific error. Memory < 7GB.  
**Scale/Scope**: Single feature branch validation; no large dataset downloads (synthetic/dummy data only).

> **Critical Feasibility Note**: The `wan_tv__3B` model is ~2.6GB in FP16. On a CPU-only runner with 7GB RAM, loading the model + overhead + video buffers is tight. The plan implements a **Tiered Precision Strategy**:
> 1. **Attempt FP16**: Force `torch.float16` if supported by CPU build.
> 2. **Fallback to INT8**: If FP fails or is unsupported, attempt `bitsandbytes` quantization (if available on CPU) to reduce weights to a significantly smaller memory footprint.
> 3. **Last Resort**: If quantization fails, reduce resolution to `128x128` and `frames=8` to fit FP32 weights.
> 4. **Fail Fast**: If all strategies fail, the script logs "Memory Limit Exceeded" and exits with a specific error code, ensuring SC-005 is not falsely passed.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

*Note: The project constitution file (`constitution.md`) was not provided in the input. Per FR-030 requirements, this plan performs a check against the **Default SSoT Principles** (Reproducibility, Resource Honesty, Failure Transparency, Scope Adherence) as a fallback.*

- [x] **Principle 1 (Reproducibility)**: Does the plan ensure deterministic seeds and version pinning? **Yes**, via `requirements.txt` and explicit seed setting in `demo.py`/`train.py` wrappers.
- [x] **Principle 2 (Resource Honesty)**: Does the plan acknowledge the lack of GPU? **Yes**, the plan explicitly targets CPU-only execution and synthetic data to avoid OOM, with a tiered fallback strategy for memory.
- [x] **Principle 3 (Failure Transparency)**: Does the plan handle missing weights? **Yes**, FR-002 and Edge Cases mandate a "fail fast" mechanism with specific error messages for missing checkpoints.
- [x] **Principle 4 (Scope Adherence)**: Does the plan avoid scientific quality claims? **Yes**, SC-001/SC-002 focus on artifact existence and code execution, not VBench scores.

## Project Structure

### Documentation (this feature)

```text
specs/580-reproduce-causal-forcing-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── validation_report.schema.yaml
│   └── artifact_manifest.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
# Option 1: Validation Scripts & Config Wrappers
external/Causal-Forcing/       # Vendored submodule (read-only)
specs/580-reproduce-causal-forcing-validation/
├── scripts/
│   ├── run_inference_cpu.py   # Wrapper to force CPU, low-res, 2 steps
│   ├── run_training_dummy.py  # Wrapper to force synthetic data, 5 steps
│   └── validate_env.py        # Dependency check & submodule hash verify
├── configs/
│   ├── cpu_inference_override.yaml # Overrides for low-resource
│   └── cpu_training_override.yaml  # Overrides for synthetic data
└── tests/
    └── test_validation.py       # Pytest suite for artifacts
```

**Structure Decision**: The validation logic is isolated in `specs/.../scripts/` to avoid modifying the vendored `external/Causal-Forcing` code directly. This ensures the original research code remains pristine while allowing us to inject CPU-specific flags and dummy data loaders.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **CPU-only execution for 1.3B model** | Free CI lacks GPU. | Running on GPU would require paid runners; skipping validation would violate FR-003. |
| **Synthetic data for training** | Downloading video datasets exceeds time and storage limits. | Using real data would cause OOM or timeout before loss computation can be verified. |
| **Fail-fast on missing weights** | Prevents silent generation of random noise. | Attempting to generate random weights would produce invalid artifacts, violating SC-001's intent (valid pipeline). |
| **Tiered Precision Strategy** | FP16 may not fit 7GB RAM on CPU. | Assuming FP16 always fits risks a silent OOM; the fallback ensures we either run or fail clearly. |

## Phased Implementation Plan

### Phase 0: Environment & Dependency Resolution (FR-001, FR-002)
1.  **Submodule Initialization**: Script to verify `external/Causal-Forcing` commit hash matches spec.
2.  **Dependency Installation**: `pip install` with strict version pinning.
3.  **Import Verification**: Execute `python -c "import wan; import model"` to confirm `ModuleNotFoundError` absence.
4.  **CPU Fallback Check**: Verify PyTorch is installed in CPU mode and `wan` supports `device="cpu"`.

### Phase 1: Lightweight Inference Execution (FR-003, SC-001)
1.  **Configuration Override**: Generate `cpu_inference_override.yaml` setting `num_steps=2`, `frames=16`, `resolution=256x256` (or lowest available). **This file must conform to the schema in `data-model.md` Section 4.1.**
2.  **Weight Check**: Script checks for `wan_t2v_1_3B` checkpoint. If missing, exit with `ERROR: Missing weights` (SC-005).
3.  **Execution**: Run `demo.py` with CPU flags.
4.  **Artifact Validation**: Verify `.mp4` file exists, size > 1KB, and contains valid video codec headers.

### Phase 2: Training Step Validation (FR-004, SC-002)
1.  **Synthetic Loader**: Implement a dummy `DataLoader` that yields random tensors matching the expected input shape.
2.  **Configuration Override**: Generate `cpu_training_override.yaml` with `max_steps=5`, `batch_size=1`. **This file must conform to the schema in `data-model.md` Section 4.2.**
3.  **Execution**: Run `train.py` (or `train_step.py`) for 5 steps.
4.  **Algorithmic Sanity Check**: Verify:
    - Loss values are finite (not NaN/Inf).
    - Gradient L2-norms are non-zero (confirming backpropagation).
5.  **Checkpoint Validation**: Verify `.pt` file exists, size > 100KB, and contains valid `state_dict` keys.

### Phase 3: Reporting & Compliance (FR-005, SC-003, SC-004, SC-005)
1.  **Report Generation**: Aggregate logs, artifact paths, and exit codes into `validation_report.json`.
2.  **Schema Validation**: Validate `validation_report.json` against `contracts/validation_report.schema.yaml` using `jsonschema`.
3.  **Resource Check**: Log peak RAM usage (if available via `psutil`) and total runtime.
4.  **Final Validation**: Assert all FRs and SCs are met.

## Risk Mitigation

- **Risk**: `wan_t2v_1_3B` exceeds 7GB RAM on CPU.
  - **Mitigation**: The plan implements a tiered precision strategy (FP16 -> INT8 -> Resolution Reduction). If all fail, the script logs "Memory Limit Exceeded" and marks the test as `FAIL` with a specific reason, rather than hanging.
- **Risk**: `wan` library hardcodes CUDA checks.
  - **Mitigation**: The `run_inference_cpu.py` wrapper will attempt to monkey-patch `torch.cuda.is_available` to `False` before import, or patch the `wan` device selection logic if the code is accessible. If the library crashes on import, the plan fails FR-002.
- **Risk**: Missing pre-trained weights.
  - **Mitigation**: The spec assumes weights are missing. The plan explicitly handles this by failing fast (Edge Case) rather than generating random noise, ensuring SC-001 is not falsely passed.
- **Risk**: Synthetic data produces trivial gradients.
  - **Mitigation**: Phase 2 includes a "Gradient Sanity Check" to ensure gradients are non-zero. If gradients are zero, the test fails, indicating a broken backprop mechanism.
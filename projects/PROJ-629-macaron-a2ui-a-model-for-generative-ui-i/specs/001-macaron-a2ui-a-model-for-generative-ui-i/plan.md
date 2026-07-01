# Implementation Plan: Macaron-A2UI Reproduction & Validation

**Branch**: `001-macaron-a2ui-reproduction` | **Date**: 2024-05-22 | **Spec**: `spec.md`

## Summary

This feature implements a strict CPU-only reproduction and validation pipeline for the "Macaron-A2UI" generative UI model. The primary requirement is to execute the vendored `Macaron-A2UI-Bench` evaluation script on a free-tier GitHub Actions runner (2 CPU, 7GB RAM) to verify code execution, generate visual UI artifacts (PNGs), and produce a quantitative evaluation report. 

**Critical Constraint**: The plan **does not permit model substitution**. If the exact model weights specified in the paper are missing or incompatible with the CPU-only environment (even with GGUF quantization), the quantitative validation of the "75.6" score is marked as **Uncomputable**. The pipeline will still attempt to run a "Mock" or "Partial" mode to verify the *infrastructure* (exit code 0, artifact generation) but will not generate a comparative score.

## Technical Context

**Language/Version**: Python 3.10 (standard for HuggingFace/PyTorch ecosystems)  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `llama-cpp-python` (for CPU quantization), `Pillow`, `jsonschema`, `pytest`  
**Storage**: Local file system (vendor submodule, `data/eval_300`, `results/`, `render/`)  
**Testing**: `pytest` (unit tests for schema validation), CI exit-code checks (integration)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research / Reproduction pipeline  
**Performance Goals**: Complete full evaluation within 6 hours; Zero OOM errors; < 7GB RAM peak usage.  
**Constraints**: 
- **NO GPU/CUDA**.
- **NO 8-bit/4-bit quantization via `bitsandbytes`** (requires CUDA kernels).
- **Mandatory GGUF Quantization**: Inference must use `llama-cpp-python` with Q4_K_M or similar quantization to fit 7B+ models in 7GB RAM.
- **No Sub-sampling for Scoring**: The full dataset must be processed for any score calculation. If the run times out, the score is marked "Incomplete".
- **Exact Weights Required**: No model substitution allowed for score validation.

> **Note on Dataset Fit**: The spec references `Macaron-A2UI-Bench` which is not in the verified datasets list. The plan assumes the codebase is vendored (submodule). If the benchmark requires external data not present in the submodule, the plan will fail at the data-loading phase; this is a known risk to be flagged in `research.md`.

## Constitution Check

*This project adheres to the per-project `constitution.md` located at `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/.specify/memory/constitution.md`. The following principles are explicitly addressed:*

1.  **Principle I (Single Source of Truth)**: The plan relies strictly on the `spec.md` and the vendored `Macaron-A2UI-Bench` as the SSoT. No external assumptions about model weights are made; verification is Step 0.2.
2.  **Principle II (Resource Fidelity)**: The plan strictly adheres to the constrained RAM and time budget by mandating GGUF quantization and forbidding FP16/FP32 inference for large models.
3.  **Principle III (Reproducibility)**: The plan mandates the use of the *exact* model weights. Substitution is forbidden to prevent construct validity errors. If weights are missing, the result is "Uncomputable", not "Approximated".
4.  **Principle IV (Transparency)**: Any deviation (e.g., timeout, missing weights) is explicitly recorded in the `EvaluationReport` as a `status: "uncomputable"` or `status: "timeout"`.

## Project Structure

### Documentation (this feature)

```text
specs/001-macaron-a2ui-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
vendor/
└── Macaron-A2UI-Bench/
    ├── evaluate_api_model.py
    ├── render_check.py
    ├── data/
    │   └── eval_300/
    │       ├── annomi_tasks.json
    │       ├── esconv_tasks.json
    │       ├── multiwoz_tasks.json
    │       └── sgd_tasks.json
    ├── results/
    └── render/
        └── public/
            └── showcase/

scripts/
└── setup-evaluation.sh  # Orchestrates the CI run

tests/
├── contract/
│   └── test_evaluation_schema.py
└── integration/
    └── test_cpu_execution.py
```

**Structure Decision**: The project utilizes a "Vendor + Scripts" structure. The core logic resides in the vendored `Macaron-A2UI-Bench` submodule, while the project's `scripts/` and `tests/` directories contain the orchestration and validation logic required to meet the CI constraints. This isolates the reproduction logic from the research code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **No Model Substitution** | Substituting a 7B model for the paper's model invalidates the "75.6" score comparison (Category Error). | Using a proxy model would produce a score that is not a reproduction of the paper's claim. |
| **No Sub-sampling for Scoring** | Sub-sampling (e.g., 50 tasks) introduces high variance, making the "75.6" comparison statistically invalid. | Running a sample would make the "validation" of the 75.6 claim methodologically unsound. |
| **Mandatory GGUF Quantization** | FP16/FP32 for 7B+ models requires >14GB RAM, exceeding the GB limit. | Standard `bitsandbytes` quantization is excluded as it often requires CUDA kernels or is not CPU-optimized in standard wheels. |

## Phases & Steps

### Phase 0: Research & Feasibility
- **Step 0.1**: Inspect `Macaron-A2UI-Bench` to identify the default model weights and configuration.
- **Step 0.2**: **Weight Verification**: Confirm the presence of the *exact* model weights (or a GGUF-quantized equivalent) in the submodule. If missing, flag the study as "Uncomputable" for score validation.
- **Step 0.3**: Determine the CPU-compatible inference engine (`llama-cpp-python` vs `transformers` CPU). **Decision**: `llama-cpp-python` is mandatory for 7B+ models to fit in 7GB RAM.
- **Step 0.4**: Define the "Mock Mode" strategy for debugging (sub-sampling) which is **disabled** for the final score run.

### Phase 1: Data Model & Contracts
- **Step 1.1**: Define the `EvaluationReport` schema (JSON) based on `evaluate_api_model.py` output, including fields for `model_name`, `status` (success/uncomputable/timeout), and `delta`.
- **Step 1.2**: Define the `TaskInstance` schema for input data, including `model_name` as a required input constraint.
- **Step 1.3**: Create `contracts/evaluation_report.schema.yaml` and `contracts/task_instance.schema.yaml` and explicitly validate the generated report against these files in the CI pipeline.

### Phase 2: Implementation (Orchestration)
- **Step 2.1**: Create `scripts/setup-evaluation.sh` to install dependencies (`llama-cpp-python`, CPU `torch`) and configure environment variables (`device="cpu"`, `quantization="q4_k_m"`).
- **Step 2.2**: Implement the "Full Dataset" logic. If the script times out, the pipeline must exit with code 0 but mark the score as "Incomplete" in the report.
- **Step 2.3**: Configure the `render` directory to generate PNGs without a build step.

### Phase 3: Execution & Validation
- **Step 3.1**: Run the evaluation pipeline on the CI runner.
- **Step 3.2**: Validate the generated JSON report against the `contracts/evaluation_report.schema.yaml`.
- **Step 3.3**: Verify the existence and validity of the generated PNG artifacts.
- **Step 3.4**: **Score Validation**: Check if `model_name` matches the paper's model. If yes, calculate delta from 75.6. If no, or if weights missing, set score to "N/A" and status to "Uncomputable".

### Phase 4: Reporting
- **Step 4.1**: Generate `research.md` summarizing the execution results, score validity (or lack thereof), and any resource constraints encountered.
- **Step 4.2**: Finalize `quickstart.md` for future reproduction.

## Success Criteria (Updated)

- **SC-001**: The reproducibility success rate is measured against the binary outcome of the CI job (Pass/Fail), where "Pass" requires exit code 0 and artifact generation.
- **SC-002**: The visual artifact completeness is measured against the count of expected task instances, requiring ≥ 10 successful image generations (if the run completes).
- **SC-003**: The quantitative score deviation is measured against the paper's reported "Overall" score of 75.6 **ONLY IF** the exact model weights are used. If weights are missing or substituted, the score is "N/A" and the claim is "Uncomputable".
- **SC-004**: The resource feasibility is measured against the free-tier runner constraints (limited CPU, limited RAM, bounded execution time), requiring zero OOM errors.
- **SC-005**: The dataset coverage is measured against the four source datasets (annomi, esconv, multiwoz, sgd), requiring successful processing of ≥ 1 instance from each **if time permits**. If the run times out, the status is "Incomplete".
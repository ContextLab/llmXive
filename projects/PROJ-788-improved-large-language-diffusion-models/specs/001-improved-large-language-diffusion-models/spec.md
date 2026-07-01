# Feature Specification: Reproduce & Validate iLLaDA

**Feature Branch**: `788-reproduce-illada`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Improved Large Language Diffusion Models"

## User Scenarios & Testing

### User Story 1 - Execute CPU-Tractable Reproduction Pipeline (Priority: P1)

As a researcher, I need to run the vendored `LLaDA` evaluation scripts on a CPU-only GitHub Actions runner to confirm the code executes without hardware errors and produces valid output artifacts (logs, metrics, or partial generations).

**Why this priority**: This is the foundational requirement. Without a successful execution on the target infrastructure (CPU-only, no GPU), the project cannot proceed to validation or comparison. The paper claims a large-scale model, which is heavy; the primary risk is OOM or CUDA dependency. This story validates feasibility.

**Independent Test**: Can be fully tested by triggering the CI job with a minimal dataset subset (e.g., 5 samples) and verifying the exit code is 0 and a non-empty log file is generated.

**Acceptance Scenarios**:

1. **Given** the `external/LLaDA` submodule is cloned and dependencies are installed, **When** the runner executes `python eval_llada.py` with a small subset flag on a CPU-only environment, **Then** the process completes within 6 hours without CUDA errors and outputs a `results.json` file containing at least one metric.
2. **Given** the environment has no GPU drivers, **When** the script attempts to initialize the model, **Then** it explicitly loads the model in `cpu` or `mps` mode (if available) and does not crash with a `CUDA out of memory` or `device_map` error.

---

### User Story 2 - Validate Benchmark Output Against Paper Claims (Priority: P2)

As a reviewer, I need to compare the generated metrics from the reproduction run against the specific numbers reported in the paper (e.g., BBH, ARC-Challenge) to determine if the implementation is faithful.

**Why this priority**: Once the code runs (P1), the scientific value lies in verifying the claims. This step determines if the "Improved" results are reproducible under the constrained environment.

**Independent Test**: Can be tested by running the evaluation on a standard subset (e.g., [deferred] of the original test set) and comparing the output JSON keys and values against the paper's abstract/table values.

**Acceptance Scenarios**:

1. **Given** a successful run of `eval_llada.py` on the `bbh` dataset subset, **When** the results are parsed, **Then** the output file contains a score for `bbh` that is within ±5% of the paper's reported `iLLaDA-Base` score (or clearly marked as a partial run due to resource limits).
2. **Given** the evaluation includes `human_eval` or `math`, **When** the results are generated, **Then** the output format matches the `opencompass` standard JSON schema, allowing for automated diffing against the paper's table.

---

### User Story 3 - Generate Visual Artifacts and Logs (Priority: P3)

As a stakeholder, I need the system to generate the visualization artifacts (e.g., `LLaDA_vs_LLaMA.svg`) and generation logs to document the behavior of the diffusion process.

**Why this priority**: While not strictly required for the "pass/fail" of the reproduction, these artifacts are necessary for the final report and to demonstrate the "diffusion" nature of the model (e.g., masking/unmasking steps) which is central to the paper's contribution.

**Independent Test**: Can be tested by running the `visualization` scripts and checking for the existence of SVG/PNG files in the output directory.

**Acceptance Scenarios**:

1. **Given** the `visualization` module is executed, **When** the script completes, **Then** it produces at least one SVG file (e.g., `diff_remask.gif` or `LLaDA_vs_LLaMA.svg`) in the `results/` directory.
2. **Given** the `generate.py` script is run, **When** it processes a prompt, **Then** it outputs the intermediate token states (masking steps) to a log file, confirming the non-autoregressive generation process.

---

### Edge Cases

- **What happens when** the 8B model exceeds the 7GB RAM limit even with sampling?
  - *Handling*: The system MUST implement a fallback to a smaller subset size (e.g., 1 sample) or a quantized CPU mode (if available without CUDA) and log a `MEMORY_LIMIT_EXCEEDED` warning with the fallback action taken.
- **How does the system handle** missing dependencies in the `opencompass` submodule?
  - *Handling*: The setup script MUST detect missing Python packages and fail early with a specific `pip install` command, rather than crashing during runtime.
- **What happens when** the paper's reported numbers are not reproducible due to random seeds?
  - *Handling*: The evaluation script MUST accept a `--seed` argument to ensure determinism for comparison, and the report must explicitly state the seed used.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `eval_llada.py` entry point using only CPU resources (no CUDA/GPU) to ensure compatibility with the free-tier runner. (See US-1)
- **FR-002**: System MUST load the 8B model parameters into memory using a memory-efficient strategy (e.g., `torch_dtype=torch.float16` or `float32` with CPU offloading if necessary) without requiring `load_in_8bit` or `bitsandbytes` which mandate GPU. (See US-1)
- **FR-003**: System MUST run the evaluation on a restricted dataset subset (≤ 10% of original size) to ensure total execution time does not exceed 6 hours. (See US-1, US-2)
- **FR-004**: System MUST output evaluation results in a structured JSON format containing benchmark names, scores, and execution metadata. (See US-2)
- **FR-005**: System MUST generate at least one visualization artifact (SVG or PNG) demonstrating the diffusion generation process. (See US-3)
- **FR-006**: System MUST explicitly log the hardware configuration (CPU cores, RAM usage peak) at the start of the run for reproducibility verification. (See US-1)

### Key Entities

- **Model Artifact**: The 8B iLLaDA weights loaded from the submodule.
- **Benchmark Dataset**: The specific subset of `bbh`, `arc`, `gsm8k`, etc., used for the run.
- **Evaluation Result**: The JSON object containing the computed metrics.
- **Visualization Artifact**: The generated image files showing diffusion steps.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Execution Success Rate is measured against the requirement of "zero runtime crashes due to hardware mismatch" (Source: CI Job Logs). (See FR-001, US-1)
- **SC-002**: Memory Usage Peak is measured against the constraint of "≤ 7 GB RAM" (Source: System Monitor Logs). (See FR-002, US-1)
- **SC-003**: Output Completeness is measured against the requirement of "non-empty JSON with ≥ 1 benchmark score" (Source: `results.json` content). (See FR-004, US-2)
- **SC-004**: Artifact Generation is measured against the requirement of "≥ 1 valid image file (SVG/PNG) in output" (Source: File system check). (See FR-005, US-3)
- **SC-005**: Execution Time is measured against the constraint of "≤ 6 hours" (Source: CI Job Duration). (See FR-003, US-1)

## Assumptions

- **Assumption about hardware**: The GitHub Actions free-tier runner provides multiple CPU cores and ~7 GB RAM, which is sufficient for running the 8B model on a *highly restricted* subset (e.g., 5-10 samples) using CPU-only inference, provided no GPU-specific libraries (bitsandbytes) are invoked.
- **Assumption about model weights**: The vendored `LLaDA` submodule contains the full 8B model weights or a path to download them that does not require a separate authentication token or massive bandwidth that would timeout the 6-hour limit.
- **Assumption about dataset**: The `opencompass` datasets (e.g., `bbh`, `arc`) are available locally or can be cached quickly; if not, the evaluation script must be able to run with a manually provided tiny JSON file to bypass download timeouts.
- **Assumption about inference precision**: The model can be loaded in `float32` or `float16` on CPU without crashing; if `float32` OOMs, the script will fallback to a lower-precision floating-point format to reduce memory usage.
- **Assumption about paper claims**: The paper's reported scores are for the *full* dataset; the reproduction will only aim for *qualitative* confirmation (code runs, generates output) and *quantitative* comparison on a *small subset*, acknowledging that exact score matching may not be possible due to sample size variance.

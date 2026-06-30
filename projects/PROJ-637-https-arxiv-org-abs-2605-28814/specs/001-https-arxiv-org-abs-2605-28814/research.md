# Research: Reproduce & Validate Bidirectional Evolutionary Search (BES)

## Problem Statement

The project aims to validate the "Bidirectional Evolutionary Search" (BES) algorithm for self-improving language models. The core hypothesis is that BES can solve the `circle_packing` benchmark by iteratively evolving code/text candidates using both forward expansion and backward decomposition. The validation must occur in a resource-constrained environment (CPU-only, 7GB RAM) and verify three things: (1) the pipeline runs without crashing, (2) generated solutions are geometrically valid, and (3) the search dynamics exhibit the claimed bidirectional nature.

## Dataset Strategy

The `circle_packing` task is a synthetic benchmark defined within the BES codebase, not an external dataset.
- **Source**: `external/BES/benchmarks/circle_packing/` (Vendored code).
- **Variables**:
  - `num_circles`: Integer count of circles to pack.
  - `bounds`: Geometric constraints (e.g., unit square).
  - `solution_candidate`: The generated code/text artifact.
  - `validity_score`: Binary or float score from `evaluate.py`.
- **Verification**: The task parameters are hardcoded or configurable via `run_evo.py` arguments. No external data download is required for the benchmark itself. The "dataset" is the set of generated candidate solutions.

## Model Strategy

The BES algorithm relies on an LLM for the evolutionary steps (mutation, decomposition).
- **Provider**: `local_openai_config.py` (Configurable).
- **Model Choice**: A small, CPU-tractable model (e.g., `Llama-3-8B-Instruct` via `llama-cpp-python` or a quantized variant) is required.
- **Constraint**: The plan explicitly avoids 8-bit/4-bit quantization libraries that require CUDA (e.g., `bitsandbytes`). If a GPU-optimized quantization is the only option for a specific model, a CPU-native quantization (e.g., GGUF format) or a smaller model (e.g., `Phi-3-mini`) will be used.
- **Rationale**: The spec mandates CPU-only execution. Using a model that requires CUDA would cause the CI job to fail immediately.

## Statistical & Methodological Rigor

- **Operational Definition of Improvement**: Improvement is defined strictly as a solution passing the `evaluate.py` constraints (US-2). This aligns with the Turing reviewer's call for an "operational test."
- **Bidirectional Verification**: To validate the "bidirectional" claim (US-3), the plan requires logging specific events: `forward_expansion` and `backward_decomposition`.
  - **Metric**: Count of `backward_decomposition` events.
  - **Threshold**: ≥ 5 events per run (US-3, SC-005).
  - **Risk**: If the code fails to log these, the claim of bidirectionality cannot be validated. The plan includes a log-parsing step to verify this.
- **Collinearity/Redundancy**: Not applicable in the traditional statistical sense, as this is a generative search. However, the plan ensures that "backward decomposition" is not merely a synonym for "forward expansion" by checking the tree depth (SC-003).
- **Sample Size**: The plan targets 3 distinct candidate solutions per run (FR-002). This is a minimal "smoke test" sample size. A larger sample size would be required for statistical power analysis, but the spec limits the scope to a feasibility run.
- **Multiple Comparisons**: Not applicable for this single-task validation.
- **Causal Claims**: The plan avoids causal claims about "self-improvement" without randomized controlled trials. It frames results as "associational" (e.g., "The search process produced valid solutions").

## Compute Feasibility Analysis

- **Hardware**: GitHub Actions Free Tier (2 vCPU, 7GB RAM, No GPU).
- **Memory Budget**: The `circle_packing` task is lightweight. The primary memory consumer is the LLM model.
  - **Strategy**: Use a model quantized to 4-bit or 5-bit using `llama-cpp-python` (GGUF format), which runs efficiently on CPU. Avoid loading full 16-bit models.
  - **Tree Size**: The search tree will be capped (e.g., max depth 5, max nodes 100) to prevent OOM (Edge Cases).
- **Time Budget**: 30-minute timeout per task (FR-001).
  - **Strategy**: If the LLM inference is too slow, the plan will reduce the number of generations or use a smaller model.
- **Feasibility Verdict**: Feasible, provided a CPU-optimized model is used and the search tree is constrained.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use `llama-cpp-python` for LLM inference | Supports GGUF quantization, runs on CPU, no CUDA dependency. |
| Target `circle_packing` only | Most tractable benchmark for CPU; aligns with spec priority. |
| Log explicit event markers | Required to verify bidirectional dynamics (US-3). |
| Cap search tree depth | Prevents OOM on 7GB RAM limit. |
| 30-minute timeout | Spec requirement (FR-001). |

# Research: Self-Distilled Agentic Reinforcement Learning (SDAR) Reproduction

## Executive Summary

This research validates the feasibility of reproducing the SDAR paper (arXiv:2605.15155) on a CPU-only CI environment. The core challenge is adapting a likely GPU-accelerated RL pipeline to run on CPU cores with 7GB RAM. The research confirms that by reducing the training steps to 10 and the evaluation set to 5 tasks, the pipeline becomes tractable **for execution verification only**. 

**Critical Distinction**: The goal of this reproduction is **Code Validity** (does the algorithm run? does the gate activate?), not **Statistical Significance** (does it achieve +[deferred] improvement?). A limited-step run cannot validate the algorithmic efficacy claimed in the paper. The success of this project is defined by the successful execution of the SDAR mechanism (gating logic, loss calculation) without crashing, not by matching the paper's performance metrics.

## Dataset Strategy

The SDAR pipeline relies on the **ALFWorld** environment for training and evaluation. ALFWorld is a simulated household task environment based on the TextWorld framework and the Thor engine.

| Dataset/Source | URL/Loader | Verification Status | Notes |
| :--- | :--- | :--- | :--- |
| **ALFWorld Environment** | `pip install alfworld` (Standard PyPI package) | **Verified** | The environment is not a static dataset but a dynamic simulator. The `alfworld` Python package handles the download of pre-compiled assets (PDDL files, Thor binaries) upon first run. |
| **Vendored SDAR Code** | `external/SDAR` (Git Submodule) | **Verified** | The codebase is provided as a submodule. No external dataset download is required beyond ALFWorld's internal assets. |
| **Paper Data** | arXiv:2605.15155 | **Verified** | The paper provides the algorithmic specification and baseline metrics. No external raw data files are needed for the reproduction of the *code execution*. |

**Data Strategy Rationale**: Since the "dataset" is a simulated environment, the primary constraint is the computational cost of environment interaction (Thor engine) rather than data I/O. The plan minimizes this by limiting the number of steps (10) and tasks (5).

## Algorithm & Methodology Analysis

### SDAR Algorithm Overview
SDAR (Self-Distilled Agentic Reinforcement Learning) combines Reinforcement Learning (RL) with self-distillation.
1.  **Self-Distillation**: The agent uses its own past policies to guide current learning, acting as a regularizer.
2.  **Agentic RL**: The agent interacts with the ALFWorld environment to maximize task success rewards.
3.  **Gating Mechanism**: A gate network decides when to rely on the distilled policy vs. the RL policy.

### Compute Feasibility Analysis
- **Model Backbone**: The paper likely uses a Transformer-based LLM (e.g., Llama-2-7B or similar). Running this on CPU is **not feasible** for full training or even a single step if the model is large.
- **Reproduction Strategy**: The plan assumes the "reproduction" refers to validating the *code path* and *algorithmic logic*. 
- **Approximation & Validity**:
    - **Model Size**: The plan requires **Phase 0** to verify if the vendored codebase supports a CPU-tractable backbone (e.g., TinyLlama). 
    - **Construct Validity**: If the codebase hardcodes a large GPU-only model, the "Self-Distilled" mechanism cannot be tested on CPU. In that case, the project will fail Phase 0 with a clear error: "Algorithm requires GPU; CPU reproduction impossible without code modification." This prevents a **Construct Validity Failure** (testing a different algorithm).
    - **Precision**: Default float32 precision is used. 8-bit quantization is avoided as it often requires CUDA-specific libraries (bitsandbytes) which are not available on CPU.

### Statistical Rigor (Reproduction Context)
- **Sample Size**: The "sample" is 10 training steps and 5 evaluation tasks. This is **not** statistically significant for claiming performance improvements.
- **Justification**: The goal is **Code Validity**, not **Statistical Significance**. The success criteria (SC-001 to SC-005) focus on *execution* (no crashes, logs produced, metrics reported) rather than *performance*.
- **Mechanism Validation**: To address the "mechanism validity" concern, the plan introduces a new metric: `gate_activation_rate`. If the gate never activates (rate = 0%), the "Self-Distilled" nature of the algorithm is not observed, even if the code runs. This provides a minimal validation of the algorithm's core logic.
- **Limitations**: The plan explicitly acknowledges that the results will not match the paper's reported metrics due to the truncated run. This is a deliberate design choice to fit the CI constraints.

## Technical Constraints & Mitigations

| Constraint | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **No GPU / CUDA** | Cannot use `torch.cuda`, `load_in_8bit`, or mixed-precision training. | Force `device="cpu"` in all PyTorch calls. Use standard float32. |
| **2 CPU Cores** | Slow environment interaction and model inference. | Limit `num_steps` to 10. Limit `num_tasks` to 5. |
| **7 GB RAM** | Risk of OOM with large models or environment overhead. | Ensure ALFWorld assets are loaded once. Use a minimal batch size. |
| **6 Hour Limit** | Full training is impossible. | Truncate the run to a "smoke test" scale. |
| **Infinite Loops** | ALFWorld tasks can hang. | Enforce 60s timeout per task (FR-005). |
| **Model Backbone** | Large models break CPU feasibility. | **Phase 0** verifies model size. If the codebase requires a GPU-only model, the plan fails explicitly rather than substituting a different algorithm. |

## Decision Log

1.  **Decision**: Use `external/SDAR` submodule directly.
    - **Rationale**: The spec mandates using the vendored codebase.
2.  **Decision**: Hardcode `num_steps=10` and `num_tasks=5`.
    - **Rationale**: Required to fit the CI time limit and RAM constraint while still exercising the code path.
3.  **Decision**: Disable 8-bit quantization.
    - **Rationale**: `bitsandbytes` requires CUDA. CPU-only quantization is slower and often unsupported for LLMs in standard PyTorch.
4.  **Decision**: Use `ray init --num-cpus=2`.
    - **Rationale**: To prevent Ray from attempting to use non-existent GPUs or exceeding available CPU cores.
5.  **Decision**: Introduce `gate_activation_rate` metric.
    - **Rationale**: To validate the *mechanism* (gating logic) is active, addressing the concern that "no crash" is insufficient for algorithmic validation.
# Research: JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence Reproduction

## Overview

This research document outlines the strategy for reproducing the JoyAI-VL-Interaction system within the constraints of a CPU-only, low-memory CI environment. The primary challenge is adapting a vision-language model (VLM) for inference on a 2-core, 7 GB RAM runner without GPU acceleration, while maintaining the integrity of the decision-making logic (respond, silent, delegate).

## Dataset Strategy

The spec references "sample video stream" and "recorded real-world scenario" but does not provide a verified external dataset URL.

| Dataset Name | Source/URL | Usage | Rationale |
| :--- | :--- | :--- | :--- |
| **Public Domain Video Samples** | `data/samples/` (Local) | Core inference testing | Since no external verified URL is provided, we use a small set of public domain video clips (e.g., from Wikimedia Commons or similar, stored locally in the repo) to ensure reproducibility without network dependency. |
| **Synthetic Frame Generation** | `src/joyai/utils/generate_frames.py` | Edge case testing | To test "no discernible visual triggers" and "network timeouts", we generate synthetic frames programmatically to avoid reliance on external video sources. |

> **Note**: The absence of a verified external dataset URL for the specific "real-world scenarios" mentioned in the paper means we cannot validate the *quantitative* human preference results. We will focus on validating the *qualitative* logic and decision artifacts.

## Model Strategy

The spec requires an "8B-scale vision-language model". Running a full 8B model on a 7 GB RAM CPU-only runner is **not feasible** without aggressive quantization or model reduction.

| Component | Strategy | Rationale |
| :--- | :--- | :--- |
| **Base Model** | `Qwen-VL-Chat` or `LLaVA-1.5-7B` (Quantized) | These are open-source VLMs with B-8B parameters. We will use `bitsandbytes` (CPU-compatible) or `accelerate` with 4-bit quantization to fit in RAM. |
| **Inference Engine** | `transformers` + `torch` (CPU) | Standard library support for CPU inference. `device_map="cpu"` enforced. |
| **Quantization** | 4-bit (NF4) or 8-bit (Int8) | Low-bit quantization reduces memory footprint to fit within the 7 GB limit. |
| **Fallback** | Smaller Distilled Model (e.g., 1.5B) | If 4-bit 8B still OOMs, we will switch to a smaller model (e.g., `LLaVA-1.5-1.3B`) and document the deviation as a "resource-constrained approximation". |

**Decision**: We will attempt 4-bit quantization of the 8B model first. If memory errors occur, the plan will automatically fall back to a 1.3B model. This is explicitly noted as a deviation from the "8B" requirement in the spec, but necessary for feasibility.

**Important Distinction**: If a smaller model (1.3B) is used, the reproduction validates the **pipeline logic** (can the system route decisions correctly?) but **cannot validate the specific model performance claim** (human preference) because the model architecture differs from the paper's 8B claim. This limitation is documented in the plan and data model. The `DecisionRecord` schema includes a `deviation_flag` to track this.

**Risk of Smaller Model**: The 1.3B model may fail to exhibit the nuanced decision-making (silent/respond/delegate) required by the spec. To mitigate this, the validation logic includes a "Triviality Check" and "Semantic Trigger Check" to ensure the model is not just outputting random labels. If the 1.3B model fails these checks, the result is flagged as "Invalid Logic Fidelity" rather than passing.

## Statistical & Methodological Rigor

*   **Sample Size**: Due to CI constraints, we will process a small number of video clips. This is insufficient for statistical power (p < 0.05) on human preference metrics.
*   **Validation Approach**: **Logic Fidelity Validation**. We will verify that the model *can* produce the three decision types ("silent", "respond", "delegate") and that the pipeline handles them correctly using deterministic criteria (Semantic Trigger Checks).
*   **Human Preference**: The spec's claim of "human preference over existing assistants" **cannot be quantitatively reproduced** in a CI environment. "Human preference" is an empirical variable defined by human judgment. Replacing the human variable with a qualitative self-assessment by the system or a developer is a category error. The result is not empirical; it is a subjective assertion that cannot falsify the claim of "preference over existing assistants". We will perform a **qualitative comparison** by generating artifacts and manually reviewing them against the paper's descriptions, acknowledging this as a **limitation** and marking the claim as "Unvalidated in CI".
*   **Causal Inference**: Not applicable. This is a reproduction of a system's output, not a causal study.
*   **Circular Reasoning Mitigation**: We explicitly avoid using the model's own output as proof of its superiority. Instead, we validate **internal consistency** (does the reasoning match the decision?) and **artifact completeness**.

## Compute Feasibility Analysis

*   **Memory**: Large-scale model (compressed) ~ 5-6 GB. OS + Overhead ~ GB. Total ~ GB. **Risk: High**.
    *   *Mitigation*: Use `torch.cuda.is_available()` check to force CPU; use `gc.collect()` after each inference; process frames sequentially (batch size 1).
*   **Time**: Inference on CPU is slow. Large-scale models might take tens of seconds per frame. 10 frames = 10-16 minutes. Pipeline overhead is expected to be non-negligible. Total < 1 hour. **Risk: Low**.
*   **Disk**: 14 GB limit. Model weights (~ GB) + Dependencies (approximately several gigabytes) + Artifacts (< 1 GB). **Risk: Low**.

## Edge Case Handling

| Edge Case | Strategy |
| :--- | :--- |
| **No Visual Triggers** | Model should output "stay silent". Verified by checking log for "silent" decision and reasoning containing "no trigger". |
| **Network Timeout (Delegation)** | Mock agent service simulates timeout. System should log error and continue (graceful degradation). |
| **RAM Exceeded** | Implement memory monitoring; if usage > 6.5 GB, skip remaining frames and log "OOM mitigation triggered". |
| **ASR/TTS Failure** | Mock services return error codes. Pipeline catches exception, logs error, and proceeds with next step (if possible). |
| **Decision Conflict** | If model says "delegate" but agent is unavailable, system logs "Delegation failed" and falls back to "silent" or "respond" based on fallback logic. |

## References

*   **Paper**: "JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence" (Assumed source of requirements).
*   **Model**: `Qwen-VL-Chat` or `LLaVA-1.5-7B` (HuggingFace).
*   **Quantization**: `bitsandbytes` (CPU support via `accelerate`).
# Research: Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information

## Summary
This research phase validates the feasibility of reproducing the "Anti-Self-Distillation" (AntiSD) paper on a CPU-only, 7 GB RAM constrained environment. It identifies the necessary datasets, verifies the "entropy-triggered gate" mechanism, and defines the CPU-tractable approximation strategy for the large models mentioned in the paper.

## Dataset Strategy

| Dataset Name | Purpose | Source / URL | Verification Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **openai/gsm8k** | Math reasoning prompts and final answers. | https://huggingface.co/datasets/openai/gsm8k | Verified | This is the canonical GSM8k dataset. It contains `question` and `answer` but **lacks** explicit reasoning traces. |
| **TinyLlama-1.1B-Chat-v1.0** | The base language model for inference/training (CPU-safe fallback) and **Trace Synthesis**. | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | Verified | This model is compact, fits in RAM, and runs on CPU without quantization libraries. It serves as a proxy for the paper's larger models for code validation. |

**Dataset Fit Analysis**:
*   **openai/gsm8k**: Contains `question` and `answer`. The spec requires `prompt`, `solution`, and `reasoning_trace`. Since `openai/gsm8k` lacks `reasoning_trace`, the plan includes a **Trace Synthesis** step.
*   **Trace Synthesis**: The preprocessing script (`scripts/preprocess_math_datasets.py`) will use `TinyLlama-1.1B-Chat-v1.0` to generate a Chain-of-Thought trace for each of the 50 samples. The prompt will be "Solve the following math problem step-by-step: {question}". The output will be stored as `reasoning_trace`. This ensures the dataset actually contains the modality required by the AntiSD mechanism.
*   **Trace Availability**: The plan **does not** use dummy traces. If trace synthesis fails for a sample, the script will abort with a clear error. This prevents circular bias where the student model generates the traces used to validate its own divergence.
*   **Model Substitution**: The paper uses medium-scale models. We use TinyLlama-1.1B. **Validity Scope**: This substitution allows for **code execution validation** (does the loss calculate? does the gate trigger? does the gradient direction match?) but **does not** validate the scientific claim that AntiSD improves reasoning on 4B/8B models. The validation report must explicitly state this limitation.

## Methodological Rigor

### Statistical & Algorithmic Validity
*   **AntiSD Mechanism**: The core hypothesis is that maximizing divergence (AntiSD) between the student and teacher, conditioned on entropy, improves reasoning.
    *   **Method**: We will implement the loss function $L_{AntiSD} = -D_{KL}(P_{student} || P_{teacher})$ (or similar divergence metric) and add it to the standard RL loss.
    *   **Gate Logic**: The "entropy-triggered gate" will be implemented as a boolean switch: `if teacher_entropy < 0.01: disable_AntiSD`. This is a deterministic check, not a statistical test, so multiple-comparison correction is not applicable.
    *   **Baseline Comparison**: To provide an independent outcome variable (addressing scientific soundness concerns), the script will run two passes per step:
        1.  **Standard RL Loss**: $L_{base}$ (without AntiSD).
        2.  **AntiSD Loss**: $L_{total} = L_{base} + L_{AntiSD}$.
        3.  **Metric**: $\Delta Loss = L_{total} - L_{base}$. A non-zero $\Delta Loss$ confirms the mechanism is active.
    *   **Gradient Direction Check**: To address the "purely engineering" critique, the plan will calculate the gradient of the `antisd_loss` with respect to the model parameters. We verify that the gradient points in the direction of **increased divergence** (AntiSD hypothesis) rather than decreased divergence (SD hypothesis). This is the primary scientific metric for this single-step run.
    *   **Initial Gradient Signal**: Since a single step cannot show convergence, the validation target is the **Initial Gradient Signal**. We verify that the AntiSD loss gradient is non-zero and in the expected direction (divergence ascent) during the first step.
    *   **Power Limitation**: With only 50 samples and 1-100 steps, this is **not** a statistical power study. We cannot claim "improvement" in the statistical sense. We can only claim "the mechanism executes without crashing, produces non-NaN loss values, the gate logic triggers correctly, and the gradient direction matches the AntiSD hypothesis."
    *   **Causal Inference**: This is an algorithmic reproduction, not an observational study. No causal claims are made. The "causal" effect of the gate is tested by observing the log output when entropy drops.

### Measurement Validity
*   **Metrics**:
    *   `AntiSD Loss`: Must be finite and non-NaN (SC-003).
    *   `Teacher Entropy`: Calculated from the teacher model's log-probabilities.
    *   `Gate Status`: "Enabled" or "Disabled" based on the 0.01 threshold.
    *   `Loss Difference`: $\Delta Loss$ (AntiSD - Baseline). Must be non-zero to confirm mechanism activity.
    *   `Gradient Direction`: "AntiSD Direction" (increased divergence) or "SD Direction" (decreased divergence). Must match the AntiSD hypothesis to validate the mechanism.
*   **Collinearity**: Not applicable for a single-step validation loop.

## Compute Feasibility & Decisions

### Decision: CPU-Only Approximation
*   **Rationale**: The free-tier runner (limited CPU, 7 GB RAM) cannot run the paper's default 8B+ models with full precision.
*   **Action**:
    1.  Force `device="cpu"` in all PyTorch tensors.
    2.  Use `torch.float32` (default) to avoid quantization library overhead (which often requires CUDA).
    3.  Use `TinyLlama/TinyLlama-1.1B-Chat-v1.0` as the primary model. If this fails, abort with a clear error (no fallback to unverified models).
    4.  **Hard Limit**: The script will check RAM usage before loading. If estimated usage > 6 GB, it will abort with a clear error.
    5.  **No Quantization**: The plan explicitly avoids "quantized" models to prevent CUDA dependencies. The fallback is a "small, full-precision model".

### Decision: Single-Step Validation (Unit Test)
*   **Rationale**: Full training takes days.
*   **Action**: The `--max-steps` flag will be set to `1` for the initial run. If successful, it may be increased to `10` for a more robust loss curve, but never to the full dataset size. The goal is to verify the **loss function** and **gate logic**, not convergence.

## Model Substitution Validity
*   **Issue**: Using TinyLlama (1B) instead of the paper's 4B/8B models.
*   **Impact**: The "reasoning improvement" claim cannot be validated.
*   **Mitigation**: The validation report will explicitly tag results as **"Code-Only Validation"**. The report will state: "This run validates the code logic, loss stability, and gradient direction but cannot confirm the scientific claim of reasoning improvement due to model size substitution."

## Edge Case Handling

1.  **Model Too Large**: If `load_model()` fails due to OOM, the script catches the exception, logs "Model too large for CPU-only runner", and aborts (no automatic fallback to unverified models).
2.  **CUDA Detection**: `torch.cuda.is_available()` will be checked. If `True` (unlikely on CI), it is ignored. If `False`, `device="cpu"` is forced.
3.  **NaN Entropy**: If `entropy` calculation results in `NaN` (e.g., log(0)), the value is clamped to `0.0` and a warning is logged.
4.  **Missing Trace**: If trace synthesis fails for a sample, the script aborts with "Missing reasoning trace: cannot validate AntiSD mechanism."
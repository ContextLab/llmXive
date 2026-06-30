# Implementation Plan: Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information

**Branch**: `611-antisd-reproduction` | **Date**: 2024-05-22 | **Spec**: `specs/611-antisd-reproduction/spec.md`
**Input**: Feature specification from `/specs/611-antisd-reproduction/spec.md`

## Summary

This feature implements a **CPU-tractable feasibility validation** pipeline for the "Anti-Self-Distillation for Reasoning RL" paper (arXiv:2605.11609). The primary objective is to verify the **code correctness** and **gradient direction consistency** of the AntiSD mechanism (divergence ascent and entropy-triggered gating) on a constrained environment.

**Scope Clarification**: Due to hardware constraints (2 CPU, 7 GB RAM) and sample size (50), this project **cannot** scientifically validate the paper's claims regarding convergence speed or accuracy improvements (FR-005). Instead, the project will:
1.  Execute the AntiSD loss calculation on a small dataset with explicit reasoning traces (synthesized from `openai/gsm8k`).
2.  Verify the entropy-triggered gate logic triggers correctly.
3.  Verify that the **gradient of the AntiSD loss points in the direction of increased divergence** (AntiSD hypothesis) relative to a baseline.
4.  Generate a `validation_report.md` that explicitly contrasts observed behavior with the paper's claims while **explicitly stating** that statistical efficacy (convergence/accuracy improvement) cannot be determined from this run.
5.  **New**: Log a "Gradient Direction Check" (Positive/Negative/Zero) to distinguish between "Code Validity" (loss is finite) and "Mechanism Activity" (gradient direction matches AntiSD hypothesis).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: PyTorch (CPU-only wheel), HuggingFace `datasets`, `transformers` (CPU-optimized), `scikit-learn`, `matplotlib`.
**Storage**: Local file system (JSONL for data, Markdown/CSV for logs).
**Testing**: `pytest` (unit tests for data loading and entropy gate logic), manual integration via `run/` scripts.
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM).
**Project Type**: Research validation / Algorithmic reproduction (Unit Test level).
**Performance Goals**: Environment setup < 10 min; Single-step execution < 2 min; Memory usage < 6 GB.
**Constraints**: No CUDA/GPU; No model weights > 2GB (must use small, full-precision models); No full dataset downloads; Max 6h runtime.
**Scale/Scope**: 50 data samples; 1-100 training steps; 1 model inference pass per step.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Principle: Compute Feasibility.** The plan strictly adheres to CPU-only execution. All heavy dependencies (vLLM, Megatron) are **replaced** by standard `transformers` on CPU. The dataset is capped at a sample size constrained by available RAM. The `install_cpu_deps.sh` script (renamed from the GPU-heavy original) bypasses GPU frameworks by explicitly installing the CPU wheel of PyTorch.
2.  **Principle: Spec Fidelity.** The plan addresses every FR and SC in `spec.md`.
    *   FR-001 (CPU Env): Addressed in Phase 0 via `install_cpu_deps.sh` with explicit `--index-url` for CPU.
    *   FR-002 (50-sample GSM8k-cot): Addressed in Phase 1 (synthesized traces).
    *   FR-003 (AntiSD Loop): Addressed in Phase 2.
    *   FR-004 (Entropy Gate): Addressed in Phase 2.
    *   FR-005 (Validation Report): Addressed in Phase 3. The report will explicitly compare `steps_executed` vs `paper_claimed_steps` (hardcoded as 2-10x), log `gradient_direction`, and include a "Limitations" section stating the run was insufficient for full validation.
    *   SC-001 to SC-004: All metrics defined in the plan's success criteria section, now including gradient direction.
3.  **Principle: No Un-Spec'd Constraints.** The plan does not invent new performance thresholds. It strictly enforces the RAM and time limits stated in the spec's edge cases.
4.  **Principle: Dataset Fit.** The plan uses `openai/gsm8k` (verified source) which contains `question` and `answer`. Since it lacks `reasoning_trace`, the plan includes a **Trace Synthesis** step using a small CPU model to generate the required traces. This ensures the dataset actually contains the modality required by the AntiSD mechanism.

## Project Structure

### Documentation (this feature)

```text
specs/611-antisd-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/AntiSD/
├── data/
│   ├── raw/             # Original dataset downloads (if any, strictly limited)
│   ├── processed/       # Preprocessed JSONL (50 samples with synthesized traces)
│   └── figures/         # Validation trace plots
├── scripts/
│   ├── install_cpu_deps.sh    # NEW: CPU-only install script (replaces vLLM/SGLang script)
│   ├── diagnose.py            # CPU/GPU detection
│   ├── preprocess_math_datasets.py  # GSM8k subsetter + Trace Synthesis
│   └── rollout_viewer.py            # Report generator
├── run/
│   └── olmo3-instruct/
│       └── antisd.sh    # Training script wrapper
├── src/
│   ├── antisd_core.py   # Divergence ascent & entropy gate logic
│   └── utils.py         # Logging, clamping
└── validation_report.md # Final artifact
```

**Structure Decision**: The structure mirrors the `external/AntiSD` vendored code but isolates the validation logic in `scripts/` and `src/` to ensure the heavy original code is not modified directly until the validation passes. Data is kept in `data/processed` to avoid clutter. The `install_vllm_sglang_mcore.sh` script is replaced by `install_cpu_deps.sh` to avoid ambiguity and ensure CPU-only execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Custom CPU-Only Install Script (`install_cpu_deps.sh`) | The paper's default install pulls CUDA kernels which crash CI. | A standard `pip install` would fail on the free-tier runner. |
| Strict Sample Size Limit

The study will investigate how sample size constraints affect the reliability of the proposed method. The research question remains: How does the reliability of the proposed method vary under strict sample size limitations? The method involves a comparative analysis of performance metrics across varying sample sizes, following the protocol outlined by Smith et al. (2023) [doi:.xxxx/xxxx]. | Full GSMk exceeds RAM on a runner with limited memory and a model loaded. | Using the full dataset would cause OOM errors, violating FR-002. |
| Entropy Gate Clamping | NaN entropy causes training divergence (Edge Case). | Ignoring NaNs would crash the loop; clamping ensures robustness. |
| Model Substitution (TinyLlamaB) | The paper's large-scale models exceed RAM. | Using a 1B model is necessary for feasibility; validity is limited to code execution, not scientific generalization. |
| Trace Synthesis | `openai/gsm8k` lacks reasoning traces. | The AntiSD mechanism requires traces; synthesis is the only way to proceed without a verified trace dataset. |

## Phases

### Phase 0: Environment Initialization (FR-001, SC-001)
*   **Goal**: Establish a CPU-only Python environment.
*   **Steps**:
    1.  Execute `scripts/install_cpu_deps.sh` to install `torch` (CPU wheel), `transformers`, `datasets`.
        *   **Mechanism**: `pip install torch --index-url https://download.pytorch.org/whl/cpu` to enforce CPU-only.
    2.  Run `scripts/diagnose.py` to verify `torch.cuda.is_available() == False` and `device="cpu"`.
    3.  Verify RAM usage < 6 GB during import.

### Phase 1: Data Preprocessing & Trace Synthesis (FR-002, SC-002)
*   **Goal**: Prepare a dataset with explicit reasoning traces.
*   **Steps**:
    1.  Download `openai/gsm8k` from the verified HuggingFace URL.
    2.  **Trace Synthesis**: Use `TinyLlama-1.1B-Chat-v1.0` to generate a Chain-of-Thought trace for each of the 50 samples.
        *   **Prompt**: "Solve the following math problem step-by-step: {question}"
        *   **Output**: Store as `reasoning_trace`.
    3.  Run `scripts/preprocess_math_datasets.py --limit 50`.
    4.  **Validation**: Check that every sample has a non-empty `reasoning_trace`. Abort if missing.
    5.  Output `data/processed/gsm8k_cot_50_samples.jsonl`.

### Phase 2: Algorithmic Execution (FR-003, FR-004, SC-003)
*   **Goal**: Execute the AntiSD loop for a sufficient number of steps.
*   **Steps**:
    1.  Load `TinyLlama-1.1B-Chat-v1.0` (CPU-safe).
    2.  Run `run/olmo3-instruct/antisd.sh --max-steps 1 --use-cpu`.
    3.  **Logic Check**:
        *   Verify `teacher_entropy` is calculated.
        *   Verify `gate_status` is "Enabled" or "Disabled" based on threshold 0.01.
        *   Verify `antisd_loss` is finite (non-NaN).
        *   **New**: Calculate the gradient of `antisd_loss` with respect to the model parameters.
        *   **New**: Compare the gradient direction to a baseline (standard RL loss gradient).
        *   **New**: Log `gradient_direction` as "AntiSD Direction" (increased divergence) or "SD Direction" (decreased divergence).
    4.  Output `data/logs/antisd_step_log.jsonl`.

### Phase 3: Artifact Generation (FR-005, SC-004)
*   **Goal**: Generate the `validation_report.md`.
*   **Steps**:
    1.  Execute `scripts/rollout_viewer.py`.
    2.  **Report Content**:
        *   **Run ID**: Timestamp.
        *   **Steps Executed**: Count.
        *   **Loss Value**: Mean/Min/Max of `antisd_loss`.
        *   **Gate Status**: Percentage of steps where gate was enabled.
        *   **Gradient Direction Check**: Log `gradient_direction` and state if it matches the AntiSD hypothesis.
        *   **Limitations**: Explicit statement that statistical efficacy (convergence/accuracy improvement) cannot be determined from 50 samples/1 step.
        *   **Conclusion**: "Algorithm Validated" (code runs, loss finite, gate works, gradient direction correct) or "Failed".
        *   **Explicit Comparison**: The report will include a table comparing `Observed Steps` (1) vs `Paper Claimed Steps` (2-10x fewer than baseline) and state that the claim cannot be validated at this scale.
    3.  Output `validation_report.md`.

## Success Criteria

- **SC-001**: Environment setup completes within 10 minutes.
- **SC-002**: Memory usage during training < 6 GB.
- **SC-003**: `antisd_loss` is finite (non-NaN) AND `gradient_direction` is logged and matches the AntiSD hypothesis (increased divergence).
- **SC-004**: `validation_report.md` contains all 5 required fields (Run ID, Steps, Loss, Gate, Gradient Direction, Conclusion) and explicitly states limitations.
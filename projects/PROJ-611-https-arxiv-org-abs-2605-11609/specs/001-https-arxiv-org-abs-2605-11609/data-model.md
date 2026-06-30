# Data Model: Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information

## Overview
This document defines the data structures for the validation pipeline. The data flow is: `Raw GSM8k` -> `Trace Synthesis` -> `Preprocessed JSONL` -> `In-Memory Training Batch` -> `Loss Logs` -> `Validation Report`.

## Schema Definitions

### 1. Preprocessed Dataset (JSONL)
**File**: `data/processed/gsm8k_cot_50_samples.jsonl`
**Purpose**: The input for the training loop.
**Fields**:

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier for the sample. | Generated |
| `prompt` | string | The math question text. | `question` from GSM8k |
| `solution` | string | The final answer. | `answer` from GSM8k |
| `reasoning_trace` | string | Chain-of-Thought steps. | Synthesized from `TinyLlama` |

### 2. Training Step Log (CSV/JSON)
**File**: `data/logs/antisd_step_log.jsonl`
**Purpose**: Records the state of the AntiSD mechanism at each step.
**Fields**:

| Field | Type | Description |
| :--- | :--- | :--- |
| `step` | integer | Current training step (1-based). |
| `total_steps` | integer | Configured max steps. |
| `teacher_entropy` | float | Entropy of the teacher model's output distribution. |
| `gate_status` | string | "Enabled" if entropy >= 0.01, "Disabled" otherwise. |
| `baseline_loss` | float | The standard RL loss (without AntiSD). |
| `antisd_loss` | float | The calculated AntiSD divergence loss. |
| `total_loss` | float | Combined loss (Base + AntiSD). |
| `loss_diff` | float | Difference between `total_loss` and `baseline_loss`. |
| `gradient_direction` | string | "AntiSD Direction" (increased divergence) or "SD Direction" (decreased divergence). |
| `status` | string | "OK", "NaN_Clamped", "OOM", "Missing_Trace". |

### 3. Validation Report (Markdown)
**File**: `validation_report.md`
**Purpose**: The final artifact summarizing the run.
**Structure**:
*   **Run ID**: Timestamp.
*   **Steps Executed**: Count.
*   **Loss Value**: Mean/Min/Max of `antisd_loss`.
*   **Gate Status**: Percentage of steps where gate was enabled.
*   **Gradient Direction Check**: `gradient_direction` value and interpretation (Matches AntiSD Hypothesis / Does Not Match).
*   **Limitations**: Explicit statement that statistical efficacy (convergence/accuracy improvement) cannot be determined from samples/1 step.
*   **Conclusion**: "Algorithm Validated" (code runs, loss finite, gate works, gradient direction correct) or "Failed".
*   **Model Substitution Note**: Explicit statement that TinyLlama was used instead of the paper's larger-scale models.

## Data Constraints
*   **Row Count**: A subset of rows in the preprocessed file (FR-002).
*   **Memory**: The entire dataset must fit in RAM (< 10 MB).
*   **Precision**: Float32 for all numerical calculations.
*   **Trace Requirement**: Every row must have a non-empty `reasoning_trace`. If missing, the pipeline aborts.
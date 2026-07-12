# Research: llmXive Follow-up: Extending EnterpriseClawBench

## Overview

This research phase investigates the feasibility of predicting "correction feasibility" for agent failures in the `EnterpriseClawBench` dataset using lightweight, CPU-tractable methods. The study posits that syntactic and pragmatic features (syntax tree depth, token frequency, error recovery markers) contain sufficient signal to distinguish between failures correctable via syntax rewriting and those requiring full model retraining.

## Dataset Strategy

### Source Verification
The `EnterpriseClawBench` dataset is the primary source.
- **Status**: **Proprietary / Not Publicly Available**. No verified public URL or accession ID exists in the provided list.
- **Action**: The implementation will check for local availability in `data/raw/`. **If the dataset is not found, the pipeline halts with a "Data Unavailable" status.** This satisfies the reproducibility requirement by defining the failure mode clearly, rather than assuming availability (Addressing `data_resources-93d8a50d`, `data_resources-1d8d6b32`).
- **Reproducibility**: If the dataset is available locally, its checksum will be recorded. If not, the project cannot proceed without external access, which is outside the scope of the free-tier CI runner.

### Data Composition
- **Total Tasks**: 852 (EnterpriseClawBench).
- **Held-out Set**: 120 tasks (Lite set) for final evaluation.
- **Data Types**: Raw execution logs (text), ground truth labels (Success/Failure), and task definitions.

### Data Access & Preprocessing
- **Access**: Local file system access for `data/raw/*.log` or `*.json`.
- **Preprocessing**:
  - **Streaming**: Large logs will be processed via chunking/streaming to avoid OOM (Addressing Edge Case: "traces too large for 7GB RAM").
  - **Labeling**: Traces labeled "failed" or "success" based on ground truth.
  - **Ambiguity**: Traces with ambiguous pragmatic markers will be flagged as "neutral" or excluded from the training split to prevent label noise (Addressing Edge Case: "ambiguous pragmatic markers").

## Feature Engineering Strategy

### Syntactic Features
- **Syntax Tree Depth**: Calculated using a parser (e.g., `networkx` or a lightweight AST parser) on the tool-call sequence structure.
- **Token Frequency**: Distribution of token types (e.g., function calls, arguments, error strings).

### Semantic Proxy Features (Construct Validity)
- **Error Codes**: Specific error strings (e.g., "SyntaxError", "Timeout").
- **Failed Function Names**: The names of functions that failed.
- **Rationale**: To address the concern that structural features may not capture "reasoning gaps" (semantic failures), we include these semantic proxies. We will explicitly test if these proxies correlate with the "correctable" label (Addressing `methodology-142dcb74`).

### Triplet Construction (FR-002)
For each failed trace, a corresponding successful trace for the same task will be identified to form a `(System_Prompt, Failed_Trace_Structure, Successful_Correction_Structure)` triplet.
- **Oracle Definition**: The "correctable" label is derived from a **Semantic Outcome Oracle**. This oracle is based on **manual expert review** (or a high-level rule-based check of the *final output*) to determine if the failure was due to a fixable syntax error vs. a fundamental reasoning gap. **Crucially, this oracle does not use the structural features (syntax depth, token freq) as inputs**, ensuring the ground truth is independent of the predictors (Addressing `scientific_soundness-702aa9f2`, `scientific_soundness-807b6018`).

## Model Strategy

### Architecture
- **Model**: Distilled T5-small (≤60M parameters).
- **Reasoning**: T5-small is small enough to train on CPU (2 cores, 7GB RAM) within 6 hours while retaining sequence-to-sequence capabilities required for predicting "correctability" based on structural inputs.
- **Constraint Compliance**:
  - **No GPU**: Training will use `device="cpu"`.
  - **No Quantization**: Standard float32 precision will be used to avoid `bitsandbytes` dependencies which often require CUDA.
  - **Memory**: Batch sizes will be tuned dynamically to stay under 7GB RAM.
  - **4-bit Option**: The Constitution (Principle VII) allows 4-bit quantization. This is **deferred** pending a resource feasibility check. If T5-small fits, we use it; if we pivot to a larger model (e.g., Llama-3-8B), we will attempt 4-bit quantization *only if* it fits within the 7GB RAM limit on CPU (Addressing `plan_consistency-31d588a9`).

### Training Objective
- **Task**: Binary classification (Correctable vs. Unfixable).
- **Loss**: Cross-Entropy Loss.
- **Optimizer**: AdamW (default settings).
- **Fallback**: If training loss does not converge, the system will revert to a rule-based heuristic model (as per Edge Cases) to ensure the evaluation step can still proceed.

### Intervention Mechanism (The "Fix")
- **Role**: The trained model acts as a **Diagnostic Gatekeeper**. It predicts "correctable" or "unfixable".
- **Action**:
  - If **Correctable**: A **Rule-Based Rewriter** is triggered. This rewriter applies deterministic syntactic corrections (e.g., reordering arguments, fixing indentation) to the trace before re-injection into the harness.
  - If **Unfixable**: The original trace is passed through unchanged.
- **Rationale**: This separates the *prediction* (model) from the *intervention* (rewriter), ensuring the evaluation measures the combined effect of the diagnostic and the correction (Addressing `methodology-7ccccac8`, `methodology-59365faf`).

## Evaluation Strategy

### Metric: Artifact Delivery Score
- **Definition**: Success rate of the agent session in delivering the required output.
- **Comparison**: Baseline ("Model + Harness") vs. Adapter-Enhanced ("Model + Adapter (Diagnostic) + Rewriter (Intervention) + Harness").
- **Set**: 120-task held-out Lite set.

### Statistical Analysis (FR-005)
- **Test**: **McNemar's Test** (for paired binary outcomes: Success/Failure per task) or **Generalized Linear Mixed Model (GLMM)** to account for task-level variance. A t-test is **not** appropriate for binary proportions (Addressing `scientific_soundness-69e347ab`).
- **Hypothesis**: $H_1$: Adapter-enhanced score > Baseline score.
- **Significance Threshold**: $p < 0.05$.
- **Multiple Comparison Correction**: If multiple feature subsets are tested, Bonferroni or Benjamini-Hoch correction will be applied (SC-001).

### Power Analysis (Addressing `methodology-dd42454a`)
- **Sample Size**: N=120 (paired tasks).
- **Calculation**: For a paired binary test (McNemar's) with $\alpha=0.05$ and Power=0.80, the minimum detectable effect size (Cohen's d equivalent) is approximately 0.35 (medium effect).
- **Implication**: If the true improvement in Artifact Delivery Score is small (d < 0.35), the study is underpowered to detect it. A non-significant result ($p > 0.05$) in this case will be reported as "inconclusive due to power limitations" rather than "no signal".

### Resource Monitoring (FR-006)
- **Memory**: Peak RSS logged via `/proc/self/status`.
- **Time**: Wall-clock time logged from start to end of training.
- **Thresholds**: Fail if >7GB RAM or >6 hours.

## Risk Analysis & Mitigation

| Risk | Probability | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **Dataset Unavailability** | High | High | **Data Feasibility Gate**: If data not found in `data/raw/`, halt immediately. |
| **OOM on CPU** | Medium | High | Implement streaming/chunking; reduce batch size; fallback to rule-based model. |
| **No Signal in Features** | Medium | Medium | If H1 rejected ($p > 0.05$), report null result or power limitation (per Assumptions). |
| **Ambiguous Labels** | Low | Medium | Flag "neutral" traces; exclude from training; sensitivity analysis on cutoffs. |

## Decision Rationale

- **Why T5-small?** It is the smallest viable sequence-to-sequence model that can handle the "input structure -> prediction" task without the overhead of larger LLMs. It fits the CPU constraint.
- **Why not fine-tune a larger model?** A larger model (e.g., Llama-3-8B) would exceed the 7GB RAM limit on a CPU-only runner, even with quantization (which is restricted by the "no 8-bit" constraint in FR-003). 4-bit quantization is a **deferred option** only if T5-small is insufficient.
- **Why McNemar's Test?** The outcome (Artifact Delivery) is binary (Success/Failure) per task. McNemar's test is the correct statistical tool for paired binary data, avoiding the category error of treating it as continuous (Addressing `scientific_soundness-69e347ab`).

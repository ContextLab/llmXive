# Research: Socratic Transformers (PROJ-582)

## Overview

This research investigates the efficacy of **negative selection on belief** as a mechanism for improving reasoning in language models. Unlike "self-teaching" which implies internal knowledge generation, this approach frames the process as an evolutionary filter: the model generates multiple reasoning paths, and an adversarial critique mechanism applies selection pressure to eliminate beliefs (outputs) that contain logical contradictions or unsupported assumptions.

## Dataset Strategy

The project relies on two primary datasets for both generation and evaluation. All sources are verified, open, and directly downloadable via programmatic loaders.

| Dataset | Purpose | Source / URL | Load Method |
| :--- | :--- | :--- | :--- |
| **GSM8K** | Training (Static/Dialogue/Ablation), Evaluation | `openai/gsm8k` (HuggingFace) | `datasets.load_dataset("openai/gsm8k", "main", split="test")` |
| **MATH** | Evaluation (held-out), Training (subset) | `HuggingFaceH4/MATH-500` | `datasets.load_dataset("HuggingFaceH4/MATH-500", split="test")` |

**Dataset Verification**:
- **GSM8K**: Verified as `openai/gsm8k` on HuggingFace. Contains a substantial set of test examples. Format: `question` (str), `answer` (str). Source: https://github.com/openai/grade-school-math
- **MATH**: Verified as `HuggingFaceH4/MATH-500`. Contains a set of test examples. Format: `problem` (str), `solution` (str).
- **Access**: Both are open, no credentials required. Downloadable via `datasets` library on CPU.

**Data Constraints**:
- **Memory**: Full datasets fit in RAM. Generation of dialogue tuples will be streamed or batched to stay within a defined storage capacity limit.
- **Processing**: No manual curation (e.g., `question_bank.json` removed). All data derived programmatically from raw sources.

## Methodology

### 1. Data Generation (US1)
Three distinct datasets are generated from the raw GSM8K/MATH sources:

1.  **Condition C (Static)**: Standard `(Question, Answer)` pairs.
    - *Input*: Raw dataset.
    - *Output*: `static.parquet`.
2.  **Condition A (Selection)**: Socratic Dialogue Tuples `(Question, Initial_Answer, Critique, Revised_Answer)`.
    - *Process*:
        1.  Generate `Initial_Answer` using a base model (e.g., `TinyLlama-1.1B` or `Phi-3-mini` 4-bit).
        2.  **Verification**: Compare `Initial_Answer` against ground truth. **If correct, discard the tuple** (no negative selection needed). Proceed only if incorrect. This ensures the training data focuses on the 'negative selection' mechanism.
        3.  Generate `Critique` using a **distinct, stronger model** (e.g., a larger LLM or different architecture) to identify logical errors, unsupported assumptions, or contradictions. This ensures independence from the base model's latent biases.
        4.  Generate `Revised_Answer` conditioned on the `Critique`.
    - *Filtering*: Tuples where `Critique` is trivial (e.g., "Good job") are discarded. **Operational Definition**: Discard if `Critique length < 20 tokens` OR `Semantic similarity (Cosine) to Initial Answer > 0.85`.
    - *Output*: `dialogue.parquet`.
3.  **Condition B (Ablation)**: Neutral Critique Tuples.
    - *Process*: Same as Condition A, but `Critique` is replaced with a **semantically coherent neutral critique** (e.g., "The answer looks correct, no changes needed") rather than a simple placeholder. This controls for token count and semantic structure while isolating the effect of *negativity* (adversarial pressure).
    - *Output*: `ablation.parquet`.

**Test Set Separation**: The `generate_dialogue.py` script explicitly filters out any examples from the GSM8K test set and MATH test set IDs used for evaluation, ensuring strict separation (Constitution Principle VI).

### 2. Training & Evaluation (US2)
- **Model**: A small, 4-bit quantized base model (e.g., `TinyLlama-1.1B-Chat-v1.0` or `Phi-3-mini-4k-instruct`).
- **Fine-tuning**: LoRA (Low-Rank Adaptation) with strict memory constraints.
    - *Hardware*: CPU-first (4-bit via `bitsandbytes` CPU support or `gguf` fallback).
    - *Hyperparameters*: `r=16`, `lora_alpha=32`, `target_modules=["q_proj", "v_proj"]`.
- **Conditions**:
    - Train `Model_A` on `dialogue.parquet`.
    - Train `Model_B` on `ablation.parquet`.
    - Train `Model_C` on `static.parquet`.
- **Evaluation**:
    - Test on held-out GSM8K test set and MATH-500 test set.
    - **Metric**: **Answer Extraction via Regex** (e.g., extracting the final number from `boxed{...}` or the last sentence) to handle formatting variations, supplemented by Exact Match. This ensures the construct "reasoning capability" is accurately measured, not just string matching.

### 3. Analysis (US3)
- **Statistical Test**: **Independent Samples t-test (Welch's t-test)** comparing accuracy of `Model_A` vs `Model_B` and `Model_A` vs `Model_C`.
    - *Rationale*: The models are distinct entities trained on disjoint datasets; a paired t-test is invalid.
    - *Fallback*: **Mann-Whitney U test** if normality assumptions are violated.
    - *Robustness*: **Permutation test** (10,000 iterations) to handle small effect sizes and variance issues in the N=500-1300 regime.
- **Correction**: Bonferroni correction applied for multiple comparisons (3 conditions -> 3 pairwise tests).
- **Power & MDES**: With N=500-1300, the **Minimum Detectable Effect Size (MDES)** is approximately 0.03 (3%) at alpha=0.05. The analysis will explicitly report MDES.
- **Causal Claims**: The experimental design (Randomized Controlled Trial via distinct training sets) supports **causal claims** that the *selection mechanism* caused the improvement, provided confounds (token count, semantic structure) are controlled via the ablation condition.

## Compute Feasibility

- **CPU-First Strategy**:
    - Use 4-bit quantization (`load_in_4bit=True`) to reduce memory footprint.
    - Use `torch_dtype=torch.float16` where supported, fallback to `float32` if memory permits.
    - Batch size = 1 or 2 to prevent OOM.
    - If CPU training is too slow (>6h), the plan relies on the **GPU Escape Hatch** (Kaggle auto-offload) for the fine-tuning step only, running a scaled-down version (fewer epochs, smaller batch) if the full run exceeds limits.
- **No Synthetic Data**: All training data is derived from real GSM8K/MATH examples.

## Decision Rationale

- **Why 4-bit Quantization?**: Essential for fitting LLMs on constrained RAM environments. Full precision is impossible.
- **Why Ablation with Neutral Critique?**: Controls for token count and semantic structure. Ensures any improvement in Condition A is due to the *negativity* of the critique (selection pressure), not just the presence of extra tokens or semantic content.
- **Why GSM8K/MATH?**: Verified, open, and directly relevant to logical reasoning. No gated data required.
- **Why Independent Samples t-test?**: Appropriate for comparing mean accuracy across independent models. Paired tests are invalid for distinct training sets.
- **Why Regex Extraction?**: Robust to formatting variations in math problems, ensuring accurate measurement of reasoning capability.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **OOM on CPU** | Use `bitsandbytes` 4-bit; fallback to smaller model (e.g., `TinyLlama`); stream data; reduce batch size to 1. |
| **Critique Quality** | Implement strict filtering (Constitution VII); discard non-adversarial tuples; use a stronger model for critique if needed (CPU fallback). |
| **Data Leakage** | Strict separation of training and test sets; no test tokens in generation loop. |
| **Statistical Power** | Report effect sizes; acknowledge limitations; use permutation tests for robustness. |
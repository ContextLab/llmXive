# Research: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Problem Statement

Does the "reverse-perplexity" curriculum used to instill self-checking behaviors in Olympiad-level models inadvertently encode rigid, domain-specific heuristics that degrade performance on open-ended, ill-structured scientific problems lacking verifiable ground-truth answers?

## Hypothesis

**H1 (Rigidity Interaction)**: The SU-01 model will exhibit a significant **interaction effect** between Model Type and Domain. Specifically, SU-01 will outperform the Baseline on Deterministic tasks (MMLU-STEM) but underperform on Ill-Structured tasks (OpenSci-Reason). This reversal (positive interaction coefficient in the LME model) is the primary evidence of rigidity.

**H2 (Descriptive Correlation)**: Within the SU-01 model, there will be a negative correlation between per-prompt correctness on deterministic tasks and creativity scores on ill-structured tasks. (Note: This is a secondary, descriptive metric).

## Dataset Strategy

The following datasets are selected based on the "Verified datasets" block provided in the project inputs. They are open, programmatic, and suitable for CPU inference.

| Dataset Role | Source Name | Verified URL | Usage |
| :--- | :--- | :--- | :--- |
| **Deterministic (Olympiad Proxy)** | `HuggingFaceH4/mmlu` (STEM subset) | `https://huggingface.co/datasets/HuggingFaceH4/mmlu` | Used as the proxy for "deterministic reasoning tasks". Contains multiple-choice questions in physics, math, and chemistry with a single correct answer, allowing for binary per-prompt correctness measurement. |
| **Ill-Structured (OpenSci)** | `nvidia/OpenScience` | `https://huggingface.co/datasets/nvidia/OpenScience` | Raw source for the "OpenSci-Reason" dataset. **Curation Required**: We will filter this dataset to retain only ill-structured prompts (open-ended, no single ground truth) and remove factual Q&A. |
| **Proxy Scoring Model** | `meta-llama/Meta-Llama-3-8B-Instruct` | *Internal HF Hub* | Used for scoring. Fine-tuned on a diverse set of general scientific reasoning (distinct from Olympiad data). |
| **Validation Set (Gold Standard)** | *Manually Curated* | *N/A* | A set of **N=50 responses** from the `OpenSci-Reason` dataset, **manually rated by human experts** for Novelty, Feasibility, and Consistency. This satisfies FR-008's requirement for expert-rated ground truth. |

**Dataset Fit & Limitations**:
- **Deterministic Proxy**: `HuggingFaceH4/mmlu` (STEM subset) is used as the deterministic proxy. It provides binary correctness (1/0) for the Point-Biserial correlation and, crucially, serves as the "Deterministic" domain in the LME interaction test. This dataset was selected over social-science proxies (e.g., Compas) because it directly measures "gold-medal" style reasoning in hard sciences, preserving construct validity.
- **OpenSci Curation**: The `nvidia/OpenScience` dataset contains a mix of factual and open-ended tasks. The plan includes a **curation step (T-002)** to filter for ill-structured prompts. If the dataset lacks sufficient ill-structured prompts, the sample size will be adjusted, and the limitation will be reported.
- **Gold Standard**: The plan explicitly rejects using `JasonOrange/ERC` or `OpenSciLM/OS_Train_Data` for validation, as these are not expert-rated for scientific creativity. Instead, we will **manually curate** N=50 responses from the generated `OpenSci-Reason` set and have them rated by human experts.

**Data Acquisition Strategy**:
- Use `datasets.load_dataset(..., streaming=True)` for `OpenSci` and `MMLU` to avoid RAM overflow.
- Cache datasets locally in `data/raw/` with checksums.
- Stream generation outputs to JSONL to prevent memory bloat.

## Methodological Approach

### 1. Dataset Curation & Unification (T-001, T-002, T-003)
- **Input**: `nvidia/OpenScience` (raw) and `HuggingFaceH4/mmlu` (STEM).
- **Process**: 
  1. Filter `OpenScience` for ill-structured prompts.
  2. Extract STEM subset from `MMLU`.
  3. **Unify**: Merge both into a single `prompts_unified.jsonl`. **Critical Step**: Add a `domain` field to every record: `domain="deterministic"` for MMLU, `domain="ill-structured"` for OpenSci. This enables the LME interaction test.
- **Output**: `data/intermediate/prompts_unified.jsonl`.

### 2. Inference Pipeline (CPU-First)
- **Models**: SU-01 (assumed available locally or via HF) and a Baseline (e.g., Llama-3-8B-Instruct).
- **Configuration**: `batch_size=1`, `temperature=0.7`, `max_new_tokens=2048`.
- **Hardware**: CPU-only. If SU-01 requires CUDA, the plan will attempt to load it in 8-bit mode or fallback to a CPU-compatible variant.
- **Output**: JSONL files with `prompt_id`, `model_id`, `response`, `domain`, `is_correct` (for MMLU), `generation_time`, `truncated`.

### 3. Automated Scoring (Proxy Model)
- **Model**: Llama-3-8B-Instruct (quantized to 8-bit using `bitsandbytes` or `accelerate` for CPU).
- **Prompt**: "Evaluate the following scientific response on Novelty, Feasibility, and Logical Consistency (1-5 scale). Provide reasoning."
- **Validation (T-010)**: Run on the **N=50 manually curated Gold Standard** set. Calculate Pearson correlation between proxy scores and human scores.
- **Fallback Strategy (T-011)**: 
  - If correlation < 0.6: **Do not abort**. Automatically switch to a secondary, smaller proxy model (e.g., Llama-3-2B-Instruct) or trigger a "Human-Only" scoring mode (slower, but valid).
  - The pipeline continues only if a valid scoring mechanism is established.

### 4. Statistical Analysis (Mandatory Two-Stage)
- **Stage 1: Descriptive Statistics (FR-005 Compliance)**
  - **Metric 1 (Descriptive)**: **Point-Biserial correlation** between per-prompt MMLU correctness (Binary) and OpenSci creativity (Continuous) *within each model*.
    - *Method*: `scipy.stats.pointbiserialr`.
    - *Note*: This is descriptive only. It does not control for the nested structure or test the interaction.
  - **Metric 2 (Descriptive)**: **Paired t-test** comparing mean creativity scores of SU-01 vs. Baseline on OpenSci.
    - *Method*: `scipy.stats.ttest_rel`.

- **Stage 2: Primary Hypothesis Test (LME)**
  - **Model**: Linear Mixed Effects (LME) model to handle nested data (multiple candidates per prompt) and test the interaction effect.
  - **Formula**: `Creativity_Score ~ Model_Type * Domain + (1|Prompt_ID)`.
    - `Creativity_Score`: Mean creativity score (Novelty+Feasibility+Consistency)/3.
    - `Model_Type`: Categorical (SU-01 vs Baseline).
    - `Domain`: Categorical (Deterministic vs Ill-Structured).
    - `(1|Prompt_ID)`: Random intercept for each prompt (handling nested candidates).
  - **Hypothesis**: A significant **interaction effect** (`Model_Type * Domain`) indicates that the performance gap between models reverses across domains (SU-01 better on Deterministic, worse on OpenSci), confirming the rigidity trade-off.
  - **Method**: `statsmodels` (MixedLM).
  - **Robustness**: Sensitivity analysis by re-running LME after excluding low-confidence prompts (variance > 1.5 or entropy > 2.0).

### 5. Power Analysis
- **Sample Size**: N=500 prompts (250 MMLU, 250 OpenSci).
- **Effect Size**: Target Cohen's d=0.5 (medium).
- **Justification**: A power analysis will be performed to confirm if N=500 provides sufficient power (target >0.80) for the expected effect size. If power is low, the limitation will be explicitly stated in the results.

## Computational Feasibility & Escape Hatch

- **CPU Path**:
  - SU-01: If available as a small model (<7GB), run directly. If large, use low-bit quantization.
  - Scoring Model: LlamaB (quantized) fits in constrained RAM.
  - Total RAM: sufficient to accommodate the OS, Python runtime, Model, and Data buffers.
  - Time: A set of prompts * 3 candidates * 2 models * [deferred]/prompt = [deferred]. **Risk**: May exceed 6h limit.
  - **Mitigation**: Reduce OpenSci sample to 200 prompts for the full pipeline if initial tests show >6h runtime. Or parallelize inference across multiple CI jobs (if allowed) or use a smaller baseline model (e.g., Phi-3-mini) for the baseline comparison.
- **GPU Escape Hatch**:
  - If CPU inference fails due to OOM or time constraints, the execution stage will auto-offload to a Kaggle GPU with sufficient VRAM capacity.
  - **Plan**: If `device="cpu"` fails, switch to `device="cuda"` with `load_in_8bit=True`. This reduces inference time by ~10x, ensuring completion within 6h.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Dataset Mismatch**: No verified IMO/IPhO dataset. | Use `HuggingFaceH4/mmlu` (STEM) as the deterministic proxy. Document the substitution. |
| **OpenSci Curation Failure**: `nvidia/OpenScience` lacks ill-structured prompts. | Adjust sample size; report limitation; use a fallback dataset if available. |
| **OOM on CPU**: 8B model + OS > 7GB. | Use low-bit quantization. If still failing, fallback to a smaller model (e.g., Llama-2B) for the proxy. |
| **Timeout**: 6h limit exceeded. | Reduce sample size to a moderate number of prompts. Use GPU escape hatch. |
| **Proxy Invalidity**: Correlation < 0.6. | **Do not abort**. Switch to secondary proxy (Llama-3-2B) or Human-Only scoring mode. |

## Decision Rationale

- **CPU-First**: Aligns with CI constraints. Most statistical analysis and small-model inference are CPU-tractable.
- **Streaming**: Essential for handling large datasets without RAM overflow.
- **Proxy Scoring**: Necessary for scalability; manual scoring is infeasible for 500 prompts * 3 candidates.
- **Quantization**: The only viable path to run 8B models on 7GB RAM.
- **Two-Stage Analysis**: Ensures compliance with FR-005 (Simple Stats) while providing the rigorous interaction test (LME) required to validly test the "rigidity" hypothesis in the presence of nested data. The LME is now the **primary** test, not an optional add-on.
- **Fallback Strategy**: Prevents total pipeline failure if the primary proxy model is invalid, ensuring the research question can still be answered (albeit with a different scoring method).

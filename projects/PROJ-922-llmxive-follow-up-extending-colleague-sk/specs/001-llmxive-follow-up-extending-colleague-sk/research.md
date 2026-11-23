# Research: llmXive follow-up: extending "COLLEAGUE.SKILL"

## 1. Research Question

Does explicitly decoupling capability heuristics from behavioral style in LLM agent prompts reduce hallucinated expertise and style drift during long-horizon interactions compared to monolithic persona prompts?

**Hypothesis**: The "Separated Tracks" prompt condition will yield a statistically significant reduction in Hallucination Rate (p < 0.05) and non-inferior Style Consistency compared to the "Monolithic" condition.

## 2. Dataset Strategy

### 2.1 Expert Profiles
*   **Source**: Simulated repository (as per `Assumption about data source` in spec).
*   **Rationale**: The public COLLEAGUE.SKILL gallery URL is not verified in the "Verified datasets" block. A simulated repository with identical structure (a set of distinct profiles) is generated programmatically to ensure reproducibility and avoid access-gated data issues.
*   **Content**: Each profile contains:
    *   `capability_track`: Rules, heuristics, domain constraints.
    *   `behavior_track`: Tone, vocabulary, structural preferences.
*   **Verification**: Generated via `code/data/generators/profile_generator.py` with pinned seeds.

### 2.2 Task Scenarios
*   **Source**: Programmatic generation (`code/data/generators/task_generator.py`).
*   **Rationale**: No public dataset exists with the specific "multi-turn, multi-hop reasoning, capability/behavior split" structure required.
*   **Content**: A set of tasks across 5 domains (coding, math, logic, creative, factual).
*   **Ground Truth**: Each task includes a `validation_set` (rules to check adherence) and `context_trace` (facts and logic steps to check for hallucination).
*   **Hallucination Definition**: Hallucination Rate is defined as the proportion of outputs that fail to derive the correct final answer *or* fail to include the required intermediate logic steps defined in `context_trace`. This uses rule-bound logic chains (e.g., "If A then B, if B then C") where the ground truth is a deterministic chain of boolean checks, allowing regex/logic verification without LLM judges.

### 2.3 Model Selection
*   **Model**: `Llama-3-8B-Instruct` (Quantized Q4_K_M) or `Phi-3-mini-4k-instruct` (Q4).
*   **Source**: Hugging Face (`meta-llama/Llama-3-8B-Instruct` or `microsoft/Phi-3-mini-4k-instruct`).
*   **Feasibility Check**:
    *   `Llama-3-8B-Q4` requires ~5-6 GB RAM for weights + context. This fits within the 7 GB limit if context is managed (batching).
    *   **Fallback**: If OOM, the specific run is logged as `status: 'oom'` and excluded from analysis. **No GPU offload is permitted** to preserve causal validity.
*   **Verified Datasets**:
    *   *Hugging Face*: `meta-llama/Llama-3-8B-Instruct` (Verified URL: `https://huggingface.co/meta-llama/Llama-3-8B-Instruct`)
    *   *Hugging Face*: `microsoft/Phi-3-mini-4k-instruct` (Verified URL: `https://huggingface.co/microsoft/Phi-3-mini-4k-instruct`)

## 3. Methodology

### 3.1 Experimental Design
*   **Design**: 3 (Prompt Condition: Monolithic, Separated, Generic) × 10 (Profiles) × 50 (Tasks).
* **Total Runs**: [deferred] (Balanced subset for LMM convergence).
*   **Randomization**: Task order randomized per profile. Seeds pinned.
*   **Sample Size Justification**: A balanced subset of runs (10 profiles × 50 tasks) ensures sufficient data per random-effect level for LMM convergence, based on simulation-based power analysis for LMMs (rather than G*Power which assumes simple ANOVA).

### 3.2 Prompt Conditions
1.  **Monolithic**: Standard persona prompt combining capability and behavior in one block.
2.  **Separated Tracks**: Distinct sections for "Capability Rules" and "Behavior Style" with explicit separation instructions. The "Behavior Style" section instructs the model to "adopt the style" without listing specific keywords to count, ensuring the metric measures emergent style adoption rather than instruction following.
3.  **Generic Baseline**: No persona, standard system prompt.

### 3.3 Evaluation Metrics (Deterministic)
*   **Heuristic Adherence**: Binary (0/1). Checks if output satisfies `capability_track` rules using regex/logic against held-out validation rules.
*   **Hallucination Rate**: Proportion. Checks if output contains entity-value pairs not in `context_trace` OR fails to derive the correct final answer via the required logic chain defined in `context_trace`.
*   **Style Consistency**: Continuous (0-1). Frequency of emergent style markers (tone, sentence structure, vocabulary) defined in `behavior_track`, measured without explicit keyword lists in the prompt to avoid confounding with instruction following.

### 3.4 Statistical Analysis
*   **Model**: Linear Mixed-Effects Model (LMM).
    *   Fixed Effect: Prompt Condition.
    *   Random Effects: (1 | Profile), (1 | Task).
*   **Correction**: Bonferroni or Holm-Bonferroni for multiple comparisons (3 metrics).
*   **Sensitivity Analysis**: Sweep Style Consistency threshold (0.01, 0.05, 0.1) to check robustness.
*   **Non-Inferiority Test**: Calculate absolute difference in Style Consistency between conditions and check against a predefined margin (e.g., 0.05).

## 4. Compute Feasibility & Risks

### 4.1 CPU Constraints
* **Risk**: [deferred] runs × [deferred]/task = 12.5 hours (exceeds 6h limit).
*   **Mitigation**:
    1.  **Batching**: Process 10 tasks at a time.
    2.  **Optimization**: Use `llama-cpp-python` with `q4_0` quantization for faster CPU inference.
    3.  **Timeout**: Enforce a timeout per task; failed runs are excluded.
    4.  **GPU**: **No GPU offload**. If CPU fails, run is excluded.

### 4.2 Model Performance
*   **Risk**: 8B model may be too slow on CPU.
*   **Mitigation**: Use `llama-cpp-python` with `q4_0` quantization for faster CPU inference. Fallback to `Phi-3-mini` if necessary (smaller model, faster inference).

## 5. Decision Rationale

*   **CPU-First**: The research question is about "deployable on standard hardware." Using GPU by default would invalidate the hypothesis. **No GPU offload** is permitted to preserve causal validity.
*   **Simulated Data**: No verified public dataset exists for this specific experimental setup. Simulation ensures reproducibility and avoids access-gated data.
*   **Deterministic Evaluation**: LLM judges introduce circularity and subjectivity. Rule-based evaluation is required by the Constitution (Principle VI).
* **Balanced Subset**: A balanced subset of [deferred] runs ensures sufficient data per random-effect level for LMM convergence, addressing the sparsity risk of a smaller subset.
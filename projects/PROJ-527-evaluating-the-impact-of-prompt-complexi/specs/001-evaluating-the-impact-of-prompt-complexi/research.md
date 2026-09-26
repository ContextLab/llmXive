# Research: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

## 1. Research Question & Hypothesis

**Primary Question**: How does prompt complexity, defined by **structural composition** (number of examples, constraints, steps), affect the code generation performance of Large Language Models on the HumanEval benchmark?

**Hypothesis**: There is a non-linear relationship between structural complexity and code generation performance. Specifically, moderate complexity (problem statement + 1 example) yields optimal performance, while degenerate complexity (redundant constraints) significantly degrades performance due to cognitive load or instruction following failures.

**Methodological Note**: To avoid construct validity failures, 'Complexity' is defined by structural element counts, not token length. Token count is treated as a continuous covariate to control for prompt length, ensuring the model estimates the effect of structure independent of length.

## 2. Dataset Strategy

**Source**: The study utilizes the **HumanEval** benchmark.
**Verification**: The dataset is accessed via the verified `human-eval` Python package, which loads a collection of real records.
**URL**: https://huggingface.co/datasets/openai/openai_humaneval (Canonical source for the package).
**Access Method**:
```python
from human_eval import data
problems = data.read_problems()
```
**Data Fields**: `task_id`, `prompt`, `canonical_solution`, `test`.
**Sample Size**: N = 164 problems.
**Power Limitation**: With N=164, the study has limited power to detect small effect sizes. This is explicitly acknowledged in the analysis (FR-011). No synthetic data is used to inflate N.

| Dataset | Source URL | Access Method | Verified? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| HumanEval | https://huggingface.co/datasets/openai/openai_humaneval | `human-eval` package | Yes | A set of Python coding problems. |

## 3. Methodological Rigor

### 3.1. Prompt Complexity Definition (FR-001)
Prompts are generated in 5 tiers based on **structural elements**, with token count as a secondary indicator:
1.  **Simple**: Problem statement only (0 examples, 0 constraints).
2.  **Moderate**: Problem statement + 1 example.
3.  **Complex**: Problem statement + constraints (e.g., "must use recursion").
4.  **Very Complex**: Problem statement + multi-step instructions (e.g., "step 1: parse, step 2: validate").
5.  **Degenerate**: Problem statement + redundant constraints/examples (e.g., "do X. Also do X. Do X again.").

**Token Counting**: `tiktoken` (cl100k_base) is used as a covariate, not the definition of the tier.
- Simple ≤ 50 tokens (typical)
- Moderate 51-150 tokens (typical)
- Complex 151-300 tokens (typical)
- Very Complex 301-500 tokens (typical)
- Degenerate > 500 tokens (typical)
*Note: These thresholds are for logging only. The primary classification is based on structural element count.*

### 3.2. Statistical Analysis (FR-005)
**Model**: Linear Mixed Model (LMM).
**Equation**: `Performance ~ Complexity_Structural + Token_Count + (1 | Problem_ID)`
- **Fixed Effects**: `Complexity_Structural` (categorical, based on structure), `Token_Count` (continuous covariate).
- **Random Effects**: Random intercept for `Problem_ID` to control for inherent problem difficulty.
- **Multiple Comparisons**: Tukey's HSD or Bonferroni correction applied for pairwise comparisons between complexity levels.
- **Collinearity Check (FR-013)**: VIF calculated for `Token_Count` vs. `Structural_Element_Count`. 
  - **Remediation**: If VIF > 5, we will **orthogonalize** the variables (regress Token_Count on Structural_Count and use residuals) or use Principal Component Analysis (PCA) to create a composite predictor. We will not simply drop the variable or report descriptive correlations, as this undermines the primary hypothesis.

### 3.3. Measurement Validity
- **Code Correctness**: HumanEval unit test pass rate (Standard benchmark metric).
- **Static Analysis**: `ruff` for style/security; `networkx`/`radon` for cyclomatic complexity (McCabe 1976).
- **Token Count**: `tiktoken` (OpenAI standard).

### 3.4. Sensitivity & Robustness (FR-010)
- **Re-binning**: Thresholds for token counts are shifted (e.g., ±10%) to test robustness of complexity classification (though primary classification is structural).
- **Manual Review**: Samples where "degenerate" prompts have token delta < 100 vs "very complex" are flagged for manual review (US-1 Scenario 3).

## 4. Compute Feasibility & GPU Strategy

- **CPU Path**: Data loading, prompt generation, unit test execution, and static analysis run entirely on CPU.
- **LLM Inference**:
  - **Preferred**: API-based inference (if key provided) to offload compute.
  - **Fallback**: Local quantized model (e.g., `phi-2` 8-bit) if offline.
  - **GPU Escape Hatch**: If a local model requires CUDA, the pipeline will attempt to run on `device="cuda"`. The execution stage detects this and auto-offloads to Kaggle. The plan does *not* fabricate a CPU approximation for transformer inference; it plans the real scaled run.
- **Constraints**: 164 problems × 5 variants = 820 generations. Even with a small local model, this fits within 6 hours on a single GPU or via API.

## 5. Ethical & Safety Considerations

- **Bias**: The study is observational. No causal claims are made regarding LLM "intelligence".
- **Safety**: Generated code is executed in an isolated sandbox (timeout, resource limits) to prevent malicious execution.
- **Data Privacy**: HumanEval contains no PII.

## 6. Decision Rationale

**Why HumanEval?** It is the standard benchmark for code generation, ensuring comparability with existing literature.
**Why LMM?** The data is nested (5 variants per problem). OLS regression would violate independence assumptions. LMM correctly models the random intercept for problem difficulty.
**Why Structural Definition?** Defining complexity by token count creates a tautology with the token count covariate. Defining it by structural elements (examples, constraints) allows us to test the hypothesis about *structure* while controlling for *length*.
**Why CPU-First?** The dataset is small (164 items). Most of the pipeline (data prep, stats, static analysis) is CPU-bound. Only inference might need GPU, handled by the escape hatch.

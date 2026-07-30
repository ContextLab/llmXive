# Research: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

## Summary

This research investigates whether Large Language Models (LLMs) generating code are robust to semantically equivalent but syntactically perturbed prompts. We hypothesize that while the *intent* of the prompt remains unchanged (validated by high cosine similarity), the *surface-level noise* (typos, synonyms, rephrasing) will cause a statistically significant drop in code correctness (pass@1) for the StarCoder2-1.5B model. Because perturbations are controlled interventions, the observed difference in pass rates is a **causal estimate** of the model's sensitivity to surface noise, not merely an associational effect.

## Dataset Strategy

### Primary Dataset: HumanEval
- **Source**: `openai/openai_humaneval` (HuggingFace Datasets).
- **Verified URL**: `https://huggingface.co/datasets/openai/openai_humaneval`
- **Format**: Parquet (via `datasets` library).
- **Content**: 164 programming problems, each with a docstring, function signature, and test suite.
- **Access Method**: `datasets.load_dataset("openai/openai_humaneval")`
- **Feasibility**: The dataset is small, easily fitting in memory. The `datasets` library supports streaming, but given the size, loading into memory is efficient and robust.

### Embedding Model: Sentence-Transformers
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Purpose**: Calculate cosine similarity between original and perturbed prompts to ensure semantic equivalence.
- **Feasibility**: This is a small model that runs efficiently on CPU. It is the standard for lightweight semantic similarity tasks.

### Model for Inference: StarCoder2-1.5B (Primary) / 3B (Fallback)
- **Model**: `bigcode/starcoder2-1.5b` (Primary), `bigcode/starcoder2-3b` (GPU Fallback).
- **Configuration**: 4-bit quantization via `bitsandbytes`.
- **Feasibility**:
  - **CPU**: The medium-scale model (weights of moderate scale) fits comfortably within the available RAM limit. Empirical estimates suggest a task duration on the order of tens of seconds on CPU, totaling several hours for the full sample set.
  - **GPU Escape Hatch**: If CPU inference fails or the 3B model is required, the execution pipeline offloads to a reproducible GPU environment (Kaggle or local with pinned versions).
  - **Constraint**: No full-precision loading is planned.

## Methodology

### 1. Perturbation Generation (FR-002)
We will generate up to 3 variants per task using three distinct rule-based transformations:
1.  **Synonym Substitution**: Replace non-keyword tokens with synonyms from WordNet, avoiding Python keywords.
2.  **Typo Injection**: Randomly inject character errors (insertions, deletions, substitutions) into the function description.
3.  **Syntactic Rephrasing**: Paraphrase the problem statement using simple syntactic rearrangements (e.g., passive to active voice).

### 2. Semantic Validation (FR-003)
- **Metric**: Cosine similarity between the embedding of the original prompt and the perturbed prompt.
- **Threshold**: `> 0.95` for inclusion in the *primary filtered dataset*.
- **Raw Data**: All candidates, regardless of score, are retained in `data/processed/perturbation_candidates_raw.json` for sensitivity analysis.
- **Construct Validity Note**: The embedding model is trained on general text, not code. A score of 0.95 is a *proxy* for semantic equivalence, not ground truth. A "Code-Specific Sanity Check" will be performed on a subset to estimate false-negative rates.

### 3. Inference & Execution (FR-004, FR-005)
- **Model**: StarCoder2-1.5B (4-bit) on CPU.
- **Timeouts**: 30s for generation, 10s for code execution.
- **Sandbox**: Subprocess execution with disabled network access.
- **Metrics**: Pass/Fail status, execution time, error type (syntax, logic, timeout, OOM), **execution_environment** (CPU/GPU).

### 4. Statistical Analysis (FR-006 - FR-013)
- **Primary Metric**: Pass@1 rate for Original vs. Perturbed.
- **Bias Mitigation**: The primary statistical models (McNemar's test, Mixed-Effects Logistic Regression) will be re-fitted on the **entire candidate pool** (including filtered-out samples). The similarity score will be included as a continuous covariate or handled via Inverse Probability Weighting (IPW) to mitigate selection bias introduced by the 0.95 filter.
- **Hypothesis Testing**: McNemar's test for paired comparisons. For tasks with multiple perturbations, outcomes will be aggregated per task (e.g., average pass rate) to form the contingency table.
- **Correction**: Bonferroni correction applied for multiple comparisons ($\alpha_{adj} = 0.05 / 3 \approx 0.0167$).
- **Clustering**: Mixed-Effects Logistic Regression with `task` (Entity 1 in `data-model.md`) as a random effect to account for multiple perturbations per task.
- **Sensitivity**: Re-evaluation of pass@1 rates across thresholds $\{0.85, 0.90, 0.95, 0.99\}$ to quantify survivorship bias.

## Statistical Rigor & Assumptions

- **Causal Claims**: Because perturbations are controlled interventions on semantically equivalent inputs, the study claims a **causal effect** of surface noise on model robustness.
- **Power Analysis**: With 164 tasks (clusters), the power to detect *small* effect sizes in Mixed-Effects models is limited. The study is powered to detect **moderate-to-large** effect sizes. Non-significant results will be framed as "inconclusive" rather than "no effect".
- **Multiple Comparisons**: Bonferroni correction explicitly addresses the family-wise error rate for the three perturbation types.
- **Collinearity**: Perturbation types are mutually exclusive categories in the analysis, avoiding collinearity issues.
- **Measurement Validity**: HumanEval is the standard benchmark for code generation. The `all-MiniLM-L6-v2` model is a validated tool for semantic similarity, though its application to code is a proxy.

## Compute Feasibility Decision

- **CPU-First**: The plan relies on **StarCoder2-1.5B** (4-bit) on CPU.
- **Rationale**: A medium-scale model fits within a constrained RAM limit. Estimated runtime is approximately on the order of tens of seconds per task, totaling several hours for samples.
- **Escape Hatch**: If CPU inference fails or the 3B model is required, the execution pipeline offloads to a reproducible GPU environment. The specified time limit applies to the primary CPU run.; the GPU path is flagged as a deviation.
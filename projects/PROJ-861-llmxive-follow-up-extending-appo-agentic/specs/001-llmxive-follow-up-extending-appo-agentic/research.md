# Research: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

## Summary of Research Strategy

This research investigates the correlation between **Static Branching Scores** (structural confidence via KL divergence) and **Dynamic Branching Scores** (procedural value via APPO rollouts). The study is designed to run on CPU-only infrastructure, adhering to strict computational constraints while maintaining statistical rigor through permutation testing and residual analysis.

## Dataset Strategy

The study utilizes the **GSM8K** and **MATH** datasets, which are verified to contain the necessary token-level reasoning traces.

| Dataset | Source URL (Verified) | Role | Variable Fit Check |
|---------|-----------------------|------|--------------------|
| **GSM8K** | ` | Primary source for arithmetic and multi-step reasoning traces. | **Verified**: Contains `question` and `answer` fields with reasoning steps. Tokenization will generate the required next-token distributions. |
| **MATH** | ` | Secondary source for complex algebraic reasoning. | **Verified**: Contains detailed solution steps. Sampling will be stratified by difficulty to ensure diversity. |
| **CPU-Only Reference** | ` | Validation set for CPU inference stability (optional). | **Verified**: Confirms compatibility with CPU-only inference pipelines. |

**Sampling Strategy**:
- Target: A substantial set of tasks (stratified split between GSM8K and MATH).
- Method: Stratified random sampling by problem difficulty (if available) or length.
- Preprocessing: Traces will be truncated to the length of the shorter trace for alignment if lengths diverge significantly (overlap < 80%).

## Methodology & Statistical Rigor

### 1. Static Branching Score Calculation (FR-001, FR-002)
- **Model**: Phi-2 (default) or Llama-3-8B (fallback), loaded in default precision (float32/float16) on CPU.
- **Metric**: Kullback-Leibler (KL) divergence between the model's actual next-token distribution $P$ and a uniform distribution $Q$ over the top-k alternatives.
 $$ D_{KL}(P || Q) = \sum P(x) \log \frac{P(x)}{Q(x)} $$
- **Stability**: Probabilities clamped to $[1e-9, 1-1e-9]$ to prevent NaN errors.
- **Constraint**: No CUDA, no quantization. Inference runs on a limited number of CPU cores.

### 2. Dynamic Branching Score Generation (FR-003)
- **Algorithm**: APPO (Agentic Procedural Policy Optimization) with online rollouts.
- **Reward**: Binary correctness (1 for correct answer, 0 for incorrect).
- **Output**: Future-aware likelihood gains for each decision point.

### 3. Correlation Analysis (FR-005, SC-001, SC-003)
- **Alignment**: Scores aligned by `task_id` and token position. Truncation applied for length mismatches.
- **Coefficients**: Pearson ($r$) and Spearman ($\rho$) correlation.
- **Significance Testing**:
 - **Permutation Test**: 10,000 iterations per run.
 - **Seeds**: 3 independent runs ($n=3$) with different random seeds.
 - **Stopping Condition**: Hard timeout (pre-specified duration) or early stop if p-value stabilizes (change < 0.001).
 - **Reporting**: If timeout triggers, report actual p-value with "inconclusive" flag.
- **Model**: Linear Mixed-Effects Model (LMM) with `task_id` as a random effect to account for autocorrelation within traces.

### 4. Residual Analysis (FR-006, SC-004)
- **Classifier**: Pre-trained BERT model fine-tuned on GSM8K labels (domain-specific) to categorize reasoning patterns (e.g., "arithmetic", "algebra").
- **Visualization**: Residual plots categorized by reasoning pattern to identify where static approximations fail.

## Decision Rationale & Constraints

- **CPU-Only Constraint**: The study prioritizes CPU feasibility to validate the "democratization" of agentic RL. GPU acceleration is explicitly excluded to ensure the method is accessible on standard hardware.
- **Permutation Test Iterations**: The [deferred]-iteration target is mandated by Constitution Principle VI to ensure robust significance testing. The hard timeout mechanism ensures the CI job does not exceed a predefined duration threshold.
- **Dataset Fit**: GSM8K and MATH are selected because they contain the necessary reasoning traces. No external variables (e.g., user demographics) are required.
- **Collinearity**: Static and dynamic scores are derived from the same underlying architecture (or fine-tuned version). The correlation is interpreted as "initial structural confidence predicting final policy value," acknowledging the training process as a confounding variable.

## Assumptions & Risks

- **Assumption**: The frozen models (Phi-2/Llama-3-8B) will not crash on CPU with default precision.
- **Risk**: Permutation test may exceed 6-hour CI limit. **Mitigation**: Hard timeout with partial result reporting.
- **Risk**: Dataset lacks specific reasoning patterns. **Mitigation**: Stratified sampling to ensure diversity; fallback to alternative verified datasets if necessary.

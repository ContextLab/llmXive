# Research: llmXive follow-up: extending "MiniMax Sparse Attention"

## 1. Research Question & Hypotheses

**Primary Question**: To what extent do local signal statistics (block entropy, gradient magnitude, recency) correlate with the semantic importance of context tokens in long-window language models, and do these local approximations achieve retrieval performance comparable to a full-context (Dense) baseline within resource-constrained environments?

**Hypotheses**:
- **H1 (Entropy)**: Block Entropy correlates positively with semantic importance in "Needle In A Haystack" tasks, allowing Top-k selection to match Dense baseline F1 within a descriptive margin (target < 10% drop).
- **H2 (Gradient)**: Local Gradient Magnitude (via targeted proxy loss) provides a robust signal for "Multi-Hop" tasks, capturing token relevance to the retrieval target.
- **H3 (Recency)**: Recency Bias serves as a strong baseline but fails in tasks requiring long-range retrieval (e.g., mid-document needles).
- **H4 (Operational Substitution)**: The best-performing heuristic will not show a statistically significant difference (p > 0.05) from the Dense baseline across the RULER subset, supporting its use as a resource-efficient operational substitute.

*Note on Causality*: Findings will be framed as **associational** (correlation between heuristic scores and retrieval success) rather than causal. The study does not claim the heuristic *causes* the performance, but that it *correlates* with the performance of the full model. "Substitution" refers to operational replacement in constrained environments, not causal replacement of the learned mechanism's function.

## 2. Dataset Strategy

**Target Benchmark**: RULER (Retrieval Under Long Contexts Evaluation).
**Specific Tasks**: "Needle In A Haystack" (NIAH) and "Multi-Hop Retrieval".

| Dataset | Verified Source URL | Usage Strategy | Notes |
|:--- |:--- |:--- |:--- |
| **RULER (Primary)** | ` | Downloaded via `datasets.load_dataset`. Processed in chunks of 4k tokens to fit RAM. | Verified source. Contains NIAH and Multi-Hop tasks. **Must be 128k context** for validity. |
| **RULER (Debug Only)** | ` | **Debug/Validation Only**. Used ONLY to verify code logic if 128k fails. **NOT** used for primary hypothesis testing. | If 128k processing fails, the experiment aborts rather than switching to 4k, preserving the "Long-Window" claim. |
| **MiniMax-M3 Model** | `https://huggingface.co/MiniMaxAI/MiniMax-M3` | Model weights loaded via `transformers` from HuggingFace Hub. | **NOT** a dataset. This is the model repository. |

**Data Mismatch Check**: The RULER dataset contains synthetic needles and multi-hop questions, which perfectly matches the requirement for "retrieval accuracy" testing. No variable mismatch exists.

**Preprocessing Strategy**:
1. **Loading**: Use `datasets` library to stream the RULER JSONL.
2. **Chunking**: Implement a sliding window (stride = 50%) to break 128k contexts into 4k blocks for memory safety (FR-007).
3. **Filtering**: Exclude samples where the "needle" string is missing or corrupted (Edge Case handling).

## 3. Methodology & Statistical Plan

### 3.1 Experimental Setup
- **Model**: MiniMax-M3 (Frozen).
- **Hardware**: CPU-only (minimal cores, limited RAM).
- **Baselines**:
 1. **Dense Attention (Ground Truth)**: Full context inference (all tokens included). This represents the maximum achievable performance and serves as the baseline for comparison.
 2. **Learned Index Branch (Reference)**: Weights are loaded frozen to verify existence, but **not** used for the primary baseline metric to avoid circularity.
- **Heuristics**:
 1. **Block Entropy**: Calculate Shannon entropy per block; select Top-k.
 2. **Local Gradient Magnitude**: Compute gradient norms of the last hidden state w.r.t. a **targeted proxy loss** (cross-entropy of the *needle* tokens). This ensures gradients reflect relevance to the retrieval target, not general entropy.
 3. **Recency Bias**: Linear decay weighting based on token position.

*Parameter-Free Definition*: The heuristics are "parameter-free" because they do not **train** new weights; they compute statistics (entropy, gradients) on **frozen** weights using deterministic functions.

### 3.2 Metrics
- **Retrieval Accuracy**: Exact Match (EM) and F1 score against the "needle" string (Ground Truth from dataset).
- **Perplexity**: Average perplexity of the model over the selected context.
- **Computational Cost**: CPU time (seconds) and Peak RAM usage.
- **False Positive Rate (FPR)**: Proportion of selected blocks that **do not** contain the needle string (calculated against dataset ground truth, NOT against the baseline's selection).

### 3.3 Statistical Analysis
- **Primary Test**: **Paired t-test** (Constitution Principle VII) comparing the F1 scores of each heuristic vs. the Dense Baseline across all RULER tasks.
 - *Null Hypothesis*: No difference in mean F1 scores.
 - *Significance Level*: α = 0.05.
 - *Multiple Comparisons*: **Holm-Bonferroni correction** applied to the p-values of the three pairwise tests (Entropy vs. Dense, Gradient vs. Dense, Recency vs. Dense) to control Family-Wise Error Rate (FWER).
- **Secondary Test**: Wilcoxon signed-rank test (robustness check if normality assumptions fail).
- **Sensitivity Analysis**: Sweep Top-k threshold (or gradient cutoff) across a range of small values.
 - *Output*: Accuracy variance and FPR (defined as selecting a block without the needle).

### 3.4 Power Analysis & Sample Size Justification
- **Sample Size**: N=50 (RULER 50 subset).
- **Power Limitation**: With N=50, the power to detect a small effect size (e.g., 1-2% drop) is low (< 0.5).
- **Interpretation**:
 - If p < 0.05: We reject the null and conclude a significant difference exists.
 - If p > 0.05: We conclude there is **no evidence of degradation**, but we **cannot** claim statistical equivalence to the 1-2% margin. The 1-2% target is treated as a descriptive goal, not a statistical hypothesis.
 - The study is powered to detect **large** effect sizes (>10% drop) with high confidence.

## 4. Compute Feasibility & Risk Mitigation

| Risk | Mitigation Strategy |
|:--- |:--- |
| **OOM (GB limit)** | Aggressive chunking (k context); batch size = 1; clear cache after each sample. |
| **Runtime > 6h** | Limit RULER subset to a representative sample size.

The research question, method, and references remain unchanged as per the planning document requirements.; use streaming; abort if time > 5h. |
| **Gradient Computation Cost** | Proxy loss computed on a single forward-backward pass on a small subset of tokens (needle tokens only), not full sequence. |
| **CUDA Errors** | Explicit `device="cpu"` flags; disable `torch.cuda` checks. |
| **Empty Selection** | Fallback to first k blocks if all scores are near-zero (Edge Case). |

## 5. Ethical & Validity Considerations
- **Causal Claims**: None. The study uses observational benchmark data; findings are correlational (Association between heuristic score and retrieval success).
- **Measurement Validity**: RULER is a standard benchmark for long-context retrieval; F1/EM are standard metrics.
- **Collinearity**: Recency and Gradient Magnitude may be correlated in sequential data; this will be noted in the discussion.
- **Circularity Avoidance**: The baseline is **Dense Attention** (Full Context), not the Learned Index Branch. The FPR is calculated against the **Dataset Ground Truth**, not the baseline's selection. This prevents tautological validation.
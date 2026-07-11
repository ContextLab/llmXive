# Research: llmXive follow-up: extending "MiniMax Sparse Attention"

## Research Question
To what extent can local statistical properties of token blocks (entropy, gradient magnitude) approximate the information-selection capability of a learned attention routing mechanism in long-context language models?

## Dataset Strategy

The research relies on the **RULER** benchmark for long-context retrieval evaluation. The dataset must be verified against the provided list.

| Dataset Name | Description | Verified URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **RULER (Official)** | Long-context retrieval tasks (Needle In A Haystack, Multi-Hop) in JSONL/Parquet format. | `https://huggingface.co/datasets/ruler/ruler` | Primary evaluation suite. Tasks will be downloaded, parsed, and aligned to block boundaries. |
| **CommonCrawl** | General text corpus for pre-training context or additional retrieval noise. | ` | **Not used** in this specific feature scope (RULER tasks are self-contained). |

**Dataset Fit Analysis**:
- The RULER dataset (Official) contains the specific "Needle In A Haystack" and "Multi-Hop" tasks required by the spec.
- The dataset provides the full context length (up to 128k) necessary to test long-context heuristics.
- **Constraint Check**: The dataset size (JSONL) is manageable within the available disk limit. If the full task suite exceeds RAM during processing, the `ruler_loader.py` will implement on-demand streaming and sampling to fit the available RAM constraint.

## Heuristic Methodology

### 1. Local Gradient Magnitude (Primary)
- **Mechanism**: Computes gradients of the **Query-Context Cross-Entropy Loss** with respect to the input context tokens.
- **Target Definition**: The "target" for the loss is the **Query Tokens** (one-hot encoded). The "prediction" is the model's output distribution over the context tokens. This measures how much the context tokens influence the prediction of the query, without requiring the ground-truth answer.
- **Aggregation**: Aggregates gradient magnitudes per block to produce a scalar importance score.
- **Constraint**: Must run entirely on CPU. A single backward pass on a small batch (≤4 sequences) is feasible on CPU but will be the primary bottleneck.
- **Validation**: If GPU is detected, the system logs an error and aborts (per FR-002). **Ground-truth answer is NEVER used in this calculation.**

### 2. Block Entropy (Secondary)
- **Mechanism**: Calculates the Shannon entropy of the token probability distribution within a block.
- **Aggregation**: High entropy indicates high information density; low entropy indicates redundancy.
- **Validation**: Zero-gradient (uniform) distribution edge case handled by assigning a default low priority or skipping the block (per Edge Cases).

### 3. Recency-Weighted Bias (Tertiary)
- **Mechanism**: Applies a decay function based on the position of the block within the context window.
- **Validation**: Serves as a naive baseline to ensure heuristics are not outperformed by simple positional bias.

## Statistical Analysis Plan

### Primary Metric: Retrieval Accuracy
- **Measure**: Exact Match (EM) for Needle In A Haystack; F1 score for Multi-Hop.
- **Comparison**: Heuristic EM/F1 vs. Dense Baseline EM/F1.
- **Target**: Delta ≤ 2% (per SC-001).

### Secondary Metric: Statistical Significance (Equivalence)
- **Test**: **Two One-Sided Tests (TOST)** for equivalence.
- **Equivalence Margin (Delta)**: **±0.02** (2% accuracy).
- **Input**: 50 paired scores (Heuristic vs. Baseline) across distinct RULER tasks.
- **Threshold**: If the confidence interval of the mean difference lies entirely within [-0.02, +0.02], the heuristic is declared "statistically equivalent" to the baseline.
- **Power Analysis**: N=50 tasks is calculated to achieve **[deferred] power (beta=0.2)** to detect an effect size (delta) of 0.02 at alpha=0.05 (one-sided for TOST). If observed variance is higher, the achieved power will be reported and the result flagged as "underpowered" rather than falsely claiming equivalence.

### Tertiary Metric: Sensitivity Analysis
- **Variable**: Top-k selection cutoff (k ∈ {small, medium, large}).
- **Output**: Accuracy drop-off curve.
- **Flag**: Accuracy drop > 5% for a 10-block increase triggers a warning (per US-3).

## Computational Feasibility & Rationale

**Constraint**: 2 CPU cores, 7 GB RAM, 6 hours, No GPU.

| Component | Feasibility Strategy | Rationale |
|:--- |:--- |:--- |
| **Model Loading** | Load MiniMax-M3 in **GGUF 4-bit quantization** via `llama-cpp-python`. | Default precision (FP16) requires >14GB RAM. GGUF -bit fits in ~-5GB, leaving room for KV cache and overhead. `n_gpu_layers=0` ensures CPU-only. |
| **Gradient Calculation** | Small batch (≤4) with `llama-cpp` backend (if supported) or `transformers` with CPU offload. | Input gradients are expensive on CPU. Limiting batch size to a conservative value ensures memory safety. |
| **RULER Execution** | Stream tasks one-by-one; no full dataset loading. | Prevents OOM. Each task is processed, scored, and results logged before moving to the next. |
| **Total Runtime** | 50 tasks × (Inference + Gradient + Overhead) ≤ 6h. | Estimated time per task is expected to be in the range of several minutes. If a task exceeds this, it is flagged and skipped to prevent job timeout. |

**Decision**: The plan prioritizes **correctness of the heuristic** over speed. If the gradient calculation is too slow on CPU to meet the 6-hour limit for 50 tasks, the plan will trigger a "Compute Limit Exceeded" flag, and the research will proceed with a reduced sample size (N=20) while explicitly noting the power limitation in the final report.

**Baseline Comparison Note**: The "Dense Baseline" run will explicitly include the computational overhead of the "Index Branch" routing mechanism (as it is part of the model's standard inference path). The "Heuristic" run disables the Index Branch. The comparison measures "selection quality + routing cost" vs "selection quality + heuristic cost", which is the correct operational comparison.

## Edge Case Handling

1. **Uniform Distribution (Zero Gradient)**:
 - *Action*: If block entropy is uniform or gradient magnitude is zero for all tokens in a block, the block is assigned a default priority score of 0.0 and excluded from the Top-k selection unless k exceeds the number of non-zero blocks.
2. **Needle Split Across Blocks**:
 - *Action*: The RULER task generator ensures "needles" are placed within blocks. If a split occurs, the heuristic may miss the needle. This is a known limitation of block-level selection and will be reported as a "False Negative" in the sensitivity analysis.
3. **Model Corruption/Version Mismatch**:
 - *Action*: The `mini_max_wrapper.py` will verify model architecture compatibility upon load. If the HF `transformers` version mismatches, the script aborts with a clear error message.

## References
- RULER Dataset: ruler/ruler (Official HuggingFace).
- MiniMax Sparse Attention: (Internal/Parent Project Reference).
# Research: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Research Question

Does reducing the depth of memory graph traversal (via "Lazy" or "Greedy" heuristics) significantly degrade reasoning accuracy on multi-hop tasks, and can we identify a complexity threshold where these heuristics fail to maintain a substantial proportion of baseline performance?

## Dataset Strategy

| Dataset Name | Description | Source URL / Loader | Usage |
| :--- | :--- | :--- | :--- |
| **LoCoMo** | Multi-hop reasoning benchmark (questions, context, ground truth). | `https://huggingface.co/datasets/Aman279/Locomo/resolve/main/locomo.csv` | Primary evaluation set for Baseline, Lazy, and Greedy strategies. |
| **Synthetic Noisy Graphs** | Programmatically generated graphs by injecting **[deferred] irrelevant edges** (randomly selected from non-relevant pairs) into LoCoMo-derived structures. | Generated via `code/data_loader.py` (no external URL). | Robustness check (Constitution Principle VII) to test heuristic stability under perturbation. |
| **MixSub-LLaMA** | CPU-optimized text subset for potential model fine-tuning or validation (if needed). | `https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet` | Fallback validation set if LoCoMo size is insufficient for statistical power (deferred). |

**Note**: MRAgent source code is referenced in the spec but has **NO verified source** in the provided list. We will re-implement the "Full" reconstruction logic based on the spec's description rather than downloading a binary or script from an unverified URL.

## Methodology

### 1. Experimental Design
*   **Independent Variable**: Traversal Strategy (Full, Lazy, Greedy).
*   **Dependent Variables**: Accuracy (0.0–1.0), Nodes Visited, Inference Latency (seconds), Token Count.
*   **Control**: "Full" active reconstruction (traverses entire relevant subgraph).
*   **Conditions**:
    *   **Baseline**: LoCoMo tasks with Full strategy.
    *   **Heuristics**: LoCoMo tasks with Lazy (threshold-triggered) and Greedy (top-k) strategies.
 * **Robustness**: Synthetic Noisy Graphs (LoCoMo context + **[deferred] irrelevant edges**) evaluated with all strategies.

### 2. Statistical Analysis Plan
*   **Hypothesis Testing**: Paired t-test (or Wilcoxon signed-rank if normality assumption fails) comparing Accuracy distributions of Heuristics vs. Baseline.
    *   *Null Hypothesis*: No difference in accuracy between heuristic and baseline.
    *   *Alternative*: Heuristic accuracy is significantly lower.
*   **Correlation**: **Point-Biserial correlation** (or Logistic Regression) between `nodes_visited` (depth) and `accuracy` (binary). Pearson correlation is avoided as it assumes linearity and normality of residuals which binary data violates.
*   **Threshold Detection**: Identify the specific `nodes_visited` count where accuracy drops below 95% of the baseline **by binning tasks by node count and finding the first bin with <95% mean accuracy** (if statistically significant, p < 0.05).
*   **Multiplicity Correction**: Apply Benjamini-Hochberg procedure if multiple comparisons are made across different noise levels or thresholds.
*   **Power Analysis**: Post-hoc power analysis will be calculated given the fixed sample size of LoCoMo.

## Decision/Rationale

*   **Why `llama-cpp-python`?** It supports 4-bit quantization on CPU without CUDA dependencies, satisfying Constitution Principle VI and the GitHub Actions free-tier constraints. `bitsandbytes` is excluded as it requires CUDA.
*   **Why Synthetic Noisy Graphs?** No verified external dataset for "noisy memory graphs" exists. Generating them programmatically ensures we can test the specific robustness requirement (Principle VII) without relying on unverified sources.
*   **Why Paired Tests?** Since the same tasks are run under different strategies, a paired test controls for task difficulty variance, increasing statistical power.
*   **Why 95% Threshold?** This is the specific success criterion (SC-004) for determining the "inflection point" of heuristic utility.
*   **Why Point-Biserial?** Accuracy is binary (0/1); Point-Biserial is the appropriate correlation coefficient for a continuous variable (depth) and a binary variable (success).

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Timeouts on Complex Tasks** | High (Data loss) | Enforce a configurable timeout per task; log failure; proceed to next. |
| **Model Out of Memory** | High (Crash) | Use smallest viable quantized model; stream tokens; monitor RAM. |
| **Graph Construction Failure** | Medium (Data gap) | Validate graph structure before traversal; handle degenerate (0-edge) cases explicitly. |
| **Statistical Power Low** | Medium (Inconclusive) | Acknowledge limitation in report; rely on effect size and confidence intervals. |

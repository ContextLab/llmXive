# Research: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Summary

This research investigates the efficiency-accuracy trade-off in LLM agent memory reconstruction. We compare a "Full" active reconstruction baseline against "Lazy" and "Greedy" heuristic traversals on the LoCoMo benchmark. We also evaluate robustness by injecting synthetic noise (via edge **replacement**) into the memory graphs.

## Dataset Strategy

We utilize the **LoCoMo** benchmark for multi-hop reasoning tasks. The dataset is publicly available on HuggingFace.

| Dataset | Source URL | Usage | Verification |
|---------|------------|-------|--------------|
| LoCoMo (MC10) | ` | Primary benchmark for tasks (questions, context, ground truth). | Verified via HuggingFace `datasets` loader. |

**Data Loading Strategy**:
- Use `datasets.load_dataset("json", data_files=URL, split="train")` for LoCoMo.
- **Graph Derivation**: The LoCoMo dataset provides text context, not explicit graph edges. We will generate the graph structure from the context text using the `graph_utils.py` module (NER/Rule-based extraction), as per FR-001. This derivation is a primary dependency.
- **Noise Injection**: As per FR-001, we will **replace** a small, reproducible proportion of edges with random edges. This is distinct from adding edges; it maintains graph size while perturbing topology.
- **Streaming**: If the LoCoMo dataset is large, we will stream it using `datasets.load_dataset(..., streaming=True)` to avoid loading the full dataset into RAM.

## Methodology

### 1. Baseline Execution (Full Strategy)
- **Algorithm**: Traverse the entire relevant subgraph for every query.
- **Metrics**: `accuracy` (vs ground truth), `nodes_visited`, `inference_time_seconds`, `token_count`.
- **Environment**: CPU-only. Timeout enforced at 30 minutes per task (FR-007) using `signal.alarm` (Unix) or `subprocess` timeout. On timeout, log `status='timeout'` and proceed.

### 2. Heuristic Strategies
- **Lazy**: Defers edge expansion until an evidence threshold (confidence > 0.7) is met. Logs the specific threshold used (`evidence_threshold`) in the output CSV.
- **Greedy**: Selects only top-k confidence edges.
- **Comparison**: Measure reduction in `nodes_visited` and `latency` against the Full baseline. Measure `accuracy` delta.

### 3. Statistical Analysis
- **Hypothesis Testing**: **McNemar's test** (primary) for paired binary accuracy outcomes. A paired t-test or Wilcoxon signed-rank test is used as a secondary check for proportions.
- **Correlation**: Point-Biserial correlation between `nodes_visited` and success rate.
- **Threshold Analysis (Inflection Point)**:
 - Bin tasks by `nodes_visited` into equal-width bins.
 - **Merging Rule**: Merge adjacent bins only if the resulting bin contains fewer than 3 tasks (n < 3), ensuring the n ≥ 3 constraint is always met.
 - Identify the first bin where mean accuracy < 95% of the baseline (if p < 0.05).
 - **Covariate Control**: Include **critical path length** as a covariate in a segmented regression analysis to control for the specific nodes visited vs. count, addressing the potential spurious correlation of node count alone.
- **Robustness**: Repeat analysis on the **Noisy** graph dataset (noise injection via edge **replacement**).

### 4. Robustness & Edge Cases
- **Degenerate Graph Detection**:
 - If `len(edges) == 0` or `len(nodes) == 1`, set `status='degenerate'`.
 - If target is unreachable in Lazy/Greedy, set `status='unresolved'`.
 - These statuses are explicitly written to the output CSV.
- **Timeouts**: Log "TIMEOUT" status for tasks exceeding 30 mins.

### 5. Ground Truth Independence
- Accuracy is measured by comparing the **LLM's generated answer** (based on the reconstructed context) against the **fixed LoCoMo ground truth label**.
- The ground truth is independent of the traversal logic or confidence scores, preventing tautological correlations.

### 6. Limitations
- **Graph Construction Quality**: Acknowledged that the accuracy metric is a composite of **graph construction quality** (derived from text) and **traversal efficiency**. The study cannot fully isolate the traversal effect without explicit graph inputs.
- **Power**: Given the fixed size of the LoCoMo benchmark subset, a post-hoc power analysis will be included.

## Compute Feasibility & Rationale

- **CPU-First**: The graph traversal algorithms and statistical tests are purely algorithmic and run efficiently on CPU.
- **LLM Inference**: If the "reconstruction" step requires generating an answer or scoring evidence, we will use a quantized small model (e.g., Llama-3-8B-4bit via `llama-cpp-python`) running on CPU. This fits within the RAM limit for a single instance.
- **No GPU Required**: No transformer training or large-batch fine-tuning is needed. The "GPU escape hatch" is not required for this specific study.
- **Streaming**: If the LoCoMo dataset is large, we will stream it using `datasets.load_dataset(..., streaming=True)` to avoid loading the full dataset into RAM.

## Decision/Rationale

- **Why LoCoMo?**: It is a verified, open benchmark for multi-hop reasoning, directly relevant to the "memory reconstruction" hypothesis.
- **Why Edge Replacement?**: Replacing edges (vs. adding) preserves the graph's density and node count, isolating the effect of *incorrect* connections rather than *noise volume*. This aligns with FR-001.
- **Why Point-Biserial?**: The outcome (success/failure) is binary, and the predictor (`nodes_visited`) is continuous. Point-biserial is the correct correlation metric.
- **Why Bin Size n≥3?**: To ensure statistical stability in the threshold analysis (SC-004).
- **Why McNemar's Test?**: It is the statistically sound test for paired binary data, superior to t-tests on binary outcomes.

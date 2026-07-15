# Research: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Executive Summary

This research investigates the trade-off between computational efficiency and reasoning accuracy in LLM agents using graph-based memory. Specifically, it compares "Full" active reconstruction against "Lazy" and "Greedy" traversal heuristics on the LoCoMo benchmark. The study aims to validate whether heuristic strategies can reduce node visitation by 40-50% while maintaining accuracy within 2% of the baseline, even in the presence of semantic noise. The study explicitly acknowledges that the "Full" strategy is a noisy baseline (not a ground-truth oracle) and focuses on relative efficiency gains.

## Dataset Strategy

### Primary Dataset: LoCoMo Benchmark
- **Source**: https://huggingface.co/datasets/Aman279/Locomo/resolve/main/locomo.csv
- **Verification**: URL verified via HuggingFace `datasets` library.
- **Usage**: Provides multi-hop reasoning queries (question, context, ground-truth answer).
- **Access**: Direct download via `datasets.load_dataset("csv", data_files="...")`.
- **Note**: The LoCoMo dataset contains the necessary text-based queries. The "graph" structure is derived synthetically from the context or simulated as per the "Memory is Reconstructed" methodology (nodes = facts, edges = relationships). The plan relies on generating this graph structure programmatically to ensure reproducibility and control over noise levels (FR-001).

### Graph Construction Protocol
To address construct validity (methodology-e0c1ef72), the base graph is constructed as follows:
1. **Entity Extraction**: Use `spaCy` NER to identify entities (nodes) in the `context` field.
2. **Relation Extraction**: Use rule-based matching (e.g., co-occurrence within a sentence window, dependency parsing) to form initial edges.
3. **Graph Formation**: Nodes are entities; edges are relationships derived from the text. This ensures the base graph is semantically valid.
4. **Noise Injection**: Instead of purely random edges (which destroy topology), we inject "distractor edges"—edges that connect nodes but represent semantically plausible yet incorrect relationships (e.g., connecting two entities that appear in the same sentence but have no causal link). This tests robustness to *semantic noise* without destroying the graph's topological validity.

### Synthetic Noisy Graph Dataset
- **Generation**: Not a pre-existing dataset. Generated programmatically from the LoCoMo context using `networkx` and `spaCy`.
- **Method**: 
  1. Extract entities and relations from context to form a base graph.
  2. Inject noise by replacing a small, reproducible proportion of edges with "distractor edges" (controlled by seed).
  3. Validate connectivity and handle disconnected components.
- **Reproducibility**: Fixed random seed ensures identical graph generation across runs (Constitution Principle I).

### Excluded/Unavailable Datasets
- **MRAgent**: No verified source found (per verified datasets list). The plan does **not** rely on an external MRAgent repository for data or code. Instead, the "Full" baseline algorithm is implemented from scratch based on the spec's definition of "active reconstruction."
- **Other LoCoMo files**: The `.h5` and `.parquet` files listed in the verified datasets (e.g., `quadruped_locomotion`, `imnet1k`) are unrelated to the text-based reasoning tasks in LoCoMo and are **not** used. Only the `locomo.csv` is relevant.

## Methodology

### Experimental Design
- **Independent Variables**: 
  - Traversal Strategy (Full, Lazy, Greedy).
  - Graph Noise Level (None, Low, High - for robustness check).
  - Evidence Threshold (Lazy strategy only: 0.5, 0.7, 0.9).
- **Dependent Variables**: 
  - Accuracy (0.0–1.0, alignment with ground truth).
  - Nodes Visited (integer count).
  - Latency (seconds).
- **Control**: Fixed random seed, fixed model (quantized LLM), fixed task subset.

### Task Difficulty Stratification
To address the confound of task difficulty (methodology-adf57f43), the analysis now controls for task difficulty:
1. **Stratification**: Tasks are grouped into 'Easy', 'Medium', and 'Hard' bins based on baseline performance (Full strategy accuracy).
2. **Analysis**: Correlations and significance tests are performed within these strata or using a mixed-effects model where 'task_id' is a random effect.
3. **Reporting**: Results are reported both aggregated and stratified to ensure that efficiency gains are not driven by task difficulty.

### Algorithm Implementation
1. **Full Strategy (Baseline)**: Traverses all reachable nodes in the relevant subgraph. Logs all nodes and edges.
2. **Lazy Strategy**: Defers edge expansion until a confidence threshold (e.g., >0.7) is met. Logs reduced node count.
3. **Greedy Strategy**: Selects top-k edges based on confidence scores. Logs reduced node count.

### Statistical Analysis Plan
- **Primary Test**: Paired t-test or Wilcoxon signed-rank test (if normality assumption fails) comparing accuracy distributions of Heuristic vs. Baseline (FR-005).
- **Correlation**: Point-Biserial correlation between `nodes_visited` (continuous) and `success` (binary) (FR-006).
  - **Interpretation**: This correlation is a descriptive statistic of the *strategy's* pruning behavior (as noted in scientific_soundness-4d552d54) and will not be interpreted as a causal 'reasoning threshold'.
- **Threshold Analysis (SC-004)**: 
  - Bin tasks by `nodes_visited` count.
  - Constraint: Each bin must contain at least 3 tasks (n ≥ 3).
  - Identify the first bin where mean accuracy < 95% of baseline.
  - If no such bin exists, report overall trend without a specific threshold.
  - **Supplementary**: Perform a 'Threshold Sensitivity Analysis' (Knee of the Curve) to identify strategy-specific efficiency thresholds.
- **Power & Multiplicity**: 
 - **Power Analysis**: Calculate Minimum Detectable Effect Size (MDES) for the given sample size (N=100-500) at 80% power and alpha=0.05. If the MDES is too large to detect the hypothesized [deferred] delta, the study will focus on 'statistically significant efficiency gains' rather than 'accuracy preservation' for small deltas.
  - **Multiplicity**: If multiple thresholds are tested, a Bonferroni correction will be applied to the significance level (α) to maintain family-wise error rate.

### Compute Feasibility
- **Environment**: CPU-only (GitHub Actions Free Tier: 2 cores, ~7GB RAM).
- **Model**: Quantized LLM (e.g., Llama-3-8B 4-bit) via `llama-cpp-python`.
- **Strategy**: 
  - Use `llama-cpp-python` with `n_gpu_layers=0` to force CPU execution.
  - If memory constraints arise, reduce context window or use a smaller model (e.g., with fewer parameters) as a faithful CPU form.
  - **No GPU**: The plan does not assume GPU availability. The "GPU escape hatch" is not triggered as the method (quantized inference) is CPU-tractable.
- **Timeout**: Hard limit of 30 minutes per task (FR-007) enforced via Python `signal` (Unix) or `threading` (cross-platform fallback).

## Decision Rationale

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| **LoCoMo CSV only** | Directly supports text-based reasoning tasks. Verified URL. | Other LoCoMo files (`.h5`, `.parquet`) are for robotics/simulation, not text reasoning. |
| **Synthetic Graph Generation (Distractor Edges)** | Ensures reproducibility and control over noise (Constitution VII). Uses 'distractor edges' to preserve semantic topology while testing robustness. | Using purely random edges would destroy graph topology and invalidate the memory graph construct. Using an external graph dataset would introduce unknown noise patterns. |
| **CPU-Only Quantized Inference** | Aligns with Constitution VI (edge constraints) and GitHub Actions limits. | GPU-based inference is not available in the target CI environment. |
| **Wilcoxon/T-test** | Standard for paired comparison of accuracy. Robust to non-normality. | Non-parametric tests preferred if normality fails (checked post-hoc). |
| **Binning for Threshold (n≥3)** | Ensures statistical stability of the inflection point estimate (SC-004). | Bins with n<1 are unstable and prone to noise. |
| **Task Difficulty Stratification** | Controls for inherent task difficulty to isolate strategy effects. | Aggregated analysis confounds strategy efficiency with task difficulty. |

## Limitations & Assumptions

- **Observational Nature**: The study compares algorithmic strategies on a fixed dataset. Claims are associational, not causal (Assumption).
- **Benchmark Validity**: Accuracy is measured against LoCoMo ground truth, which may contain ambiguities. No external validation of benchmark quality is performed.
- **Noisy Baseline**: The "Full" strategy is a noisy baseline (not a ground-truth oracle). Accuracy is 'alignment with LoCoMo labels' and the study measures 'retrieval efficiency impact on model performance' rather than 'reasoning stability' in an absolute sense (scientific_soundness-e1c1260f).
- **Power Limitation**: Sample size is fixed by the LoCoMo subset. Post-hoc power analysis will be reported. If MDES is too large, the hypothesis is reframed.
- **Model Constraints**: Quantized models may have lower accuracy than full-precision models, but this is consistent across all strategies, preserving comparative validity.
- **Causal Interpretation Warning**: The Point-Biserial correlation is a descriptive statistic of the strategy's pruning behavior and will not be interpreted as a causal 'reasoning threshold' (scientific_soundness-4d552d54).
- **Noise Definition**: Noise is defined as 'distractor edges' (semantically plausible but incorrect) rather than purely random edges to preserve graph topology (scientific_soundness-80217f74).
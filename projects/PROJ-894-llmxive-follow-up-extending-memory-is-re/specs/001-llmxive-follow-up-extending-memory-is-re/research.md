# Research: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Research Question

Do heuristic traversal strategies ("Lazy", "Greedy") in graph-based memory reconstruction for LLM agents achieve a significant reduction in computational cost (nodes visited) while maintaining reasoning accuracy within a [deferred] delta of the "Full" baseline, and at what task complexity (measured by baseline nodes visited) does accuracy degrade significantly?

## Dataset Strategy

The project relies on the LoCoMo benchmark for the primary evaluation of multi-hop reasoning tasks. The official HuggingFace `datasets` loader is used to ensure proper handling of multi-modal context (video/audio) and extraction of text facts.

| Dataset | Role | Source URL (Verified) | Access Method | Notes |
| :--- | :--- | :--- | :--- :--- |
| **LoCoMo** | Primary Benchmark (Tasks, Context, Ground Truth) | `https://huggingface.co/datasets/Aman279/Locomo` | HuggingFace `datasets.load_dataset("Aman279/Locomo", split="test")` | Official loader handles multi-modal context extraction. Contains multi-hop reasoning queries. |
| **MixSub** | Not Used | N/A | N/A | Removed as a source for graph generation. Synthetic graphs are generated programmatically from LoCoMo text. |
| **MRAgent** | Reference Framework | NO verified source found | N/A | The MRAgent framework is referenced in the spec as the conceptual baseline, but no URL is available for direct download. The implementation will re-implement the "Full" strategy logic based on the paper's description rather than cloning a repo. |

**Data Availability & Feasibility**:
- **LoCoMo**: The official HuggingFace loader is feasible on a CPU-only CI runner. The dataset size is expected to be manageable.
- **Synthetic Graphs**: The project implements a **synthetic noise injection** step (FR-Edge Case) where random edges are added *only to the relevant subgraph* (nodes reachable within 3 hops of the query) to simulate retrieval noise without confounding with irrelevant global paths.
- **MRAgent**: Since no verified URL exists, the "Full" baseline will be implemented from scratch based on the "Active Reconstruction" description in the spec and the original paper's logic, ensuring the code is self-contained.

## Methodology

### 1. Data Ingestion & Graph Construction
- **Step 1.1**: Download LoCoMo dataset using `datasets.load_dataset("Aman279/Locomo", split="test")` and extract text context (ignoring video/audio frames for graph construction, but preserving them if needed for LLM context).
- **Step 1.2**: For each task, construct a directed `Memory Graph` where nodes represent facts (sentences/paragraphs from context). **Edge Formation Rule**: Edges are created between nodes if the cosine similarity of their `all-MiniLM-L6-v2` embeddings exceeds a threshold of **0.75**. This metric and threshold are deterministic and reproducible.
- **Step 1.3**: Generate a **Noisy Variant** for robustness testing by injecting random edges at a fixed density (e.g., 5-10% of total possible edges) **only within the relevant subgraph** (nodes reachable within 3 hops of the query node) to avoid confounding with irrelevant global paths.
- **Step 1.4 (Graph Validation)**: Before traversal, verify that the ground-truth reasoning path (if inferable from metadata) or a path of sufficient length exists in the constructed graph. If the graph is disconnected such that the answer is unreachable, flag the task as "invalid_graph" and exclude it from accuracy calculations.

### 2. Traversal Execution (CPU-First)
- **Step 2.1 (Baseline)**: Execute the "Full" active reconstruction strategy. This traverses the entire relevant subgraph for the query.
- **Step 2.2 (Heuristics)**: Execute "Lazy" and "Greedy" strategies on the same graphs with the following explicit decision logic:
  - **Lazy**: Expand a node only if `confidence_score > 0.7` AND `evidence_count < 3`.
  - **Greedy**: Select only the **top-3** edges by confidence score at each step.
  - **Sensitivity Analysis**: These thresholds (0.7, 3, 3) will be swept in a sensitivity analysis (e.g., {0.5, 0.7, 0.9} for confidence) to ensure robustness.
- **Step 2.3 (Constraints)**: Enforce a timeout per task. Log "TIMEOUT" if exceeded. Handle disconnected graphs by flagging as "unresolved" or defaulting to full traversal if the path is validated in Step 1.4.
- **Step 2.4 (Metrics)**: Log `task_id`, `strategy`, `accuracy` (1 if answer matches ground truth, 0 otherwise), `nodes_visited`, `inference_time_seconds`, and `token_count` (if LLM is used).

### 3. Statistical Analysis
- **Step 3.1**: Calculate **Percentage Reduction** in nodes visited for heuristics vs. baseline (SC-001).
- **Step 3.2**: Calculate **Accuracy Delta** (heuristic - baseline) (SC-002).
- **Step 3.3**: Perform **Paired t-test** (or Wilcoxon signed-rank if normality assumptions fail) on accuracy distributions (FR-005).
- **Step 3.4 (Reframed Correlation)**: Compute **Point-Biserial Correlation** ($r_{pb}$) between `nodes_visited` and `success` (binary) **using only the Baseline strategy results**. This treats the baseline traversal depth as a proxy for task complexity, avoiding the tautology of correlating a heuristic's cost with its own success.
  - *Note: The spec (User Story 3) implies a general calculation across the dataset. This plan restricts it to the Baseline to avoid the tautological confound where the predictor (nodes_visited) is a direct output of the algorithm determining the target (success). This is flagged as a spec-root cause for kickback.*
- **Step 3.5 (Reframed Inflection Point)**: Replace fixed binning with **LOESS smoothing** to generate an "Accuracy-Depth Trade-off Curve" for the Baseline strategy. Identify the "complexity threshold" where the smoothed curve drops below [deferred] of the global mean accuracy. Report this threshold only if the trend is statistically significant (p < 0.05). If N < 30, report a power limitation and omit the threshold.
  - *Note: The spec (User Story 3) mandates binning into groups of 5. This plan uses LOESS smoothing to avoid high variance in small samples, which is statistically more sound. This is flagged as a spec-root cause for kickback.*
- **Step 3.6 (Robustness Test)**: Perform a **paired t-test or Wilcoxon signed-rank test** comparing the "Lazy" heuristic accuracy against the "Full" baseline accuracy specifically on the **Noisy Variant** dataset to satisfy Constitution Principle VII.

## Decision Rationale: Compute Strategy

- **CPU-First**: The entire pipeline (graph construction, traversal, statistical analysis) is computationally lightweight and can run entirely on CPU. The "inference" step (if an LLM is used for node scoring) will use a small, quantized model (e.g., `llama.cpp` in 4-bit mode) or a heuristic scoring function if the dataset provides explicit scores. This ensures the project fits within the GitHub Actions free-tier (2 CPU, 7GB RAM).
- **No GPU Required**: The project does not involve training large models or running diffusion models. The "GPU escape hatch" is not needed.
- **Streaming**: The LoCoMo dataset is small enough to load entirely into memory. No streaming is required, but the code will be written to handle datasets that might be larger in the future.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: If multiple heuristics are tested against the baseline, a correction (e.g., Bonferroni) will be applied to the p-values to control the family-wise error rate.
- **Power Limitation**: The study acknowledges the fixed sample size of the LoCoMo benchmark. A post-hoc power analysis will be included in the final report. If N < 30, the LOESS smoothing will be noted as exploratory.
- **Causal Framing**: Since the study compares algorithmic strategies on a fixed dataset without random assignment of agents, all findings regarding the relationship between traversal depth and accuracy will be framed as **associational**, not causal.
- **Measurement Validity**: Accuracy is measured against the benchmark's ground truth. We acknowledge the potential for hallucinated ground truths but treat them as the standard for this study.
- **Collinearity**: If `nodes_visited` is highly correlated with `inference_time`, this will be reported descriptively. Independent effects will not be claimed for these derived metrics.

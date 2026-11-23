# Research: llmXive follow-up: extending "ABot-AgentOS" with Symbolic Memory

## Research Question

What is the trade-off between computational efficiency (latency, RAM) and task success rate when replacing the neural embedding-based memory of ABot-AgentOS with a purely symbolic, CPU-tractable knowledge base for long-horizon robotic navigation?

## Methodology

### Experimental Design

This is a **comparative, associational study**. We compare two system architectures (Symbolic vs. Neural) executing the same set of navigation tasks.
-   **Independent Variables**:
    1.  **Tokenization Granularity**: Coarse (e.g., "room", "object") vs. Fine (e.g., "red_cup_kitchen_counter").
    2.  **Predicate Expressiveness**: Spatial-only (e.g., `near`, `on`) vs. Spatial+Temporal (e.g., `before`, `after`).
    3.  **System Architecture**: Symbolic (CPU) vs. Neural (GPU/CPU).
-   **Dependent Variables**:
    1.  **Task Success Rate**: Binary (1=success, 0=failure) against ground truth.
    2.  **Query Latency**: Mean and median time (ms) per query on CPU.
    3.  **Memory Footprint**: Peak RAM (MB) during graph traversal.
-   **Control Variables**:
    -   Task set (traces from ALFWorld).
    -   Random seeds for any stochastic elements (pinned in `config.py`).
    -   Hardware environment (CPU-only for symbolic; GPU for neural baseline).

### Data Strategy

**Dataset**: **ALFWorld** (Embodied World Benchmark).
**Source URL**: `https://huggingface.co/datasets/alfworld/alfworld` (Verified).
**Loading Method**: `datasets.load_dataset("alfworld/alfworld", split="train")`.
**Variable Coverage Check**:
-   **Required**: Dialogue, spatial coordinates (x, y, z), temporal sequences, task outcome (success/failure).
-   **Dynamic Design Pruning**:
    -   **Check**: The data loader verifies the presence of `spatial_coords` and `temporal_seq`.
    -   **If Missing**: If `spatial_coords` are absent, the 'spatial+temporal' condition is **automatically pruned** from the experimental design. The study proceeds with the 'spatial-only' condition only. A warning is logged: "Spatial coordinates missing; pruning 'spatial+temporal' condition. Study proceeds with spatial-only predicates."
    -   **If Missing (Critical)**: If `dialogue` or `outcome` are missing, the pipeline halts with a fatal error, as these are essential for the core research question.

**Sampling**:
-   A stratified random sample of traces is drawn using a fixed seed.
-   **Adaptive Sampling for Power**: If the initial run shows high agreement between systems (low discordant pairs), the sampling strategy will oversample failure cases to ensure a minimum of 50 discordant pairs per condition, as required for the Mixed Effects Model.

### Statistical Analysis

1.  **Success Rate Comparison**:
    -   **Method**: **Logistic Mixed Effects Model (GLMM)**.
    -   **Rationale**: The study involves a 2x2 factorial sweep (Granularity x Expressiveness) with repeated measures (same tasks across conditions). GLMM accounts for the binary outcome (success/failure), models the fixed effects of architecture, granularity, and expressiveness, and includes task-level random effects to handle the repeated measures structure. This replaces the invalid McNemar's test for multi-condition sweeps.
    -   **Model Formula**: `Success ~ Architecture * Granularity * Expressiveness + (1 | Task_ID)`
    -   **Significance**: P-values for fixed effects (architecture, interactions) are derived from likelihood ratio tests or Wald Z-tests.
    -   **Multiple Comparisons**: The GLMM inherently handles the factorial structure. Post-hoc pairwise comparisons (if needed) will use Tukey's HSD with correction.

2.  **Efficiency Metrics**:
    -   **Latency**: Mean and standard deviation reported. Paired t-tests or Wilcoxon signed-rank tests will be used for pairwise comparisons of latency distributions.
    -   **Memory**: Peak RAM reported. No statistical test required for "reduction" if the difference is deterministic and large (SC-002 target ≥ 80%).

3.  **Power Analysis**:
    -   The study targets a minimum of **50 discordant pairs** per condition to ensure sufficient power for the GLMM to detect a moderate effect size (Cohen's h ≈ 0.3) in success rates. If the initial sample yields fewer discordant pairs, the sampling strategy will be adjusted to oversample failure cases.

### Statistical Rigor & Assumptions

-   **Associational Framing**: As the study compares two architectures on the same observational dataset without random assignment of agents to architectures, claims are framed as **associational**.
-   **Baseline Execution**: The neural baseline (ABot-AgentOS v1.0) is **re-executed** on the exact same 500 traces to ensure the paired comparison is valid. Pre-computed embeddings are **not** used for success rate comparisons.
-   **Measurement Validity**: The frozen VLM mapping is assumed to be accurate. If the mapping error rate is high, the "discretization ambiguity" error category will capture this.
-   **Collinearity**: Token granularity and predicate expressiveness may be correlated. The GLMM will model this interaction explicitly.

## Dataset Strategy

| Dataset | Source URL (Verified) | Loading Method | Variable Coverage Check |
| :--- | :--- | :--- | :--- |
| **ALFWorld** | `https://huggingface.co/datasets/alfworld/alfworld` | `datasets.load_dataset("alfworld/alfworld")` | **Check**: Requires `dialogue`, `spatial_coords`, `temporal_seq`, `outcome`. If `spatial_coords` missing, prune 'spatial+temporal' condition. If `dialogue`/`outcome` missing, halt. |

## Compute Feasibility & Escape Hatch

-   **CPU-First**: The entire symbolic pipeline (graph construction, traversal, statistical analysis) is designed to run on the GitHub Actions free-tier (2 CPU, ~7 GB RAM).
    -   **Graph Construction**: $O(N)$ where $N$ is the number of traces. With 500 traces, memory usage is negligible (< 2 GB).
    -   **Query Execution**: Depth-first traversal on a DAG is $O(V+E)$. With a graph size of ~10k nodes/edges, latency is < 100 ms.
    -   **Statistics**: `statsmodels` GLMM is computationally tractable for N=500.
-   **GPU Escape Hatch**:
    -   **Baseline**: The neural baseline (ABot-AgentOS v1.0) requires GPU for embedding generation and execution.
    -   **Strategy**: The symbolic system runs on CPU. The neural baseline is **re-executed** on a Kaggle GPU (16 GB VRAM) via the execution stage's auto-offload mechanism. The results (CPU symbolic + GPU neural) are merged for the GLMM analysis.
    -   **No Fabrication**: The baseline is not mocked. It is run dynamically to ensure empirical validity.

## Risk Mitigation

-   **Data Unavailability**: ALFWorld is verified and accessible. If the download fails, the system uses a versioned, checksummed fallback artifact from `data/raw/`.
-   **High Discretization Error**: If the frozen VLM mapping fails > 10% of the time, the "discretization ambiguity" error rate will exceed the target. The sensitivity analysis will adjust the taxonomy granularity to mitigate this.
-   **Logical Inconsistency**: The graph construction module will detect cycles (contradictory spatial info) and flag them, ensuring the DAG property is maintained.
-   **Insufficient Discordant Pairs**: If the initial run yields too few discordant pairs, the adaptive sampling strategy will oversample failure cases to ensure statistical power.
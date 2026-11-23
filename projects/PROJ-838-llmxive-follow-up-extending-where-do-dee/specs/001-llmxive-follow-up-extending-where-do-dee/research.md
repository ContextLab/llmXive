# Research: 001-gene-regulation

## Overview

This research investigates whether early-stage topological signatures (connectivity and branching) in deep-research agent trajectories can predict final trajectory collapse. The study utilizes the TELBench dataset to extract Claim-Dependency Graphs from the first portion of reasoning spans, computes normalized metrics, and validates a threshold-based predictor against ground-truth labels.

## Dataset Strategy

### Verified Datasets
The project relies exclusively on the following verified sources, as mandated by the project constitution:

| Dataset Name | Description | Verified URL | Load Strategy |
| :--- | :--- | :--- | :--- |
| **TELBench** | Annotated deep-research trajectories with success/failure labels. | `https://huggingface.co/datasets/NJU-LINK/TELBench` | `datasets.load_dataset("NJU-LINK/TELBench")` |

*Note on Dataset Fit*: The TELBench dataset is confirmed to contain semantic spans and final success/failure labels, which are the required variables for this study. The dataset is public and accessible via the Hugging Face Hub.

### Data Availability & Feasibility
- **Open Access**: TELBench is hosted on Hugging Face, allowing programmatic download via the `datasets` library without requiring special credentials (beyond standard HF token if any).
- **Streaming**: To handle potential dataset size > 7 GB RAM, the `downloader.py` will use `streaming=True` to iterate over rows without loading the entire dataset into memory.
- **No Synthetic Data**: The plan uses real data only. If the dataset is inaccessible, the pipeline will fail explicitly rather than generating synthetic stand-ins.

## Methodological Rigor

### Statistical Approach
1. **Graph Construction**: Directed Acyclic Graphs (DAGs) built from the first `cutoff_depth` (default [deferred]) of spans. Edges inferred via textual co-reference and citation logic (e.g., "this claim", "as cited in").
2. **Metrics**:
   - **Average Branching Factor**: $\frac{\sum \text{out-degree}}{\text{node count}}$
   - **Global Connectivity**: $\frac{\text{edge count}}{\text{node count} \times (\text{node count} - 1)}$
   - **Linear Reasoning Index**: $\frac{\text{longest path length}}{\text{node count}}$ (to rule out valid linear reasoning).
   - *Normalization*: Both metrics are normalized by node count to distinguish structural density from text volume.
3. **Thresholding**: The prediction threshold is optimized on the training split by sweeping percentiles {10, 20, 30} to maximize F1-score, rather than fixed at 20th percentile a priori.
4. **Validation**: Precision, Recall, F1-score, and Confusion Matrix calculated against ground-truth labels on the held-out test set.
5. **Correlation**: Spearman/Pearson correlation and p-value calculated between connectivity and collapse.

### Rigor Checks
- **Multiple Comparisons**: Sensitivity analysis (SC-004) sweeps thresholds to control for arbitrary cutoff selection.
- **Sample Size/Power**: The study will report the number of trajectories used. If the dataset is small, the power limitation will be explicitly acknowledged in the final report.
- **Causal Inference**: The study is **observational**. Claims will be framed as *associational* (e.g., "low connectivity is associated with collapse") rather than causal. No randomization exists.
- **Measurement Validity**: The metrics (Branching, Connectivity) are standard graph theory measures. The "Claim-Dependency" inference is heuristic; validity will be checked via manual inspection of a sample (US-1).
- **Collinearity**: Branching and Connectivity are mathematically related. The plan will use PCA or regularized logistic regression to handle this collinearity, ensuring a robust composite construct.
- **Small Graph Stability**: For graphs with < 5 nodes, the metric will be flagged as 'unstable' and excluded from threshold derivation or handled via bootstrap resampling to ensure reliability.

### Compute Feasibility (CPU-First)
- **Method**: Graph construction and metric calculation are $O(N \cdot E)$ where $N$ is spans and $E$ is edges. For typical trajectories, this is trivial on CPU.
- **Escape Hatch**: No GPU required. The entire pipeline is designed for the GitHub Actions free-tier (2 CPU, 7 GB RAM).
- **Strategy**: Use `pandas` for tabular data and `networkx` for graph operations. Streaming ensures memory safety.

## Decision / Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-only execution** | The analysis involves graph theory on text, not deep learning. GPU is unnecessary and would waste resources. |
| **Hugging Face `datasets` library** | Provides robust streaming and caching, essential for large datasets on constrained CI runners. |
| **Optimized Threshold** | Replacing the fixed 20th percentile with an optimization sweep {10, 20, 30} ensures the threshold is data-driven and maximizes predictive power, avoiding arbitrary heuristics. |
| **Normalization by Node Count** | Prevents conflating "longer trajectories" with "better structure". Ensures metrics are density-based. |
| **Graceful Degradation** | Handles short trajectories (< cutoff) and zero-edge cases by returning 0.0, ensuring the pipeline does not crash on edge cases. |
| **Data Leakage Prevention** | Explicit separation of training (threshold derivation) and test (evaluation) sets prevents circular validation. |

## Limitations & Risks

- **Dataset Access**: If the dataset requires authentication not covered by the standard HF token, the pipeline may fail. Mitigation: Fallback to public mirror if available, or report access failure.
- **Heuristic Edge Inference**: Co-reference/citation logic may miss implicit dependencies. This is a known limitation of text-based graph construction.
- **Observational Nature**: Cannot claim causality between topology and collapse.
- **Power**: If the dataset is small, statistical significance may be low.
- **Metric Instability**: Small graphs may yield unstable metrics. Mitigation: Flag and exclude or use bootstrap.
- **Collinearity**: Branching and Connectivity are correlated. Mitigation: Use PCA/regularized regression.

## Data Leakage Prevention

The threshold derivation (Phase 3) is performed **only** on the `train_metrics.csv` (derived from the training split). The evaluation (Phase 4) is performed **only** on the `test_metrics.csv`. The test set labels are never used during threshold optimization or metric calculation, ensuring no data leakage.
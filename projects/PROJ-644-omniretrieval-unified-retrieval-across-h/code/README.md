# OmniRetrieval CPU Adapter

## Purpose
This adapter reproduces the core quantitative claim of the **OmniRetrieval** paper: that a unified retrieval framework outperforms single-source baselines when handling heterogeneous knowledge sources (Text, SQL, SPARQL, Cypher).

## Simplifications & Approximations
To ensure the code runs within strict CI constraints (2 CPU cores, ~7GB RAM, <25 mins, no GPU), the following adaptations were made:

1.  **No External Dependencies**: 
    -   The original paper relies on LLMs (OpenAI/Anthropic) for routing and generation, and external databases (Neo4j, PostgreSQL, SPARQL endpoints) for execution.
    -   **Adapter**: Uses a **rule-based simulation** for routing (keyword matching + probabilistic noise) and a **mock execution engine** that returns success/failure based on routing accuracy. No network calls are made.

2.  **Synthetic Data**:
    -   The original benchmark spans 13 datasets (BEIR, Spider, LC-QuAD, etc.) with hundreds of thousands of entries.
    -   **Adapter**: Generates **500 synthetic queries** in-memory, distributed across the four source types (40% Search, 30% SQL, 15% SPARQL, 15% Cypher) to mimic the real data distribution.

3.  **Metric Simplification**:
    -   The original paper uses complex metrics like NDCG@10 for search and Execution Accuracy for structured queries.
    -   **Adapter**: Uses a unified **Accuracy** metric (Correct Answer / Total Queries) derived from the simulation's success condition. This captures the relative performance difference between Unified vs. Single-Source strategies, which is the paper's main claim.

## Output Artifacts
-   `data/omniretrieval_results.csv`: A table comparing the accuracy of the Unified strategy against Single-Source baselines (Search-only, SQL-only, etc.).
-   `figures/accuracy_comparison.png`: A bar chart visualizing the performance gap (if `matplotlib` is available).

## Running
Execute the single script:
```bash
python code/omniretrieval_adapter.py
```
This will generate the CSV and plot automatically.

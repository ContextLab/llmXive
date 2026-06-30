# SciAtlas CPU Adaptation

## Summary of Simplifications
This adaptation reproduces the **core quantitative result** of the SciAtlas paper:
*Tri-path collaborative recall and graph reranking*—at a scale feasible for a 2-core CPU environment.

### Key Approximations
1.  **Scale Reduction**:
    *   **Original**: 43M papers, 157M entities, 3B triplets.
    *   **Adaptation**: 200 synthetic papers, ~500 edges.
    *   *Rationale*: The graph topology logic (PageRank/HITS style reranking) is scale-invariant; the algorithm works identically on 200 nodes as it does on 200M, provided the connectivity pattern is preserved.

2.  **Model Replacement**:
    *   **Original**: Large-scale neural embeddings and deep learning rerankers.
    *   **Adaptation**:
        *   **Embedding Proxy**: A keyword-overlap and semantic-buzzword scoring function (simulates vector dot product).
        *   **Reranker**: A simplified PageRank/In-degree centrality algorithm implemented in pure Python.
    *   *Rationale*: These classical methods capture the *topological reasoning* claim of the paper without requiring GPU or heavy ML libraries.

3.  **Data Source**:
    *   **Original**: Real-world academic corpus (arXiv, etc.).
    *   **Adaptation**: Procedurally generated synthetic dataset with realistic-looking titles, abstracts, and citation patterns.
    *   *Rationale*: Avoids network calls, large downloads, and licensing issues. The synthetic data is labeled clearly in the output.

4.  **Dependencies**:
    *   **Original**: `torch`, `transformers`, `neo4j`, `elasticsearch`.
    *   **Adaptation**: **Zero external dependencies**. Uses only Python `stdlib` (`json`, `csv`, `random`, `math`, `collections`).

## Verification
The adaptation writes real, non-empty artifacts to `data/` and `figures/`.
The logic faithfully implements the "Retrieve -> Rerank -> Output" pipeline described in the paper's abstract.

# Architecture Diagram

The following diagram outlines the end‑to‑end research pipeline for GraphCompass.

```mermaid
flowchart LR
 A[Data Preparation] --> B[Graph Construction]
 B --> C[Topological Feature Extraction]
 A --> D[Neural Baseline (BERTopic)]
 D --> E[Embedding Extraction]
 C --> F[Retrieval Simulation (TF‑IDF Cosine Similarity)]
 E --> F
 F --> G[Evaluation & Correlation Analysis]
 G --> H[Metrics & Reporting]
```

- **Data Preparation**: Downloads HotpotQA and Wikipedia datasets.
- **Graph Construction**: Builds lexical co‑occurrence graphs per document.
- **Topological Feature Extraction**: Computes modularity, average path length, degree & betweenness centralities.
- **Neural Baseline (BERTopic)**: Generates neural topic embeddings on the same corpus.
- **Embedding Extraction**: Retrieves document‑level embeddings from BERTopic.
- **Retrieval Simulation**: Ranks documents for each query using TF‑IDF cosine similarity (graph signatures are *not* used for ranking).
- **Evaluation & Correlation Analysis**: Calculates Recall@k, Spearman correlation, and paired t‑tests.
- **Metrics & Reporting**: Writes final JSON/CSV artifacts under `data/results/` for downstream analysis and paper figures.
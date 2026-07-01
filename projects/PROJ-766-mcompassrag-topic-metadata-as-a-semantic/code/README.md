# MCompassRAG Adaptation: "CompassLite"

## Goal
Reproduce the core quantitative claim of **MCompassRAG**: that enriching chunk representations with **topic metadata** improves retrieval precision (measured by **Hit Rate@K**) compared to a standard dense baseline, specifically in a "noisy" retrieval setting.

## Simplifications & Approximations
To fit the CPU constraints (2 cores, ~7GB RAM) while maintaining scientific validity:
1.  **Dataset**: Replaced the large heterogeneous corpus with a **small, real sample** (100 chunks) from the `20newsgroups` dataset (a standard NLP benchmark). This simulates the "heterogeneous" nature without the scale.
2.  **Embeddings**: Replaced the heavy `Qwen3-Embedding-4B` and LLM distillation pipeline with **Sentence-BERT (`all-MiniLM-L6-v2`)**. This is a standard, lightweight, CPU-tractable embedding model that produces the necessary vector space for the experiment.
3.  **Topic Model**: Replaced the complex CEMTM/CWTM training with a **sklearn `LatentDirichletAllocation` (LDA)** on TF-IDF vectors. This generates the "topic metadata" (topic distributions per chunk) required for the Compass mechanism.
4.  **Retriever Logic**:
    *   **Baseline**: Standard Cosine Similarity on raw chunk embeddings.
    *   **MCompass (Ours)**: A simplified "Compass Score" = `Cosine(Query, Chunk) + λ * Cosine(Query_Topic, Chunk_Topics)`. We simulate the "Topic Query" by averaging the topic distributions of the top-K baseline results (a lightweight proxy for the "expanded query" in the paper).
5.  **Scale**: 100 chunks, 20 queries. This runs in < 2 minutes on CPU.

## Metrics
*   **Hit Rate@5**: Fraction of queries where the ground-truth relevant chunk appears in the top 5 results.
*   **Mean Reciprocal Rank (MRR)**: Average of `1/rank` for the first relevant hit.

## Artifacts
*   `data/results.csv`: Per-query metrics and final aggregated scores.
*   `figures/comparison.png`: Bar chart comparing Baseline vs. Compass.

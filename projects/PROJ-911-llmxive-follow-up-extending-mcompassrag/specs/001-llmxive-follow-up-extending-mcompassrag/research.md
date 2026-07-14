# Research: GraphCompass: Topological Predictors of Semantic Coherence in CPU-Constrained RAG

## Executive Summary

This research validates the hypothesis that deterministic topological features of lexical co-occurrence graphs (GraphCompass) can predict semantic coherence in RAG systems with comparable precision to neural embeddings (BERTopic), but with significantly lower computational overhead. The study focuses on CPU-constrained environments (2 cores, 7GB RAM), targeting a Spearman correlation coefficient (r) > 0.6 between topological signatures (aggregated from retrieved documents) and retrieval precision (Recall@10).

**Methodological Correction**: To avoid circular validation, the retrieval ranking is performed using **TF-IDF Cosine Similarity** (standard IR). Topological signatures are extracted *only* from the *retrieved* documents to serve as the independent variable in the correlation analysis. This tests whether the *topology of retrieved documents* predicts *retrieval success*, without the topology itself being used to generate the rank.

## Dataset Strategy

### Verified Datasets
The following datasets are used, sourced strictly from verified URLs/programmatic loaders:

| Dataset Name | Purpose | Source / Loader | Verified Status |
| :--- | :--- | :--- | :--- |
| **HotpotQA** | Ground-truth queries and answers for retrieval simulation. | `datasets.load_dataset("hotpot_qa", "fullwiki")` | **Verified**: Available on HuggingFace Datasets. |
| **Wikipedia** (2023-10 dump) | Corpus for graph construction, neural baseline training, and retrieval pool. | `datasets.load_dataset("wikipedia", "20231001.en")` | **Verified**: Available on HuggingFace Datasets. |

*Note: The ArXiv corpus was rejected due to domain mismatch with HotpotQA. HotpotQA queries cover general knowledge (history, pop culture, etc.), while ArXiv is strictly academic. Using ArXiv would result in near-zero Recall@k for all methods, rendering the correlation analysis meaningless. Wikipedia is selected to ensure ground-truth answers exist in the retrieval pool.*

### Data Partitioning Strategy
To prevent data leakage (Constitution Principle VI):
1.  **Corpus Split**: The Wikipedia corpus is split into `train` and `test` sets.
2.  **Query Filtering**: HotpotQA queries are filtered to retain only those where the ground-truth answer string is found within the `test` corpus (exact substring match). This ensures valid Recall@k calculation and prevents "noise vs noise" correlation.
3.  **Graph Construction**: Graphs are built **only** on the `train` corpus to generate topic models and the Fixed Reference Vocabulary.
4.  **Retrieval Simulation**: Queries are matched against the `test` corpus graphs and embeddings.
5.  **Evaluation**: Metrics are computed on the filtered `test` set only.

## Methodology

### 1. Graph Construction (FR-001, FR-002)
- **Input**: Document text from the `train` corpus.
- **Preprocessing**: Tokenization, lowercasing, stop-word removal.
- **Term Filtering (Deterministic)**: 
 - **Fixed Reference Vocabulary**: A static list of the top [deferred] terms is pre-computed from the *entire* Wikipedia 20231001 dump and stored as `data/processed/fixed_vocab.json`.
  - TF-IDF scores are calculated relative to this *fixed* global distribution, not the sample subset. This ensures the "topological signature" is a property of the document's content relative to the global language, not the specific sample, satisfying the "Deterministic Topology" principle.
  - Retain a subset of top-ranked terms per document based on TF-IDF scores relative to this *fixed* vocabulary.
- **Graph Construction**:
  - **Sliding Window**: Size = 10.
  - **Edges**: Undirected edges between co-occurring terms within the window.
  - **Library**: `networkx`.
- **Feature Extraction**:
  - **Modularity**: Community detection (Louvain algorithm).
  - **Centrality**: Degree and Betweenness distributions (mean, std, max).
  - **Path Length**: Average shortest path (if graph is connected; else infinity or 0).
- **Edge Case Handling**: Documents with <5 unique terms are assigned zero vectors and logged (Edge Case 1).

### 2. Neural Baseline (FR-003)
- **Model**: BERTopic.
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (CPU-optimized, small footprint).
- **Configuration**:
  - `calculate_probabilities=False` (to save RAM).
  - `language="en"`.
  - **Critical**: `device="cpu"` enforced explicitly. No `load_in_8bit`.
- **Fallback**: If memory pressure is detected (>6GB usage), reduce `min_topic_size` or corpus sample size dynamically.

### 3. Retrieval Simulation (FR-004)
- **Query Processing**: HotpotQA queries are processed identically to documents (tokenization, TF-IDF for graph, embedding for neural).
- **Similarity Metrics**:
  - **Graph-Based Ranking**: **TF-IDF Cosine Similarity** between query TF-IDF vector and document TF-IDF vectors. (Topological signatures are **NOT** used for ranking).
  - **Neural Ranking**: Cosine similarity between query embedding and document topic embeddings.
- **Ranking**: Documents ranked by similarity score.
- **Metrics**: Recall@5 and Recall@10 calculated against HotpotQA ground-truth answers.
- **Query Filtering**: Queries where the ground-truth answer is not found in the `test` corpus are excluded from evaluation.

### 4. Statistical Analysis (FR-005, FR-006)
- **Correlation**: Spearman rank correlation between **aggregated topological features** and Recall@10 scores.
  - **Aggregation Logic (Unit of Analysis)**: For each query, calculate the topological metric (e.g., modularity) for each of the top-10 retrieved documents. Compute the **mean** of these values. This mean value is the query-level predictor.
  - **Hypothesis**: r > 0.6 between the mean topological metric (of retrieved docs) and the binary/continuous Recall@10 score.
  - This aligns the unit of analysis (query-level aggregated feature) with the unit of analysis for the outcome (query-level Recall@10 score).
- **Comparison**: Paired t-test comparing Recall@10 of Graph vs. Neural methods.
  - **Significance**: Alpha = 0.05.
- **Latency**: Wall-clock time measured for graph construction vs. BERTopic fitting.

## Statistical Rigor & Limitations

### Multiple Comparisons
- Since multiple topological metrics (modularity, centrality, path length) are tested against retrieval scores, a **Bonferroni correction** will be applied to the p-values to control family-wise error rate.

### Sample Size & Power
- **Sample Size**: N ≤ 360 documents.
- **Power Limitation**: With N=360, the power to detect a correlation of r=0.6 at alpha=0.05 is high (>0.99). However, if the true correlation is lower (e.g., r=0.3), power drops. The analysis will report the observed effect size and confidence intervals. If N is reduced due to memory constraints, the limitation will be explicitly stated in the results.

### Causal Inference
- This is an **observational** study of graph properties vs. retrieval performance. No causal claims (e.g., "changing modularity causes better retrieval") will be made. Claims are strictly associational.

### Measurement Validity
- **TF-IDF**: Standard information retrieval measure.
- **BERTopic**: Validated topic modeling approach; `all-MiniLM-L6-v2` is a standard, lightweight model for semantic similarity.
- **Graph Metrics**: Standard network science metrics (modularity, betweenness) with established theoretical backing in semantic coherence.

### Predictor Collinearity
- Topological metrics (e.g., degree and betweenness) are often correlated. The plan will report the correlation matrix of predictors. If high collinearity is found (>0.8), independent effects will not be claimed; instead, the composite "topological signature" will be treated as a single predictor block.

## Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Memory Management**:
  - Data loading: Chunked reading.
  - Graphs: Stored as adjacency lists (NetworkX) rather than dense matrices.
  - Embeddings: Batched processing.
- **Runtime**:
  - Graph construction: Target <60s/doc. 360 docs = 6 hours max.
  - BERTopic: Target <2 hours for N=360 on CPU.
  - Total pipeline: <6 hours.
- **GPU**: **Strictly prohibited**. All libraries selected have CPU wheels.

## Decision Rationale

- **Why BERTopic?** It provides a direct topic-level embedding comparable to the "topical" nature of graph modularity, unlike sentence embeddings which are local.
- **Why TF-IDF + Graph?** It is deterministic, CPU-efficient, and interpretable, aligning with the "deterministic topology" principle.
- **Why Spearman?** It is robust to non-linear monotonic relationships and outliers, which are common in graph metric distributions.
- **Why Wikipedia?** It aligns with the domain of HotpotQA, ensuring ground-truth answers are present for valid evaluation and avoiding the domain mismatch of ArXiv.
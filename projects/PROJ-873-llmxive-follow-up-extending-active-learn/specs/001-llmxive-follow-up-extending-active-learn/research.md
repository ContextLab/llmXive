# Research: Active Learners as Efficient PRP Rerankers (Redundancy Analysis)

## Objective
To quantify the efficiency loss (wasted LLM calls) caused by semantic redundancy in information retrieval datasets and validate that MinHash-LSH pre-clustering can recover this efficiency within strict CPU resource constraints.

## Dataset Strategy

### Primary Datasets
We utilize the **BEIR** (Benchmarking Information Retrieval) benchmark suite. The specific datasets selected are:
1.  **`nfcorpus`**: A non-parallel, multi-lingual corpus for ad-hoc retrieval.
2.  **`scifact`**: Scientific fact verification dataset.
3.  **`trec-covid`**: Used for validating redundancy distributions against real-world near-duplicates (FR-009).

### Verified Sources & Access
Per the project's "Verified datasets" block, we use the following HuggingFace sources for direct programmatic loading:
-   **BEIR (parquet)**:
    -   `nfcorpus`: `https://huggingface.co/datasets/BeIR/fiqa/resolve/main/corpus/corpus-00000-of-00001.parquet` (Note: `fiqa` is a BEIR dataset; `nfcorpus` is loaded via `beir` library which maps to its canonical source).
    -   `trec-covid`: `https://huggingface.co/datasets/BeIR/trec-covid/resolve/main/corpus/corpus-00000-of-00001.parquet`
    -   Qrels: `https://huggingface.co/datasets/BeIR/trec-covid-qrels/resolve/main/test.tsv`

**Loading Strategy**:
We will use the `beir` Python library (`GenericDataLoader`) to fetch these datasets. This library handles the download from the canonical URLs and provides a standardized dictionary format (`corpus`, `queries`, `qrels`).
-   **Streaming**: For large datasets, we will use `streaming=True` where supported, or load shards sequentially to stay within 7GB RAM.
-   **Synthetic Injection**: We do *not* rely on pre-existing near-duplicates for the primary experiment. Instead, we implement **FR-001** (Exact Copy Perturbation) to *inject* controlled redundancy into the unique `nfcorpus` and `scifact` subsets. This ensures we have ground-truth knowledge of which pairs are "wasted" (simulated duplicates) versus "informative."

### Dataset Variable Fit
-   **Required**: `document` (text), `query` (text), `relevance` (label).
-   **Available**: BEIR datasets provide all these fields.
-   **Fit**: Perfect. The `document` field allows for injection and embedding generation. The `relevance` field allows for NDCG@10 calculation.

## Methodology

### 1. Data Ingestion & Baseline Analysis (Phase 1)
-   Load `nfcorpus`, `scifact`, `trec-covid`.
-   **Scan for Natural Duplicates**: Compute cosine similarity for all pairs in `nfcorpus`/`scifact`. If < 5 clusters of size ≥3 are found (similarity > 0.95), trigger injection.
-   **Real-World Check**: Scan `trec-covid` for natural near-duplicates. If sparse, note as limitation for FR-009.

### 2. Redundancy Injection (Phase 2)
-   **Method**: **Exact Copy Perturbation**.
    1.  Select a random subset of documents (target: a representative proportion of the corpus).
    2.  Create exact duplicates.
    3.  Add 1-2% random noise (whitespace, character flips) to ensure cosine similarity > 0.95 but < 1.0 (avoiding perfect identity which might break some tokenizers).
    4.  Generate **Near-Duplicate Clusters**: Create 20+ clusters of 3–5 documents each.
-   **Threshold**: Cosine similarity > 0.95 identifies these as near-duplicates.
-   **Verification**: Count clusters. Abort if target not met.

### 3. Validation Proxy (Phase 2.4)
-   Sample 50 high-similarity pairs (similarity > 0.95).
-   Run the LLM on both documents in the pair.
-   **Goal**: Confirm that the LLM produces identical or near-identical outputs. This validates that "high similarity" implies "wasted call" (compute redundancy).

### 4. Baseline Active Learning (Phase 3)
-   **Baseline (No Filter)**: Run the active learning ranker on the **redundant dataset** (original + injected).
-   **Filter Run**: Run the active learning ranker on the **redundant dataset** with MinHash-LSH pre-clustering.
-   **Unique Baseline**: Run on `unique_subset` only for NDCG effectiveness check (not for efficiency comparison).

### 5. Wasted Call Detection (Phase 3)
-   **Definition**: A "wasted call" is a pairwise comparison between two documents with cosine similarity > 0.95.
-   **Metric**: Ratio of wasted calls to total calls.

### 6. Statistical Validation (Phase 4)
-   **Seeds**: 5 independent seeds (as per `2603.28921`).
-   **Test**: Wilcoxon signed-rank test comparing **Wasted Call Ratio** of (No Filter) vs (With Filter).
-   **Correction**: Bonferroni correction for multiple comparisons.
-   **Hypothesis**: Pre-clustering significantly reduces Wasted Call Ratio without degrading NDCG@10.
-   **Real-World Validation**: Compare synthetic redundancy distribution against `trec-covid` natural duplicates using KS-test.

## Compute Feasibility

### CPU-First Strategy
-   **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (CPU-optimized, ~20MB model).
-   **Clustering**: `datasketch` (pure Python/C, highly efficient).
-   **Ranking**: `llama-cpp-python` (TinyLlama Q4_K_M) running on CPU.
-   **Memory**:
    -   BEIR `nfcorpus` (~thousands of docs) + embeddings (~megabytes).
    -   MinHash signatures (moderate storage footprint).
    -   Total estimated peak: <3GB.
-   **Time**:
 - Embedding k docs: [deferred].
    -   MinHash LSH: ~ mins.
 - Active Learning (multiple seeds): [deferred].
    -   **Total**: Well within 6-hour limit.

### GPU Escape Hatch
-   **Not Required**: The methodology is designed to be fully CPU-tractable. No GPU is needed for TinyLlama inference on small batches or MinHash LSH.

## Decision/Rationale
-   **Exact Copy Perturbation vs. Synonym Replacement**: Synonym replacement fails to achieve cosine > 0.95 reliably. Exact copy with noise guarantees the threshold while preserving semantic meaning.
-   **MinHash-LSH**: Chosen over exact clustering (O(N^2)) because it is O(N) and fits within 7GB RAM, satisfying Principle VII.
-   **5 Seeds**: Required for statistical significance (FR-007) and to match the methodology of `2603.28921`.
-   **Statistical Test**: Comparing Wasted Call Ratio (No Filter) vs (With Filter) on the *same* population eliminates confounds of different document sets.

## Risks & Mitigations
-   **Risk**: Synthetic injection creates unrealistic text.
    -   **Mitigation**: Use conservative noise rates (1-2%) and validate via embedding similarity.
-   **Risk**: `trec-covid` lacks natural near-duplicates.
    -   **Mitigation**: Report limitation; rely on synthetic distribution as primary baseline.
-   **Risk**: MinHash threshold too aggressive, filtering out relevant docs.
    -   **Mitigation**: Tune `threshold` in `config.py` and report recall@k on the unique subset.
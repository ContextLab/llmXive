# Research: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

## Problem Statement

Active Pairwise Ranking Prompting (PRP) rankers rely on LLM calls to compare document pairs. When the retrieval candidate list contains near-duplicates, the ranker may waste budget comparing semantically identical items, degrading NDCG@10 relative to a unique baseline of the same size. This research quantifies that loss and validates a CPU-tractable MinHash-LSH pre-clustering solution.

## Dataset Strategy

### Primary Source: BEIR
The research utilizes the **BEIR** benchmark, specifically the `scifact`, `nfcorpus`, and `trec-covid` datasets.
- **BEIR scifact**: https://huggingface.co/datasets/BeIR/scifact/resolve/main/corpus/corpus-00000-of-00001.parquet
- **BEIR nfcorpus**: Fetched via the official `beir` Python library (which resolves to canonical HuggingFace sources). This dataset is required by FR-002 and will be processed identically to `scifact`.
- **BEIR trec-covid**: https://huggingface.co/datasets/BeIR/trec-covid/resolve/main/corpus/corpus-00000-of-00001.parquet

*Note: The `nfcorpus` dataset is explicitly included to satisfy FR-002. It will be processed via the standard BEIR library access patterns.*

### Synthetic Redundancy Generation
Per FR-002, the system will inject redundancy into the base datasets.
- **Method**: Synonym replacement (using **WordNet via NLTK**) and sentence shuffling to create 20 clusters of 3–5 near-duplicate items.
- **Validation**: The synthetic proxy will be validated against real-world near-duplicates from `trec-covid` (FR-009) by comparing the distribution of cosine similarities and lexical overlap.

### Embedding Model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Rationale**: CPU-tractable, widely validated for semantic similarity, and sufficient for distinguishing near-duplicates (similarity > 0.95) as per Assumptions in spec.

### MinHash-LSH Reference
- **Library**: `datasketch`
- **Rationale**: Efficient, CPU-only implementation of MinHash and LSH for near-duplicate detection.

## Methodology

### Phase 1: Data Preparation & Redundancy Injection
1. Download `scifact`, `nfcorpus`, and `trec-covid` from verified sources (BEIR library for `nfcorpus`).
2. Implement synthetic redundancy injection:
   - Select 20 random document clusters from the combined `scifact` and `nfcorpus` pools.
   - Apply synonym replacement (**NLTK WordNet**) and sentence shuffling to generate 3–5 variants per cluster.
   - Merge variants back into the candidate list, creating a "Redundant" dataset.
3. Create a "Unique Baseline" pool of N=100 unique documents. **Crucially, this pool is constructed from unique documents distinct from the redundant list** to ensure fair comparison of pool size (avoiding the confound of pool size vs. redundancy).
4. **Validation**: Compare the distribution of synthetic near-duplicates (cosine similarity, length, lexical overlap) against real near-duplicates from `trec-covid`. If the distributions diverge significantly, adjust the injection parameters (e.g., synonym frequency) before proceeding.

### Phase 2: Baseline Active Ranking (High Redundancy)
1. Run the baseline active ranker on the Redundant list with fixed budgets across a range of low, medium, and high values.
2. Log every comparison pair.
3. Compute cosine similarity for each pair using `all-MiniLM-L6-v2`.
4. **Operational Classification**: Classify pairs as "wasted" if similarity > 0.95. This classification is used for the main loop's budget accounting (Constitution Principle VI).
5. Calculate NDCG@10 against ground truth.
6. **Scientific Validation**: Run LLM consensus on a **stratified random sample from ALL calls** (stratified by similarity bins: <0.8, 0.8-0.95, >0.95) to estimate the ground truth accuracy of the "wasted" proxy.
   - **Ground Truth Definition**: A pair is "wasted" if the LLM returns "tie" or "low confidence" and the decision does not alter the relative order of the pair.
   - Calculate false positive/negative rates of the cosine proxy against this ground truth.

### Phase 3: Clustering-Aided Ranking
1. Apply MinHash-LSH (Jaccard threshold > 0.95) to the Redundant list to identify clusters.
2. **Representative Selection**: For each cluster, select the document with the **highest cosine similarity to the cluster centroid** as the representative. This prevents selection bias and ensures the representative is central to the cluster.
3. Filter the candidate list to one representative per cluster.
4. Run the active ranker on the filtered list with the same budgets, including a low budget setting.
5. Calculate NDCG@10 and wasted call ratio (should be near zero by design).
6. **Validation**: Compare results against the Unique Baseline (N=100) to measure recovery.

### Phase 4: Statistical Significance & Robustness
1. Repeat Phases & N with 5 random seeds.
2. Perform Wilcoxon signed-rank tests on NDCG@10 and wasted call ratios (FR-005).
3. Apply Bonferroni correction for multiple comparisons (FR-007).
4. Sweep MinHash-LSH threshold (e.g., 0.85, 0.90, 0.95, 0.99) to measure sensitivity (SC-005).
5. **Correlation Analysis**: Validate the correlation between Jaccard (MinHash) and Cosine (Embedding) similarity on a labeled subset. Store results in `CorrelationResult` entity and output to `data/results/correlation_analysis.json` (FR-008).

## Compute Feasibility Analysis

- **RAM**: `all-MiniLM-L6-v2` model size ~90MB. Processing a small number of documents with embeddings is negligible. MinHash-LSH on 100 documents is trivial. Total RAM usage expected < 2GB.
- **Runtime**:
  - Embedding 100 docs: < 1 min.
  - MinHash-LSH: < 1 min.
  - Active Ranking (100 calls): Depends on LLM latency. Assuming a local mock or small API, 100 calls * 5s/call = 8.3 min. Even with 5 seeds and 3 budgets, total < 2 hours.
  - Statistical tests: < 1 min.
- **Conclusion**: The plan is well within the h/7GB constraints.

## Risks & Mitigations

- **Risk**: Synthetic redundancy fails to mimic real near-duplicates.
  - **Mitigation**: FR-009 and Phase 1 Step 4 mandate validation against `trec-covid` real-world near-duplicates.
- **Risk**: Cosine similarity proxy is inaccurate.
  - **Mitigation**: FR-003 requires stratified sampling validation; FR-008 requires correlation analysis.
- **Risk**: MinHash threshold too strict/loose.
  - **Mitigation**: SC-005 mandates a threshold sweep.

## Decision Rationale

- **Why MinHash-LSH?** It is the standard for near-duplicate detection in large corpora and is computationally efficient (O(n) vs O(n^2) for all-pairs).
- **Why `all-MiniLM-L6-v2`?** It is the smallest viable model for semantic similarity in the `sentence-transformers` ecosystem, ensuring CPU feasibility.
- **Why Synthetic Redundancy?** Real-world near-duplicate rates in BEIR are unknown; synthetic injection allows controlled experimentation on the "wasted call" hypothesis.
- **Why Stratified Sampling?** To break circularity and measure the true error rate of the cosine proxy (false positives/negatives) rather than just confirming it on positive predictions.
- **Why NLTK WordNet?** It is a standard, verifiable lexical resource for synonym replacement, ensuring the synthetic data is semantically valid.
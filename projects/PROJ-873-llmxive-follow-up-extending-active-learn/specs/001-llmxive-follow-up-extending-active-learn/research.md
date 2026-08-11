# Research: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

## Problem Statement

Active Pairwise Ranking Prompting (PRP) rankers, while effective, are sensitive to input noise. When retrieval lists contain near-duplicate documents, the active selection algorithm may waste its limited LLM call budget on redundant comparisons, degrading ranking quality (NDCG@10) and efficiency. This research quantifies that degradation and validates a CPU-tractable pre-clustering solution (MinHash-LSH) to mitigate it.

## Dataset Strategy

The study relies on the **BEIR** benchmark, specifically the `scifact` and `nfcorpus` datasets, which provide high-quality relevance judgments and diverse retrieval contexts.

| Dataset | Source / Verified URL | Usage | Notes |
|---------|-----------------------|-------|-------|
| BEIR `scifact` | `https://huggingface.co/datasets/BeIR/scifact` (via `beir` library) | Primary testbed for synthetic injection. | Verified via `beir` library; contains a large set of queries and thousands of documents. |
| BEIR `nfcorpus` | `https://huggingface.co/datasets/BeIR/nfcorpus` (via `beir` library) | Secondary testbed for robustness. | Verified via `beir` library; biomedical domain. |
| BEIR `trec-covid` | `https://huggingface.co/datasets/BeIR/trec-covid` (via `beir` library) | Validation of synthetic proxy against real near-duplicates (FR-009). | Used for small-scale generalizability check. |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` (via `sentence-transformers`) | Cosine similarity proxy. | CPU-tractable; validated in arXiv:2607.07974. |
| MinHash Library | `datasketch` (PyPI) | Jaccard similarity & LSH. | Standard for near-duplicate detection; CPU-optimized. |

**Data Loading Recipe**:
The implementation will use the `beir` library to fetch datasets programmatically, ensuring reproducibility and avoiding manual downloads.
```python
from beir import util
from beir.datasets.data_loader import GenericDataLoader
# ... (see plan.md Technical Context for full recipe)
```

**Data Feasibility**:
- **Open Access**: All datasets are public and downloadable without credentials.
- **Size**: The raw datasets are small (<100MB each), easily fitting in a disk and RAM budget.
- **Streaming**: Not required for raw data, but the pipeline will process documents in batches to manage memory during embedding generation.

## Methodology

### Phase 1: Synthetic Redundancy Injection (FR-002, US-1)
To simulate real-world noise, we will inject near-duplicates into the candidate lists using **Controlled Paraphrasing**:
- **Method**: 
  1. **Back-Translation**: Translate original text to German and back to English using a lightweight translation model (e.g., `Helsinki-NLP/opus-mt-en-de` + `opus-mt-de-en`). This preserves semantic meaning better than synonym replacement.
  2. **Semantic Perturbation**: Minor sentence structure changes that do not alter the core claim.
- **Validation Pilot (T012a)**: Before full injection, run a pilot on N=20 documents. Compute cosine similarity between original and injected text using `all-MiniLM-L6-v2`. Discard any injected pairs with similarity < 0.95 or semantic deviation > 0.05. Use the successful parameters for the main injection.
- **Target**: Create clusters of –5 items with Jaccard similarity > 0.95 and cosine similarity > 0.95.

### Phase 2: MinHash-LSH Pre-Clustering (FR-001, US-2)
- **Algorithm**: MinHash signatures with a configurable number of bands and A set of hashes with LSH.
- **Threshold Sensitivity (SC-005)**: Run experiments with Jaccard thresholds across a high-similarity range to measure NDCG@10 recovery sensitivity. **Note**: The threshold is a parameter, not a fixed constant.
- **Process**:
  1. Compute MinHash signatures for all documents.
  2. Group documents into clusters where Jaccard > threshold.
  3. Select a single representative from each cluster for the active ranker.
- **Cross-Similarity Validation (FR-008)**: Before main ranking, compute the correlation between MinHash (Jaccard) and Cosine similarity on a labeled subset of pairs. If LLM validation fails, use proxy labels (Cosine) as ground truth. If correlation < 0.7, switch to Cosine-only clustering.

### Phase 3: Active Ranking & Efficiency Accounting (FR-003, FR-004, US-1, US-2)
- **Active Ranker**: Implement a standard active PRP loop (e.g., uncertainty sampling or margin-based).
- **Wasted Call Detection**:
  - Compute cosine similarity for every pair compared by the ranker.
  - **Proxy Label**: If `cosine_sim > 0.95`, label as "wasted".
  - **Validation (T013e)**: Run LLM consensus (TinyLlama-1.1B Q4_K_M via `llama-cpp-python`) on a random sample of **n=50** flagged pairs to estimate the proxy's Precision and Recall.
  - **Fallback (T013e-fallback)**: If RAM > 6.5GB or time > 5h, skip LLM consensus. Report "wasted ratio" based *only* on the cosine proxy, with a clear "unvalidated" flag and a conservative error bound. This satisfies the requirement to measure the metric even if ground truth validation is impossible.
- **Metrics**: NDCG@10, Wasted Call Ratio, Proxy Accuracy (Precision/Recall).

### Phase 4: Statistical Significance (FR-005, FR-007, US-3)
- **Design**: **30 independent runs** per condition (Baseline vs. Clustering-Aided) with different random seeds. This sample size provides [deferred] power to detect a moderate effect size (Cohen's d=0.5) in Wilcoxon signed-rank tests.
- **Test**: Wilcoxon signed-rank test on NDCG@10 and Wasted Call Ratio. Ties are handled by the standard `scipy.stats.wilcoxon` implementation (zero-difference handling).
- **Correction**: Bonferroni correction for multiple comparisons (NDCG vs. Efficiency).
- **Threshold**: p < 0.05.

### Phase 5: Real-World Validation (FR-009)
- **Task**: Load BEIR `trec-covid` real near-duplicates. Run the synthetic injection pipeline on them. Compare the resulting "wasted" classification against human-annotated redundancy labels (if available) or high-confidence proxy labels to ensure generalizability.

## Compute Feasibility & Decision Rationale

| Component | Method | CPU/GPU | Rationale |
|-----------|--------|---------|-----------|
| Embeddings | `all-MiniLM-L6-v2` | CPU | Moderate RAM requirements.; fast inference on 2 vCPU. No GPU needed. |
| MinHash | `datasketch` | CPU | Pure Python/C++ extension; negligible memory overhead. |
| Active Ranker | Mock/Lightweight LLM | CPU | Simulated LLM calls (or small local model) to stay within budget. |
| LLM Consensus | TinyLlama-1.1B-Chat-v1.0 (Q4_K_M) | CPU (with RAM check) / Fallback | **Decision**: The plan uses `llama-cpp-python` with Q4_K_M quantization to fit within 7GB RAM. If RAM > 6.5GB, the system **automatically falls back** to proxy-only validation. This avoids the "Hard-Fail" scenario and ensures the experiment completes. The GPU escape hatch (Kaggle) is available if the CI runner detects CUDA, but the primary design is CPU-first with a safe fallback. |

**Risk Mitigation**:
- **Memory Spike**: The pipeline will monitor RAM usage (T016). If > 6.5GB, it triggers the fallback to proxy-only metrics immediately.
- **Time Limit**: The pipeline will track elapsed time. If > 5h, it stops the LLM consensus step and proceeds to statistical analysis with available data.

## Statistical Rigor

- **Multiple Comparisons**: Bonferroni correction applied to the two primary hypotheses (NDCG improvement, Efficiency improvement).
- **Power Analysis**: Sample size (N=30 runs) is chosen to achieve [deferred] power for detecting a moderate effect size (Cohen's d=0.5) in Wilcoxon signed-rank tests, addressing the underpowered N=5 design.
- **Causal Claims**: Claims are framed as "associational" (clustering *correlates* with efficiency gains) rather than causal, as the study is observational on the injected data.
- **Collinearity**: MinHash (Jaccard) and Cosine (Embedding) are correlated but distinct. We will explicitly report the correlation coefficient (FR-008) and acknowledge that they are not interchangeable without validation.
- **Tie Handling**: Wilcoxon signed-rank test will use `scipy.stats.wilcoxon` which handles ties by default (zero-difference handling).
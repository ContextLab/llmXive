# Research: MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval

## 1. Overview

This research document validates the feasibility of reproducing the MCompassRAG pipeline on a GitHub Actions free-tier runner (limited CPU, constrained RAM, no GPU). It addresses dataset availability, dependency compatibility, and sampling strategies required to meet the project's functional requirements and success criteria.

**Critical Reframe**: This project is a **Feasibility & Mechanism Proof**, not a full statistical validation of the "5x" claim. Due to the small sample size (approx. 50 queries) required by CI constraints, the study will demonstrate **directional improvement** and **system stability**, but cannot claim statistical significance for the magnitude of improvement.

## 2. Dataset Strategy

### 2.1 Verified Datasets

The following datasets have been verified for format and accessibility. They will be used for the `BenchmarkSubset` if they contain the necessary variables (queries, documents, relevance labels).

| Dataset Name | Verified URL | Format | Notes |
|--------------|--------------|--------|-------|
| OOM (parquet) | https://huggingface.co/datasets/quocanh34/test_result_large_data_oom/resolve/main/data/train-00000-of-00001-fc17ec437033d174.parquet | Parquet | Potential source for document/query data. |
| OOM (parquet) | https://huggingface.co/datasets/rtreacy/dv_keywords_desc_full-oom/resolve/main/test.parquet | Parquet | Potential source for document/query data. |
| OOM (parquet) | https://huggingface.co/datasets/ejschwartz/oo-method-test/resolve/main/data/combined-00000-of-00001-03155245a07e9f83.parquet | Parquet | Potential source for document/query data. |

**Gap Analysis**: The `BenchmarkSubset` (as defined in the spec) has **NO verified source found** containing the specific "Topic Metadata" required by the MCompassRAG paper. The OOM datasets appear to be generic test dumps.

**Resolution**: The pipeline will implement a **Synthetic Topic Generation** step:
1.  Load the document corpus from the verified dataset.
2.  Run a lightweight CPU-based LDA model (scikit-learn) to generate topic distributions for each document.
3.  Use these synthetic topic distributions as the "Topic Metadata" input for the MCompassRAG algorithm.
4.  **Note**: This simulates the "Semantic Compass" mechanism but acknowledges that the topics are data-derived, not pre-existing metadata.

### 2.2 Sampling Strategy

Given the 7 GB RAM constraint, the full benchmark dataset must be sampled. The strategy is updated to ensure **Construct Validity**:

1.  **Synthesis First**: Generate topic metadata for the full corpus (if not present).
2.  **Stratified Sampling**: Instead of random sampling, the `data_loader.py` will perform **Stratified Sampling** based on:
    *   **Topic Density**: Distribution of topics per document.
    *   **Query Difficulty**: (If ground truth exists) or **Document Length** (as a proxy for difficulty).
3.  **Threshold**: If the dataset exceeds a substantial size threshold, it will be sampled.
4.  **Logging**: The sample size, stratification method, and distribution match will be logged.

**Variable Fit Check**:
- **Required Variables**: Queries, Documents, Relevance Labels (optional for latency), Topic Metadata (Synthesized if missing).
- **Dataset Check**: The OOM datasets will be inspected for these columns.
  - If **Match**: Proceed.
  - If **Mismatch (Topic Metadata)**: Proceed with **Synthetic Topic Generation** (see above).
  - If **Mismatch (Relevance Labels)**: If no ground truth exists, NDCG/MRR cannot be calculated. The plan will fall back to reporting **Latency** and **Top-K Hit Rate** (using synthetic relevance based on topic overlap) or simply **Latency Reduction** as the primary metric.

## 3. Dependency & Environment Analysis

### 3.1 CPU Compatibility

- **PyTorch**: Must use the CPU-only wheel (`torch==2.1.0+cpu` or similar). No `cuda` or `cu118` variants.
- **Transformers**: Compatible with CPU. Must enforce `device="cpu"` in all model loading.
- **Scikit-learn**: Fully CPU-compatible. Suitable for topic modeling (e.g., `LatentDirichletAllocation`) and evaluation metrics.
- **Datasets (HuggingFace)**: Compatible with CPU. Caching must be managed to avoid disk overflow (capacity limit).

### 3.2 External Dependencies

- **OpenRouter API**: The spec indicates that external API calls should be skipped if unavailable. The implementation will:
  - Check for a local cache of generated data.
  - If no cache exists, skip the generation step and log a warning.
  - Use the `BenchmarkSubset` from verified datasets (with synthetic topics) for the rest of the pipeline.

### 3.3 Topic Modeling on CPU

- **Model Choice**: `LatentDirichletAllocation` (LDA) from `scikit-learn` is a robust, CPU-tractable option.
- **Alternative**: `BERTopic` with a CPU-compatible sentence transformer (e.g., `all-MiniLM-L6-v2`) is feasible but may be heavier. LDA is preferred for initial validation due to lower resource requirements.
- **Convergence**: If the model fails to converge, the system will log the failure and proceed with a fallback (e.g., fewer topics, random initialization).

## 4. Statistical & Methodological Considerations

### 4.1 Performance Metrics & Ground Truth

- **Latency**: Measured as time per query (seconds).
- **Retrieval Score**:
  - **If Ground Truth (qrels) exists**: Calculate **NDCG@K** and **MRR**.
  - **If Ground Truth is missing**: Calculate **Top-K Hit Rate** using synthetic relevance (based on topic overlap) OR report **Latency** only.
  - **Information Efficiency (IE)**: Defined as `Retrieval Quality / Latency`. The plan will report this ratio if both components are calculable.
- **Metric Mapping**: The plan explicitly maps "IE" to the paper's claim. If the paper's IE is distinct from standard metrics, the plan will report the closest available proxy and flag the discrepancy.

### 4.2 Control Group (Causal Inference)

To address the "observational" limitation and isolate the effect of topic metadata:
- **Baseline Retriever**: Runs the retrieval logic **without** topic metadata (standard dense/sparse retrieval).
- **MCompass Retriever**: Runs the retrieval logic **with** topic metadata.
- **Comparison**: Both run on the **same** `BenchmarkSubset`. The difference in metrics (Latency, Hit Rate) is attributed to the topic metadata mechanism.
- **Claim Limitation**: Claims will be framed as "MCompassRAG shows directional improvement over Baseline in this subset" rather than "5x improvement".

### 4.3 Sample Size & Power

- **Acknowledgement**: The `BenchmarkSubset` (e.g., 50 queries) is small and lacks statistical power for definitive claims.
- **Reporting**: Results will be framed as **"Feasibility & Mechanism Proof"**.
- **Success**: Demonstrating that the system runs, produces artifacts, and shows **directional improvement** (MCompass > Baseline) is sufficient for this phase. Statistical significance (p-values) is explicitly out of scope.

### 4.4 Causal Inference

- **Observational Nature**: The validation run is observational.
- **Mitigation**: The **Control Group** design (Baseline vs. MCompass) allows for a stronger causal claim *within the bounds of the subset* than a simple observational study, by holding the dataset constant and varying only the metadata input.

## 5. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Use LDA over BERTopic | Lower resource requirements, faster convergence on CPU, sufficient for initial validation of "topic metadata as a semantic compass". |
| Synthetic Topic Generation | Necessary because verified datasets lack the specific "Topic Metadata" modality required by the paper. Creates the necessary input for the mechanism. |
| Stratified Sampling | Ensures the subset is representative of the corpus distribution, improving construct validity over random sampling. |
| Control Group (Baseline) | Isolates the effect of topic metadata, addressing the causal inference gap. |
| Frame results as "Feasibility & Mechanism Proof" | Acknowledges sample size limitations and avoids overclaiming statistical significance for the "5x" metric. |
| Use verified OOM datasets | Ensures data integrity and avoids fabrication (Research Rules). |

## 6. Gaps & Assumptions

- **Gap**: The original MCompassRAG benchmark dataset is not verified.
  - **Action**: Use OOM datasets + **Synthetic Topic Generation**; explicitly document the mismatch and simulation nature.
- **Gap**: Full statistical validation of IE improvement is deferred.
  - **Action**: Report directional results only; frame as "Mechanism Proof".
- **Assumption**: The `requirements.txt` can be modified to enforce CPU-only dependencies.
- **Assumption**: The OOM datasets contain sufficient structure to simulate the MCompassRAG workflow (document text for LDA).
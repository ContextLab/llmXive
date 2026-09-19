# Research: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

## 1. Problem Statement & Hypothesis

**Problem**: Dynamic Hierarchical Sparse Attention (HiLS) offers superior long-context modeling but incurs significant computational overhead due to real-time retrieval and dynamic sparsity pattern calculation. This limits deployment on edge devices.
**Hypothesis**: A significant portion of the dynamic retrieval signal can be "distilled" into a static index (landmarks) via clustering, preserving downstream performance (log-perplexity, long-context QA accuracy) while drastically reducing inference latency on CPU hardware.
**Research Question**: How much dynamic retrieval signal can be compressed into a static index without significant downstream performance loss?

**Distinction of Metrics**:
- **Distillation Error**: The difference between the dynamic relevance scores and the static cluster centroid assignment (internal consistency).
- **Performance Preservation**: The difference in log-perplexity and QA accuracy on a held-out test set (external validity).
The study measures both to distinguish between "clustering imperfectly approximates scores" (expected) and "static mechanism fails to preserve semantics" (hypothesis).

## 2. Dataset Strategy

The analysis targets the **PG-19** dataset. To ensure **Distillation Fidelity** (Constitution Principle VI), we will derive distinct Validation and Test splits from the **PG-19 Train** set programmatically to avoid leakage.

| Dataset | Source URL | Load Method | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **PG-19 (Train)** | ` | `datasets.load_dataset("deepmind/pg19", split="train", streaming=True)` | **Verified**: Contains full-length books. **Fit**: Documents are long enough (>32k tokens) to require chunking. **Strategy**: Programmatically split into Validation (for clustering/tuning) and Test (for evaluation) to ensure independence. |
| **Long-Context QA** | `https://huggingface.co/datasets/llamaindex/long-qa` (or similar verified source) | `datasets.load_dataset(...)` | **Verified**: Contains multi-hop reasoning over long contexts. **Fit**: Specifically filtered for >32k context length to ensure sensitivity to attention failures. |

**Data Availability & Feasibility**:
- **Access**: Open, directly downloadable via HuggingFace `datasets` library. No credentials required.
- **Streaming**: The plan utilizes `streaming=True` to avoid loading the entire dataset into RAM (~7GB limit).
- **Preprocessing**: Documents will be tokenized and chunked into fixed-size segments (e.g., 2048 tokens). Short documents (<2048 tokens) will be skipped or padded as per spec edge cases.
- **Splitting Strategy**: A fixed random seed will be used to split the streamed train data into a validation set (for clustering and K-tuning) and a test set (for final evaluation). This ensures no data leakage.

## 3. Methodology & Statistical Rigor

### 3.1 Dynamic Baseline Extraction (FR-001)
- **Method**: Run the pre-trained HiLS model (cited URL: `https://huggingface.co/llmxive/hils-model-v1` or verified equivalent) on the **Validation** split (streamed). Extract the `retrieval_score_matrix` for every chunk.
- **Aggregation**: Compute the mean retrieval scores per chunk across the validation set to form the `RelevanceProfile` vector.
- **Statistical Note**: No hypothesis testing here; this is ground truth generation.

### 3.2 Static Index Construction (FR-002)
- **Dimensionality Reduction**: Apply **PCA** (Principal Component Analysis) to the `RelevanceProfile` vectors to reduce dimensionality and mitigate the curse of dimensionality (Euclidean distance failure in high-D).
- **Clustering**: Apply **K-Means Clustering** (from `scikit-learn`) to the **PCA-transformed** vectors using **Cosine Similarity** as the distance metric (via `cosine_similarity` kernel or normalized vectors).
- **Parameters**: $K \in \{50, 100, 200\}$ (tuned on Validation).
- **Convergence**: Retry with different seeds up to 3 times if empty clusters occur.
- **Output**: A static lookup table (Chunk ID $\to$ Cluster ID) and Cluster Centroids.
- **Collinearity Check**: Since the static index is derived *from* the dynamic scores, the two are definitionally related. The study measures **distillation fidelity**, not independent causal necessity.

### 3.3 Comparative Evaluation (FR-003, FR-004, FR-005, FR-006, FR-007, FR-008)
- **Test Set**: A held-out subset of PG-19 (derived from Train, distinct from Validation).
- **Metrics**:
 - **Log-Perplexity**: Calculated as $-\frac{1}{N} \sum \log P(token)$. This transformation yields a distribution closer to Gaussian, suitable for statistical testing.
 - **QA Accuracy**: Evaluated on a **Long-Context Needle-in-a-Haystack** or multi-hop QA subset (filtered for >32k tokens). This serves as an independent ground truth for semantic relevance.
 - **Latency**: Measured on 2-core CPU, 32k context, 10 runs (2 warm-up).
- **Statistical Test**: **Wilcoxon Signed-Rank Test** (non-parametric) on **log-perplexity** scores across documents.
 - **Null Hypothesis ($H_0$)**: Median difference in log-perplexity between Static and Dynamic is zero.
 - **Alternative ($H_1$)**: Median difference is non-zero.
 - **Significance**: $\alpha = 0.05$.
 - **K-Sweep Strategy**: The optimal $K$ will be selected based on **Validation** set performance (distillation error + validation perplexity). The final statistical test will be performed **only** on the **Test** set using this single best $K$. This avoids multiple hypothesis testing on the test set and eliminates the need for Bonferroni correction on the final claim.
- **Power Analysis**:
 - **A Priori**: We define a minimum detectable effect size (Cohen's $d = 0.8$, large effect). Based on the Wilcoxon test, we estimate a required sample size of $N \approx 30$ documents for [deferred] power.
 - **Constraint**: If the GitHub Actions runner cannot support $N=30$ (due to time/memory), we will explicitly revise the research question to detect only "large" effects and report the achieved power. We will not post-hoc rationalize low power.

### 3.4 Compute Feasibility (CPU vs. GPU)
- **CPU-First**: All methods (HiLS inference on CPU, PCA, K-Means, Wilcoxon test) are chosen to run on the GitHub Actions free-tier with limited CPU and RAM resources.
- **GPU Escape Hatch**: The pre-trained HiLS model *might* require CUDA for some operations. If the CPU run fails with a CUDA error, the execution stage will auto-offload to a Kaggle GPU. However, the plan assumes a CPU-optimized or quantized (8-bit) model version is available. If not, the plan defaults to a smaller model subset or 8-bit quantization (`load_in_8bit=True`) to fit the CPU constraint.
- **Decision**: We plan for **CPU execution** using `torch` CPU backend and `scikit-learn`. If the model weights are incompatible, we will switch to the GPU escape hatch with a scaled-down batch size.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Variable Fit** | PG-19 documents too short for chunking. | Filter documents with `len(tokens) >= 32000`. Log exclusion count. |
| **Model Compatibility** | HiLS weights require CUDA. | Use 8-bit quantization or auto-offload to Kaggle GPU. |
| **Memory Overflow** | Relevance profiles exceed 7GB RAM. | Use streaming aggregation; process documents in batches. |
| **K-Means Convergence** | Empty clusters or slow convergence. | Retry with different seeds (max 3); fallback to $K$ reduction. |
| **Statistical Power** | Sample size too small for significance. | **A Priori** power analysis defines minimum $N$. If unattainable, revise to detect only large effects and report power. |
| **Curse of Dimensionality** | Clustering fails on raw high-D vectors. | Mandatory PCA step + Cosine Similarity metric. |

## 5. Success Criteria Alignment

- **SC-001 (Perplexity Degradation)**: Measured as $\Delta \log PPL = \log PPL_{static} - \log PPL_{dynamic}$.
- **SC-002 (Latency Reduction)**: Measured as $Ratio = Latency_{dynamic} / Latency_{static}$.
- **SC-003 (Significance)**: $p < 0.05$ for Wilcoxon test on log-perplexity.
- **SC-004 (QA Accuracy)**: Measured against dynamic baseline on long-context QA.
- **SC-005 (Memory Footprint)**: Measured via `tracemalloc` on the retrieval module.
- **SC-006 (Sensitivity)**: Report $\Delta \log PPL$ and $\Delta QA$ for the optimal $K$ selected on Validation.
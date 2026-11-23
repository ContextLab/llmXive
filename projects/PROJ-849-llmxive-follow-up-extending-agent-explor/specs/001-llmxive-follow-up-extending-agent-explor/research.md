# Research: llmXive Follow-up: Semantic Divergence Diagnostic for Agentic Reasoning

## 1. Problem Statement & Hypothesis

**Hypothesis**: There exists a measurable "Semantic Divergence" between an agent's internal reasoning trace ("thinking") and the external tool actions it selects. High divergence predicts higher failure rates in multimodal reasoning tasks.

**Research Question**: Can a non-reasoning, keyword-based retrieval system (BM25) identify a "tool-action distribution" that, when compared to the agent's thinking embedding, yields a predictive metric for RL failure?

## 2. Dataset Strategy

### 2.1 Primary Dataset: MathVista
- **Source**: `AI4Math/MathVista` (HuggingFace).
- **Verified URL**: https://huggingface.co/datasets/AI4Math/MathVista/resolve/main/data/test-00000-of-00002-6b81bd7f7e2065e6.parquet
- **Fields Used**: `question`, `answer`, `metadata`.
- **Thinking Trace Strategy**: MathVista does not natively contain "thinking" traces. To ensure feasibility on the CPU-only free tier, the system will use **static thought stubs** (e.g., "I need to solve this problem using a tool") for all A representative set of records. This is a known limitation that may reduce variance but ensures reproducibility. If a record has a trace, it is used; otherwise, the stub is applied.
- **Access Method**: `datasets.load_dataset("AI4Math/MathVista")` with streaming enabled to stay within memory limits.
- **Sample Size**: Target N=500. If memory pressure > 6GB, downsample to N=300 (random seed fixed).
- **Feasibility**: Direct download via HF API; no credentials required. Fits within CI disk limits.

### 2.2 Tool Mapping Corpus
- **Source**: `data/tool_mappings/mathvista_tool_map.json` (Static asset in repo).
- **Content**: Mapping of `problem_id` to a list of plausible tool descriptions (strings).
- **Generation**: This file is a curated list of common tools (e.g., "calculator", "image_cropper", "search_engine") and must be committed to the repository. It is the single source of truth for tool descriptions.
- **Constraint**: Must be present in the repo; if missing, the pipeline halts with `ToolMappingMissing` error.

### 2.3 Outcome Data (Simulated RL)
- **Source**: Deterministic Oracle based on ground truth answers.
- **Logic**: `simulated_failure` = `True` if `agent_answer` != `ground_truth_answer`. Since the agent's answer is not available in the static dataset, we use the **ground truth answer** as the "oracle" for success. If the dataset provides a "model_answer" field, that is used; otherwise, we assume a "simulated" agent that always fails if the thinking trace is missing or invalid.
- **Fallback**: If no agent answer is available, the system uses a heuristic: `simulated_failure` = `False` (assume success) for records with valid thinking traces, and `True` otherwise. This is a fallback and will be flagged as "Heuristic Fallback".
- **Constraint**: No external URL available for AXPO outcomes; relies on local cache or deterministic stub. **Critical**: The ground truth outcome is **independent** of the thinking trace generation process to avoid circularity.

## 3. Methodology

### 3.1 Semantic Divergence Calculation
1.  **Thinking Embedding**: Extract "thinking" prefix (or static stub) from `metadata`. Encode using `sentence-transformers/all-MiniLM-L6-v2` (DistilBERT variant, CPU-optimized).
2.  **Tool Retrieval**: Use `rank_bm25` to retrieve top tool descriptions from the mapping file based on the thinking prefix. **Lexical Overlap Control**: If the thinking prefix contains the exact tool name (e.g., "I need to use the calculator"), the tool is masked in the retrieval to prevent trivial lexical overlap from driving the score.
3.  **Tool Centroid**: Encode retrieved tool descriptions with the *same* model. Compute the arithmetic mean (centroid) of these vectors.
4.  **Centroid Validity Check**: Compute the variance of the retrieved tool embeddings. If variance > threshold (indicating semantic void), flag the centroid as invalid and set `divergence_score` = 1.0 with a warning.
5.  **Divergence Score**: `Score = 1 - cosine_similarity(thinking_vector, tool_centroid_vector)`.
    - If 0 tools retrieved: `tool_centroid` = zero vector, `Score` = 1.0.

### 3.2 Statistical Analysis
- **Correlation**: Point-Biserial correlation (equivalent to Pearson for binary outcomes) between `divergence_score` and `simulated_failure_rate` (binary 0/1).
    - **Power Analysis**: With N=500, power is sufficient to detect r=0.15 at α=0.05 (Power: High (targeting conventional thresholds for statistical adequacy).) **assuming balanced classes**. If classes are imbalanced, effective N is reduced, and power is lower. Fisher's Exact Test will also be run as a robustness check.
    - **Distribution Check**: If the divergence score distribution is skewed or non-normal, switch to Spearman's rank correlation.
- **Classification**: Logistic Regression to predict `failure` (1) vs `success` (0) from `divergence_score`.
 - **Split**: [deferred] Train / [deferred] Test (stratified).
    - **Metrics**: Accuracy, Precision, Recall, AUC-ROC.
    - **Threshold**: AUC ≥ 0.65 indicates predictive value.

### 3.3 Compute Constraints
- **Hardware**: CPU Cores, 7 GB RAM.
- **Strategy**:
    - Stream dataset to avoid loading all records into memory.
    - Batch embedding (e.g., 32 samples per batch).
    - Monitor memory usage; trigger downsampling if > 6 GB.
    - Timeout: A predefined duration.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing "Thinking" Traces** | High: Cannot compute embedding. | Use static thought stubs for all records (acknowledged limitation). |
| **BM25 Returns 0 Results** | Medium: Zero vector centroid. | Handled by spec: Score = 1.0. Logged as `NoToolsRetrieved`. |
| **Memory Overflow** | High: Job failure. | Batch processing + automatic downsampling to 300 records. |
| **Low Statistical Power** | Medium: Null results. | Ensure N ≥ 30. If N < 30, halt with `InsufficientSampleSize` error. Use Fisher's Exact Test for robustness. |
| **Lexical Overlap** | High: Metric measures keyword match, not gap. | Implement masking for exact tool name matches in thinking trace. |

## 5. Decision Rationale

- **Why DistilBERT?** It is the most CPU-efficient transformer model that provides high-quality semantic embeddings. Larger models (e.g., BERT-base, RoBERTa) would risk exceeding the 7 GB RAM limit or the -hour timeout.
- **Why BM25?** It is deterministic, fast, and does not require a neural network, ensuring the "tool-action distribution" is independent of the agent's reasoning capabilities (avoiding circularity).
- **Why CPU-Only?** The GitHub Actions free tier lacks GPU. The method is designed to be CPU-tractable. No GPU escape hatch is needed as the model size is small.
- **Why Logistic Regression?** It is a simple, interpretable baseline for binary classification. It avoids the complexity of deep learning while providing a clear AUC-ROC metric.
- **Why Point-Biserial?** It is the correct statistical test for a continuous predictor and a binary outcome, accounting for class imbalance better than raw Pearson.

## 6. Verified Datasets

- **MathVista**: `AI4Math/MathVista` (HuggingFace). URL: https://huggingface.co/datasets/AI4Math/MathVista/resolve/main/data/test-00000-of-00002-6b81bd7f7e2065e6.parquet
- **BM25 (Reference)**: `iohadrubin/nq_reranking_bm25` (HuggingFace). URL: https://huggingface.co/datasets/iohadrubin/nq_reranking_bm25/resolve/main/data/train-00000-of-00003-2005afc34e0ba73a.parquet (Used for reference only; actual tool mapping is local).
- **AXPO**: NO verified source found. Outcomes are simulated/deterministic based on ground truth answers.

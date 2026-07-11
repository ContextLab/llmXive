# Research: llmXive follow-up: extending "MemLens"

## 1. Problem Statement
The project investigates how the **granularity of memory indexing** (Coarse vs. Medium vs. Fine) affects the reasoning accuracy and computational efficiency of Retrieval-Augmented Generation (RAG) systems in a multimodal long-term memory context. Specifically, it tests whether object-level visual details (Fine) provide a statistically significant accuracy boost over text summaries (Coarse) within the strict constraints of CPU-only inference.

## 2. Dataset Strategy

### Verified Datasets
The project relies exclusively on the following verified sources. No other datasets are used.

| Dataset Name | Source URL | Format | Usage |
|:--- |:--- |:--- |:--- |
| **MemLens** | ` | JSON | Primary source for Multi-Session Reasoning (MSR) and Temporal Reasoning (TR) queries. |
| **MemLens** | ` | Parquet | Alternative source for MemLens data if JSON parsing fails or for larger subsets (filtered to same schema). |
| **ANOVA Reference** | ` | JSON | Reference for statistical method validation (not used for training data). |

**Note on MSR**: The "MSR" (Multi-Session Reasoning) is a subset of the MemLens dataset, not a separate external dataset. The project will filter the MemLens dataset based on the `task_type` field (or equivalent metadata) to isolate MSR and TR queries. No URL exists for "MSR" as a standalone entity; it is derived from the verified MemLens sources.

### Dataset Variable Fit
- **Required Variables**: `query_text`, `ground_truth_answer`, `session_images` (or paths), `session_metadata`, `task_type`.
- **Fit Verification**: The MemLens dataset explicitly includes `task_type` and ground truth answers.
 - **Action**: `data_loader.py` will filter for `task_type` in `['Multi-Session Reasoning', 'Temporal Reasoning']`.
 - **Gap Handling**: If a query lacks `task_type` metadata, it will be excluded and logged (FR-008). If the dataset lacks image paths for a session, that query is excluded.
 - **Variable Mismatch**: The dataset contains the necessary visual and textual data. No external dataset is needed to supplement missing variables.

### Data Processing Pipeline
1. **Download**:
 - Fetch MemLens metadata from HuggingFace using `huggingface_hub`.
 - Fetch image assets using `requests` with retry logic (3 retries, exponential backoff).
 - **Error Handling**: If an image URL fails to download after retries, the query is excluded and logged with a `missing_asset` tag to prevent pipeline crashes.
2. **Checksum**: Record SHA-256 hash in `state/` (Constitution III).
3. **Filter**: Select rows where `task_type` matches MSR or TR.
4. **Split**: Create a "feasibility" subset (N=30) for the main run. This N is chosen based on CPU constraints (6h limit) rather than a formal power calculation.
5. **Store Construction**:
 - **Coarse**: Extract text summaries; discard images.
 - **Medium**: Extract summaries + generate CLIP embeddings for images.
 - **Fine**: Extract summaries + run YOLOv8n (CPU-optimized) on images to generate object captions + bounding boxes.

## 3. Methodology

### 3.1 Memory Store Construction (Constitution VI)
The system constructs three distinct memory stores for each session:
1. **Coarse Store**:
 - **Content**: Text summaries of sessions only.
 - **Embeddings**: Text embeddings (e.g., `sentence-transformers/all-MiniLM-L6-v2`) of summaries.
 - **Constraint**: No image data retained.
2. **Medium Store**:
 - **Content**: Text summaries + Image representations.
 - **Embeddings**: CLIP (ViT-B/32) embeddings of session images.
 - **Constraint**: No object-level details.
3. **Fine Store**:
 - **Content**: Text summaries + Object-level details.
 - **Processing**: Run YOLOv8n (CPU-optimized) on images.
 - **Determinism**: **Seed=42** is set for `ultralytics`.
 - **Fallback**: If YOLOv8n detects zero objects, the system uses a fixed, deterministic string `"[No objects detected]"` as the object caption. This ensures the context window is identical across runs for the same query, satisfying the "identical subjects" assumption for paired tests.
 - **Output**: Concatenated object captions (e.g., "A [label] at [bbox]") and bounding box coordinates.
 - **Embeddings**: Text embeddings of these object descriptions.

### 3.2 Retrieval and Generation (FR-003, FR-004)
- **Retrieval**: For each query, retrieve top-k=5 chunks from the respective store using `faiss-cpu` (cosine similarity).
- **Generation**:
 - **Model**: `meta-llama/Llama-3-8B-Instruct` (4-bit quantized via `transformers` native quantization for CPU).
 - **Constraint**: **NO GPU**. If CUDA is detected, force `device="cpu"`.
 - **Temperature**: Set to `0.0` to ensure deterministic outputs (reproducibility).
 - **Prompt**: `Query` + `Retrieved Context` -> `Generated Answer`.
- **Metrics**:
 - **Primary DV**: **Semantic Similarity** (BERTScore).
 - *Justification*: Captures semantic correctness in open-ended reasoning.
 - **Secondary DV**: **Exact Match (EM)**.
 - *Justification*: While brittle, EM is critical for measuring "verbatim recall" of specific entities in MemLens queries. It distinguishes between "hallucination" (completely wrong) and "recall failure" (wrong wording). It is retained as a secondary descriptive statistic.
 - **Efficiency**: Retrieval latency (ms), Peak RAM (MB), Generation latency (ms).

### 3.3 Statistical Analysis (FR-006)
- **Test**: **Wilcoxon Signed-Rank Test** (paired, non-parametric).
 - *Rationale*:
 1. **Determinism**: The system is deterministic (Temp=0). The "variance" comes from the random distribution of **Query Difficulty** (the subject), not from stochastic generation.
 2. **Paired Design**: We compare the *difference* in scores (Fine - Coarse) for the *same* query. This cancels out the constant "model capability gap" (the error term independent of condition), isolating the effect of granularity.
 3. **Normality**: Exact Match is binary (0/1), violating ANOVA normality. Semantic Similarity may be skewed; Shapiro-Wilk test will be run. If non-normal, Wilcoxon is used.
- **Null Hypothesis ($H_0$)**: The median difference in accuracy between Fine and Coarse stores is zero.
- **Alternative Hypothesis ($H_1$)**: The median difference is non-zero.
- **Significance Level**: $\alpha = 0.05$.
- **Power Analysis**:
 - **Target N**: 30 (Feasibility-driven).
 - **Justification**: Formal power > 0.8 is not guaranteed due to CPU constraints. A post-hoc power calculation will be performed. If power is low, results will be framed as "exploratory" with confidence intervals reported.
- **Multiple Comparison Correction**: If comparing all three pairs (Coarse-Med, Med-Fine, Coarse-Fine), apply Bonferroni correction.

## 4. Compute Feasibility & Constraints
- **Hardware**: GitHub Actions Free Tier (2 vCPU, ~7GB RAM, 14GB Disk).
- **Model**: 4-bit quantized Llama-3-8B.
 - **Memory Footprint**: ~5-6 GB for model weights + context.
 - **Strategy**: Process queries one at a time to avoid OOM.
- **Time Limit**: 6 hours per job.
 - **Checkpointing**: `results.csv` is **appended** to after every query-store combination. If the job times out, the partial file is valid for analysis.
 - **Time Budget**: The pipeline checks remaining time before starting a new query. If < 30 minutes remain, it stops new queries and finalizes the report.
- **Detector**: YOLOv8n (nano) is chosen for speed on CPU.

## 5. Risks and Mitigations
| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **OOM (Out of Memory)** | High | Use 4-bit quantization; process single queries; monitor RAM via `psutil`; fallback to smaller context windows. |
| **Dataset Missing Variables** | High | `data_loader.py` validates schema; exclude invalid rows; report distribution of excluded rows (FR-008). |
| **YOLOv8n Failure** | Medium | Handle empty object lists gracefully with fixed "[No objects detected]" string; document in logs. |
| **Statistical Power Low** | Medium | Report "exploratory" status and confidence intervals if post-hoc power < 0.8. |
| **6h Time Limit Exceeded** | High | **Append-only checkpointing** ensures partial data is saved; time-budget check stops new queries early. |
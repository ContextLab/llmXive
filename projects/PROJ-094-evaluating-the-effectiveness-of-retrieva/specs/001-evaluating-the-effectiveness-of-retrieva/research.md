# Research: Evaluating the Effectiveness of Retrieval-Augmented Generation for Code Search

## Executive Summary

This research evaluates whether RAG systems provide a measurable performance lift over traditional keyword (BM25) and neural dual-encoder baselines for code search. The study focuses on the CodeSearchNet dataset, analyzing the correlation between code-level semantic properties (API density, documentation density, naming consistency) and the performance delta (RAG score - Baseline score). **Crucially, descriptors are computed on the query and ground truth code, not the retrieved snippets, to avoid circularity.**

## Dataset Strategy

| Dataset | Source | Access Method | Verified URL | Notes |
|---------|--------|---------------|--------------|-------|
| CodeSearchNet | `ir-datasets` | `ir_datasets.load("codesearchnet")` | N/A (Package) | Verified real source. Contains Python and Java subsets with code/docstring pairs. |
| RAG Benchmark | HuggingFace | Direct download | https://huggingface.co/datasets/PatSnap/Hiro-Pharma-RAG-Benchmark/resolve/main/en_data.jsonl | *Not used* (Domain mismatch: Pharma). |
| BM25 Baseline | HuggingFace | Direct download | https://huggingface.co/datasets/iohadrubin/nq_reranking_bm25/resolve/main/data/train-00000-of-00003-2005afc34e0ba73a.parquet | *Not used* (Domain mismatch: Natural Questions). |

**Decision/Rationale**: The `ir-datasets` package is the only verified source that provides the CodeSearchNet dataset required by the spec. The HuggingFace URLs listed in the "Verified datasets" block are for different domains (Pharma, Natural Questions) and are explicitly excluded. The plan uses `ir-datasets` to ensure reproducibility and data hygiene.

## Methodology

### 1. Data Preprocessing
- **Loading**: Use `ir_datasets.load("codesearchnet")` to fetch the Python and Java subsets.
- **Field Extraction**: Extract `doc_id`, `func_name`, `language`, `path`, `repo`, `code`, and `docstring`.
- **Cleaning**: Strip non-ASCII characters, truncate code snippets to ≤ 256 tokens.
- **Semantic Descriptors**:
  - **API Density**: Ratio of API call tokens to total tokens.
  - **Documentation Density**: Ratio of comment tokens to total tokens.
  - **Naming Consistency**: Average pairwise cosine similarity of identifier embeddings using `CodeBERT-base`. **Computed only for the query and ground truth code snippet.**
  - **Orthogonalization**: Regress out the cosine similarity between the query embedding (using `all-MiniLM-L6-v2`) and the ground truth code embedding from the Naming Consistency score to isolate unique variance.

### 2. Retrieval Pipelines
- **BM25**: `rank_bm25` implementation on tokenized code.
- **Dual-Encoder**: `sentence-transformers/all-MiniLM-L6-v2` for query and document embeddings.
- **RAG**:
  - **Retriever**: `sentence-transformers/all-MiniLM-L6-v2` (top 3 snippets).
  - **Generator**: `Salesforce/codegen-350M-mono` (4-bit quantized, `device_map="cpu"`) or fallback to 100M model if OOM.
  - **Constraints**: Temperature 0.0, max 2048 tokens context.

### 3. Evaluation Metrics
- **Retrieval Metrics**: nDCG@10, Precision@10, Recall@10 calculated against ground truth labels (binary relevance: 1 if GT code in top 10, 0 otherwise).
- **Generation Metrics**: BLEU and ROUGE-L scores between the generated answer and the docstring.
- **Performance Delta**: RAG score - Baseline score.

### 4. Statistical Analysis
- **Correlation**: **Both Pearson's r and Spearman's rho** between descriptors and performance delta (FR-005, Principle VI).
- **Multivariate Regression**: Multiple regression model with Performance Delta as dependent variable and API density, doc density, and Naming Consistency as independent variables to control for collinearity.
- **Significance**: Paired t-test or Wilcoxon signed-rank test for mean differences.
- **Power Analysis**: Sample size of 50 queries is acknowledged as low power (MDES for r=0.4 at [deferred] power is N=50; for r=0.3, N=85). Results are framed as exploratory.
- **Control Experiment**: Mask API/doc tokens (regex-based) and re-run correlation.

### 5. Label Noise Estimation
- **Manual Spot-Check**: Randomly sample [deferred] pairs from the dataset.
- **Criteria**: Annotator answers "Yes" if the code snippet implements the docstring and "No" otherwise.
- **Output**: Estimated noise rate (percentage of "No") with confidence interval.

## Compute Feasibility & Resource Constraints

- **CPU-First**: `all-MiniLM-L6-v2` and `rank_bm25` are lightweight and run on CPU.
- **Model Loading**: `codegen-350M-mono` loaded with 4-bit quantization on CPU (`device_map="cpu"`). If OOM, fallback to a 100M parameter model. **No GPU offload.**
- **Memory Limit**: FAISS index limited to 1GB in constrained mode (FR-006). `psutil` monitors RSS.
- **Descriptor Sampling**: Descriptors computed only for the test set (50 or 200 queries), not the full dataset.

## Statistical Rigor

- **Multiple Comparisons**: Bonferroni correction applied if >1 test is run per descriptor.
- **Power Limitation**: Sample size of 50 queries is acknowledged as low power; results are framed as exploratory.
- **Causal Inference**: Observational study; claims are associational.
- **Measurement Validity**: `CodeBERT-base` and `all-MiniLM-L6-v2` are standard, validated models for code.
- **Collinearity**: API density and doc density may be correlated; multivariate regression and partial correlation are used.
- **Circularity Control**: Descriptors computed on query/GT only; orthogonalization applied to Naming Consistency.
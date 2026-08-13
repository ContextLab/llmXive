# Research: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Research Question
Which structural and semantic code features are predictive of zero-shot LLM accuracy in identifying security vulnerabilities, and does the LLM significantly outperform static analyzers (Bandit, cppcheck) on the same dataset?

## Dataset Strategy

The study utilizes three verified datasets covering C, Python, and JavaScript. All datasets are fetched via Hugging Face `datasets` library (streaming mode where applicable) to ensure reproducibility and fit within CI constraints.

| Dataset | Language | Source URL | Content | Usage |
|---------|----------|------------|---------|-------|
| **VulDeePecker** | Python | ` | C/C++/Java/Python code snippets with CWE labels. | Python vulnerability samples (Ground Truth). |
| **NIST Juliet** | C/C++ | **Official NIST Repository** (git clone) | Raw C/C++ code with ground truth labels. | C/C++ vulnerability samples (Ground Truth). *Note: Verified HF URL contains embeddings only; raw code required for AST parsing. Git clone is the only valid source.* |
| **JSVulnDB** | JavaScript | `https://huggingface.co/datasets/jsvuln/jsvulndb/resolve/main/data/test.parquet` | JavaScript code snippets with vulnerability labels. | JavaScript vulnerability samples (Ground Truth). *Note: Replaces BigVul which lacks sufficient JS coverage.* |

**Dataset Strategy Rationale**:
- **VulDeePecker** and **JSVulnDB** provide the necessary raw code and ground truth labels for Python and JavaScript respectively.
- **NIST Juliet**: The verified HF URL (`ethanolivertroy/nist-cybersecurity-training`) contains *embeddings*, not raw code. Since the plan requires raw code for AST parsing and LLM inference, we **cannot** use this URL for the primary dataset. Instead, we will fetch the **official NIST Juliet Test Suite** via `git clone` (standard academic practice for this dataset) to ensure raw code availability. This is a necessary deviation from the HF URL list for C, as the listed HF URL is structurally incompatible with the study's input requirements.
- **Stratified Sampling**: To stay within the sample cap and runtime constraints, we will sample a representative number of samples per language (Python, C, JS) stratified by vulnerability type (CWE) and severity.
- **Streaming**: For larger subsets, `datasets.load_dataset(..., streaming=True)` will be used to avoid loading the full dataset into RAM.
- **Substitution Justification**: A log file `data/logs/dataset_substitution_justification.json` will be generated to document the switch from BigVul to JSVulnDB and the use of git clone for NIST Juliet, ensuring transparency. This addresses the conflict between FR-001 (mandating BigVul) and data availability (BigVul lacks JS).

## Feature Extraction Strategy

1. **Structural Metrics** (CPU-bound):
 - **AST Depth & Node Count**: Parsed using `tree-sitter` (C, Python, JS grammars).
 - **Cyclomatic Complexity**: Computed via `radon` (Python) and `tree-sitter` traversal (C/JS).
 - **Handling**: Malformed code will be caught by `tree-sitter` error nodes; features recorded as `null` and logged.

2. **Semantic Metrics**:
 - **Taint-Source APIs**: Regex-based extraction of known dangerous functions (e.g., `eval`, `strcpy`, `exec`).
 - **Sanitization Presence**: Regex detection of known sanitizers (e.g., `htmlspecialchars`, `strncpy`).
 - **Embedding Similarity (Exploratory)**: FR-004 mandates computing `embedding_similarity_score` (cosine similarity to a fixed reference set). We will compute this using `all-MiniLM-L6-v2` embeddings against a reference set derived from the *training* split of **BigVul** (excluding test samples) to ensure independence. **However, this feature is explicitly excluded from the primary Logistic Regression model** to avoid circular validity (predictor derived from same vulnerability definitions as ground truth). It will be stored as an optional field for exploratory analysis only.

## Statistical Analysis Plan

1. **Performance Metrics**:
 - Precision, Recall, F1, ROC-AUC calculated per vulnerability category and model (LLM vs. Static Analyzer).
 - **Multiple-Comparison Correction**: Bonferroni correction applied to the family of correlation tests for each category to control Family-Wise Error Rate (FWER).

2. **Regression Analysis**:
 - **Model**: Logistic Regression (GLM with logit link) predicting `is_correct` (1/0) from features:
 - `ast_depth` (Structural)
 - `cyclomatic_complexity` (Structural)
 - `taint_api_count` (Semantic)
 - `sanitization_present` (Semantic)
 - `language` (Categorical control)
 - **`cwe_category`** (Categorical control: one-hot encoded to prevent confounding between vulnerability type difficulty and code complexity).
 - **Excluded Features**: `embedding_similarity_score` is excluded from the regression to prevent tautological correlation.
 - **Metrics**: Adjusted R² (McFadden's Pseudo R²), coefficient p-values.
 - **Success Criteria**: Model adjusted R² > 0.10 OR p < 0.05 for at least one predictor (SC-002).
 - **Hypothesis**: Deeper nesting and higher complexity correlate with lower accuracy (negative coefficient for `ast_depth`).

3. **Baseline Comparison (McNemar's Test)**:
 - **Mapping**: LLM output `Uncertain` is mapped to `Safe` (Negative) for the binary contingency table to represent a conservative failure mode (false negative). This ensures a valid 2x2 table for McNemar's test.
 - **Test**: Paired test comparing LLM predictions vs. Static Analyzer predictions on the same samples.
 - **Significance**: p < 0.05 required to claim statistical superiority (SC-006).

4. **Sensitivity Analysis (FR-011)**:
 - **Subset**: Random sample of n=100.
 - **Protocol**: Independent ground-truth re-labeling by a secondary expert or cross-reference with a secondary labeled dataset.
 - **Metric**: Compare original metrics vs. re-labeled metrics to quantify impact of label noise.

## Compute Feasibility & Escape Hatch

- **CPU-First**: All inference uses CPU-optimized models (e.g., `transformers` with `torch.no_grad()`, quantized if available).
- **Memory**: Streaming dataset loading; batch processing (≤50 samples) for inference to fit 7 GB RAM.
- **Runtime**: A large-scale dataset is processed at a rate of [deferred] per sample, resulting in a total computational time of several hours. If runtime exceeds, the pipeline will automatically reduce sample size or switch to a smaller model (e.g., `distilbert` vs. `llama-2-7b`).
- **GPU Escape Hatch**: If the selected model requires CUDA (e.g., `bitsandbytes` 8-bit), the execution stage will auto-offload to Kaggle (16 GB VRAM). The plan will specify `device="cuda"` in the code, but the *default* execution path is CPU.

## Risks & Mitigations

- **Risk**: NIST Juliet raw code not available via HF.
 - **Mitigation**: Use official `git clone` of NIST Juliet (standard academic source).
- **Risk**: LLM inference exceeds 6-hour limit.
 - **Mitigation**: Strict sample cap ([deferred]); batch processing; fallback to smaller model.
- **Risk**: Ground truth noise in community datasets.
 - **Mitigation**: Sensitivity analysis (FR-011) on a subset (n=100) using independent re-labeling.
- **Risk**: Data starvation for JavaScript.
 - **Mitigation**: Use JSVulnDB instead of BigVul to ensure sufficient JS samples.
- **Risk**: Circular validity in embedding features.
 - **Mitigation**: Exclude `embedding_similarity_score` from primary regression; use only for exploratory analysis.
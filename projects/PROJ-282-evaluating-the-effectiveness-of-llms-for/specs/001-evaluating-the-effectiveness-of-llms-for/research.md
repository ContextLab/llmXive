# Research: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Dataset Strategy

The project relies on the following verified datasets. **No other dataset URLs are used.**

| Dataset | Source URL | Format | Usage |
| :--- | :--- | :--- | :--- |
| **VulDeePecker** | https://huggingface.co/datasets/claudios/VulDeePecker/resolve/main/data/test-00000-of-00001.parquet | Parquet | Primary source for labeled vulnerable/safe snippets (C, Python, JS). |
| **VulDeePecker (Full)** | https://huggingface.co/datasets/ijakenorton/vuldeepecker_for_ml/resolve/main/vuldeepecker_full_dataset.jsonl | JSONL | Backup/extended set if test split is insufficient. |
| **VulDeePecker (CWE)** | https://huggingface.co/datasets/rufimelo/vuldeepecker-cwe/resolve/main/data/train-00000-of-00001.parquet | Parquet | Used if CWE-specific categorization is required for FR-001. |
| **JavaScript (Small)** | https://huggingface.co/datasets/hchautran/javascript/resolve/main/data/test-00000-of-00038.parquet | Parquet | Supplementary JS code for diversity (if VulDeePecker JS is sparse). |
| **NIST Juliet Test Suite** | https://cwe.mitre.org/data/definitions/79.html | ZIP/Source | Canonical source for C/Java/C++ vulnerabilities. Used for baseline comparison and schema validation of `ground_truth_category`. |

**Dataset Fit Verification**:
- **Required Variables**: `ground_truth_label` (binary), `ground_truth_category` (CWE/Type), `code_snippet` (string), `language`.
- **Verification**: The `download.py` script includes a schema validation step. It checks if `ground_truth_category` exists in the downloaded Parquet/JSONL. If the community mirror lacks CWE labels, the pipeline falls back to the original NIST source or flags a coverage gap.
- **Gap Handling**: If the verified test split lacks sufficient C or Python samples, the pipeline will automatically fall back to the `vuldeepecker_full_dataset.jsonl` or the `vuldeepecker-cwe` split to meet the [deferred] sample cap (FR-001). If a specific category (e.g., "Buffer Overflow") is missing, the plan will report a coverage gap rather than fabricating data.

## Feature Extraction Strategy

### Structural Metrics (FR-003)
- **Tool**: `tree-sitter` (CPU-tractable).
- **Metrics**:
  - `ast_depth`: Maximum depth of the Abstract Syntax Tree.
  - `node_count`: Total number of AST nodes.
  - `cyclomatic_complexity`: Calculated via control flow graph (CFG) construction from AST.
- **Handling Malformed Code**: If `tree-sitter` fails to parse, `ast_depth` and `complexity` are recorded as `null`, and the snippet is logged for exclusion from regression (but included in feature extraction logs).

### Semantic Metrics (FR-004)
- **Taint-Source APIs**: Regex/Keyword matching against a curated list (e.g., `eval()`, `strcpy()`, `exec()`).
- **Sanitization**: Presence of known sanitization functions (e.g., `htmlspecialchars`, `strncpy`).
- **Embedding Similarity**:
  - **Model**: A small, CPU-optimized code encoder (e.g., `microsoft/CodeBERT-base` or a distilled variant like `Salesforce/codet5-small`).
  - **Strategy**: Compute cosine similarity between the snippet embedding and a set of "canonical vulnerable pattern" embeddings.
  - **Independence Constraint**: The "canonical vulnerable patterns" are derived from a **strictly independent** source (e.g., a subset of the NIST Juliet suite not used in the test set) to prevent tautological validation. If the embedding model was trained on general code, this is valid. If derived from the test set, it is invalid.
  - **Constraint**: Model must run in default precision (FP32/FP16) on CPU. No 8-bit quantization requiring CUDA.

## Statistical Analysis Plan (FR-005, FR-006, FR-010)

### 1. Performance Metrics
- **Calculations**: Precision, Recall, F1, ROC-AUC per vulnerability category and per model (LLM vs. Static Analyzer).
- **Baseline**: Static analyzers (Bandit for Python, cppcheck for C) run on the same snippets.

### 2. Correlation Analysis (FR-005)
- **Method**: **Point-Biserial correlation** between each feature (AST depth, complexity, etc.) and the binary `is_correct` outcome.
  - *Rationale*: Pearson correlation assumes continuous variables. Point-Biserial is the correct metric for binary vs. continuous relationships.
- **Correction**: **Benjamini-Hochberg (FDR)** correction applied to the family of tests for each category to control False Discovery Rate.
  - *Rationale*: Bonferroni is overly conservative for exploratory research with many correlated features, risking Type II errors. FDR provides a better balance.
- **Output**: Correlation coefficient ($r$), p-value, and adjusted p-value.

### 3. Regression Analysis (FR-006)
- **Model**: **Logistic Regression** (GLM with logit link) predicting `is_correct` (0/1) from all features.
  - *Rationale*: Multiple Linear Regression assumes a continuous, normally distributed dependent variable. Using it on a binary target violates assumptions, rendering R² and p-values invalid. Logistic Regression is the correct method.
- **Metrics**: **Nagelkerke Pseudo-R²**, coefficient significance (p-values).
- **Collinearity Check**: Variance Inflation Factor (VIF) calculated.
  - **Threshold**: Features with VIF > 5 are excluded to ensure stable coefficients.
  - *Rationale*: AST depth and node count are often definitionally correlated. Excluding high-VIF features prevents spurious coefficient estimates.
- **Success Criterion**: The model must explain a meaningful portion of variance (Pseudo-R² > 0.10) as per SC-002.

### 4. Baseline Comparison
- **Test**: McNemar's test comparing LLM predictions vs. Static Analyzer predictions on the same samples.
- **Goal**: Determine if the difference in performance is statistically significant (SC-006).

## Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (multiple CPU, ample RAM).
- **Memory Management**:
  - **Batch Size**: Reduced to **10 samples** (from 50) to accommodate 4-bit quantization overhead.
  - **Quantization**: LLM loaded with **4-bit quantization** using `bitsandbytes` (CPU-compatible path) or `llama.cpp` backend.
  - **Embedding Model**: `all-MiniLM-L6-v2` (small, CPU-fast).
- **Runtime**:
  - Target: ≤ 6 hours total.
  - Inference Budget: ≤ 43 seconds per sample.
  - Calculation: 5000 samples / 10 = 500 batches. 500 * (inference time + overhead) must fit in 6 hours. With 4-bit models, inference is fast enough.
- **Model Selection**:
  - **LLM**: A distilled model (e.g., `TinyLlama-1.1B` or `Phi-2` quantized to 4-bit) to ensure <7GB RAM.
  - **Embedding**: `all-MiniLM-L6-v2` or a code-specific distilled model.

## Decision Rationale

- **Why CPU-only?** The spec mandates execution on free-tier CI. GPU models are not viable.
- **Why Logistic Regression?** Binary outcome `is_correct` violates Linear Regression assumptions. Logistic Regression is statistically valid.
- **Why FDR?** Exploratory research with many features benefits from FDR over Bonferroni to avoid false negatives.
- **Why VIF > 5?** Standard threshold for multicollinearity in social science/research contexts.
- **Why Small Batch Size?** To prevent OOM errors on 7GB RAM while handling 4-bit quantization overhead.
- **Why Static Analyzers?** Constitution Principle VII and FR-008/009 mandate a baseline for "effectiveness" claims.

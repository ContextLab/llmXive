# Research: Quantifying Hallucination in LLM-Generated API Documentation

## Research Question

Does intrinsic code complexity (function length, naming style, cyclomatic complexity) correlate with the frequency of **hallucinated entities** (invented parameters) and **omitted entities** (missing parameters) in LLM-generated API documentation? Can an entity-overlap F1 metric reliably quantify this, and does it align with human judgment of **behavioral accuracy**?

## Dataset Strategy

| Dataset | Source/URL | Variables Used | Verification Status |
| :--- | :--- | :--- | :--- |
| **CodeSearchNet (Python)** | `https://huggingface.co/datasets/kejian/codesearchnet-python-raw/resolve/main/data/train-00000-of-00002-022fcdc5658ecd68.parquet` (and test split) | `code`, `docstring`, `func_name` | **Verified**: Direct Hugging Face URL. Contains source code and reference docstrings. |
| **CPU-tractable Models** | `Salesforce/codegen-350M`, `bigcode/starcoderbase-1b` | N/A (Inference) | **Verified**: Available via Hugging Face Transformers; confirmed to run on CPU within 7GB RAM limits for small batches. |
| **Manual Validation** | N/A (Human Annotation) | `function_id`, `human_score` | **Verified**: Generated via `validate.py` interface; no external dataset needed. |

**Note**: The "CPU-tractable" entry refers to the model capability, not a dataset. No external dataset URL is provided for models as they are fetched via the Hugging Face `transformers` library.

## Methodology

### 1. Data Ingestion & Preprocessing
- **Source**: Download CodeSearchNet Python parquet files.
- **Extraction**: Parse `code` (source), `docstring` (reference), and `func_name`.
- **Filtering**: Remove rows with missing code or empty docstrings.
- **Metrics Calculation**:
  - **Token Count**: Count tokens in **source code** (used for regression control).
  - **Naming Style**: Regex detection of `camelCase` vs `snake_case`.
  - **Cyclomatic Complexity**: Use `radon` library on source code.
  - **AST Extraction**: Parse source code to extract parameter names and return types (Ground Truth for *Automated Metric*).

### 2. Generation Pipeline (FR-002)
- **Models**: `codegen-350M` and `starcoderbase-1b`.
- **Prompt**: "Describe the function `{func_name}` in one sentence based on the code."
- **Constraints**:
  - Enforce one-sentence output via regex truncation (`.`, `!`, `?`).
  - **Reproducibility**: Pin `torch.manual_seed`, `numpy.random.seed`, `random.seed` in `generate.py` (T008b).
  - **Batching**: Batch size 1 to minimize memory footprint.

### 3. Hallucination Metric (FR-003) - Decomposed
- **Entity Extraction**: Use `spacy` (`en_core_web_sm`) to extract entities (parameters, return types) from:
  1. Source Code AST (Ground Truth for *Automated Metric*).
  2. Generated Description.
- **Metric Components**:
  - **Precision Hallucination**: (Entities in Generated NOT in AST) / (Total Entities in Generated). Measures "invented" facts.
  - **Recall Omission**: (Entities in AST NOT in Generated) / (Total Entities in AST). Measures "missing" facts.
  - **Composite Index**: Harmonic mean of Precision and Recall (F1).
- **Ground Truth Validity**: The AST is acknowledged as a *Proxy* for ground truth. It captures syntax but not implicit behavior (side effects, exceptions).

### 4. Statistical Analysis (FR-004, FR-008)
- **Correlation**:
  - **Continuous Predictors** (Token count, Complexity): Spearman rank correlation.
  - **Categorical Predictor** (Naming Style): Mann-Whitney U test (or Point-Biserial) to avoid invalid application of Spearman to nominal data.
- **Control**: Include **source code token count** as a covariate in Multiple Linear Regression. **Excluded**: Generated description token count (to avoid mathematical coupling with the F1 denominator).
- **Multicollinearity**: Calculate Variance Inflation Factors (VIF) for all predictors. If VIF > 5, apply dimension reduction (PCA) or remove correlated predictors.
- **Correction**: Apply Bonferroni correction to p-values for the three hypothesis tests (FR-005).
- **Causal Framing**: All findings framed as "correlation observed" (observational study).

### 5. Robustness & Validation (FR-006, FR-009, FR-011)
- **Sensitivity Analysis**: Sweep threshold $\in \{0.01, 0.05, 0.1\}$; report "high hallucination" rate.
- **Manual Validation (Independent Ground Truth)**:
  - Randomly sample a subset of data (stratified).
  - Human annotators score against a **Behavioral Consistency** rubric (FR-009):
    - **Score 3**: Description accurately reflects function logic, side effects, and exceptions.
    - **Score 2**: Minor discrepancies in logic or missing non-critical side effects.
    - **Score 1**: Major discrepancies in logic or missing required behavior.
    - **Score 0**: Description is factually wrong regarding core behavior (e.g., wrong return type, hallucinated side effects).
  - *Note*: This rubric is **independent** of the AST-based entity extraction used in the automated metric, resolving circular validation.
  - Normalize to [0, 1].
- **Calibration Check**: Correlate automated F1 score with normalized manual score. Flag if $r < 0.7$.

## Decision Rationale: Compute Feasibility

- **CPU-First Strategy**: The selected models (`codegen-350M`, `starcoderbase-1b`) are small enough to run on CPU with 16-bit precision within 7GB RAM.
- **No GPU Escape Hatch Needed**: These models do not require CUDA for faithful execution.
- **Data Streaming**: The CodeSearchNet parquet files are downloaded in full (or sampled subsets) to local disk before processing to avoid streaming overhead during generation, ensuring deterministic reproducibility.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni correction applied to avoid Type I errors (FR-005).
- **Power Limitation**: A sample size of sufficient functions provides adequate power for large effects; small effects may be underpowered.
- **Observational Nature**: No causal claims; regression controls for confounders (source length) but unmeasured confounders may exist.
- **Metric Validity**: Relies on entity-overlap F1 (AST-based). Validity is empirically checked against an independent human behavioral score (FR-011).
- **Mathematical Coupling**: Avoided by using `source_code_token_count` as the covariate, not `generated_description_token_count`.
- **Multicollinearity**: Addressed via VIF checks and potential PCA.
- **Categorical Correlation**: Addressed via Mann-Whitney U test for naming style.
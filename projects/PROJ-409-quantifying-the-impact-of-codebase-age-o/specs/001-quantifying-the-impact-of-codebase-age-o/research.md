# Research: Quantifying the Impact of Codebase Age on LLM Code Understanding

## 1. Research Question & Hypotheses

**Primary Question**: Is there a statistically significant correlation between the "age" of code (median commit age of files) and the structural/textual properties of that code as perceived by small-scale CodeLLMs?

**Hypotheses**:
- **H1 (Perplexity)**: Older code (higher median commit age) is associated with higher perplexity scores, potentially due to outdated coding patterns or lower representation in training data.
- **H2 (Structural Integrity)**: Older code is associated with lower `syntax_validity_rate` (proportion of snippets with valid syntax). *Note: This is a structural baseline, not a semantic correctness proxy.*
- **Null Hypothesis ($H_0$)**: There is no correlation between code age and model performance metrics (rho = 0), after controlling for complexity and length.

**Methodological Note**: This is an **observational study**. We frame results as "associational" only. We explicitly control for **cyclomatic complexity** and **token length** to ensure correlations are not driven by code quality or size differences.

## 2. Dataset Strategy

### 2.1 Target Repositories
We will select a small number of popular Python repositories. Selection criteria:
- High activity (to ensure git history exists).
- Diverse domains (e.g., data processing, web, utilities) to reduce domain bias.
- Publicly accessible on GitHub.

**Verified Datasets / Sources**:
The following repositories will be used as the source for code extraction. These are verified public GitHub URLs.
- `psf/requests` (URL: `)
- `pallets/flask` (URL: `)
- `urllib3/urllib3` (URL: `)
- `django/django` (URL: `)
- `pandas-dev/pandas` (URL: `)

*Note: If a repository is inaccessible or lacks sufficient git history, it will be skipped, and the next candidate will be selected to meet the minimum of 3 repos.*

### 2.2 Variable Fit & Verification
- **Predictor**: `median_commit_age` (days). Derived from `git log` of the **file** containing the snippets. Calculated once per file.
- **Outcomes**:
 - `mean_perplexity`: Mean perplexity of all snippets in the file.
 - `syntax_validity_rate`: Proportion of snippets in the file with valid syntax (0.0 to 1.0).
- **Covariates**:
 - `mean_cyclomatic_complexity`: Average complexity of snippets in the file.
 - `mean_token_length`: Average length of snippets in the file.

**Verification**: The datasets (GitHub repos) contain the necessary variables (source code and git history). No external dataset is required. The "age" variable is derived directly from the repository's git metadata, satisfying the requirement for verifiable temporal metadata.

## 3. Methodology

### 3.1 Data Extraction (US-1)
1. **Clone**: Clone target repositories to a temporary directory.
2. **Scan**: Traverse `.py` files.
3. **Extract**: Use Python's `ast` module to parse files and extract function definitions.
4. **Filter**:
 - Keep snippets with length $\ge$ 50 tokens.
 - Limit to 200 snippets per repository (randomly sampled if > 200 valid functions exist).
5. **Age Calculation**: For each **file**, run `git log --format=%ct` to get commit timestamps. Calculate the median age of these commits relative to the current date.
 - *Edge Case*: If < 2 commits, use the single commit age or 0, flagging `low_confidence_age`.
 - **Aggregation**: Store age once per file.

### 3.2 Inference & Metric Generation (US-2)
1. **Model**: `Salesforce/codegen-350M-mono` (or similar small CodeLLM).
 - **Loading**: Load in 8-bit quantization using `bitsandbytes` (CPU-compatible) or `llama.cpp` if applicable, ensuring memory < 4 GB.
 - **Device**: Explicitly set `device="cpu"`. No CUDA.
2. **Perplexity**: Calculate perplexity of the snippet text under the model.
3. **Syntax Validity**:
 - **Check**: For each snippet, run a static syntax check (e.g., `ast.parse()`).
 - **Rate**: Calculate `syntax_validity_rate` as the proportion of valid snippets per file.
 - **Complexity**: Calculate `cyclomatic_complexity` for each snippet (using `networkx` or `radon`).
 - **Timeout**: Enforce a per-snippet timeout (e.g., 30s). If exceeded, record `NaN`.
4. **Robustness**: Log all failures. Continue processing.

### 3.3 Statistical Analysis (US-3)
1. **Aggregate**: Group data by `file_path` and `repo_url`. Calculate mean perplexity, mean complexity, mean length, and syntax validity rate for each file.
2. **Filter**: Remove rows with `NaN` in any metric.
3. **Test**: Perform **Spearman rank correlation** between `median_commit_age` and:
 - `mean_perplexity`
 - `syntax_validity_rate`
4. **Control**: Use **partial Spearman correlation** to control for `mean_cyclomatic_complexity` and `mean_token_length`. This isolates the effect of age from code quality and size.
 - *Note*: Since `syntax_validity_rate` is a proportion (0.0-1.0), Spearman correlation is appropriate. Point-Biserial is incorrect for continuous proportions.
5. **Correction**: Since only two primary tests are run, Bonferroni correction is not strictly necessary but will be noted. If additional analyses are added, family-wise error correction will be applied.
6. **Power**: Acknowledge that with ~800 samples (aggregated to ~200-500 files), the study has high power to detect moderate correlations (rho > 0.1), but may lack power for very weak effects.

## 4. Compute Feasibility & Rationale

**Constraint**: 2 CPU cores, 7 GB RAM, 6 hours.

**Rationale for Model Choice**:
- **CodeGen-350M**: ~350M parameters. In low-bit quantization, this occupies a moderate amount of RAM. This leaves ample room for the Python runtime and data structures within the specified memory limit.
- **Inference Speed**: On a multi-core CPU, generating perplexity for a short token snippet takes a few seconds. For a representative set of snippets, total time is expected to be well within the 6-hour limit.
- **Quantization**: Using `bitsandbytes` or native `torch` 8-bit support is critical to avoid OOM errors. We will explicitly disable GPU device maps.

**Decision**: We will use `transformers` with `load_in_8bit=True` (if supported on CPU) or `torch_dtype=torch.float16` (if memory permits, but 8-bit is safer) on CPU. If `bitsandbytes` CPU support is unstable, we will fallback to standard `float32` with a smaller model (e.g., TinyLlama-1.1B might be too large for 8-bit CPU inference in this specific runner; CodeGen-350M is the safest bet).

## 5. Limitations & Assumptions

- **Causal Claims**: This is an observational study. We will frame results as "associational" only.
- **Age Proxy**: "Median commit age" is a proxy for code logic age. A file might be old but contain modern logic if it was copied from a newer project.
- **Model Bias**: Small models may have different biases than large models (e.g., better at older syntax).
- **Syntax Validity**: `syntax_validity_rate` is a structural baseline, not a semantic correctness proxy. We explicitly acknowledge this limitation and control for complexity to mitigate confounding.
- **Test Coverage**: We do not rely on unit tests for correctness; we use static analysis to ensure structural validity.

## 6. Success Metrics

- **SC-001**: Correlation coefficient (rho) and p-value for Age vs. Perplexity (controlled for complexity/length).
- **SC-002**: Correlation coefficient (rho) and p-value for Age vs. Syntax Validity Rate (controlled for complexity/length).
- **SC-003**: Total runtime < 6 hours.
- **SC-004**: Data completeness $\ge$ [deferred] (valid non-NaN metrics at file level).


# Research: Quantifying Hallucination in LLM-Generated API Documentation

## Dataset Strategy

The study relies on the **CodeSearchNet Python** subset, a verified open-source dataset containing Python functions with source code and reference docstrings.

| Dataset | Source URL | Access Method | Variables Available | Suitability |
|:--- |:--- |:--- |:--- |:--- |
| CodeSearchNet (Python) | ` (Train) <br> ` (Test) | `datasets.load_dataset("parquet", data_files=[...])` with `streaming=True` | `code` (source), `docstring` (reference), `function_name` | **High**: Contains source code (ground truth), reference docstrings, and function names. No external variables needed. |

**Dataset Verification**:
- The dataset is publicly available on Hugging Face and supports programmatic downloading via the `datasets` library.
- It contains the necessary variables: `source_code` (for AST extraction and ground truth), `docstring` (for reference), and `function_name`.
- **Note**: The dataset does not contain "post-task anxiety" or "personality measures" (irrelevant to this study), but it *does* contain the required code metrics (length, complexity, naming) and the ground truth (source code) needed for entity extraction.
- **No Gated Data**: No access credentials or Data Use Agreements are required.

## Model Strategy

Two CPU-tractable models are selected to balance performance and feasibility on the GitHub Actions free tier (2 CPU, ~7GB RAM).

| Model | Source | Hardware Target | Rationale |
|:--- |:--- |:--- |:--- |
| `Salesforce/codegen-350M` | Hugging Face Hub | CPU (16-bit) | Small parameter count (350M) allows inference on CPU without exceeding RAM limits. Proven for code generation. |
| `bigcode/starcoderbase-1b` | Hugging Face Hub | CPU (16-bit) | Slightly larger (1B) but still feasible on CPU with careful batching/streaming. Provides a robustness check against model variance. |

**Decision/Rationale**:
- **CPU-First**: Both models are selected specifically because they have a faithful CPU-tractable form. No GPU escape hatch is required. The plan explicitly targets CPU to ensure compatibility with the free-tier runner.
- **No Synthetic Data**: The plan uses the real CodeSearchNet dataset. No synthetic stand-ins are used.
- **Streaming**: The dataset will be processed via `streaming=True` to ensure the full dataset (or a large sample) can be processed without loading it all into RAM.

## Statistical Rigor & Methodology

### Hypothesis Testing
The study tests the association between intrinsic code characteristics and hallucination rates.
- **Null Hypothesis ($H_0$)**: There is no correlation between code complexity/length/naming style and the hallucination index.
- **Alternative Hypothesis ($H_1$)**: A significant correlation exists.

**Statistical Methods**:
1. **Correlation**: Spearman rank-correlation coefficient (non-parametric) to assess monotonic relationships between predictors (token count, naming style, complexity) and the Hallucination Index.
2. **Regression**: Multiple Linear Regression (MLR) with the Hallucination Index as the dependent variable.
 - **Predictors**: Token count, Naming Style (categorical encoded), Cyclomatic Complexity.
 - **Covariate**: Generated description token count (to control for length bias).
 - **Encoding Strategy**: `naming_style` will be One-Hot Encoded with `drop_first=True` (to avoid the dummy variable trap) before regression fitting.
 - **Multicollinearity Check**: A Variance Inflation Factor (VIF) check will be performed on all predictors before model fitting. If VIF > 5 for any predictor, the model will be re-specified or the predictor excluded.
 - **Mathematical Coupling Check**: A preliminary check will verify that `naming_style` is not mathematically coupled to the entity extraction logic (e.g., if `spacy` treats casing differently). If coupling is detected, the predictor will be excluded.
 - **Assumption**: Observational data. Claims will be framed as "associational," not causal.
3. **Multiplicity Correction**: Bonferroni correction applied to p-values of the three correlation tests to control family-wise error rate (FR-005).
4. **Power Analysis**: A sample size of **1500+ functions** is targeted. This is calculated based on the power requirements for a multiple regression model with 3-4 predictors to detect a small effect size ($\rho > 0.1$) with power $\ge 0.8$ (accounting for the reduced power compared to bivariate correlation). If the dataset yields a limited number of valid records, the power limitation will be explicitly stated.

### Measurement Validity
- **Hallucination Index**: Defined as the entity-overlap F1 score (0.0 to 1.0) between entities extracted from the generated text and entities extracted from the **source code AST**.
- **Validation**: A stratified random sample of $\ge 5\%$ of the dataset will be manually verified.
 - **Rubric Independence**: The manual rubric assesses **semantic intent** and **runtime behavior** (e.g., "Does the description accurately describe what the function *does*?"), not just the static AST signature. This ensures the manual score is an independent ground truth, avoiding circular validation where both metrics rely on the same AST extraction logic.
 - **Scoring**: 0-3 rubric (normalized to 0-1). The correlation between the automated F1 score and the manual score will be calculated. If $r < 0.7$, the metric calibration is flagged as "needs review" (FR-011).

### Sensitivity Analysis
- The "high hallucination" rate (defined as `index >= threshold`) will be computed for thresholds $\in \{0.01, 0.05, 0.1\}$ to ensure results are not artifacts of an arbitrary cutoff (FR-006).

## Compute Feasibility Plan

- **Memory Management**:
 - Use `torch.backends.mkl.set_num_threads(1)` to limit thread usage.
 - Process data in batches of 1 (or small batches if memory allows) to avoid OOM.
 - Use `streaming=True` for dataset loading to avoid loading the full CSV/Parquet into RAM.
- **Analysis Memory Strategy**:
 - The statistical analysis (Correlation, Regression) requires the full feature matrix.
 - If the sample size exceeds 1000 functions, the pipeline will materialize the feature matrix in a memory-mapped file (`numpy.memmap` or `polars` with memory mapping) or process in chunks if the full matrix exceeds 7GB.
 - If the full matrix fits in RAM (expected for N=1500), it will be loaded directly. If N > 5000, a fixed-seed random sample of 1500-2000 will be used for the regression step to ensure stability, with the power limitation noted.
- **Time Limits**:
 - Target: 1500 functions in < 4 hours.
 - If the full dataset (e.g., a large-scale collection of functions) is targeted, the plan assumes streaming and batch processing will keep the job [deferred]. If not, a fixed-seed random sample of 1500-2000 functions will be used, with the power limitation noted.

## Ethical Considerations

- **Bias**: The dataset may contain code from various domains. The analysis will not make claims about "good" or "bad" code, only about statistical associations between code properties and hallucination rates.
- **Privacy**: The CodeSearchNet dataset is open source. No PII is expected, but the pipeline will include a PII scan step (Constitution Principle III) before committing any derived data.
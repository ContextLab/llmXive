# Research: Evaluating the Impact of Code Complexity on LLM Code Understanding

## Research Question

Does code complexity (Cyclomatic Complexity, Halstead Volume, Maintainability Index) negatively correlate with **Phi-3-mini-4k-instruct** performance across Summarization, Bug Detection, and Code Completion tasks?

*Note: The hypothesis is explicitly scoped to the capabilities of the Phi-3 model due to compute constraints.*

## Dataset Strategy

| Dataset | Source URL | Usage | Notes |
|:--- |:--- |:--- |:--- |
| **CodeSearchNet (Python)** | ` | Primary source for code snippets and ground truth (docstrings, original code). | Will be filtered to Python subset. Parquet format ensures efficient streaming. |
| **Derived Bug Dataset** | *Programmatic Generation* | Ground truth for Bug Detection. | Created by injecting synthetic bugs (operator swaps, off-by-one) into a subset of CodeSearchNet functions. |

**Dataset Variable Fit Verification**:
- **Required**: Source code, docstrings (for Summarization GT), original code (for Completion GT), injected bugs (for Bug Detection GT).
- **Verified**: CodeSearchNet Python subset contains `func_code` and `func_doc`.
- **Gap**: The raw dataset does **not** contain pre-injected bugs or completion continuations.
- **Mitigation**: The implementation includes a **Derived Dataset Generation** step in `02_complexity_annotation.py` to programmatically inject bugs and truncate code for completion tasks. This creates a *derived* artifact, not a raw download, to satisfy FR-003.

**Stratified Sampling Strategy**:
To address the heavy-tailed distribution of code complexity:
1. Calculate complexity metrics for a large initial sample (e.g., [deferred] snippets).
2. Identify the top % of functions by Cyclomatic Complexity.
3. Sample an approximately equal proportion of the final dataset from this "High" tail, and the remaining proportion from the rest (Low/Medium).
4. This ensures sufficient statistical power to detect correlations in the high-complexity region.

## Model Strategy

- **Primary Model**: `microsoft/Phi-3-mini-4k-instruct`
- **Rationale**:
 - **Feasibility**: The spec-requested `codellama/CodeLlama-7b-Instruct-hf` requires ~14 GB RAM in default precision, exceeding the 7 GB CI limit.
 - **Capacity Justification**: Phi-mini is state-of-the-art for its size, supports 4k context, and has demonstrated reasoning capabilities sufficient for code tasks. While it may have a "floor effect" on very complex code, the study explicitly tests **Phi-3's** performance, not a generic "LLM" capability. If Phi-3 fails to correlate, the conclusion is specific to this model tier.
 - **Inference Configuration**:
 - `device`: `cpu`
 - `torch_dtype`: `torch.float16` (if supported) or `torch.float32`
 - `max_new_tokens`: 256 (summarization/completion), 128 (bug detection)
 - `temperature`: 0.0 (deterministic for reproducibility)
 - `batch_size`: Dynamically adjusted based on memory guard (max 1-2 snippets per batch).

## Statistical Methodology

1. **Correlation Analysis**:
 - **Metric**: Spearman's Rank Correlation Coefficient (ρ).
 - **Rationale**: Robust to non-normality and outliers.
 - **Correction**: Bonferroni correction applied for multiple comparisons (3 tasks × 3 metrics = 9 tests). Adjusted α = 0.05 / 9 ≈ 0.0056.

2. **Generalized Linear Model (GLM) with Splines**:
 - **Family**: Binomial (Logit link) for binary outcomes (Pass/Fail).
 - **Family**: Gaussian (Identity link) for continuous outcomes (BLEU/ROUGE).
 - **Variables**:
 - *Dependent*: Task Performance (Score).
 - *Independent*: Cyclomatic Complexity, Halstead Volume, Maintainability Index (modeled with natural cubic splines to capture non-linearity).
 - *Controls*: Snippet Length (tokens), Task Type (categorical).
 - **Collinearity & Size Control**:
 - **VIF Check**: Variance Inflation Factor calculated for all predictors.
 - **PCA Fallback**: If **VIF > 5**, the plan mandates **Principal Component Analysis (PCA)** to generate orthogonal complexity components. The GLM will then use these components instead of raw metrics.
 - **Length Orthogonalization**: Snippet length will be orthogonalized against complexity metrics or included as a covariate only after VIF checks to disentangle "size" from "complexity".

3. **Binning Strategy (Descriptive Only)**:
 - Complexity scores will be binned into **Low (0-33rd percentile)**, **Medium (34-66th)**, and **High (67-100th)** tertiles.
 - **Maintainability Index**: Due to potential negative values, binning will be performed using **quantile-based** methods specific to its distribution.
 - **Usage**: Binning is used for descriptive visualization (ANOVA/Kruskal-Wallis) and robustness checks, **not** as the primary inference method. Continuous analysis with splines is prioritized.

## Construct Validity Mitigation

- **Synthetic Bugs**: The "Bug Detection" task uses programmatic bug injection. This is a known limitation. The research claims are explicitly scoped to "synthetic bug detection" and not "natural bug detection". The study acknowledges that detecting simple injected bugs may not generalize to complex real-world defects.
- **Model Capacity**: The hypothesis is framed as "Phi-3's performance vs. complexity". If Phi-3 lacks the reasoning depth to understand complex code, the study may find no correlation. This is a valid finding for the Phi-3 model tier, not a failure of the complexity hypothesis generally.

## Feasibility & Constraints

- **Runtime**: Data acquisition and annotation are fast (<30 min). Inference is the bottleneck. With Phi-mini on CPU cores, inference speed is ~2-4 tokens/sec. Processing a substantial set of snippets across 3 tasks, yielding thousands of prompts. Estimated time: [deferred] or less. Well within 6h limit.
- **Memory**: Phi-3-mini model size (~2.5 GB) + overhead fits within 7 GB. Memory guard will abort if usage > 6.5 GB.
- **Data Volume**: Will sample a stratified subset of valid functions to ensure high-quality parsing and fit within disk limits.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Radon Parse Failure** | High | Snippets with syntax errors are logged and excluded. |
| **Context Window Exceeded** | Medium | Truncate code to a predefined token limit; log as "context_exceeded". |
| **Model OOM** | Critical | Memory guard script monitors RAM; reduces batch size to 1 or aborts. |
| **Bug Detection GT Missing** | High | Programmatic bug injection (random operator swap) for a subset of snippets; scope limited to "synthetic bug detection". |
| **High Complexity Tail Missing** | High | Stratified sampling ensures representation of top [deferred] complexity. |
| **Collinearity** | High | VIF check with mandatory PCA fallback if VIF > 5. |
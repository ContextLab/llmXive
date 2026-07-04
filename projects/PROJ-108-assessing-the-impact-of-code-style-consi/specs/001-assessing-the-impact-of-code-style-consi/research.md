# Research: Assessing the Impact of Code Style Consistency on LLM Code Understanding

## Dataset Strategy

The study utilizes two primary datasets for code samples and ground truth. All sources are verified and cited below.

| Dataset | Description | Source URL | Usage |
|:--- |:--- |:--- |:--- |
| **CodeSearchNet (Python)** | Large-scale dataset of Python code with docstrings. | ` | Source for code samples and reference docstrings for summarization tasks (BLEU). |
| **Defects4J (Context)** | Java/Python bug localization dataset with context. | ` | Source for bug-localization tasks (Precision/Recall/F1). *Note: Primarily Java. Python subset will be filtered.* |
| **Defects4J (Adapted)** | Adapted Defects4J dataset for prompt engineering. | ` | Alternative source for bug-localization ground truth. *Note: Language coverage mixed; Python samples will be filtered.* |

**Dataset Fit Verification**:
- **CodeSearchNet**: Contains `code` (source) and `docstring` (target) fields required for summarization (FR-004).
- **Defects4J**: Contains `code`, `bug_line` (target), and `context` required for localization (FR-004).
- **Language Check**: Defects4J is primarily Java. The pipeline will filter for Python samples. If the Python subset is < 50 samples, the plan will fallback to a synthetic Python bug dataset (e.g., from `santander` or similar verified source) to ensure FR-004 is met for the Python domain.
- **Missing Variables**: No dataset explicitly contains "file age" or "cyclomatic complexity" as pre-computed columns. The plan will compute these dynamically during the `01_style_scoring.py` phase using `radon` (complexity) and repository metadata (file age) if available, or proxy with file size/line count if age is missing.

## Methodology & Statistical Rigor

### 1. Style Consistency Scoring (FR-001, FR-002)
- **Tools**: `pylint` (for indentation variance, naming convention violations) and `radon` (for line length variance).
- **Normalization**: Raw scores will be min-max normalized to the unit interval. based on the distribution of the specific dataset subset.
- **Stratification**: Samples will be split into High (top tertile), Medium (middle tertile), and Low (bottom tertile) groups. Thresholds are deferred to data distribution analysis.
- **Note**: Stratification is a heuristic for visualization and group comparison. The primary continuous analysis uses regression.

### 2. Inference (FR-003, FR-007)
- **Model**: `huggingface/starcoder-1b` (CPU-optimized).
- **Constraints**: Max tokens = 64. Timeout = 30s per sample. Memory limit = 7 GB.
- **Fallback**: If a sample causes OOM or timeout, it is logged and skipped (FR-007).
- **Dynamic Sampling**: The pipeline will estimate the maximum number of samples processable within 6 hours (approx. 30s/sample = 720 samples). If the required power analysis dictates N > 720, the study will proceed with N=720 and report the "Achieved Power" and "Confidence Intervals", acknowledging the limitation rather than arbitrarily capping N and claiming validity.

### 3. Statistical Analysis (FR-005, FR-006, FR-008, FR-009)
- **Primary Test (Group Difference)**: One-way ANCOVA on BLEU scores with `consistency_group` as factor and `file_size` (proxy for complexity) as covariate. *Note: `file_age` is dropped if proxied by `file_size` to avoid confounding.*
- **Primary Test (Continuous)**: Linear Regression of performance on continuous `style_score` to measure correlation (SC-001, SC-004).
- **Secondary Test**: Two-sample t-test (High vs. Low) on F1 scores.
- **Correction**: Bonferroni correction applied to the family of tests (ANCOVA + t-test). Tukey HSD for post-hoc pairwise comparisons if ANCOVA is significant.
- **Pre-Check Gate (FR-009)**: Before running main tests, the pipeline verifies that the effect size (Cohen's d) between High and Low groups is > 0.5. If not, the pipeline halts and reports "Insufficient Group Separation".
- **Power Analysis**: **A priori** power analysis will be performed. If the required sample size exceeds the compute budget, the study will report the "Achieved Power" and "Confidence Intervals" without labeling the study as merely "exploratory" based on post-hoc power.
- **Causal Framing**: As data is observational, claims are strictly associational. Unmeasured confounders (e.g., developer expertise) are acknowledged as a limitation.

### 4. Ablation & Robustness (FR-008, SC-005)
- **Ablation**: Regression of performance on style score with and without complexity controls to verify independent predictive power.
- **Robustness**: If time permits, a second model (CodeLlama 7B or a smaller CPU-tractable proxy) will be run on a subset, and the Spearman correlation of effect directions will be computed.

## Computational Feasibility
- **Hardware**: GitHub Actions free-tier (multi-core CPU, multi-GB RAM).
- **Strategy**:
 - Use `datasets.load_dataset` with streaming or partial loading to stay within RAM.
 - Limit inference batch size to sequential processing or small batches. to prevent OOM.
 - Use `scikit-learn` and `statsmodels` (CPU-only) for all statistical tasks.
 - No GPU/CUDA libraries.
 - **Timeout Enforcement**: The `timeout` command (Linux) or a wrapper script will enforce the 6-hour limit and capture exit code 137.

## Missing Data Handling
- **File Age**: If git history is unavailable for >20% of samples, `file_age` will be imputed with the median age of the dataset subset. If imputation is not feasible, `file_age` will be dropped from the ANCOVA to avoid bias.
- **Complexity**: `file_size` (lines of code) will be used as the primary complexity proxy to avoid multicollinearity with style metrics derived from the same AST.
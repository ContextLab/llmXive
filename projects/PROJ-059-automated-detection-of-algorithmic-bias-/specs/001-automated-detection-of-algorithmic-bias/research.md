# Research: Automated Detection of Algorithmic Bias in Public Code Repositories

## 1. Problem Statement & Hypothesis

**Problem**: Algorithmic bias in software often stems from implicit assumptions encoded in variable names, comments, and design choices. While fairness metrics (Demographic Parity, Equalized Odds) are well-defined for *executed* models, there is no standard method to predict potential bias from *static* code artifacts alone.

**Hypothesis**: A statistically significant positive correlation exists between "Textual Bias Scores" (frequency of demographic terms/stereotypes in code comments/variables) and simulated fairness disparity metrics, even when the simulation uses an independent bias injection parameter.

**Methodological Framing**: This is an **observational study**. We cannot randomize code styles. Therefore, we frame findings as **associational**. The "Fairness Metric" is a **simulated proxy** derived from synthetic data, not a measurement of the repository's actual execution. The simulation uses a controlled `injected_skew_magnitude` parameter to test the sensitivity of the correlation hypothesis.

## 2. Dataset Strategy

### Verified Datasets
Per the project constraints, we use only verified, open, and programmatic sources:

| Dataset | Source URL | Usage | Access Method |
| :--- | :--- | :--- | :--- |
| **VADER Sentiment** | `https://huggingface.co/datasets/bartoszmaj/vader_sentiment_full/resolve/main/data/train-00000-of-00001-16eab957b5f41fe3.parquet` | Validation of VADER thresholds against ground truth sentiment labels. | `datasets.load_dataset(..., data_files=...)` |
| **VADER (Alt)** | `https://huggingface.co/datasets/samdotme/vader-speak/resolve/main/data/train-00000-of-00001.parquet` | Supplementary validation data if primary source is insufficient. | `datasets.load_dataset(...)` |
| **VADER (Video)** | `https://huggingface.co/datasets/samdotme/vader-speak-video/resolve/main/data/train-00000-of-00001.parquet` | Supplementary validation data. | `datasets.load_dataset(...)` |
| **AIF360** | NO verified source found | **Not used** for data download. Used only as a library (`pip install aif360`) for metric calculation. | `pip install` |

### Data Availability & Feasibility
- **GitHub Repositories**: The plan assumes access to the GitHub API for downloading a curated list of 500 public Python repositories. Rate limits are handled via exponential backoff. If a repo cannot be downloaded, it is skipped (FR-014, SC-005).
- **Synthetic Data**: Generated locally using `numpy`. No external download required.
- **Validation Set**: A small, curated CSV of 200 manually labeled comments (`data/curated/validation_comments.csv`) is generated as part of the setup, not downloaded from an external source, to ensure the ground truth is controlled and reproducible.

### Dataset-Variable Fit
- **Predictors**: Variable names, function names, string literals (extracted via AST).
- **Outcome**: Simulated Fairness Metrics (Demographic Parity, Equalized Odds).
- **Covariates**: `injected_skew_magnitude` (controlled input), repository size (LOC).
- **Fit Check**: The VADER dataset provides sentiment labels to validate the *method* of scoring, but the actual analysis uses the code's comments. The synthetic data generator produces the *outcome* variable. There is no mismatch; the synthetic data is designed specifically to lack the predictor variables, ensuring independence (Constitution Principle VI).

## 3. Methodology & Statistical Rigor

### Phase 1: Static Artifact Extraction (FR-001, FR-002, FR-003)
1.  **Parsing**: Use Python `ast` to traverse the AST of every `.py` file.
2.  **Tokenization**: Normalize `camelCase` and `snake_case` into tokens.
3.  **Lexicon Matching**: Compare tokens against a curated demographic lexicon (e.g., gendered terms, stereotypes). Count matches.
4.  **Sentiment Analysis**: Apply VADER (via `nltk`) to string literals and comments. Compute compound scores.
5.  **Aggregation**: Calculate per-file scores, then aggregate to repository level using arithmetic mean (FR-009).

### Phase 2: Simulation & Bias Injection (FR-004, FR-005, FR-011)
1.  **Synthetic Data Generation**: Generate $N=1000$ samples per repository using `numpy`.
    -   **Features**: Domain-neutral (Gaussian/Uniform).
    -   **Sensitive Attribute**: Randomly assigned (binary).
    -   **True Label**: Derived from features + noise.
    -   **Constraint**: No tokens from source code are used (FR-015).
2.  **Bias Injection**: Introduce a controlled skew `injected_skew_magnitude` to the positive class rate of the sensitive group.
    -   If `magnitude` = 0, disparity $\le 0.01$ (statistical noise) (FR-011).
3.  **Metric Calculation**: Compute Demographic Parity and Equalized Odds using `fairlearn` or `aif360`.

### Phase 3: Correlation & Validation (FR-006, FR-007, FR-008)
1.  **Correlation**: Compute Spearman's rank correlation between `Textual Bias Score` and `Fairness Disparity`.
    -   **Rationale**: Data is likely non-normal and zero-inflated.
2.  **Multiple Comparison Correction**: Apply **Bonferroni correction** to p-values when testing multiple hypotheses (e.g., variable names vs. comments, or multiple metrics).
3.  **Sensitivity Analysis**: Sweep $\alpha \in \{0.01, 0.05, 0.10\}$ and report the number of "High Risk" repositories (FR-008).
4.  **Validation**: Compute Cohen's Kappa between VADER scores and the manual validation dataset. Require $\kappa \ge 0.6$ to proceed (FR-013).

### Statistical Assumptions & Limitations
-   **Causal Inference**: None claimed. Results are associational.
-   **Power**: $N=500$ repositories provides reasonable power for correlation detection, but the synthetic sample size per repo ($N=1000$) is fixed.
-   **Collinearity**: Predictors (variable names vs. comments) may be correlated. We report them separately but acknowledge potential collinearity in the discussion.
-   **Measurement Validity**: VADER is a standard tool for short text, but code comments may contain domain-specific jargon that skews sentiment. The validation step (FR-013) mitigates this.

## 4. Compute Feasibility (CPU-First)

-   **Environment**: GitHub Actions Free Tier (2 cores, ~7 GB RAM).
-   **Strategy**:
    -   **Streaming**: GitHub repos are cloned one by one; memory is released after processing each repo.
    -   **Sampling**: Synthetic data generation is $O(N)$ with $N=1000$, trivial for CPU.
    -   **Libraries**: `scipy`, `numpy`, `pandas`, `fairlearn` are all CPU-optimized. No GPU required.
    -   **Time Limit**: 500 repos $\times$ ~5 mins/repo (parsing + simulation) = ~41 hours. This exceeds the 6h limit.
    -   **Optimization**: The plan must **parallelize** the repo processing (using `multiprocessing` or `joblib`) across the 2 cores, and potentially reduce the sample size to $N=500$ if time is critical, or limit the repo count to 100-200 for the initial run.
    -   **Revised Plan**: Process 100 repositories in the initial run to meet the 6h constraint, scaling to 500 if time permits or if the runner is upgraded. *Correction*: The spec demands 500 repos in 6h. We must optimize parsing.
    -   **Optimization Strategy**:
        1.  Use `ast` with `visit` to skip non-leaf nodes where possible.
        2.  Limit the number of Python files per repo to the top 50 largest files.
        3.  Use `joblib` to parallelize the 500 repos across 2 cores (250 each).
        4.  Synthetic data generation is negligible.
        5.  If 500 repos in 6h is impossible, the spec's SC-003 is a blocking constraint. We will aim for 500 but flag the risk. If the job fails, we will report the actual count processed.

## 5. Decision Rationale

-   **CPU vs GPU**: CPU is sufficient. Synthetic data and AST parsing are not GPU-bound.
-   **VADER**: Chosen for speed and suitability for short text (comments).
-   **Spearman vs Pearson**: Spearman chosen for robustness to non-normality and outliers in bias scores.
-   **Bonferroni**: Chosen for strict control of family-wise error rate in multiple hypothesis testing.

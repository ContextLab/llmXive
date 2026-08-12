# Research: Statistical Bias in Pre-Print Server Publication Trends

## 1. Problem Statement & Research Question

**Question**: Do pre-print versions of scientific papers exhibit statistically significant "bias" (e.g., p-hacking, effect size inflation) compared to their final peer-reviewed journal versions?

**Hypotheses**:
- **H1**: The distribution of p-values in pre-prints shows a higher density just below 0.05 compared to journal versions (indicative of p-hacking).
- **H2**: Effect sizes reported in pre-prints are systematically larger than those in journal versions ($\Delta$ES > 0), suggesting correction during peer review.
- **H3**: These effects are robust across significance thresholds (0.01, 0.05, 0.1).

## 2. Dataset Strategy

### Verified Datasets
The project relies exclusively on the following verified sources for metadata and linkage:
- **OpenAlex Works Metadata**: Used to match pre-prints to journal DOIs.
  - Source: `https://huggingface.co/datasets/openalex/works` (or the specific metadata-only snapshot containing `arxiv_id`, `bioRxiv_id`, `doi`, `title`, `authors`).
  - *Verification*: We will verify the presence of `bioRxiv_id` in the HF dataset version. If the HF subset lacks `bioRxiv_id` for a specific record, the system will fallback to streaming the OpenAlex API for that specific ID to retrieve the missing linkage field.
  - *Note*: The full OpenAlex dump is too large for direct loading; the plan uses the verified Hugging Face metadata-only dump or streams the data to identify papers with `arxiv_id` or `bioRxiv_id` fields and corresponding `doi` fields.

### Data Acquisition Plan
1.  **Source Identification**: Use the verified OpenAlex Hugging Face dataset to filter for papers with `arxiv_id` or `bioRxiv_id` published between recent years and 2023.
2.  **Matching Logic**:
    -   Extract `title`, `authors`, and `doi` from OpenAlex.
    -   Fuzzy match `title` against arXiv/bioRxiv metadata (scraped via `arxiv` Python package or direct API) to confirm the pre-print ID.
    -   If a match is found, link the pre-print version to the journal `doi`.
3.  **Variable Fit Verification**:
    -   **Required Variables**: `p-value`, `effect-size`, `sample-size (N)`, `statistical-method`.
    -   **Verification**: The OpenAlex metadata provides the *linkage* (ID, Title, Authors). The *statistical values* are NOT in OpenAlex; they must be extracted from the full-text PDFs.
    -   **Feasibility**: This is feasible. We download the PDFs (via arXiv API for pre-prints and Crossref/OpenURL for journals) and parse them. The dataset strategy is: **Metadata from OpenAlex (verified) + Content from PDFs (scraped/processed)**.

### Data Constraints & Handling
-   **Access**: OpenAlex data is open. arXiv/bioRxiv PDFs are open. No credentials required.
-   **Size**: The full OpenAlex dump is large in scale. We will **stream** the verified Hugging Face subset or query the OpenAlex API for specific IDs to stay within the GB RAM limit.
-   **Missing Data**: If a paper lacks a journal DOI in OpenAlex, it is excluded from the matched analysis (logged as "unmatched"). If a PDF is missing or unreadable, the pair is excluded from analysis (logged as "extraction failure").

## 3. Methodology & Statistical Rigor

### 3.1. Data Cleaning & Filtering
-   **Inclusion**: Papers with both pre-print and journal versions; statistical tests reported (t-test, ANOVA, regression, etc.).
-   **Exclusion**:
    -   Theoretical papers or case studies (no empirical stats).
    -   Pairs where the statistical method changes (e.g., t-test $\to$ regression) -> Flagged as "methodological shift".
    -   Pairs where sample size (N) changes by > 20% -> Flagged and excluded from $\Delta$ES calculation (per FR-006).
    -   **Censored P-Values**: P-values reported as inequalities (e.g., "p < 0.05") are treated as interval-censored data. For p-curve analysis, they are excluded per Simonsohn et al. to avoid noise. For density ratio estimation, we use a likelihood-based method that incorporates interval-censored data. If >20% of p-values are censored, we will use a Kaplan-Meier estimator adapted for p-values or exclude the density ratio metric for that subset to avoid high variance.

### 3.2. Statistical Tests

#### A. Distributional Shift (Primary Analysis)
-   **Method**: Kolmogorov-Smirnov (KS) test and density ratio estimation.
-   **Input**: Right-skewed distribution of significant p-values ($p < 0.05$).
-   **Correction**: If stratifying by field (e.g., Physics vs. Biology), **Bonferroni correction** will be applied to the primary hypothesis tests to control the family-wise error rate.
-   **Output**: KS statistic and p-value; density ratio magnitude at p=0.05.
-   **Note**: P-curve analysis is used as a **secondary diagnostic** to estimate evidential value. If comparing p-curve estimates (estimated power), a **bootstrap test of the difference** in estimated power will be performed to ensure statistical validity.

#### B. Effect Size Comparison (Magnitude Analysis)
-   **Metric**: $\Delta$ES = $ES_{preprint} - ES_{journal}$.
-   **Test**: Paired t-test (if $\Delta$ES is normally distributed) or Wilcoxon signed-rank test (if non-normal).
-   **Censored Data**: For effect sizes reported as inequalities or ranges, we will use a **Paired Interval-Censored Bootstrap** approach. This involves resampling the paired differences while respecting the interval bounds, rather than using standard Tobit regression (which assumes independence) or simple imputation.
-   **Assumption**: Observational study. Claims are associational ("pre-prints report higher effect sizes") not causal ("peer review reduces effect sizes").
-   **Collinearity**: Since pairs are matched, we analyze the *difference*, avoiding the need for collinearity diagnostics between independent predictors.

#### C. Sensitivity Analysis
-   **Thresholds**: Sweep significance thresholds $\alpha \in \{0.01, 0.05, 0.1\}$.
-   **Metric**: "Significance Flip Rate" = Proportion of pairs where $p_{preprint} < \alpha$ AND $p_{journal} \ge \alpha$ (or vice versa).
-   **Robustness**: If the direction of bias (pre-print > journal) is consistent across all thresholds, the finding is robust.

### 3.3. Sample Size & Power
-   **Plan**: Target a sufficient number of valid matched pairs to ensure statistical power and robustness.
-   **Power Calculation**: We will run a **pilot study** on 50 pairs to estimate the variance of $\Delta$ES. Using this variance estimate, we will calculate the minimum detectable effect size for N=500 at adequate power. If the pilot indicates that 500 pairs is underpowered to detect the expected bias magnitude, we will explicitly report this limitation in the final analysis rather than claiming sufficiency.
-   **Feasibility**: 500 pairs is well within the h CI limit for PDF parsing and statistical tests.

## 4. Compute Feasibility (CPU-First)

-   **Environment**: GitHub Actions free-tier (multi-core CPU, multi-gigabyte RAM).
-   **Strategy**:
    -   **PDF Parsing**: `pdfplumber` is CPU-bound but efficient. We will process PDFs sequentially or in small batches (A limited number of concurrent processes.) to stay under 7GB RAM.
    -   **Statistics**: `scipy` and `statsmodels` are pure Python/C and run efficiently on CPU.
    -   **No GPU Needed**: No deep learning models are used for extraction (regex + NLP heuristics only) or analysis.
-   **Scaling**: If the dataset grows beyond a large scale, we will stream the OpenAlex data and process PDFs in chunks to avoid memory overflow.

## 5. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **OpenAlex via Hugging Face** | Verified source; programmatic access; avoids manual scraping of the OpenAlex S3 bucket. Fallback to API ensures `bioRxiv_id` availability. |
| **PDF Parsing over API** | Statistical values are rarely in metadata APIs; full-text parsing is required for p-values/effect sizes. |
| **Paired Interval-Censored Bootstrap** | Standard Tobit models assume independence and are invalid for paired data. The bootstrap approach respects the paired structure and interval censoring without violating assumptions. |
| **Paired Analysis** | Directly compares the same study, controlling for study-specific confounders (design, population). |
| **CPU-First** | The statistical methods (KS test, t-tests, bootstrap) are lightweight; no GPU acceleration is necessary. |
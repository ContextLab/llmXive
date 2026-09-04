# Research: Statistical Bias in Pre-Print Server Publication Trends

## Research Question

Does the peer-review process systematically alter reported p-values and effect sizes, leading to a reduction in statistical bias (e.g., p-hacking, inflation) between pre-print and journal versions of the same study?

## Background & Motivation

Pre-print servers (arXiv, bioRxiv) allow rapid dissemination of research, but lack the gatekeeping of peer review. Concerns exist that pre-prints may contain inflated effect sizes or p-hacked results that are corrected during peer review. This project quantifies that shift by comparing matched pre-print/journal pairs.

## Dataset Strategy

| Dataset | Source | Access Method | Variables | Justification |
|---------|--------|---------------|-----------|---------------|
| **OpenAlex Works** | https://api.openalex.org (S3 raw dumps) | `datasets.load_dataset(..., streaming=True)` | Title, Authors, DOI, Publication Date, Venue | Canonical source for matching pre-prints to journal DOIs. Verified via OpenAlex. |
| **arXiv/bioRxiv Metadata** | arXiv API, bioRxiv API | `requests` | Pre-print ID, Title, Authors, Date | Primary source for pre-print versions. Public APIs allow unattended fetching. |
| **PDFs** | Open Access Journals (via Unpaywall/CORE) | Unpaywall/CORE APIs | Full-text PDF | Source for statistical metric extraction. Restricted to Open Access to ensure feasibility. |

**Dataset Variable Fit**: The OpenAlex dataset contains the necessary metadata (title, authors, DOI) to perform fuzzy matching between pre-prints and journal versions. The PDFs contain the statistical metrics (p-values, effect sizes) required for analysis. No variables are missing from the verified sources.

**Access-Gated Data**: No access-gated data is used. All datasets are publicly available via OpenAlex, public APIs, or open-access repositories (Unpaywall/CORE).

**Streaming Strategy**: The OpenAlex metadata will be streamed using `datasets.load_dataset(..., streaming=True)` to avoid loading the entire corpus into memory. PDFs will be downloaded one at a time and processed sequentially to stay within available RAM limits.

## Methodological Approach

### 1. Matched Dataset Construction (US-1)
- **Input**: List of pre-print IDs (arXiv/bioRxiv) from 2018–2023.
- **Process**: 
  1. Fetch pre-print metadata via APIs.
  2. Query OpenAlex (streamed) to find matching journal DOIs using fuzzy title/author similarity (threshold ≥ 0.9).
  3. **Secondary Verification**: Cross-reference the match against the OpenAlex canonical DOI for the pre-print ID (if available) to confirm the match. Matches without a DOI or with low canonical confidence are flagged for exclusion.
  4. Filter to pairs where the journal version is within 2 years of the pre-print.
  5. Exclude pairs with no match, methodological shifts, or unverified DOIs.
- **Output**: `matched_pairs.csv` with columns: `preprint_id`, `journal_doi`, `title`, `authors`, `preprint_date`, `journal_date`.
- **Target**: N=1000 pre-prints queried to achieve ≥ 80% match rate (minimum SC-001: ≥ 60%).

### 2. Statistical Metric Extraction (US-1)
- **Input**: PDFs of pre-print and journal versions (Open Access only).
- **Process**:
  1. Extract text from PDFs using `pdfplumber`.
  2. Parse p-values (exact and inequalities) and effect sizes (Cohen's d, Hedges' g, odds ratios, etc.) using regex and context-aware NLP.
  3. Handle inequalities as interval-censored data (e.g., `p < 0.05` → `[0, 0.05]`) for general reporting.
  4. **P-Curve Inclusion**: Per FR-002 and scientific soundness requirements, incorporate interval-censored p-values into p-curve estimation using **survival analysis techniques (e.g., Turnbull estimator)** rather than discarding them.
  5. Exclude pairs where the statistical method changes (flagged as "methodological shift").
  6. **Inclusion of Identical P-Values**: Pairs with identical p-values are **INCLUDED** to measure the rate of correction (zero change).
- **Output**: `extracted_metrics.csv` with columns: `pair_id`, `version` (preprint/journal), `metric_type`, `value`, `inequality_flag`, `interval_bounds`, `stat_method`, `n_sample`.

### 3. Distributional & Magnitude Analysis (US-2)
- **P-Curve Analysis**: Perform separate p-curve analyses on pre-print and journal p-values (including censored values via survival analysis). Compare the estimated power and p-hacking prevalence parameters. Standard p-curve is applied to the *set* of pre-print p-values and the *set* of journal p-values separately (as independent distributions of reported statistics). **Compare findings against meta-analytic consensus or replication studies where available to verify if the journal version is actually less biased.**
- **Effect Size Comparison**: Calculate $\Delta$ES = ES_journal - ES_preprint.
  - **Primary Method**: Use **Tobit regression** (via `lifelines` or `statsmodels`) to handle censored effect sizes and account for heteroscedasticity due to changing N. **Model N as a covariate.**
  - **Exclusion Criterion**: **Do not exclude** pairs where sample size (N) changes by > 20%. Instead, model N as a covariate in the Tobit regression to avoid selection bias.
  - **Stratified Analysis**: Analyze pairs with N > 20% increase separately to characterize the nature of the correction (e.g., did they get larger N and smaller ES?).
  - **Stratified Analysis**: Analyze by field (e.g., Quantitative Biology) as required by US-2.
- **Independent Validation**: Compare findings against meta-analytic consensus or replication studies where available to verify if the journal version is actually less biased.
- **Output**: `p_curve_results.json`, `effect_size_results.json` with test statistics, p-values, and confidence intervals.

### 4. Sensitivity Analysis (US-3)
- **Input**: Extracted p-values.
- **Process**: Sweep significance thresholds across {0.01, 0.05, 0.1}. Calculate "significance flip rate" (proportion of pairs where p crosses the threshold in opposite directions) at each threshold.
- **Robustness Check**: Account for **reporting precision artifacts** (e.g., rounding differences) in the flip rate calculation.
- **Direction Consistency**: Explicitly check that the **direction of the bias** (pre-print > journal or vice versa) remains consistent across all thresholds (SC-004).
- **Output**: `sensitivity_results.json` with flip rates and bias direction consistency.

## Statistical Rigor

- **Multiple-Comparison Correction**: When performing multiple tests (e.g., p-curve, effect size, sensitivity), apply Benjamini-Hochberg correction to control false discovery rate.
- **Sample-Size Justification**: The initial query size of N=1000 pre-prints is chosen to achieve a target match rate of ≥ 80% (SC-001) with expected failure rates. **Power Analysis**: Assuming a moderate effect size ($\Delta$ES > 0.3) and a standard deviation of 0.5 for the difference, a paired sample size of N=200 provides 80% power at $\alpha$=0.05. The target N=1000 ensures robustness against attrition and allows for stratification by field.
- **Causal-Inference Assumptions**: The analysis is observational. Findings describe associations between publication stage and statistical values, not causal effects of peer review. No randomization exists.
- **Measurement Validity**: P-value and effect size extraction relies on regex and context-aware NLP. Validation is performed on a subset of known papers to estimate extraction accuracy.
- **Collinearity Handling**: Pre-print and journal versions are not independent. The analysis focuses on the *difference* ($\Delta$ES) rather than treating them as independent predictors. No collinearity diagnostics are required for the paired difference test.
- **Paired P-Curve**: Standard p-curve assumes independence. This analysis uses separate p-curve estimation for pre-print and journal distributions (independent samples of reported statistics) and compares the estimated parameters, avoiding the paired dependency issue.

## Compute Feasibility

- **CPU-First**: All methods (p-curve, Tobit regression, weighted t-test) are implemented using `scipy`, `statsmodels`, `lifelines`, and `numpy`, which run efficiently on CPU.
- **Memory Constraints**: Streaming OpenAlex metadata and processing PDFs one at a time ensures memory usage remains within manageable limits.
- **Time Constraints**: The pipeline is designed to complete within 6 hours for **N=200 pairs (CI limit)**. For **N=1000**, the pipeline will be **chunked or run on a dedicated runner**. PDF extraction is the most time-consuming step; parallelization is avoided to simplify error handling and reproducibility.
- **GPU Escape Hatch**: Not required. No transformer models or CUDA kernels are used.

## Decision/Rationale

- **Why CPU-First?**: The statistical methods (p-curve, Tobit, t-test) do not require GPU acceleration. Running on CPU ensures compatibility with GitHub Actions free-tier and simplifies reproducibility.
- **Why Streaming?**: The OpenAlex dataset is too large to load entirely into memory. Streaming allows processing of the full corpus without exceeding RAM limits.
- **Why Interval-Censoring for General Reporting?**: Inequalities (e.g., `p < 0.05`) are common in scientific literature. Treating them as interval-censored data preserves information for general reporting without introducing bias from arbitrary imputation.
- **Why Include Interval-Censored in P-Curve?**: Per scientific soundness requirements, discarding inequalities introduces massive selection bias. Survival analysis techniques (e.g., Turnbull estimator) are used to incorporate them.
- **Why Tobit for Effect Sizes?**: Effect sizes are often censored or bounded. Tobit regression handles censored data and heteroscedasticity better than a simple t-test.
- **Why Include Identical P-Values?**: Excluding identical p-values creates selection bias. Including them allows measurement of the rate of correction (zero change).
- **Why Model N as Covariate (instead of exclusion)?**: Per scientific soundness requirements, excluding pairs with N > 20% increase removes the very cases where 'correction' might be most evident. Modeling N as a covariate avoids selection bias.
- **Why Permutation Testing?**: To validate the observed density ratio against a null distribution (SC-002), permutation testing (shuffling venue labels) is used.
- **Why Precision Robustness Check?**: To ensure the significance flip rate is not driven by reporting conventions (e.g., rounding).
- **Why Independent Validation?**: To address circularity concerns, findings are compared against meta-analytic consensus or replication studies.

## Risks & Mitigations

- **Risk**: Low match rate (< 80%) between pre-prints and journals.  
  **Mitigation**: Increase initial query size to N=2000; improve fuzzy matching algorithm (e.g., use Levenshtein distance with author name normalization); rely on DOI cross-verification.
- **Risk**: High exclusion rate due to methodological shifts or missing data.  
  **Mitigation**: Log excluded pairs with reasons; report exclusion rate in final results.
- **Risk**: PDF extraction failures due to non-standard formatting.  
  **Mitigation**: Use multiple regex patterns; fallback to manual inspection for a subset of papers; report extraction failure rate.
- **Risk**: Time limit exceeded for N=1000.  
  **Mitigation**: Run initial N=200 on CI; scale to N=1000 on dedicated runner or via chunked execution.
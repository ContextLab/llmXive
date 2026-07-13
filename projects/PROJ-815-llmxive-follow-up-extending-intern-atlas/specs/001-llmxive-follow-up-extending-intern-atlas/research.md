# Research: llmXive follow-up: extending "Intern-Atlas: A Methodological Evolution Graph as Research Infrastruct"

## Summary

This research phase validates the feasibility of the proposed study, identifies the specific datasets to be used, and outlines the statistical methodology to ensure compliance with the specification and the project constitution. The core hypothesis is that topological features (Bottleneck Resolution Ratio, Branching Entropy) predict retraction status better than citation counts alone.

## 1. Problem Formulation

### Primary Analysis Datasets
These datasets drive the primary research results. If unavailable, the pipeline will abort.

| Dataset Name | Description | Verified Source URL | Usage |
|:--- |:--- |:--- |:--- |
| **Intern-Atlas Graph** | Methodological evolution graph containing nodes (papers) and typed edges (improves, replaces, etc.). | *Note: NO VERIFIED SOURCE provided in input. The plan assumes the graph is available locally or via a private repository. If not found in `data/raw/`, the pipeline will ABORT with a clear error message.* | Primary source for graph topology and node metadata (2010-2018). |
| **Retraction Watch Database** | External database of retracted papers with reasons (methodological error, fraud, etc.). | *Note: NO VERIFIED SOURCE provided in input. The plan assumes access to the official Retraction Watch CSV/JSON dump or API. If the specific 2010-2018 CSV dump is not found, the pipeline will ABORT.* | Ground truth labeling (Fragile/Robust/Retraction-Only). |
| **Replication Index** | Database of replication studies (success/failure). | *Note: NO VERIFIED SOURCE provided in input. If unavailable, the 'Robust' label will be assigned based solely on the absence of retraction in the Retraction Watch DB.* | Supplementary labeling for "Robust" status if retraction data is sparse. |

### Test Fixtures
These datasets are used **ONLY** for unit testing and validation of specific functions. They are **NOT** used for primary analysis.

| Dataset Name | Description | Verified Source URL | Usage |
|:--- |:--- |:--- |:--- |
| **VIF (parquet)** | Sample dataset for testing VIF/MI calculations. | ` | **Constraint**: This dataset is **NOT** suitable for the primary analysis as it contains fact-checking data, not methodological evolution graph data. It will be used **only** for unit testing the VIF/MI calculation functions to ensure they run on CPU. |

**Critical Note on Dataset Availability**: The specification assumes the Intern-Atlas graph and Retraction Watch Database are accessible. The implementation plan must include a "Data Fetching" step that attempts to download these from their canonical sources. If the Retraction Watch Database is unavailable for the 2010-2018 window, the system must abort as per the Edge Cases in the spec.

### 2.1 Primary Data Sources

### 1. Data Extraction & Feature Engineering (FR-001 to FR-004)

- **Filtering**: Extract nodes with `year` in [2010, 2018].
- **Non-Circularity Enforcement**:
 - **Blinding**: Before feature calculation, the script MUST explicitly drop any graph node fields containing 'retracted', 'correction', 'status', or 'outcome' metadata to prevent semantic leakage.
 - **Separation**: Edge annotation must be blinded to retraction status. The feature extraction logic (`graph_utils.py`) must operate strictly on the graph topology and edge types, with no access to the retraction database.
 - **Label Assignment**: Label assignment occurs in a separate step (`match_utils.py`) after feature extraction, using only external data.
- **Edge Typing**: Use only human-annotated edge types (`improves`, `replaces`, `extends`, `variant`). **Exclude** any LLM-inferred types.
- **Feature Calculation**:
 - `bottleneck_resolution_ratio`: Count of (`improves` + `replaces`) / Total outgoing edges. If total outgoing is 0, set to 0.0.
 - `branching_entropy`: Shannon entropy of the distribution of downstream method types.
- **Label Mapping**:
 - Match nodes to Retraction Watch DB via exact DOI.
 - **Fuzzy Fallback**: If no DOI match, use fuzzy title/author match with **Levenshtein ratio >= 0.95** (FR-011, revised for precision).
 - **Confidence Threshold**: Matches with Levenshtein < 0.95 are **excluded** from the training set and logged as 'unmatched' to ensure high precision and prevent false positives from biasing the AUC.
 - **Label Assignment**:
 - `1` (Fragile): Retraction due to methodological error/irreproducibility.
 - `2` (Retraction-Only): Retraction due to fraud/plagiarism.
 - `0` (Robust): No retraction or retraction for other reasons.
 - **Conflict Resolution**: If multiple matches, select earliest by date; if tie, first alphabetically by journal (FR-010).
- **Class Balance & Power**:
 - The primary model predicts `retraction_status` (binary: **Label 1 = Fragile** vs **Label 0 = Robust**). **Label 2 (Retraction-Only) is EXCLUDED** from the primary binary model to ensure the construct 'Methodological Fragility' is measured correctly.
 - **Power Analysis**:
 - **Test**: Two-sided z-test for difference in AUC.
 - **Effect Size**: Assumed Cohen's h = 0.2 (small but meaningful improvement).
 - **Power**: [deferred] (0.8).
 - **Alpha**: 0.05.
 - **Required Sample Size**: N >= 384 per group (or total N >= 768 for balanced design).
 - **Action**: If the count of Label 1 (Fragile) is < 50, the system will switch to **Firth's penalized logistic regression** to handle convergence issues. If Label 1 count is too low for meaningful analysis (e.g., < 20), the study will report this as a power limitation and interpret results as exploratory.

### 2. Model Training & Validation (FR-005, FR-006)

- **Model Type**: Logistic Regression (Interpretable, CPU-friendly).
- **Primary Model**: Predict `retraction_status` (binary: **Label 1 = Fragile** vs **Label 0 = Robust**). **Label 2 (Retraction-Only) is EXCLUDED** from the primary binary model.
- **Baseline Model**: Predict `retraction_status` using `citation_count` and `publication_year`.
- **Evaluation**: AUC-ROC, Precision-PR.
- **Statistical Rigor**:
 - **Multiple Comparisons**: The study performs three sets of hypothesis tests: Model Comparison, Permutation Test, and Threshold Sweep. **Bonferroni correction** is applied to the threshold sweep results (alpha = 0.05/3 ≈ 0.0167) to control family-wise error rate.
 - **Causal Claims**: The study is observational. Claims will be framed as "associational" or "predictive," not causal. No randomization exists.
 - **Measurement Validity**: Edge types are human-annotated (high validity). Retraction reasons are from a curated database (high validity).
 - **Collinearity**: `bottleneck_resolution_ratio` and `branching_entropy` are mathematically distinct (ratio vs. entropy). However, VIF and MI will be calculated (FR-009) to ensure they are not definitionally collinear.

### 3. Robustness & Sensitivity (FR-007 to FR-012)

- **Permutation Test**: Shuffle labels **n=100** times (strictly per FR-007). Verify observed AUC > mean_permuted_AUC + 2 * std_dev.
 - **Statistical Limitation**: With n=100, the minimum p-value resolution is 0.01. The study cannot claim significance at p < 0.01. Results are interpreted as "significant at the [deferred] level" only if the permutation count strictly exceeds the threshold, acknowledging this floor.
- **Threshold Sweep**: Test cutoffs **{0.3, 0.5, 0.7}** for FPR/FNR (FR-008). Apply Bonferroni correction (alpha/3) to these results.
- **Collinearity Check**: Calculate VIF and MI. Flag if VIF > 5 or MI > 0.1.
- **Confounding Control**: **Mandatory** stratified permutation test or covariate adjustment for 'field of study' and 'publication venue' (FR-012).
 - **Fallback Strategy**: If > 50% of strata have < 5 samples, the system **MUST** switch to **covariate adjustment with L2 regularization (alpha=1.0)**. This ensures the analysis proceeds even with sparse data, maintaining the mandatory nature of the requirement.

## Decision Rationale

- **CPU-Only Constraint**: All chosen methods (Logistic Regression, Shannon Entropy, Permutation Tests with n=100) are computationally lightweight and will run within the 6-hour, 7GB RAM limit of the GitHub Actions free tier. No GPU or deep learning models are used.
- **Binary Classification**: The spec defines labels 1 (Fragile) and 0 (Robust) for the primary prediction task. The "Retraction-Only" (2) label is excluded from the primary binary model to ensure the construct 'Methodological Fragility' is measured correctly.
- **Permutation Count**: Strictly adhering to FR-007 (n=100) to balance statistical validity with runtime constraints, despite the p-value resolution limit.
- **Fuzzy Matching**: Replaced manual verification with a strict Levenshtein >= 0.95 threshold for fuzzy matches to ensure high precision without human intervention in CI, and excludes lower-confidence matches to prevent false positives.
- **Confounding Control**: The analysis is mandatory. The fallback to covariate adjustment ensures the requirement is met even with sparse data.
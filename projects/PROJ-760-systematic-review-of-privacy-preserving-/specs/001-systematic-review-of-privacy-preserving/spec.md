# Feature Specification: Systematic Review of Privacy-Preserving Federated Learning Protocols

**Feature Branch**: `001-systematic-review-privacy-fl`  
**Created**: 2026-09-02  
**Status**: Draft  
**Input**: User description: "Systematic Review of Privacy-Preserving Federated Learning Protocols"

## User Scenarios & Testing

### User Story 1 - Automated Literature Retrieval and Metadata Extraction (US-1) (Priority: P1)

The system MUST retrieve peer-reviewed papers from arXiv and Semantic Scholar using specific search strings, filter them by publication date (2018-2024), and extract structured metadata including **data heterogeneity parameters (e.g., Dirichlet alpha, non-IID skew metrics)** alongside title, authors, abstract, and PDF URL.

**Why this priority**: Without a complete and reproducible dataset of candidate papers including skew parameters, no analysis of the interaction between privacy and data heterogeneity can occur. This is the foundational data ingestion step.

**Independent Test**: Can be fully tested by running the retrieval script against a fixed seed query and verifying the output CSV contains ≥10 records with valid metadata fields, including a `skew_parameter` field (or `skew_unknown` flag), and no duplicates.

**Acceptance Scenarios**:

1. **Given** a search string for "federated learning" AND "differential privacy", **When** the system queries the APIs, **Then** the output CSV contains all papers from 2018-2024 matching the criteria, excluding duplicates, with `skew_parameter` extracted or flagged as `skew_unknown`.
2. **Given** a paper with missing metadata fields (e.g., no abstract or skew metric), **When** the system processes it, **Then** the record is flagged in a `review_needed.log` file with the specific missing field rather than silently dropped.
3. **Given** an API rate limit or timeout, **When** the script retries up to 3 times, **Then** the system logs the failure and continues processing remaining queries without crashing.

### User Story 2 - Quantitative Data Extraction from PDFs (US-2) (Priority: P2)

The system MUST parse PDFs of selected papers to extract specific quantitative performance metrics **(accuracy loss % and privacy budget ε)** and **data skew parameters**. The system MUST normalize any reported privacy budget to a standard ε scale where possible.

**Why this priority**: This transforms unstructured text into the structured dataset required for the meta‑analysis, specifically enabling the analysis of privacy‑utility trade‑offs under varying data skew.

**Independent Test**: Can be fully tested by running the parser on a manually annotated random sample of ≤5 papers (selected by the researchers) to verify extraction accuracy against the ground truth labels created for this sample. The system MUST NOT require manual extraction of the full corpus to proceed with the automated analysis pipeline.

**Acceptance Scenarios**:

1. **Given** a PDF containing a table with "Accuracy Loss" and "Privacy Budget (ε)", **When** the parser processes it, **Then** the values are correctly extracted into `extracted_metrics.csv` with the correct privacy mechanism tag and `skew_parameter`.
2. **Given** a PDF with non‑standard table formatting (e.g., merged cells), **When** the parser encounters it, **Then** the system logs a `parsing_error` and skips the specific table row, preserving the rest of the file's data.
3. **Given** a paper reporting metrics in different units, **When** the system processes the data, **Then** all values are normalized to standard units: Accuracy Loss to '%' and Privacy Budget to ε. **If a privacy budget is reported only as a range, the system extracts the midpoint**; otherwise, it flags the record as `invalid_format`.

### User Story 3 - Meta-Analysis and Visualization Generation (US-3) (Priority: P3)

The system MUST perform meta‑analysis to compute effect sizes linking **privacy mechanism types (Differential Privacy and Secure Aggregation)** and **data skew levels** to accuracy loss, generate forest plots and bar charts, and produce a summary Markdown report. If variance data is missing, the system MUST fall back to descriptive statistics (median, IQR) rather than fixed‑effects models. Exploratory descriptive summaries for Secure Aggregation, Homomorphic Encryption, and Hybrid mechanisms may also be generated but are not part of the primary hypothesis testing.

**Why this priority**: This delivers the final research output, synthesizing the extracted data into actionable insights regarding the interaction between privacy mechanisms and data heterogeneity.

**Independent Test**: Can be fully tested by running the analysis on the **actual** `extracted_metrics.csv` generated from the retrieved PDFs. The test verifies that the generated plots reflect the **real** statistical distribution of the extracted data (e.g., confidence intervals are calculated from actual reported standard deviations, not simulated values) and that the summary report contains the calculated confidence intervals (regardless of whether they include zero).

**Acceptance Scenarios**:

1. **Given** a dataset of 20 extracted studies, **When** the meta‑analysis runs, **Then** the output includes a forest plot for "Accuracy Loss vs. Privacy Mechanism" with 95% confidence intervals derived from the **actual** extracted variance data, stratified by skew level if sufficient data exists.
2. **Given** a scenario where a specific privacy mechanism has <3 data points **for a specific skew level**, **When** the analysis runs, **Then** the system flags this as "Insufficient Data" in the report rather than calculating a statistically invalid effect size.
3. **Given** the full analysis pipeline, **When** the `run.sh` script completes, **Then** it generates a `results_summary.md` containing the main findings, tables, and links to all generated figures, where all numerical results are derived strictly from the `extracted_metrics.csv` file.

### Edge Cases

- What happens when a PDF cannot be downloaded due to a paywall or broken link? (System must log the DOI and skip, ensuring the pipeline continues).
- How does the system handle papers that use a hybrid mechanism but do not clearly separate metrics for each component? (System must categorize as "Hybrid" and extract aggregate metrics, flagging for manual review if disentanglement is impossible).
- What if the search returns zero results for a specific mechanism (e.g., FHE) in the 2018-2024 window? (System must report "No Data Available" for that category rather than crashing).
- What if a paper reports "approx. [deferred]" or a range "40-60%" for a metric? (System must flag as `invalid_format` or extract midpoint if bounded, per FR‑002).

## Requirements

### Functional Requirements

- **FR-001**: System MUST query arXiv and Semantic Scholar APIs using the exact search strings defined in the *Methodology Details* section to retrieve papers published between 2018 and 2024. The search MUST include terms related to "non-IID", "data heterogeneity", or "skew" to ensure retrieval of relevant studies. (See US-1).

- **FR-002**: System MUST use table‑parsing libraries (pdfplumber or tabula‑py) combined with regex patterns to extract numeric values **only for** Accuracy Loss (%), Privacy Budget (ε), and Data Skew parameters from PDF tables into a single CSV file.  
    - **Ambiguous Text Rule**: If a metric is reported as "approx. X" or "about X", the system MUST flag the value as `invalid_format` and exclude it from the primary analysis.  
    - **Range Rule**: If a metric is reported as a range "X‑Y", the system MUST extract the midpoint `(X+Y)/2` ONLY if both X and Y are numeric and bounded; otherwise, flag as `invalid_format`.  
    - **Exploratory Metrics**: Extraction of communication overhead, convergence rounds, and computational cost is OPTIONAL and, when performed, must be clearly marked as exploratory (see FR‑012).  

- **FR-003**: System MUST categorize each extracted study into one of **two** mandatory privacy mechanism types: Differential Privacy (DP) or Secure Aggregation (SA). Studies employing Homomorphic Encryption or Hybrid mechanisms may be categorized for **exploratory descriptive summaries** but are **NOT** required for the primary hypothesis testing.  
  **Primary Analysis Scope**: The primary meta‑analysis MUST focus on the interaction between **Data Skew** and **both DP and SA** mechanisms. This restriction aligns with the original research question (DP vs. SA) while preserving statistical power. (See US-2, US-3).

- **FR-004**: System MUST perform a meta‑analysis to compute effect sizes (e.g., Hedges' g) and 95% confidence intervals for Accuracy Loss per mechanism, **stratified by data skew level** (Low, Medium, High, or continuous α). If variance data (SD/SE) is missing for >50% of studies *within a specific mechanism‑skew group*, the system MUST fall back to descriptive aggregation (median, IQR) and MUST NOT use fixed‑effects models for that group. In this fallback mode, the system MUST use non‑parametric tests (e.g., Kruskal‑Wallis) for group comparison if raw data is available, and label the output as "Descriptive Summary". (See US‑3).  

- **FR-005**: System MUST generate at least three visualization types: forest plots for effect sizes (when computable), bar charts for mean Accuracy Loss per mechanism, and a scatter plot for Accuracy Loss vs. Privacy Budget (ε). Plots MUST be stratified by skew level where data permits. (See US‑3).

- **FR-006**: System MUST apply multiple‑comparison correction (Benjamini‑Hochberg) to the family of hypothesis tests pertaining to **DP and SA** metrics only. The family comprises the two performance metrics evaluated for each mechanism, yielding **4** comparisons (k = 4). This limited correction aligns with the narrowed primary analysis scope and preserves statistical power.  
  **Justification**: Limiting correction to the core mechanisms avoids unnecessary loss of power introduced by testing unrelated exploratory mechanisms, while still controlling the false discovery rate for the core hypotheses. (See US‑3).

- **FR-007**: System MUST detect studies lacking variance estimates (SD/SE) and exclude them from random‑effects models. If the exclusion rate within a group exceeds a majority threshold, the system MUST switch to the descriptive review pathway defined in FR‑004. (See US‑3).

- **FR-008**: *(Exploratory)* System MAY extract and normalize "Computational Cost" to a "relative overhead ratio" when such data are available. Records lacking a valid baseline are flagged with `valid_baseline: false` and may be used only in sensitivity‑analysis branches. (See US‑2).

- **FR-009**: *(Exploratory)* System MUST report the count and percentage of studies excluded from the primary computational‑cost analysis due to missing baselines. If this exclusion rate exceeds a substantial proportion, a sensitivity analysis comparing results with and without the excluded studies must be performed. (See US‑3).

- **FR-010**: System MUST ensure all numerical results in the final report are derived **exclusively from the actual extracted values** in the `extracted_metrics.csv` file. The system MUST NOT introduce any simulated, placeholder, or hardcoded values into the statistical analysis or visualization generation steps. Any proxy values (e.g., cohort median) used for normalization MUST be explicitly flagged and documented as such, but the primary statistical outputs (means, effect sizes, p‑values) MUST be computed directly from the observed data points. (See US‑3).

- **FR-011**: System MUST extract `skew_parameter` (e.g., Dirichlet alpha) from papers. If a study lacks a reported skew parameter, the system MUST flag it as `skew_unknown`. Studies with `skew_unknown` MUST be excluded from the primary interaction analysis (FR‑004) but included in a general descriptive summary. (See US‑1).

- **FR-012**: Inclusion of Homomorphic Encryption and Hybrid mechanisms is **optional** and only for exploratory descriptive summaries to evaluate whether data‑skew effects are consistent across a broader set of privacy techniques, thereby strengthening external validity without affecting the core DP vs SA hypothesis. (See US‑1, US‑2, US‑3).

- **FR-013**: System MUST conduct a formal interaction test using meta‑regression with **Data Skew** as a moderator to assess whether the effect of the privacy mechanism (DP vs SA) on Accuracy Loss differs across skew levels. The interaction term’s p‑value and confidence interval must be reported in the final summary. (See US‑3, FR‑004).

### Data Schema *(new subsection)*

`extracted_metrics.csv` MUST contain the following columns:

| Column               | Type                                    | Description |
|----------------------|-----------------------------------------|-------------|
| `study_id`           | string (UUID)                           | Unique identifier for each study |
| `doi`                | string                                  | DOI of the paper |
| `mechanism_type`     | enum {DP, SA, HE, Hybrid, Unknown}      | Privacy mechanism classification |
| `skew_parameter`     | float or NULL                           | Reported Dirichlet α or similar metric |
| `skew_unknown`       | boolean                                 | TRUE if no skew parameter reported |
| `accuracy_loss`      | float (percent)                         | Reported accuracy loss |
| `privacy_budget`     | float (ε)                               | Reported privacy budget |
| `variance_accuracy`  | float or NULL                           | Reported variance (SD or SE) for accuracy loss |
| `transformation_log` | string (JSON list)                      | Record of all transformations applied to each numeric field (e.g., `["percent_to_fraction","log_transform"]`) |
| `valid_baseline`     | boolean                                 | *(Exploratory)* Whether a valid baseline for computational cost is present |
| `proxy_baseline`     | boolean                                 | *(Exploratory)* Whether a proxy baseline was used |

**Whitelist of allowed operations** for `transformation_log` (must be a subset of): `["percent_to_fraction", "log_transform", "sqrt_transform", "ratio", "difference", "normalize_to_bytes", "scale_by_median"]`.

All other columns not listed are prohibited.

### Key Entities

- **Study**: A unique publication record containing metadata (DOI, title, authors), **skew parameters** (e.g., `skew_parameter`, `skew_unknown` flag), and extracted quantitative metrics.
- **Mechanism**: A categorical attribute of a study (DP, SA, HE, Hybrid, Unknown) used as the independent variable.
- **Metric**: A quantitative outcome variable (Accuracy Loss, Privacy Budget) extracted from a study. Each metric record MUST include:
    - `raw_value`: **Single float** (percentage for accuracy loss, ε for privacy budget) or **List of floats** if per‑client values are reported.
    - `value_type`: Enum `['aggregate', 'per_client_list']`.
    - `normalized_value`: The value normalized to standard units or dimensionless ratio.
    - `valid_baseline`: Boolean (true if specific baseline exists) – exploratory only.
    - `proxy_baseline`: Boolean (true if cohort median was used) – exploratory only.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, percentages) to the implementation/research phase.

- **SC-001**: The system extracts and reports the count (N) of studies per mechanism category and skew level. The system MUST successfully complete the pipeline even if N < 5, in which case the output is a "Descriptive Review" (See US‑1, US‑2).
- **SC-002**: The validity of the synthesized findings is measured by a manual spot‑check of the **entire** dataset if N ≤ 100, or a random sample if N > 100. A human reviewer MUST confirm that the extracted data in `extracted_metrics.csv` accurately reflects the source PDFs. The pass criterion is **0 errors for N ≤ 100**, or **error rate < 1% for N > 100** across all rows for the fields 'raw_value', 'mechanism_type', and 'skew_parameter'. (See US‑2).
- **SC-003**: The statistical validity of the meta‑analysis is measured by the generation of specific statistical outputs: 95% confidence intervals for effect sizes (Hedges' g) when variance data permits, OR descriptive statistics (median, IQR) with explicit qualitative summaries when variance data is insufficient. The output MUST include a forest plot with 95% CI and a p‑value for the primary comparison when applicable. (See US‑3).
- **SC-004**: The reproducibility of the pipeline is measured by the ability to re‑run the entire process on a fresh runner using a *fixed input snapshot* (e.g., a git‑tagged version of `extracted_metrics.csv`) and produce identical `results_summary.md` outputs, ensuring all results are derived from the actual extracted dataset without simulated or placeholder values. (See US‑1, US‑3).
- **SC-005**: The integrity of the results is measured by the absence of any simulated or hardcoded values in the final statistical outputs. A validation script MUST confirm that every numerical value in the final report matches a value present in `extracted_metrics.csv` or is a direct mathematical transformation of such values. The script MUST verify that all transformations (e.g., mean, median, log, sqrt) are recorded in a `transformation_log` column in the CSV and are part of the whitelisted set of allowed operations. **Crucially, the script MUST verify that no random number generation or synthetic data injection occurred during the computation of effect sizes or p‑values.** (See US‑3).
- **SC-006**: **Metadata Extraction Completeness** (See US‑1). The system MUST produce a CSV file `retrieved_papers.csv` containing columns: `doi`, `title`, `authors`, `abstract`, `pdf_url`, `skew_parameter`, `skew_unknown`. The pipeline passes if the file contains at least 10 records, each row has non‑empty values for `doi`, `title`, `authors`, and `pdf_url`; missing `abstract` or `skew_parameter` must be flagged with `abstract_missing` or `skew_unknown` columns. All missing‑field incidents are logged in `metadata_issues.log`. Success is achieved when both the CSV and log are generated without pipeline error.

## Assumptions

- The arXiv and Semantic Scholar APIs provide sufficient access to PDFs and metadata for the 2018-2024 window without requiring institutional paywalls.
- The `tabula-py` or `pdfplumber` libraries can successfully extract tabular data from at least 80% of the target PDFs; the remaining [deferred] will be flagged for manual review.
- The "privacy budget" metric is reported in a comparable ε scale across the majority of studies; studies using non‑comparable units without a clear ε conversion will be excluded from the primary analysis but may appear in exploratory summaries per FR‑012.
- The GitHub Actions free‑tier runner (2 CPU, 7GB RAM) is sufficient to run the `statsmodels` meta‑analysis and generate plots on the extracted dataset (expected size <100 rows).
- The search strings will yield a sufficient sample size (N≥5 per mechanism‑skew category) to perform a meta‑analysis. If N < 5 per category, the project is valid and will output a "Descriptive Systematic Review" rather than a quantitative meta‑analysis (See SC‑001).
- The dataset contains the necessary variables (privacy mechanism type, accuracy loss, privacy budget, **data skew parameters**) for all included studies; if a study lacks a specific metric or skew parameter, that study will be excluded from the primary analysis of that specific metric or interaction.
- All quantitative results presented in the final report are derived exclusively from the text extracted from the retrieved PDFs; no synthetic data, simulated values, or hardcoded placeholders are introduced at any stage of the analysis pipeline. Any proxy values (e.g., cohort median) are explicitly flagged and reported in sensitivity analysis.

### Methodology Details *(new subsection)*

The exact search strings used by the system are:

| Mechanism | Search String (quoted) |
|-----------|------------------------|
| Differential Privacy (DP) | `"federated learning" AND "differential privacy" AND ("non-iid" OR "data heterogeneity" OR "skew")` |
| Secure Aggregation (SA)   | `"federated learning" AND "secure aggregation" AND ("non-iid" OR "data heterogeneity" OR "skew")` |
| Homomorphic Encryption (HE) – Exploratory | `"federated learning" AND "homomorphic encryption"` |
| Hybrid (DP + SA) – Exploratory | `"federated learning" AND ("differential privacy" OR "secure aggregation") AND "hybrid"` |

All queries are limited to the publication date range **2018‑01‑01** to **2024‑12‑31** and to peer‑reviewed articles (as indicated by the `journal` field in Semantic Scholar metadata). The system logs the exact query string used for each API call for reproducibility.

# Feature Specification: Systematic Review of Privacy-Preserving Federated Learning Protocols

**Feature Branch**: `001-systematic-review-privacy-fl`  
**Created**: 2026-08-15  
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

The system MUST parse PDFs of selected papers to extract specific quantitative performance metrics (communication overhead, convergence rounds, accuracy drop %, computational cost) and **data skew parameters**. The system MUST normalize computational cost to a dimensionless **relative overhead ratio** where possible.

**Why this priority**: This transforms unstructured text into the structured dataset required for the meta-analysis, specifically enabling the analysis of privacy-utility trade‑offs under varying data skew.

**Independent Test**: Can be fully tested by running the parser on a manually annotated random sample of ≤5 papers (selected by the researchers) to verify extraction accuracy against the ground truth labels created for this sample. The system MUST NOT require manual extraction of the full corpus to proceed with the automated analysis pipeline.

**Acceptance Scenarios**:

1. **Given** a PDF containing a table with "Accuracy Loss" and "Privacy Budget", **When** the parser processes it, **Then** the values are correctly extracted into `extracted_metrics.csv` with the correct privacy mechanism tag and `skew_parameter`.
2. **Given** a PDF with non‑standard table formatting (e.g., merged cells), **When** the parser encounters it, **Then** the system logs a `parsing_error` and skips the specific table row, preserving the rest of the file's data.
3. **Given** a paper reporting metrics in different units, **When** the system processes the data, **Then** all values are normalized to standard units: Convergence Speed to 'rounds' (integer), Communication Overhead to 'bytes', and Computational Cost to 'relative overhead ratio' (if baseline is available). **If a baseline is NOT available, the system MUST generate a proxy baseline using the median overhead of the cohort for that mechanism, flag the record with `valid_baseline: false` and `proxy_baseline: true`, and include it in the primary analysis dataset while marking it for separate sensitivity‑analysis reporting** (per FR‑008).

### User Story 3 - Meta-Analysis and Visualization Generation (US-3) (Priority: P3)

The system MUST perform meta-analysis to compute effect sizes linking privacy mechanism types and **data skew levels** to performance metrics, generate forest plots and bar charts, and produce a summary Markdown report. If variance data is missing, the system MUST fall back to descriptive statistics (median, IQR) rather than fixed‑effects models.

**Why this priority**: This delivers the final research output, synthesizing the extracted data into actionable insights regarding the interaction between privacy mechanisms and data heterogeneity.

**Independent Test**: Can be fully tested by running the analysis on the **actual** `extracted_metrics.csv` generated from the retrieved PDFs. The test verifies that the generated plots reflect the **real** statistical distribution of the extracted data (e.g., confidence intervals are calculated from actual reported standard deviations, not simulated values) and that the summary report contains the calculated confidence intervals (regardless of whether they include zero).

**Acceptance Scenarios**:

1. **Given** a dataset of 20 extracted studies, **When** the meta-analysis runs, **Then** the output includes a forest plot for "Accuracy Loss vs. Privacy Mechanism" with 95% confidence intervals derived from the **actual** extracted variance data, stratified by skew level if sufficient data exists.
2. **Given** a scenario where a specific privacy mechanism has <3 data points **for a specific skew level**, **When** the analysis runs, **Then** the system flags this as "Insufficient Data" in the report rather than calculating a statistically invalid effect size.
3. **Given** the full analysis pipeline, **When** the `run.sh` script completes, **Then** it generates a `results_summary.md` containing the main findings, tables, and links to all generated figures, where all numerical results are derived strictly from the `extracted_metrics.csv` file.

### Edge Cases

- What happens when a PDF cannot be downloaded due to a paywall or broken link? (System must log the DOI and skip, ensuring the pipeline continues).
- How does the system handle papers that use a hybrid mechanism but do not clearly separate metrics for each component? (System must categorize as "Hybrid" and extract aggregate metrics, flagging for manual review if disentanglement is impossible).
- What if the search returns zero results for a specific mechanism (e.g., FHE) in the 2018-2024 window? (System must report "No Data Available" for that category rather than crashing).
- What if a paper reports "approx. [deferred]" or a range "40-60%" for a metric? (System must flag as `invalid_format` or extract midpoint if bounded, per FR-002).

## Requirements

### Functional Requirements

- **FR-001**: System MUST query arXiv and Semantic Scholar APIs using the exact search strings defined in the methodology to retrieve papers published between 2018 and 2024. The search MUST include terms related to "non-IID", "data heterogeneity", or "skew" to ensure retrieval of relevant studies. (See US-1).

- **FR-002**: System MUST use table‑parsing libraries (pdfplumber or tabula‑py) combined with regex patterns to extract numeric values from PDF tables into a single CSV file. The system MUST extract *reported* values from source PDFs.
    - **Ambiguous Text Rule**: If a metric is reported as "approx. X" or "about X", the system MUST flag the value as `invalid_format` and exclude it from the primary analysis.
    - **Range Rule**: If a metric is reported as a range "X‑Y", the system MUST extract the midpoint `(X+Y)/2` ONLY if both X and Y are numeric and bounded; otherwise, flag as `invalid_format`.
    - **Imputation Exception**: For the specific case of missing baseline information required to compute the *relative overhead ratio* for Computational Cost (see FR‑008), the system MAY generate a proxy baseline using the cohort median. This proxy is explicitly recorded (`proxy_baseline: true`) and is considered a permissible normalization step, not a prohibited imputation of the primary metric itself. All other metric values must not be imputed, interpolated, synthesized, or placeholder‑filled for the final analysis. (See US‑2).

- **FR-003**: System MUST categorize each extracted study into one of four privacy mechanism types: Differential Privacy, Secure Aggregation, Homomorphic Encryption, or Hybrid. **Primary Analysis Scope**: The primary meta‑analysis MUST focus on the interaction between **Data Skew** and **Differential Privacy vs. Secure Aggregation**. FHE and Hybrid mechanisms are to be included in the dataset but analyzed only as an exploratory secondary category unless sufficient data exists for a separate interaction analysis. (See US‑2).

- **FR-004**: System MUST perform a meta‑analysis to compute effect sizes (e.g., Hedges' g) and 95% confidence intervals for each performance metric per mechanism, **stratified by data skew level** (e.g., Low, Medium, High, or continuous alpha). If variance data (SD/SE) is missing for >50% of studies *within the specific mechanism group for the specific metric and skew level*, the system MUST fall back to descriptive aggregation (median, IQR) and MUST NOT use fixed‑effects models for that group. In this fallback mode, the system MUST use non‑parametric tests (e.g., Kruskal‑Wallis) for group comparison if raw data is available, but MUST NOT generate effect sizes or confidence intervals for that group; the output MUST be explicitly labeled as "Descriptive Summary" to avoid scientific misrepresentation. (See US‑3).

- **FR-005**: System MUST generate at least three visualization types: forest plots for effect sizes (when computable), bar charts for mean overhead, and a scatter plot for accuracy vs. privacy budget. Plots MUST be stratified by skew level where data permits. (See US‑3).

- **FR-006**: System MUST apply multiple‑comparison correction (e.g., Benjamini‑Hochberg) to the family of hypothesis tests comparing mechanism groups. The 'family' is defined as all pairwise comparisons across the 4 performance metrics and 4 mechanism groups, yielding **24** comparisons (k = 24). The system MUST use the Kruskal‑Wallis H test on **normalized raw extracted metric values** (column `normalized_value` in `extracted_metrics.csv`) to assess distributional differences, provided there are ≥3 raw data points per group. **Normalization Requirement**: For "Computational Cost", values MUST be normalized to a dimensionless **relative overhead ratio** before the test. If a study lacks a specific baseline, the system MAY generate a proxy baseline using the median overhead of the cohort for that mechanism, flagging the record as `proxy_baseline: true`. Records with `proxy_baseline: true` are permitted in the omnibus Kruskal‑Wallis test but are **excluded from subsequent random‑effects effect‑size estimation**; they are reported separately in a sensitivity‑analysis section. If the omnibus test is significant, the system MUST perform post‑hoc Dunn's tests with Benjamini‑Hochberg correction. This test is distinct from effect size estimation; effect sizes are computed via random‑effects models only when variance data is sufficient and when records have a valid baseline. (See US‑3).

- **FR-007**: System MUST detect studies lacking variance estimates (SD/SE) and exclude them from random‑effects models. If the exclusion rate within a group exceeds a majority threshold, the system MUST switch to the descriptive review pathway defined in the relevant system specification. (See US‑3).

- **FR-008**: System MUST normalize "Computational Cost" to a "relative overhead ratio" (Private Baseline / Non‑Private Baseline) for studies reporting both. A valid baseline is defined as a reported non‑private execution on the same hardware architecture OR a reported relative overhead ratio. Studies reporting only absolute time/FLOPs without such a baseline MUST be extracted with `valid_baseline: false`. The system MAY calculate a **proxy baseline** using the median of the cohort for that mechanism if no specific baseline is reported, flagging the record as `proxy_baseline: true`. **Records with `proxy_baseline: true` are INCLUDED in the dataset but EXCLUDED from primary random‑effects effect‑size computation; they are presented only in a sensitivity‑analysis branch**. (See US‑2).

- **FR-009**: System MUST report the count and percentage of studies excluded from the primary computational cost analysis due to missing baselines (those with `valid_baseline: false` AND `proxy_baseline: false`). The denominator for this percentage MUST be the total number of retrieved studies. If this exclusion rate exceeds a substantial proportion, the system MUST perform and report a sensitivity analysis comparing the results with and without the excluded studies to assess selection bias. (See US‑3).

- **FR-010**: System MUST ensure all numerical results in the final report are derived **exclusively from the actual extracted values** in the `extracted_metrics.csv` file. The system MUST NOT introduce any simulated, placeholder, hardcoded, or random values into the statistical analysis or visualization generation steps. Any proxy values (e.g., cohort median) used for normalization MUST be explicitly flagged and documented as such, but the primary statistical outputs (means, effect sizes, p‑values) MUST be computed directly from the observed data points. (See US‑3).

- **FR-011**: System MUST extract `skew_parameter` (e.g., Dirichlet alpha) from papers. If a study lacks a reported skew parameter, the system MUST flag it as `skew_unknown`. Studies with `skew_unknown` MUST be excluded from the primary interaction analysis (FR‑004) but included in a general descriptive summary. (See US‑1).

### Key Entities

- **Study**: A unique publication record containing metadata (DOI, title, authors), **skew parameters** (e.g., `skew_parameter`, `skew_unknown` flag), and extracted quantitative metrics.
- **Mechanism**: A categorical attribute of a study (DP, SecureAgg, FHE, Hybrid) used as the independent variable.
- **Metric**: A quantitative outcome variable (Communication Overhead, Convergence Speed, Accuracy Loss, Computational Cost) extracted from a study. Each metric record MUST include:
    - `raw_value`: **List of floats** (per‑client/per‑round metrics) OR **Single float** (aggregate study‑level metric).
    - `value_type`: Enum `['aggregate', 'per_client_list']`.
    - `normalized_value`: The value normalized to standard units or dimensionless ratio.
    - `valid_baseline`: Boolean (true if specific baseline exists).
    - `proxy_baseline`: Boolean (true if cohort median was used).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system extracts and reports the count (N) of studies per mechanism category and skew level. The system MUST successfully complete the pipeline even if N < 5, in which case the output is a "Descriptive Review" (See US‑1, US‑2).
- **SC-002**: The validity of the synthesized findings is measured by a manual spot‑check of the **entire** dataset if N ≤ 100, or a random sample if N > 100. A human reviewer MUST confirm that the extracted data in `extracted_metrics.csv` accurately reflects the source PDFs. The pass criterion is **0 errors for N ≤ 100**, or **error rate < 1% for N > 100** across all rows for the fields 'raw_value', 'mechanism_type', and 'skew_parameter'. (See US‑2).
- **SC-003**: The statistical validity of the meta‑analysis is measured by the generation of specific statistical outputs: 95% confidence intervals for effect sizes (Hedges' g) when variance data permits, OR descriptive statistics (median, IQR) with explicit qualitative summaries when variance data is insufficient. The output MUST include a forest plot with 95% CI and a p‑value for the primary comparison when applicable. (See US‑3).
- **SC-004**: The reproducibility of the pipeline is measured by the ability to re‑run the entire process on a fresh runner using a *fixed input snapshot* (e.g., a git‑tagged version of `extracted_metrics.csv`) and produce identical `results_summary.md` outputs, ensuring all results are derived from the actual extracted dataset without simulated or placeholder values. (See US‑1, US‑3).
- **SC-005**: The integrity of the results is measured by the absence of any simulated or hardcoded values in the final statistical outputs. A validation script MUST confirm that every numerical value in the final report matches a value present in `extracted_metrics.csv` or is a direct mathematical transformation of such values. The script MUST verify that all transformations (e.g., mean, median, log, sqrt) are recorded in a `transformation_log` column in the CSV and are part of a whitelisted set of allowed operations. **Crucially, the script MUST verify that no random number generation or synthetic data injection occurred during the computation of effect sizes or p-values.** (See US‑3).
- **SC-006**: **Metadata Extraction Completeness** (See US‑1). The system MUST produce a CSV file `retrieved_papers.csv` containing columns: `doi`, `title`, `authors`, `abstract`, `pdf_url`, `skew_parameter`, `skew_unknown`. The pipeline passes if the file contains at least 10 records, each row has non‑empty values for `doi`, `title`, `authors`, and `pdf_url`; missing `abstract` or `skew_parameter` must be flagged with `abstract_missing` or `skew_unknown` columns. All missing‑field incidents are logged in `metadata_issues.log`. Success is achieved when both the CSV and log are generated without pipeline error.

## Assumptions

- The arXiv and Semantic Scholar APIs provide sufficient access to PDFs and metadata for the 2018-2024 window without requiring institutional paywalls.
- The `tabula-py` or `pdfplumber` libraries can successfully extract tabular data from at least 80% of the target PDFs; the remaining [deferred] will be flagged for manual review.
- The "computational cost" metric is reported in a comparable unit (e.g., seconds, FLOPs, or relative overhead) across the majority of studies; studies using non‑comparable units without a baseline will be excluded from the primary aggregation but included in sensitivity analysis per FR‑009.
- The GitHub Actions free‑tier runner (2 CPU, 7GB RAM) is sufficient to run the `statsmodels` meta‑analysis and generate plots on the extracted dataset (expected size <100 rows).
- The search strings will yield a sufficient sample size (N≥5 per category) to perform a meta‑analysis. If N < 5 per category, the project is valid and will output a "Descriptive Systematic Review" rather than a quantitative meta‑analysis (See SC‑001).
- The dataset contains the necessary variables (privacy mechanism type, communication overhead, convergence speed, accuracy loss, computational cost, **data skew parameters**) for all included studies; if a study lacks a specific metric or skew parameter, that study will be excluded from the primary analysis of that specific metric or interaction.
- All quantitative results presented in the final report are derived exclusively from the text extracted from the retrieved PDFs; no synthetic data, simulated values, or hardcoded placeholders are introduced at any stage of the analysis pipeline. Any proxy values (e.g., cohort median) are explicitly flagged and reported in sensitivity analysis.

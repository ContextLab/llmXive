# Feature Specification: Systematic Review of Privacy-Preserving Federated Learning Protocols

**Feature Branch**: `001-systematic-review-privacy-fl`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Systematic Review of Privacy-Preserving Federated Learning Protocols"

## User Scenarios & Testing

### User Story 1 - Automated Literature Retrieval and Metadata Extraction (Priority: P1)

The system MUST retrieve peer-reviewed papers from arXiv and Semantic Scholar using specific search strings, filter them by publication date (recent years), and extract structured metadata (title, authors, abstract, PDF URL) for all candidates.

**Why this priority**: Without a complete and reproducible dataset of candidate papers, no analysis can occur. This is the foundational data ingestion step.

**Independent Test**: Can be fully tested by running the retrieval script against a fixed seed query and verifying the output CSV contains ≥10 records with valid metadata fields and no duplicates.

**Acceptance Scenarios**:

1. **Given** a search string for "federated learning" AND "differential privacy", **When** the system queries the APIs, **Then** the output CSV contains all papers from 2018-2024 matching the criteria, excluding duplicates.
2. **Given** a paper with missing metadata fields (e.g., no abstract), **When** the system processes it, **Then** the record is flagged in a `review_needed.log` file rather than silently dropped.
3. **Given** an API rate limit or timeout, **When** the script retries up to 3 times, **Then** the system logs the failure and continues processing remaining queries without crashing.

---

### User Story 2 - Quantitative Data Extraction from PDFs (Priority: P2)

The system MUST parse PDFs of selected papers to extract specific quantitative performance metrics (communication overhead in KB/MB, convergence rounds, accuracy drop %, computational runtime) and map them to the corresponding privacy mechanism category (DP, SecureAgg, FHE, Hybrid).

**Why this priority**: This transforms unstructured text into the structured dataset required for the meta-analysis. It is the core data processing step.

**Independent Test**: Can be fully tested by running the parser on a set of 5 known PDFs with pre-validated ground truth tables and verifying the extracted CSV values match within a 5% tolerance or flagging discrepancies for manual review.

**Acceptance Scenarios**:

1. **Given** a PDF containing a table with "Accuracy Loss" and "Privacy Budget", **When** the parser processes the file, **Then** the values are correctly extracted into `extracted_metrics.csv` with the correct privacy mechanism tag.
2. **Given** a PDF with non-standard table formatting (e.g., merged cells), **When** the parser encounters it, **Then** the system logs a `parsing_error` and skips the specific table row, preserving the rest of the file's data.
3. **Given** a paper reporting metrics in different units (e.g., seconds vs. milliseconds), **When** the system processes the data, **Then** all values are normalized to a standard unit (seconds for time, bytes for communication) before storage.

---

### User Story 3 - Meta-Analysis and Visualization Generation (Priority: P3)

The system MUST perform random-effects meta-analysis to compute effect sizes linking privacy mechanism types to performance metrics, generate forest plots and bar charts, and produce a summary Markdown report.

**Why this priority**: This delivers the final research output, synthesizing the extracted data into actionable insights and visual evidence.

**Independent Test**: Can be fully tested by running the analysis on a small synthetic dataset with known effect sizes and verifying the generated plots match the expected statistical trends and the summary report contains the calculated confidence intervals.

**Acceptance Scenarios**:

1. **Given** a dataset of 20 extracted studies, **When** the meta-analysis runs, **Then** the output includes a forest plot for "Accuracy Loss vs. Privacy Mechanism" with 95% confidence intervals.
2. **Given** a scenario where a specific privacy mechanism has <3 data points, **When** the analysis runs, **Then** the system flags this as "Insufficient Data" in the report rather than calculating a statistically invalid effect size.
3. **Given** the full analysis pipeline, **When** the `run.sh` script completes, **Then** it generates a `results_summary.md` containing the main findings, tables, and links to all generated figures.

### Edge Cases

- What happens when a PDF cannot be downloaded due to a paywall or broken link? (System must log the DOI and skip, ensuring the pipeline continues).
- How does the system handle papers that use a hybrid mechanism but do not clearly separate metrics for each component? (System must categorize as "Hybrid" and extract aggregate metrics, flagging for manual review if disentanglement is impossible).
- What if the search returns zero results for a specific mechanism (e.g., FHE) in the 2018-2024 window? (System must report "No Data Available" for that category rather than crashing).

## Requirements

### Functional Requirements

- **FR-001**: System MUST query arXiv and Semantic Scholar APIs using the exact search strings defined in the methodology to retrieve papers published between 2018 and 2024 (See US-1).
- **FR-002**: System MUST extract and normalize communication overhead, convergence speed, accuracy loss, and computational cost from PDF tables into a single CSV file (See US-2).
- **FR-003**: System MUST categorize each extracted study into one of four privacy mechanism types: Differential Privacy, Secure Aggregation, Homomorphic Encryption, or Hybrid (See US-2).
- **FR-004**: System MUST perform a random-effects meta-analysis using `statsmodels` to compute effect sizes and 95% confidence intervals for each performance metric per mechanism (See US-3).
- **FR-005**: System MUST generate at least three visualization types: forest plots for effect sizes, bar charts for mean overhead, and a scatter plot for accuracy vs. privacy budget (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to all hypothesis tests where >1 metric is analyzed simultaneously (See US-3).

### Key Entities

- **Study**: A unique publication record containing metadata (DOI, title, authors) and extracted quantitative metrics.
- **Mechanism**: A categorical attribute of a study (DP, SecureAgg, FHE, Hybrid) used as the independent variable.
- **Metric**: A quantitative outcome variable (Communication Overhead, Convergence Speed, Accuracy Loss, Computational Cost) extracted from a study.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The total number of successfully extracted studies with ≥3 valid data points per mechanism category is measured against the inclusion criteria (≥5 studies per category required for statistical power) (See US-1, US-2).
- **SC-002**: The accuracy of extracted numerical values is measured against a manually verified ground-truth subset of 10 papers (target: ≥95% exact match or within 5% tolerance) (See US-2).
- **SC-003**: The statistical validity of the meta-analysis is measured by the successful generation of confidence intervals that do not include zero for at least one significant effect size, or a clear "no significant difference" conclusion if null (See US-3).
- **SC-004**: The computational feasibility is measured by the total runtime of the `run.sh` script on a GitHub Actions free-tier runner (target: ≤6 hours) (See US-3).
- **SC-005**: The reproducibility of the pipeline is measured by the ability to re-run the entire process on a fresh runner and produce identical `extracted_metrics.csv` and `results_summary.md` outputs (See US-1, US-3).

## Assumptions

- The arXiv and Semantic Scholar APIs provide sufficient access to PDFs and metadata for the 2018-2024 window without requiring institutional paywalls.
- The `tabula-py` or `pdfplumber` libraries can successfully extract tabular data from at least 80% of the target PDFs; the remaining [deferred] will be flagged for manual review.
- The "computational cost" metric is reported in a comparable unit (e.g., seconds, FLOPs, or relative overhead) across the majority of studies; studies using non-comparable units will be excluded or normalized if a conversion factor is explicitly stated.
- The GitHub Actions free-tier runner (2 CPU, 7GB RAM) is sufficient to run the `statsmodels` random-effects meta-analysis and generate plots on the extracted dataset (expected size <100 rows).
- The search strings will yield a sufficient sample size (N≥15 per category) to perform a meaningful random-effects meta-analysis; if N<15, the analysis will be limited to descriptive statistics.
- The dataset contains the necessary variables (privacy mechanism type, communication overhead, convergence speed, accuracy loss, computational cost) for all included studies; if a study lacks a specific metric, that study will be excluded from the analysis of that specific metric.

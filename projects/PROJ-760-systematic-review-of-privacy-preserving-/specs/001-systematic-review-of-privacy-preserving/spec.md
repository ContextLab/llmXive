# Feature Specification: Systematic Review of Privacy-Preserving Federated Learning Protocols

**Feature Branch**: `001-systematic-review-privacy-fl`  
**Created**: 2026-07-10  
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

**Independent Test**: Can be fully tested by running the parser on a manually annotated random sample of ≤5 papers (selected by the researchers) to verify extraction accuracy against the ground truth labels created for this sample. The system MUST NOT require manual extraction of the full corpus to proceed with the automated analysis pipeline.

**Acceptance Scenarios**:

1. **Given** a PDF containing a table with "Accuracy Loss" and "Privacy Budget", **When** the parser processes it, **Then** the values are correctly extracted into `extracted_metrics.csv` with the correct privacy mechanism tag.
2. **Given** a PDF with non-standard table formatting (e.g., merged cells), **When** the parser encounters it, **Then** the system logs a `parsing_error` and skips the specific table row, preserving the rest of the file's data.
3. **Given** a paper reporting metrics in different units, **When** the system processes the data, **Then** all values are normalized to standard units: Convergence Speed to 'rounds' (integer), Communication Overhead to 'bytes', and Computational Cost to 'seconds' or 'relative overhead ratio' (if baseline is available).

---

### User Story 3 - Meta-Analysis and Visualization Generation (Priority: P3)

The system MUST perform meta-analysis to compute effect sizes linking privacy mechanism types to performance metrics, generate forest plots and bar charts, and produce a summary Markdown report. If variance data is missing, the system MUST fall back to descriptive statistics (median, IQR) rather than fixed-effects models.

**Why this priority**: This delivers the final research output, synthesizing the extracted data into actionable insights and visual evidence.

**Independent Test**: Can be fully tested by running the analysis on a small synthetic dataset with known effect sizes and verifying the generated plots match the expected statistical trends and the summary report contains the calculated confidence intervals (regardless of whether they include zero).

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
- **FR-002**: System MUST extract and normalize communication overhead, convergence speed, accuracy loss, and computational cost from PDF tables into a single CSV file. All values MUST be derived strictly from extracted text; the system MUST NOT generate, simulate, placeholder, or hardcode any metric values for the final analysis (See US-2).
- **FR-003**: System MUST categorize each extracted study into one of four privacy mechanism types: Differential Privacy, Secure Aggregation, Homomorphic Encryption, or Hybrid (See US-2).
- **FR-004**: System MUST perform a meta-analysis to compute effect sizes (e.g., Hedges' g) and 95% confidence intervals for each performance metric per mechanism. If variance data (SD/SE) is missing for >50% of studies *within a specific mechanism group* for a specific metric, the system MUST fall back to descriptive aggregation (median, IQR) and MUST NOT use fixed-effects models for that group. In this fallback mode, the system MUST use non-parametric tests (e.g., Kruskal-Wallis) for group comparison instead of effect size estimation (See US-3).
- **FR-005**: System MUST generate at least three visualization types: forest plots for effect sizes (when computable), bar charts for mean overhead, and a scatter plot for accuracy vs. privacy budget (See US-3).
- **FR-006**: System MUST apply multiple-comparison correction (e.g., Benjamini-Hochberg) to the family of hypothesis tests comparing mechanism groups. The test MUST use the Kruskal-Wallis H test on *raw extracted metric values* (e.g., raw accuracy drop %) across groups to assess distributional differences. This test is distinct from effect size estimation; effect sizes are computed via random-effects models only when variance data is sufficient (See US-3).
- **FR-007**: System MUST detect studies lacking variance estimates (SD/SE) and exclude them from random-effects models. If the exclusion rate within a group exceeds 50%, the system MUST switch to the descriptive review pathway defined in FR-004 (See US-3).
- **FR-008**: System MUST normalize "Computational Cost" to a "relative overhead ratio" (Private Baseline / Non-Private Baseline) for studies reporting both. A valid baseline is defined as a reported non-private execution on the same hardware architecture. Studies reporting only absolute time/FLOPs without such a baseline MUST be excluded from the computational cost meta-analysis to ensure metric commensurability (See US-2).
- **FR-009**: System MUST report the count and percentage of studies excluded from the computational cost analysis due to missing baselines. If this exclusion rate exceeds 20%, the system MUST perform and report a sensitivity analysis comparing the results with and without the excluded studies to assess selection bias (See US-3).

### Key Entities

- **Study**: A unique publication record containing metadata (DOI, title, authors) and extracted quantitative metrics.
- **Mechanism**: A categorical attribute of a study (DP, SecureAgg, FHE, Hybrid) used as the independent variable.
- **Metric**: A quantitative outcome variable (Communication Overhead, Convergence Speed, Accuracy Loss, Computational Cost) extracted from a study.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system extracts and reports the count (N) of studies per mechanism category. The system MUST successfully complete the pipeline even if N < 5, in which case the output is a "Descriptive Review" (See US-1, US-2).
- **SC-002**: The validity of the synthesized findings is measured by a manual spot-check of a random sample of 5 extracted studies. A human reviewer MUST confirm that the extracted data in `extracted_metrics.csv` accurately reflects the source PDFs and supports the reported conclusions in `results_summary.md` (See US-2).
- **SC-003**: The statistical validity of the meta-analysis is measured by the generation of appropriate statistical outputs: 95% confidence intervals for effect sizes when variance data permits, or descriptive statistics (median, IQR) with explicit qualitative summaries when variance data is insufficient (See US-3).
- **SC-004**: The reproducibility of the pipeline is measured by the ability to re-run the entire process on a fresh runner using a *fixed input snapshot* (e.g., a git-tagged version of `extracted_metrics.csv`) and produce identical `results_summary.md` outputs, ensuring no simulated, placeholder, or hardcoded values are introduced into the final dataset (See US-1, US-3).

## Assumptions

- The arXiv and Semantic Scholar APIs provide sufficient access to PDFs and metadata for the 2018-2024 window without requiring institutional paywalls.
- The `tabula-py` or `pdfplumber` libraries can successfully extract tabular data from at least 80% of the target PDFs; the remaining [deferred] will be flagged for manual review.
- The "computational cost" metric is reported in a comparable unit (e.g., seconds, FLOPs, or relative overhead) across the majority of studies; studies using non-comparable units without a baseline will be excluded per FR-008.
- The GitHub Actions free-tier runner (2 CPU, 7GB RAM) is sufficient to run the `statsmodels` meta-analysis and generate plots on the extracted dataset (expected size <100 rows).
- The search strings will yield a sufficient sample size (N≥5 per category) to perform a meta-analysis. If N < 5 per category, the project is valid and will output a "Descriptive Systematic Review" rather than a quantitative meta-analysis (See SC-001).
- The dataset contains the necessary variables (privacy mechanism type, communication overhead, convergence speed, accuracy loss, computational cost) for all included studies; if a study lacks a specific metric, that study will be excluded from the analysis of that specific metric.
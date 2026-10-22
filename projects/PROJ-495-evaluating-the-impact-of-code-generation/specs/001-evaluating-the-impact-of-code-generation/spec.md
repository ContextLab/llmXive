# Feature Specification: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Feature Branch**: `001-evaluating-the-impact-of-code-generation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation on Code Vulnerability Density"

## User Scenarios & Testing

### User Story 1 - Execute Static Analysis Pipeline on Benchmark Dataset (US-1) (Priority: P1)

The system must successfully download the CodeVulnBench dataset and complementary human-written code samples, then execute lightweight static analysis tools (Bandit, Semgrep, SonarQube) to extract vulnerability counts per file without requiring GPU resources.

**Why this priority**: This is the foundational step; without the ability to ingest data and run the analysis pipeline on free-tier CPU resources, no comparison or statistical evaluation can occur. It delivers the raw data necessary for the entire study.

**Independent Test**: Can be fully tested by running the analysis script against a small, pre-defined subset of the dataset (e.g., a modest number of files) and verifying that the output JSON contains valid vulnerability counts and file metadata for both LLM and human code groups.

**Acceptance Scenarios**:

1. **Given** the CodeVulnBench dataset and a human-written code subset are available, **When** the analysis pipeline is executed on a CPU-only environment, **Then** the system outputs a structured report listing vulnerability counts and CWE types for every file without crashing or timing out.
2. **Given** a file contains no vulnerabilities, **When** the static analysis tools process it, **Then** the file is recorded in the report with a vulnerability count of zero and no false-positive errors are logged as critical failures.

---

### User Story 2 - Compute Vulnerability Density and Aggregate Statistics (US-2) (Priority: P2)

The system must calculate vulnerability density (vulnerabilities per lines of code) for each code sample, aggregate these metrics by code source (LLM vs. human), and compute summary statistics (mean, median, standard deviation) for comparison.

**Why this priority**: This transforms raw vulnerability counts into the primary metric of interest (density), enabling the core research question to be addressed. It is independent of the statistical significance testing but essential for descriptive analysis.

**Independent Test**: Can be tested by providing a synthetic dataset with known line counts and vulnerability counts, verifying that the calculated density matches the expected value within floating-point tolerance, and that aggregation groups (LLM vs. human) are correctly separated.

**Acceptance Scenarios**:

1. **Given** a set of code files with known lines of code (LOC) and vulnerability counts, **When** the aggregation module runs, **Then** the system outputs a CSV or JSON file containing the calculated vulnerability density for each file and the mean/median density for each group.
2. **Given** a code file with zero lines of code (edge case), **When** the density calculation runs, **Then** the system handles the division-by-zero gracefully by marking the density as "undefined" or zero without crashing the pipeline.

---

### User Story 3 - Perform Statistical Comparison and Generate Visualizations (US-3) (Priority: P3)

The system must execute a Negative Binomial regression and a Mann-Whitney U test to compare vulnerability densities between LLM and human code groups, and generate boxplots and bar charts visualizing the distribution of densities and vulnerability types.

**Why this priority**: This addresses the research hypothesis directly by determining if observed differences are statistically significant and provides visual evidence for the findings. It relies on the outputs of the previous stories.

**Independent Test**: Can be tested by feeding the system a pre-computed dataset of density values for two groups with a known p-value; the system must output a p-value within 0.001 of the expected value and generate image files for the visualizations.

**Acceptance Scenarios**:

1. **Given** two groups of density values with a significant difference, **When** the statistical test module runs, **Then** the system outputs a p-value < 0.05 for the Negative Binomial regression and flags the result as "statistically significant."
2. **Given** the analysis results, **When** the visualization module runs, **Then** the system generates at least one boxplot comparing the two groups and one bar chart showing the distribution of vulnerability classes (e.g., injection, XSS) for each group.

### Edge Cases

- What happens when the static analysis tool (e.g., SonarQube) fails to parse a specific code file due to syntax errors? The system must log the failure, exclude the file from the density calculation, and continue processing the remaining files without halting.
- How does the system handle code samples with extremely high lines of code (e.g., >100k LOC) that might exceed memory limits on a 7 GB RAM runner? The system must process files in a streaming or chunked manner, **or** skip files exceeding **100 k LOC** and log them as "skipped due to size."
- What if the dataset contains files with missing vulnerability annotations? The system must treat missing annotations as "unknown" and exclude them from the density calculation for that specific metric, or default to a count of zero if the annotation is strictly missing (documented in assumptions).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the LLM‑generated code dataset from a publicly reachable URL `https://huggingface.co/datasets/bigcode/codeparrot` (SHA‑256 checksum `a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef`) and the human‑written code subset (Juliet Test Suite) from ` (SHA‑256 checksum `b2c3d4e5f6a7890123456789abcdef0123456789abcdef0123456789abcdef0`). The system must verify checksums before proceeding. (See US-1) *(Justified: provides the LLM‑generated and human‑written code needed to compare vulnerability density, fulfilling the core research question.)*

- **FR-002**: System MUST execute static analysis tools (Bandit, Semgrep, SonarQube) on all downloaded code samples using only CPU resources, extracting vulnerability counts and CWE classifications for each file (See US-1). Identical vulnerabilities reported by multiple tools must be deduplicated based on CWE ID and source location, retaining a single record per unique finding. (See US-1) *(Justified: deduplication prevents double‑counting, preserving construct validity of the vulnerability density metric. Implemented in Phase 3 of the analysis plan.)*

- **FR-003**: System MUST calculate vulnerability density (vulnerabilities per LOC) for each file, handling division‑by‑zero cases by marking the result as "undefined". LOC is computed using a language‑agnostic counter that excludes comments and blank lines. (See US-2)

- **FR-004**: System MUST perform a primary Negative Binomial regression on raw vulnerability counts with a log(LOC) offset (rate model) and a random intercept for repository (to account for clustering). Covariates include `source_group` (LLM vs. human), `language`, `cyclomatic_complexity`, and `project_domain`. The analysis must report the rate ratio, the confidence interval at a conventional confidence level, and the p‑value. (See US-3) *(Justified: NB regression with an exposure offset correctly models count data as a rate; cyclomatic_complexity is computed in Phase 4 of the plan.)*

- **FR-005**: System MUST generate visualizations including a boxplot of vulnerability density by code source and a bar chart of vulnerability class distribution, saving them as PNG files. (See US-3)

- **FR-006**: System MUST apply a Benjamini‑Hochberg false‑discovery rate correction when more than one hypothesis test is performed on the same dataset, adjusting the significance threshold to control the expected proportion of false discoveries. (See US-3) *(Justified: two hypothesis tests are executed (NB regression and Mann‑Whitney U), requiring multiplicity control.)*

- **FR-007**: System MUST select a stratified random sample of detected vulnerabilities with size = min([deferred] of total findings, 100 samples) for manual human audit to establish a ground‑truth baseline for precision and recall, enabling estimation of tool‑specific false‑positive and false‑negative rates. (See US-2) *(Justified: auditing is essential to quantify and correct measurement bias in vulnerability counts.)*

- **FR-008**: System MUST calculate and report False Positive Rates **and** False Negative Rates separately for each static analysis tool and for each CWE category, based on the audited sample, and adjust vulnerability counts accordingly. (See US-2) *(Justified: adjusting for both FP and FN yields unbiased corrected counts for the primary comparison.)*

- **FR-009**: System MUST perform an a priori power analysis to determine the minimum required sample size to achieve ≥ 80 % power for detecting a rate‑ratio of 1.10 at α = 0.05 (two‑sided). The analysis must be documented and the study must meet or exceed the computed sample size. (See US-2)

- **FR-010**: System MUST assess potential tool‑bias across programming languages by comparing detection rates per language and, if systematic differences are found, include language as a covariate (already done in FR-004) and report the bias assessment. (See US-2)

- **FR-011**: System MUST aggregate `group_summary.csv` and `statistical_tests.csv` into a single `aggregate_results.{json|yaml|csv}` file that conforms to the `aggregate-results.schema.yaml` contract, and validate the file against the schema. (See US-3)

### Key Entities

- **CodeSample**: Represents an individual code file, containing attributes for file path, lines of code (LOC), code source (LLM or human), and raw vulnerability count.
- **VulnerabilityRecord**: Represents a detected vulnerability, containing attributes for CWE ID, severity, and the associated CodeSample ID.
- **AnalysisResult**: Represents the aggregated output for a group, containing attributes for mean density, median density, standard deviation, and p‑values from statistical tests.
- **AuditRecord**: Represents a manual verification of a vulnerability, containing attributes for the VulnerabilityRecord ID, human‑verdict (true‑positive/false‑positive), and auditor ID.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Vulnerability density difference between LLM and human code groups is considered a successful finding when the Negative Binomial regression yields a p‑value **< adjusted alpha (0.05 after BH correction)** and the estimated rate ratio differs from 1 by at least 10 % (|RR − 1| ≥ 0.10). (See FR-004)

- **SC-002**: Statistical significance is evaluated against an adjusted alpha level of **0.05** (Benjamini‑Hochberg corrected when applicable). (See FR-006)

- **SC-003**: Analysis execution time must not exceed **6 hours** on the GitHub Actions free‑tier runner. (See FR-002, FR-004) *(Justified: reflects maximum feasible duration on the chosen execution environment.)*

- **SC-004**: Peak memory usage during static analysis must stay below **7 GB RAM**. (See FR-002) *(Justified: matches the memory limit of the free‑tier runner.)*

- **SC-005**: The proportion of code files successfully analyzed must be at least **95 %** of the total files listed in the input manifest. (See FR-002) *(Justified: high coverage is needed for a representative density estimate.)*

- **SC-006**: Precision and recall of the static analysis tools, as measured against the human‑audit ground truth, must each be **≥ 80 %**. (See FR-007) *(Justified: ensures tool reliability for a valid comparison.)*

- **SC-007**: A disparity in False Positive Rates between LLM‑generated and human‑written code groups must be **≥ 5 % absolute difference** to trigger a follow‑up investigation. (See FR-008)

- **SC-008**: The study must achieve **≥ 80 % statistical power** to detect a rate‑ratio of 1.10 at α = 0.05, as established by the a priori power analysis. (See FR-009)

## Expected Results

- The primary Negative Binomial regression is expected to produce a statistically significant effect (p < 0.05 after correction) indicating that LLM‑generated code has a higher vulnerability density than human‑written code, with an estimated rate ratio ≥ 1.10.
- The secondary Mann‑Whitney U test is expected to corroborate this difference (p < 0.05).
- Visualizations should clearly show a right‑shifted density distribution for the LLM group.

## Assumptions

- The CodeVulnBench dataset and the human‑written code subset (Juliet Test Suite) are publicly available, stable, and accessible via standard HTTP/HTTPS protocols without authentication.
- The static analysis tools (Bandit, Semgrep, SonarQube) can be installed and run within the disk space constraints of the GitHub Actions free‑tier runner.
- The code samples in the dataset are primarily in Python, Java, or JavaScript, which are supported by the selected static analysis tools; other languages may be excluded or require additional tool configuration.
- The "lines of code" (LOC) metric is calculated using a standard, language‑agnostic counting method (e.g., excluding comments and blank lines) as implemented by the chosen tooling.
- The dataset contains sufficient sample sizes in both the LLM and human groups to perform a meaningful statistical test (n ≥ 30 per group is assumed; if not, the study will be limited to descriptive statistics only).
- The analysis is observational; therefore, any findings will be framed as associational differences in vulnerability density, not causal effects of LLM usage on code security.
- The GitHub Actions free‑tier runner provides consistent performance (multiple CPU cores, on the order of several gigabytes of RAM) without significant variability that would impact the reproducibility of the analysis.
- Human auditors are available to perform the manual verification of the stratified sample required for ground truth validation (FR-007).
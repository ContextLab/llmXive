# Feature Specification: Assessing Statistical Power in Reproducible Research with Public Datasets

**Feature Branch**: `001-assess-statistical-power`
**Created**: 2024-05-21
**Status**: Draft
**Input**: User description: "Assessing Statistical Power in Reproducible Research with Public Datasets"

## User Scenarios & Testing

### User Story 1 - Retrieve and Filter Top Public Datasets (Priority: P1)

The system must successfully connect to the OpenML API, retrieve metadata for the most-downloaded classification datasets, and filter this list to retain only those with associated primary analysis publications or task IDs required for the audit.

**Why this priority**: This is the foundational data ingestion step. Without a valid, filtered list of target datasets, no subsequent analysis, power calculation, or auditing can occur. It delivers immediate value by establishing the audit corpus. Note: The selection of "most-downloaded" datasets is a proxy for high-impact studies, though this introduces a sampling bias toward popular methods which is acknowledged in the Assumptions.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output JSON file contains a variable number of entries, capped by the API's maximum response limit or the available data volume with non-null publication metadata fields.

**Acceptance Scenarios**:

1. **Given** the OpenML API is reachable, **When** the system requests the top 50 classification datasets, **Then** the system receives a list of 50 dataset objects with metadata.
2. **Given** the retrieved list, **When** the system filters for datasets with associated publication links OR task IDs, **Then** the resulting list contains only datasets where the publication link field OR task ID field is present and non-empty.
3. **Given** the API returns fewer than 50 datasets, **When** the system processes the response, **Then** the system proceeds with the available count without crashing.

---

### User Story 2 - Extract Statistical Parameters via Full-Text Parsing (Priority: P2)

The system must parse the full-text content of associated publications (or abstracts as a fallback) to extract the reported sample size (N) and effect sizes (e.g., Cohen's d, F-statistic) required for power calculation, handling missing or malformed data gracefully. The system acknowledges that abstracts rarely contain raw effect sizes; if full text is unavailable, the entry is marked "unparseable" to avoid false extraction.

**Why this priority**: This step translates raw metadata into the specific variables needed for the statistical audit. It is critical for the "what" of the research question but depends on the successful data retrieval from P1. The reliance on full-text is a necessary constraint to ensure scientific validity.

**Independent Test**: Can be fully tested by running the extraction script on a known subset of datasets with manually verified effect sizes and sample sizes, comparing the script's output against the manual verification to ensure parsing accuracy.

**Acceptance Scenarios**:

1. **Given** a full-text publication containing "N=150, Cohen's d=0.5", **When** the parser processes the text, **Then** it extracts sample_size=150 and effect_size=0.5 with the correct type.
2. **Given** a publication where the effect size is reported as an F-statistic (e.g., "F(2, 145)=4.5"), **When** the parser processes the text, **Then** it extracts the F-statistic value, degrees of freedom, and flags the metric type as "F".
3. **Given** a publication with no extractable statistical parameters in either full-text or abstract, **When** the parser processes the text, **Then** it records the dataset as "unparseable" and excludes it from the power calculation step without halting execution.

---

### User Story 3 - Compute Observed Power and Generate Audit Report (Priority: P3)

The system must calculate observed statistical power for each extractable dataset using the `statsmodels` library, compare results against the 0.8 threshold, and generate a summary report visualizing the distribution of power values with a mandatory disclaimer about the post-hoc power fallacy.

**Why this priority**: This is the core analytical deliverable. It answers the primary research question by quantifying the prevalence of underpowered studies. It depends on the successful extraction of parameters from P2.

**Independent Test**: Can be fully tested by running the analysis on a small, synthetic dataset with known parameters where the expected observed power is calculable by hand, verifying the script's output matches the theoretical value.

**Acceptance Scenarios**:

1. **Given** a dataset with N=100 and effect_size=0.2 (small), **When** the power calculation runs, **Then** the output power value is approximately consistent with the theoretical prediction (or within a 5% tolerance of the theoretical value).
2. **Given** a list of calculated power values, **When** the system generates the report, **Then** the report includes a histogram showing the distribution of power values, a count of studies with power < 0.8, and a disclaimer stating "Observed power is a monotone function of the p-value and should not be used for post-hoc validation (Hoenig & Heisey).."
3. **Given** a dataset where the effect size is missing, **When** the calculation runs, **Then** the system skips the power calculation for that entry and logs a warning without crashing.

### Edge Cases

- **What happens when** the OpenML API returns a rate-limit error (HTTP 429) during the initial fetch?
 - The system must implement a retry mechanism with exponential backoff (a configurable number of retries, initial delay, and maximum delay) before failing the job.
- **How does the system handle** publications that report effect sizes in non-standard formats (e.g., "p < 0.05" without an effect size)?
 - The system must log these as "insufficient data" and exclude them from the quantitative power analysis, ensuring they do not bias the power distribution.
- **What happens when** the calculated power exceeds 1.0 due to rounding errors in the input effect size?
 - The system must clamp the output value to 1.0 and log a warning regarding input precision.

## Requirements

### Functional Requirements

- **FR-001**: System MUST connect to the OpenML API () and retrieve metadata for the top 50 most-downloaded classification datasets (See US-1).
- **FR-002**: System MUST filter the retrieved dataset list to retain only entries with non-null publication links OR task IDs (See US-1).
- **FR-003**: System MUST parse full-text publications (or abstracts as fallback) to extract sample size (N) and effect sizes (e.g., Cohen's d, F-statistic) using regex or lightweight NLP (See US-2).
- **FR-004**: System MUST calculate observed statistical power using the `statsmodels.stats.power` library for all successfully parsed datasets (See US-3).
- **FR-005**: System MUST generate a summary report containing a histogram of power values, a count of studies with power < 0.8, and a disclaimer regarding the post-hoc power fallacy (See US-3).
- **FR-006**: System MUST include a capability for A Priori Power Analysis for future study design validation (See US-3).
- **FR-007**: System MUST validate that the publication reports the specific univariate effect sizes required for the analysis before attempting extraction (See US-1).
- **FR-008**: System MUST perform a sensitivity analysis on the extraction success rate by comparing results when using full-text only versus full-text + abstract fallback, reporting the delta in the final audit (See US-2).
- **FR-009**: System MUST report the distribution of dataset types (e.g., binary, multi-class) and source categories in the final audit to assess representativeness of the sampling frame (See US-1).

### Key Entities

- **DatasetMetadata**: Represents an entry from the OpenML API, containing fields for `dataset_id`, `name`, `download_count`, `publication_link`, and `task_id`.
- **StatisticalParameters**: Represents the extracted values from a publication, containing `sample_size` (int/float), `effect_size` (float), `metric_type` (string, e.g., "Cohen's d", "F"), and `degrees_of_freedom` (optional tuple or int, **required** for F-statistic conversion).
- **PowerAuditResult**: Represents the outcome of the calculation for a single dataset, containing `dataset_id`, `calculated_power` (float), `threshold_met` (boolean), and `status` (string, e.g., "success", "unparseable").

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of successfully parsed datasets (vs. total filtered datasets) is measured against the target of ≥ 60% extraction success rate (See US-2).
- **SC-002**: The calculated observed power values are measured against the conventional threshold for adequate statistical power. to determine the fraction of studies with power < 0.8 (See US-3).
- **SC-003**: The total execution time of the data download, parsing, and analysis pipeline is measured against the CI job limit. defined in Assumptions (See Assumptions).
- **SC-004**: The memory usage of the analysis script is measured against the system's available RAM limit. defined in Assumptions (See Assumptions).

## Assumptions

- The OpenML API allows unauthenticated access for retrieving metadata of the top 50 datasets without requiring an API key.
- The full-text content of associated publications contains sufficient text to allow regex-based extraction of sample sizes and effect sizes; abstracts are used only as a fallback and are not expected to contain the required effect size statistics.
- The analysis will run on a CPU-only environment; no GPU acceleration is required or available for the `statsmodels` calculations.
- The dataset of top publications and their associated text data will fit within the standard disk limit of the CI runner (GitHub Actions free-tier standard).
- The `statsmodels` library is pre-installed or can be installed within the standard time limit of the CI job..
- Effect sizes reported as F-statistics will be treated as direct inputs for power calculation approximations or converted using standard formulas if degrees of freedom are available in the metadata.
- The free-tier GitHub Actions runner provides a limited RAM allocation (GitHub Actions free-tier standard).
- The selection of "most-downloaded" datasets introduces a sampling bias toward high-impact studies; the audit results reflect this specific subset and are not generalizable to all scientific literature without further weighting.
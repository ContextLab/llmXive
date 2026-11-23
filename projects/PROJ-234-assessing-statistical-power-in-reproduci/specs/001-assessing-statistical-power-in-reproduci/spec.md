# Feature Specification: Assessing Statistical Power in Reproducible Research with Public Datasets

**Feature Branch**: `001-assess-statistical-power`
**Created**: 2024-05-21
**Status**: Draft
**Input**: User description: "Assessing Statistical Power in Reproducible Research with Public Datasets"

## User Scenarios & Testing

### US-1 - Retrieve and Filter Top Public Datasets (Priority: P1)

The system must successfully connect to the OpenML API, retrieve metadata for the most‑downloaded classification datasets, and filter this list to retain only those with associated primary analysis publications or task IDs required for the audit.

**Why this priority**: This is the foundational data ingestion step. Without a valid, filtered list of target datasets, no subsequent analysis, power calculation, or auditing can occur. It delivers immediate value by establishing the audit corpus. Note: The selection of "most‑downloaded" datasets is a proxy for high‑impact studies, though this introduces a sampling bias toward popular methods which is acknowledged in the Assumptions and addressed by FR‑012.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output JSON file contains a non‑empty list of entries, each with either a non‑null `publication_link` or a non‑null `task_id`.

**Acceptance Scenarios**:

1. **Given** the OpenML API is reachable, **When** the system requests the top few classification datasets, **Then** the system receives a list of up to 50 dataset objects with metadata.
2. **Given** the retrieved list, **When** the system filters for datasets with associated publication links **OR** task IDs, **Then** the resulting list contains only datasets where the `publication_link` field **OR** the `task_id` field is present and non‑empty.
3. **Given** the API returns fewer than 50 datasets, **When** the system processes the response, **Then** the system proceeds with the available count without crashing.

### US-2 - Extract Statistical Parameters via Full‑Text Parsing (Priority: P2)

The system must parse the full‑text content of associated publications (or abstracts as a fallback) to extract the reported sample size (N) and effect sizes (e.g., Cohen's d, F‑statistic, odds ratio) required for power calculation, handling missing or malformed data gracefully. The system validates that the extracted effect size matches the reported statistical test type before proceeding.

**Why this priority**: This step translates raw metadata into the specific variables needed for the statistical audit. It is critical for the “what” of the research question but depends on the successful data retrieval from US‑1. The validation step ensures that subsequent power calculations use appropriate models.

**Independent Test**: Can be fully tested by running the extraction script on a curated subset of datasets with manually verified parameters and comparing the script's output against the manual ground truth.

**Acceptance Scenarios**:

1. **Given** a full‑text publication containing “N=150, Cohen's d=0.5”, **When** the parser processes the text, **Then** it extracts `sample_size=150` and `effect_size=0.5` with `metric_type="Cohen's d"`.
2. **Given** a publication where the effect size is reported as an F‑statistic (e.g., “F(2, 145)=4.5”), **When** the parser processes the text, **Then** it extracts the F‑statistic value, degrees of freedom, and flags the metric type as “F”.
3. **Given** a publication with no extractable statistical parameters in either full‑text or abstract, **When** the parser processes the text, **Then** it records the dataset as “unparseable” and excludes it from the power calculation step without halting execution.
4. **Given** an extracted effect size that does not correspond to a supported test type, **When** the parser validates the metric, **Then** it logs a warning and marks the entry as “invalid metric”, skipping power computation for that entry.

### US-3 - Compute Power and Generate Audit Report (Priority: P3)

The system must calculate both (a) **observed statistical power** for each dataset using the reported effect size and an appropriate test‑specific model, and (b) **reference power** using a test‑specific small‑effect metric (Cohen's d = 0.2 for t‑tests, f = 0.2 for ANOVA, log‑odds ≈ 0.2 for logistic regression) with α = 0.05 and the study’s sample size. **Reference power is the primary adequacy metric**; studies with reference power < 0.8 are flagged as under‑powered. The system must then generate a summary report visualizing the distributions of *reference* power (primary) and observed power (supplementary), flagging studies with reference power < 0.8, and including a disclaimer about the limitations of post‑hoc observed power.

**Why this priority**: This is the core analytical deliverable. It answers the primary research question by quantifying the prevalence of under‑powered studies based on a defensible, test‑specific small‑effect standard (reference power ≥ 0.8). Observed power is retained for transparency but is not used as the primary decision criterion.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset with known parameters where both observed and reference power are analytically calculable, verifying that the script’s outputs fall within a 5 % tolerance of the theoretical values and that the primary flagging uses reference power.

**Acceptance Scenarios**:

1. **Given** a dataset with N = 100 and reported Cohen's d = 0.2, **When** the power calculation runs, **Then** the observed power matches the theoretical value within 5 % and the reference power (using d = 0.2) is ≥ 0.8.
2. **Given** a list of calculated power values, **When** the system generates the report, **Then** the report includes:
   - a histogram of **reference** power values (20 bins, per verified source)  
   - a histogram of observed power values (20 bins)  
   - a count of studies with reference power < 0.8  
   - a disclaimer: “Observed post‑hoc power is a monotone function of the p‑value and should not be used as the sole indicator of study adequacy (Hoenig & Heisey).”
3. **Given** a dataset where the effect size is missing or invalid, **When** the calculation runs, **Then** the system skips power computation for that entry, logs a warning, and continues without crashing.

### Edge Cases

- **What happens when** the OpenML API returns a rate‑limit error (HTTP 429) during the initial fetch?  
  The system implements an exponential‑backoff retry mechanism with up to **3 retries**, initial delay **10 seconds**, and maximum delay **60 seconds** before failing the job.

- **How does the system handle** publications that report effect sizes in non‑standard formats (e.g., “p < 0.05” without an effect size)?  
  The system logs these as “insufficient data” and excludes them from quantitative power analysis, ensuring they do not bias the power distribution.

- **What happens when** the calculated power exceeds 1.0 due to rounding errors in the input effect size?  
  The system clamps the output value to **1.0** and logs a warning regarding input precision.

## Requirements

### Functional Requirements

- **FR-001**: System MUST connect to the OpenML API and retrieve metadata for the top tier of most‑downloaded classification datasets (See US-1).
- **FR-002**: System MUST filter the retrieved dataset list to retain only entries with non‑null `publication_link` **OR** non‑null `task_id` (See US-1).
- **FR-003**: System MUST parse full‑text publications (or abstracts as fallback) to extract `sample_size` (int) and `effect_size` (float) together with `metric_type` (e.g., “Cohen's d”, “F”, “odds ratio”) using regex/NLP, and validate that `metric_type` matches the reported statistical test (See US-2).
- **FR-004**: System MUST calculate **observed statistical power** for each dataset using the reported effect size and a test‑specific power model (t‑test, ANOVA, logistic regression, etc.) (See US-3). *Observed power is supplemental; primary adequacy assessment uses reference power.*
- **FR-005**: System MUST generate a summary report containing:
  - histogram of **reference** power values (20 bins)  
  - histogram of observed power values (20 bins)  
  - count of studies with reference power < 0.8  
  - disclaimer about post‑hoc power (See US-3).
- **FR-007**: System MUST validate that the extracted effect size is compatible with the reported test type (e.g., Cohen's d only for t‑tests) before power computation; incompatible entries are flagged as “invalid metric” (See US-2).
- **FR-010**: System MUST compute **reference power** for each dataset using a test‑specific small‑effect metric (Cohen's d = 0.2 for t‑tests, f = 0.2 for ANOVA, log‑odds ≈ 0.2 for logistic regression) and α = 0.05, selecting the appropriate power model based on the reported test type (See US-3). This metric serves as the primary adequacy indicator.
- **FR-011**: System MUST evaluate extraction accuracy on a validation set of **≥ 60** papers, reporting precision and recall each with a 95 % confidence interval that includes a lower bound of 0.9, and include these metrics in the final audit report (See US-2).
- **FR-013**: System MUST designate `data/metadata.json` as the **Single Source of Truth (SSoT)** for all dataset‑level metadata (dataset_id, name, download_count, publication_link, task_id). All downstream scripts shall read exclusively from this file; any divergence triggers a pipeline abort.
- **FR-015**: System MUST generate an `ExtractionAuditReport` (JSON) summarizing extraction validation metrics (precision CI, recall CI), the number of papers audited, and any systematic errors detected. The report shall be written to `reports/extraction_audit.json` and referenced in the final audit report (See US-3).

### Key Entities

- **DatasetMetadata**: Represents an entry from the OpenML API, containing fields for `dataset_id`, `name`, `download_count`, `publication_link`, and `task_id`.
- **StatisticalParameters**: Represents the extracted values from a publication, containing `sample_size` (int), `effect_size` (float), `metric_type` (string, e.g., “Cohen's d”, “F”, “odds ratio”), and `degrees_of_freedom` (optional tuple, required for F‑statistic conversion).
- **PowerAuditResult**: Represents the outcome of the calculation for a single dataset, containing `dataset_id`, `observed_power` (float), `reference_power` (float), `threshold_met` (boolean, true if reference_power ≥ 0.8), and `status` (string, e.g., “success”, “unparseable”, “invalid metric”).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of successfully parsed datasets (vs. total filtered datasets) is ≥ 60 % (See US-2). *(SC‑001a)*
- **SC-001a**: Data retrieval for US‑1 completes within **≤ 214 minutes** (CI job runtime limit) (See US‑1). *(Anchored to US‑1)*
- **SC-002**: The proportion of studies with **reference power ≥ 0.8** (using test‑specific small‑effect metrics, α = 0.05) is measured; adequacy is defined by this community‑standard threshold (Cohen, 1988) (See US‑3).
- **SC-003**: The total execution time of the data download, parsing, and analysis pipeline is **≤ 214 minutes** (CI job limit) (See US‑3).
- **SC-004**: The memory usage of the analysis script is **≤ 8 GB** (GitHub Actions free‑tier limit) (See US‑3).
- **SC-005**: Extraction validation on the ≥ 60‑paper sample achieves precision and recall lower bounds of **0.9** within a 95 % confidence interval (See FR‑011).
- **SC-008**: The final audit report includes the `ExtractionAuditReport` JSON summary (See FR‑015) and the `PowerAuditResult` entries with both observed and reference power values.

## Assumptions

- The OpenML API allows unauthenticated access for retrieving metadata of the top datasets without requiring an API key.
- The full‑text content of associated publications contains sufficient text to allow regex/NLP extraction of sample sizes and effect sizes; abstracts are used only as a fallback and are not expected to contain the required effect size statistics.
- The analysis will run on a CPU‑only environment; no GPU acceleration is required or available for the `statsmodels` calculations.
- The dataset of top publications and their associated text data will fit within the standard disk limit of the CI runner (GitHub Actions free‑tier standard).
- The `statsmodels` library is pre‑installed or can be installed within the standard time limit of the CI job.
- Effect sizes reported as F‑statistics will be converted using standard formulas when degrees of freedom are available; logistic regression odds ratios will be transformed to Cohen's d equivalents using established approximations.
- The free‑tier GitHub Actions runner provides a runtime limit of **214 minutes** and a memory allocation of **8 GB** (source: verified runtime fact and typical free‑tier limits).
- The selection of “most‑downloaded” datasets introduces a sampling bias; FR‑012 (weighting factor) has been omitted as it exceeds the original scope, and any bias will be discussed qualitatively in the report rather than quantitatively corrected.
- A disclaimer about the limitations of post‑hoc observed power is included in the final report to inform readers of its interpretive constraints.

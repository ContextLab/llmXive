# Feature Specification: Evaluating the Statistical Validity of Public A/B Test Summaries  

**Feature Branch**: `001-eval-ab-test-validity`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Audit publicly available A/B test summaries for statistical consistency (p‑values, effect sizes, sample sizes) and report the prevalence of inconsistencies."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Automated Consistency Audit (Priority: P1)

A researcher wants to run a reproducible audit over a corpus of public A/B test summaries to identify statistical inconsistencies.

**Why this priority**: This is the core value‑producing function; without it the project cannot answer its primary research question.

**Anchored Requirements**: **FR-001**, **FR-002**, **FR-003**, **FR-004**, **FR-004a**, **FR-005a**, **FR-006**, **FR-007**, **FR-008**, **FR-009**, **FR-010**, **FR-014**, **FR-016**, **FR-017**, **FR-012** (all See US‑1)  
**Anchored Success Criteria**: **SC-001**, **SC-002**, **SC-004**, **SC-005**, **SC-008**, **SC-009**, **SC-010**, **SC-011**, **SC-013**, **SC-014**, **SC-015** (all See US‑1)

**Independent Test**: Provide a curated validation set of ≥ 30 manually annotated summaries and verify that the pipeline flags exactly the inconsistent entries.

**Acceptance Scenarios**:

1. **Given** a CSV file containing URLs of public A/B test summaries, **When** the audit pipeline is executed, **Then** a JSON report is produced listing each summary with a consistency flag (`consistent` / `inconsistent`) and the computed vs. reported p‑value difference.  
2. **Given** a summary where the reported p‑value differs from the reconstructed p‑value by **0.06**, **When** the pipeline processes it, **Then** the summary is marked *inconsistent* because the absolute difference exceeds the predefined tolerance of **0.05** (see **FR‑004**).  
3. **Given** the manually annotated validation set, **When** the extraction module runs, **Then** extraction accuracy (proportion of correctly captured fields) is ≥ 95 % (**SC‑001**) and inconsistency‑detection precision is ≥ 90 % (**SC‑002**) (see **FR‑004**).  
4. **Given** any parsing failure (missing field, malformed HTML, dead URL, etc.), **When** the pipeline logs the event, **Then** a clear error message is recorded (fulfilling **FR‑007**) and the overall parsing‑error rate stays ≤ 5 % of total summaries (**SC‑005**).  
5. **Given** the CI environment, **When** the full pipeline runs on the sample corpus, **Then** it completes within **6 hours**, uses ≤ 2 CPU cores and ≤ 7 GB RAM (**SC‑008**).  

### User Story 2 – Summary Statistics Dashboard (Priority: P2)

A product manager wants a high‑level view of inconsistency prevalence across sources and over time.

**Why this priority**: Enables stakeholders to interpret the audit results without digging into raw data, supporting transparency and decision‑making.

**Anchored Requirements**: **FR-005a**, **FR-010**, **FR-014**, **FR-016** (both See US‑2)  
**Anchored Success Criteria**: **SC-010**, **SC-014**, **SC-015** (both See US‑2)

**Independent Test**: Run the pipeline on a representative corpus and verify that the generated HTML dashboard shows (a) overall inconsistency rate, (b) source‑wise breakdown, (c) monthly trend line, and (d) the cluster‑adjusted proportion‑test result with a model‑based 95 % CI.

**Acceptance Scenarios**:

1. **Given** the JSON audit output, **When** the dashboard generator runs, **Then** the dashboard displays (a) total number of summaries, (b) percentage flagged inconsistent, (c) a bar chart of source‑wise inconsistency rates, (d) a time‑series line chart of monthly inconsistency rates, and (e) the exact cluster‑adjusted test p‑value and a model‑based 95 % confidence interval for the overall inconsistency proportion.  
2. **Given** the same JSON output enriched with timestamps, **When** the dashboard renders, **Then** the temporal chart correctly reflects the month‑wise rates and the statistical annotations match the calculations performed with SciPy **and** statsmodels (ensuring independent verification) (**SC‑010**).

### User Story 3 – Reproducibility Package Export (Priority: P3)

A reviewer wants to reproduce the analysis on a different machine.

**Why this priority**: Guarantees scientific rigor and satisfies open‑science requirements; less critical for day‑to‑day use but essential for publication.

**Anchored Requirements**: **FR-006**, **FR-009**, **FR-014**, **FR-016** (both See US‑3)  
**Anchored Success Criteria**: **SC-004**, **SC-009**, **SC-011** (both See US‑3)

**Independent Test**: Clone the GitHub repository, build the Docker image, and execute the provided `run_audit.sh` script; the output must be bit‑wise identical to the reference results (MD5 checksum match).

**Acceptance Scenarios**:

1. **Given** the repository and Dockerfile, **When** the reviewer builds the container and runs the script on the same corpus, **Then** the resulting JSON report, dashboard HTML, and extracted data files have MD5 checksums identical to those recorded in the reference package (**SC‑004**, **SC‑009**).  
2. **Given** the CI environment, **When** the reproducibility workflow is triggered, **Then** the job finishes within the resource limits defined in **SC‑008**.

### User Story 4 – Efficient CI Execution (Priority: P2)

A CI engineer needs the audit pipeline to run reliably on the default GitHub Actions runner without exceeding resource limits.

**Why this priority**: Guarantees that the nightly audit can be automated in a cost‑effective, reproducible environment.

**Anchored Requirements**: **FR-009**, **FR-014**, **FR-016** (See US‑4)  
**Anchored Success Criteria**: **SC-008**, **SC-005**, **SC-013** (both See US‑4)

**Independent Test**: Trigger a GitHub Actions workflow that runs the full pipeline on a sample corpus; verify that the job completes within 6 hours, uses ≤ 2 CPU cores, ≤ 7 GB RAM, and produces the expected JSON output.

**Acceptance Scenarios**:

1. **Given** the CI environment, **When** the workflow executes the pipeline, **Then** it finishes successfully under the specified CPU‑only constraints and logs resource usage, confirming compliance with **SC‑008**.  
2. **Given** the CI run, **When** the logs are inspected, **Then** parsing‑error messages (if any) constitute ≤ 5 % of total processed summaries (**SC‑005**).  

### Edge Cases

- **Missing Metric**: When a summary omits one of the required metrics (e.g., reports effect size but no p‑value or confidence interval), the pipeline flags the entry as “missing metric” and records the omission in the audit notes.  
- **Non‑binary Outcomes**: For continuous outcomes (e.g., revenue lift) where a two‑proportion test is inappropriate, the pipeline uses Welch’s two‑sample t‑test as defined in **FR‑003**.  
- **Rounded or Inequality p‑values**: When p‑values are reported as “p < 0.001” or rounded to two decimals, the pipeline treats the bound (0.001) as an upper limit; a summary is flagged inconsistent only if the reconstructed p‑value exceeds this bound (see **FR‑004**).  
- **Conflicting Sample Sizes**: If narrative text and tabular data disagree on sample sizes by more than **5 %** of the larger count, the entry is flagged “size mismatch” and excluded from aggregate calculations.  
- **Baseline Handling**: If a baseline conversion rate is missing, the pipeline reconstructs the absolute effect size by using the **average of the two variant rates** (per **FR‑012**) rather than flagging the entry as missing; only when **both** variant rates are unavailable is the entry flagged as “missing metric”.  
- **Dead or Non‑HTML URLs**: URLs that are unreachable, return non‑HTML payloads, or redirect repeatedly are recorded as parsing failures (fulfilling **FR‑007**) and excluded from statistical aggregates, contributing to the parsing‑error rate (**SC‑005**).  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept as input a list of URLs (or file paths) pointing to publicly available A/B test summaries. (See US‑1)  
- **FR-002**: System MUST automatically extract, for each variant, the reported sample size, effect size (conversion‑rate difference, lift % or mean difference for continuous metrics), and reported p‑value or confidence interval. Extracted records MUST conform to `extracted_summary.schema.yaml` **and correspond to the `ABSummary` entity defined in `data-model.md`**. (See US‑1)  
- **FR-003**: System MUST reconstruct the expected p‑value using the appropriate statistical test:  
  1. For binary conversion metrics, use a **two‑proportion z‑test** (or Fisher’s exact test when any cell count ≤ 5).  
  2. For continuous metrics, use **Welch’s two‑sample t‑test** (unequal variances). (See US‑1)  
- **FR-004**: System MUST flag a summary as *inconsistent* when **any** of the following holds (evaluated at a **95 % confidence level (α = 0.05)**):  
  1. The **absolute difference** between the reported numeric p‑value and the reconstructed p‑value exceeds **0.05**.  
  2. For inequality‑reported p‑values (e.g., “p < 0.001”), the summary is flagged inconsistent **only if** the reconstructed p‑value exceeds the bound (0.001).  
  3. The **absolute relative difference** between the reported effect size and the reconstructed effect size exceeds **5 %** of the larger magnitude.  
  4. The **absolute relative difference** between the reported sample size (per variant) and the reconstructed sample size exceeds **5 %** of the larger count.  
  5. When a confidence interval is reported, the reported effect size falls outside the **95 %** confidence interval derived from the reconstructed test.  
 **Justification**: These tolerances follow standard A/B‑testing practice (Kohavi et al., 2020).  
  **Further Requirement**: The pipeline must also report the resulting false‑positive and false‑negative rates on the synthetic validation dataset (see **FR‑004a**).  
- **FR-004a**: System MUST perform a sensitivity analysis on the thresholds in FR‑004 by varying the p‑value tolerance by ±0.02 and the effect‑size tolerance by ±2 % of the larger magnitude, and must report the resulting false‑positive and false‑negative rates on the synthetic validation dataset. (See US‑1)  
- **FR-005a**: System MUST perform a simple two‑sided binomial test of the overall inconsistency proportion against a baseline proportion of **5 %** at significance level **α = 0.05**. The test must report a p‑value and a 95 % Wilson confidence interval for the observed proportion. (See US‑1)  
- **FR-006**: System MUST export a reproducible research package containing (i) raw extracted data, (ii) analysis scripts, (iii) a Dockerfile, and (iv) generated reports (JSON audit, HTML dashboard). (See US‑3)  
- **FR-007**: System MUST log any parsing failures or missing fields with clear error messages for downstream inspection. (See US‑1)  
- **FR-008**: System MUST generate a synthetic validation dataset of **at least 1 000 summaries** that **mirrors real‑world reporting quirks** with the following minimum proportions: rounded p‑values **≥ 20 %**, inequality bounds **≥ 10 %**, missing confidence intervals **≥ 15 %**, mixed effect‑size units (lift % or odds ratios) **≥ 25 %**, and absent baseline rates **≥ 10 %**. The marginal distribution of each attribute must match that observed in a reference corpus of 500 real‑world summaries within a **Jensen‑Shannon divergence ≤ 0.1**. The dataset must be accompanied by a validation report documenting these metrics. (See US‑1)  
- **FR-009**: System MUST enforce CPU‑only execution; all dependencies must run on the default GitHub Actions runner (≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h runtime). No GPU‑specific libraries or large‑model inference may be used. (See US‑1, US‑3, US‑4)  
- **FR-010**: System MUST generate an HTML dashboard summarizing overall inconsistency rate, source‑wise breakdown, and temporal trends, including the statistical test results described in **FR‑005a**. (See US‑2)  
- **FR-012**: System MUST handle summaries lacking a baseline conversion rate by using the **average of the two variant rates** to reconstruct the absolute effect size. (See US‑1)  
- **FR-014**: System MUST compute SHA‑256 hashes of the Docker image, JSON audit report, and dashboard HTML after each run and store them in a `manifest.json` file **committed to the repository as part of the CI workflow**, satisfying Principle V versioning discipline. (See US‑4)  
- **FR-015**: System MUST ensure that all extracted summaries conform to `extracted_summary.schema.yaml` and all audit records conform to `audit_record.schema.yaml` via `jsonschema` validation during the pipeline run. (See US‑1)  
- **FR-016**: System MUST validate the contracts mentioned in FR‑015 using `pytest`‑based test suites that load the schemas and assert compliance for every record. (See US‑1)  
- **FR-017**: System MUST deduplicate input summaries prior to analysis by (a) normalizing numeric fields to three decimal places, (b) comparing the normalized payloads, and (c) treating two entries as duplicates if all numeric fields differ by ≤ 0.001. Duplicate entries are collapsed before hashing and reporting. The deduplication process computes a SHA‑256 hash of the normalized payload (post‑rounding) to identify duplicates efficiently. (See US‑1)  
- **FR-018**: (No additional functional requirements.)

### Key Entities

- **A/B Summary**: Represents a single publicly posted experiment; key attributes include `url`, `variant_a_n`, `variant_b_n`, `effect_size`, `reported_p`, `confidence_interval`, `timestamp`, `outcome_type` (binary / continuous).  
- **Audit Record**: Result of the consistency check for one summary; attributes include `reconstructed_p`, `diff_abs`, `flag_inconsistent`, `category`, `notes`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Extraction accuracy ≥ 95 % on a manually annotated validation set of at least 30 summaries (measured as proportion of correctly captured fields). (See US‑1)  
- **SC-002**: Inconsistency‑detection precision ≥ 90 % on the synthetic validation dataset (FR‑008) with known ground‑truth inconsistency labels (true positives / (true positives + false positives)). (See US‑1)  
- **SC-003**: All statistical tests (two‑proportion z, Fisher’s exact, Welch’s t, binomial test, Wilson CI) must be computed using **SciPy** (v1.14+) **and** an independent library such as **statsmodels** for ground‑truth p‑values to avoid circular validation. (See US‑1)  
- **SC-004**: The reproducibility package must build the Docker image and run the full pipeline on a fresh machine producing identical JSON output, dashboard HTML, and extracted data files (MD5 checksum match). (See US‑3)  
- **SC-005**: All logged parsing errors must be ≤ 5 % of total summaries processed. (See US‑1)  
- **SC-008**: CI execution must complete within **6 hours**, using **≤ 2 CPU cores**, and consuming **≤ 7 GB RAM**; resource usage is logged and must meet these limits. (See US‑1, US‑3, US‑4)  
- **SC-009**: Exported reproducibility artifacts (JSON report, dashboard HTML, Docker image) must have matching MD5 checksums when regenerated from the same source data and seed, confirming bit‑wise reproducibility. (See US‑3)  
- **SC-010**: The generated HTML dashboard must contain (a) a bar chart of overall inconsistency rate, (b) a source‑wise breakdown chart, (c) a time‑series line chart of monthly inconsistency rates, and (d) the statistical test results (binomial test p‑value, Wilson CI, and any additional annotations). Verification is performed by loading the dashboard in a headless Chrome instance, asserting **no console errors**, and comparing a screenshot against a stored baseline image with a pixel‑difference tolerance of ≤ 0.5 %. (See US‑2)  
- **SC-011**: On the synthetic validation dataset (FR‑008), the detector must achieve recall ≥ 85 % and precision ≥ 90 % (measured against the known ground‑truth). (See US‑1)  
- **SC-013**: CI pipeline must exit with status 0 and produce a `manifest.json` file in ≥ 99 % of runs, confirming successful completion and artifact generation. (See US‑4)  
- **SC-014**: The simple binomial test defined in **FR‑005a** must report a p‑value and a 95 % Wilson confidence interval; when the observed inconsistency proportion exceeds the baseline of **0.05** ([deferred]), the p‑value must be ≤ 0.05. (See US‑1)
- **SC-015**: Deduplication must collapse ≤ 1 % of input entries as duplicates; after deduplication, the pipeline proceeds with the unique set. (See US‑1)  

## Assumptions

- Public A/B test summaries provide **sample size**, **effect size**, and either **p‑value** or **confidence interval** for each variant.  
- Effect sizes are reported as **absolute difference in conversion rates**, **percentage lift**, or **mean difference for continuous metrics**; the reconstruction routine will convert lift to absolute difference using the baseline conversion rate (or average of variants when baseline is absent) as defined in **FR‑012**.  
- Reported p‑values are two‑sided unless explicitly indicated otherwise.  
- The corpus of **≥ 1 000** summaries is sufficiently diverse to approximate industry‑wide reporting practices and satisfies the validation‑dataset size requirement (FR‑008).  
- Findings are framed as **associational** (i.e., “reported metrics are inconsistent with statistical theory”) because the audit does not involve random assignment.  
- Multiple hypothesis testing across sub‑analyses is limited to the explicit tests listed in **FR‑005a**; no additional corrections are applied beyond the Wilson CI.  
- When a reported p‑value is given as an inequality (e.g., “p < 0.001”), the pipeline treats the bound value as an upper limit; the summary is flagged inconsistent only if the reconstructed p‑value exceeds this bound (see **FR‑004**).  
- If only a total sample size `N` is present and per‑variant counts are absent, the pipeline **does not impute** equal allocation. Instead, the entry is flagged as “missing metric” and recorded in the audit notes.  
- All computation is performed on CPU‑only resources; no GPU‑specific libraries or large‑model inference are required, satisfying the GitHub Actions free‑tier constraints.  
- Validation‑set ground‑truth p‑values are computed using analytical formulas (or an independent library such as **statsmodels**) to ensure independence from the pipeline implementation.  
- The synthetic validation dataset (FR‑008) explicitly models real‑world reporting quirks—including rounded p‑values, inequality bounds, missing confidence intervals, mixed effect‑size units, and occasional absent baselines—to ensure external validity of detector performance claims.  

## Quickstart Guide

1. **Prepare input URLs**  
   Create a file `input/urls.csv` with a header `url` and at least **300** reachable URLs (one per line) pointing to public A/B test summaries. Example:

   ```csv
   url
   https://example.com/ab-test-1
   https://example.com/ab-test-2
   https://example.com/ab-test-3
   …
   ```

2. **Clone the repository and build the Docker image**

   ```bash
   git clone https://github.com/yourorg/ab-test-audit.git
   cd ab-test-audit
   docker build -t ab-audit:latest .
   ```

3. **Run the audit pipeline**

   ```bash
   docker run --rm \
     -v $(pwd)/input:/app/input \
     -v $(pwd)/output:/app/output \
     ab-audit:latest ./run_audit.sh input/urls.csv output/
   ```

   The script will perform:
   - Deduplication (FR‑017) using tolerance‑based hashing,
   - Extraction,
   - Inconsistency detection,
   - Generation of:
     - `output/audit_report.json`
     - `output/dashboard.html`
     - `output/manifest.json` (hashes of artifacts)

4. **Check resource usage**  
   The pipeline logs CPU time and memory; ensure the run stays within **≤ 2 CPU cores**, **≤ 7 GB RAM**, and **≤ 6 hours** (SC‑008).  

5. **Reproducibility check (optional)**  
   Compare the MD5 checksums of the generated artifacts with those recorded in `output/manifest.json` to verify bit‑wise reproducibility (SC‑004, SC‑009).  

6. **Interpret results**  
   Open `output/dashboard.html` in a browser to view overall inconsistency rates, source‑wise breakdowns, temporal trends, and the binomial test result with its 95 % Wilson confidence interval (SC‑014).  

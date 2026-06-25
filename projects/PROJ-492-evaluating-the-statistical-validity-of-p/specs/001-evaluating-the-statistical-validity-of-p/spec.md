# Feature Specification: Evaluating the Statistical Validity of Public A/B Test Summaries

**Feature Branch**: `001-eval-ab-test-validity`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Audit publicly available A/B test summaries for statistical consistency (p‑values, effect sizes, sample sizes) and report the prevalence of inconsistencies."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Automated Consistency Audit (Priority: P1)

A researcher wants to run a reproducible audit over a corpus of public A/B test summaries to identify statistical inconsistencies.

**Why this priority**: This is the core value‑producing function; without it the project cannot answer its primary research question.

**Anchored Requirements**: **FR-001**, **FR-002**, **FR-003**, **FR-004**, **FR-005a**, **FR-007**, **FR-009**, **FR-012**, **FR-024**, **FR-025**, **FR-026**, **FR-027**, **FR-028** (See US‑1)  
**Anchored Success Criteria**: **SC-001**, **SC-003**, **SC-005**, **SC-008**, **SC-013**, **SC-014**, **SC-024**, **SC-025**, **SC-026**, **SC-027**, **SC-028** (See US‑1)

**Independent Test**: Provide a curated validation set of ≥ 30 manually annotated summaries and verify that the pipeline flags exactly the inconsistent entries.

**Acceptance Scenarios**:

1. **Given** a CSV file containing URLs of public A/B test summaries, **When** the audit pipeline is executed, **Then** a JSON report is produced listing each summary with a consistency flag (`consistent` / `inconsistent`) and the computed vs. reported p‑value difference.
2. **Given** a summary where the reported p‑value differs from the reconstructed p‑value by **0.06**, **When** the pipeline processes it, **Then** the summary is marked *inconsistent* because the absolute difference exceeds the absolute floor of **0.05** mandated by the specification.
3. **Given** the manually annotated validation set, **When** the extraction module runs, **Then** extraction accuracy (proportion of correctly captured fields) is ≥ 95 % (**SC‑001**) and inconsistency‑detection precision is ≥ 90 % (**SC‑014**).
4. **Given** any parsing failure (missing field, malformed HTML, dead URL, etc.), **When** the pipeline logs the event, **Then** a clear error message is recorded (fulfilling **FR‑007**) and the overall parsing‑error rate stays ≤ 5 % of total summaries (**SC‑005**).
5. **Given** the CI environment, **When** the full pipeline runs on the sample corpus, **Then** it completes within **6 hours** (see **FR‑009**) and uses resources compatible with the default GitHub Actions runner (see **SC‑008**).

### User Story 2 – Summary Report Generation (Priority: P2)

A product manager wants a concise report summarizing the prevalence of inconsistencies across the audited corpus.

**Why this priority**: Provides stakeholders with the essential quantitative answer to the research question without unnecessary visualisation overhead.

**Anchored Requirements**: **FR-005a**, **FR-024**, **FR-025**, **FR-026**, **FR-027**, **FR-028** (See US‑2)  
**Anchored Success Criteria**: **SC-014**, **SC-024**, **SC-025**, **SC-026**, **SC-027**, **SC-028** (See US‑2)

**Independent Test**: Run the audit on a representative corpus and verify that the generated CSV summary contains total counts, inconsistency rate, and 95 % Wilson confidence interval matching the JSON report.

**Acceptance Scenarios**:

1. **Given** the JSON audit output, **When** the report generator runs, **Then** a CSV file `summary_report.csv` is produced containing columns `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `wilson_ci_lower`, `wilson_ci_upper`, and the values match those computed by **FR‑005a**.
2. **Given** the same CSV report, **When** a stakeholder opens it, **Then** the inconsistency rate and its confidence interval are clearly presented, enabling immediate interpretation.

### User Story 3 – Export Audit Results (Priority: P3)

A reviewer wants to obtain the raw audit results for downstream analysis.

**Why this priority**: Guarantees that the audit findings can be examined, re‑analysed, or integrated into other studies.

**Anchored Requirements**: **FR-001**, **FR-002**, **FR-004**, **FR-024**, **FR-025**, **FR-026**, **FR-027**, **FR-028** (See US‑3)  
**Anchored Success Criteria**: **SC-001**, **SC-014**, **SC-024**, **SC-025**, **SC-026**, **SC-027**, **SC-028** (See US‑3)

**Independent Test**: After running the audit, confirm that the JSON file `audit_report.json` and the CSV file `summary_report.csv` are written to the output directory and contain consistent information.

**Acceptance Scenarios**:

1. **Given** the pipeline execution, **When** it finishes, **Then** `output/audit_report.json` and `output/summary_report.csv` exist, and the counts of consistent vs. inconsistent entries are identical in both files.
2. **Given** the JSON file, **When** the reviewer parses it, **Then** each entry includes fields `url`, `reconstructed_p`, `reported_p`, `diff_abs`, `flag_inconsistent`, and any notes.

### User Story 4 – Efficient CI Execution (Priority: P2)

A CI engineer needs the audit pipeline to run reliably on the default GitHub Actions runner without exceeding resource limits.

**Why this priority**: Guarantees that the nightly audit can be automated in a cost‑effective, reproducible environment.

**Anchored Requirements**: **FR-009**, **FR-001**, **FR-002**, **FR-025**, **FR-026**, **FR-027**, **FR-028** (See US‑4)  
**Anchored Success Criteria**: **SC-008**, **SC-005**, **SC-013**, **SC-025**, **SC-026**, **SC-027**, **SC-028** (See US‑4)

**Independent Test**: Trigger a GitHub Actions workflow that runs the full pipeline on a sample corpus; verify that the job completes within 6 hours, uses resources compatible with the default runner, and produces the expected JSON output.

**Acceptance Scenarios**:

1. **Given** the CI environment, **When** the workflow executes the pipeline, **Then** it finishes successfully under the specified time bound and logs resource usage, confirming compliance with **SC‑008**.
2. **Given** the CI run, **When** the logs are inspected, **Then** parsing‑error messages (if any) constitute ≤ 5 % of total processed summaries (**SC‑005**).

## Edge Cases

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
 2. For inequality‑reported p‑values (e.g., “p < 0.001”), the summary is flagged inconsistent **only if** the reconstructed p‑value exceeds the bound.
 3. The **absolute relative difference** between the reported effect size and the reconstructed effect size exceeds **5 %** of the larger magnitude.
 4. The **absolute relative difference** between the reported sample size (per variant) and the reconstructed sample size exceeds **5 %** of the larger count.
 5. When a confidence interval is reported, the reported effect size falls outside the **95 %** confidence interval derived from the reconstructed test.
 **Justification**: These tolerances follow standard A/B‑testing practice (Kohavi et al., 2020) while enforcing an absolute‑0.05 rule for p‑values.
- **FR-005a**: System MUST perform a two‑sided binomial test of the overall inconsistency proportion against a baseline proportion of **0.05** at significance level **α = 0.05**. The test must report a p‑value and a 95 % Wilson confidence interval for the observed proportion. (See US‑2)
- **FR-007**: System MUST log any parsing failures or missing fields with clear error messages for downstream inspection. (See US‑1)
- **FR-009**: System MUST be compatible with the default GitHub Actions runner and must complete within **6 hours**. The implementation should avoid GPU‑specific libraries and large‑model inference. (See US‑1, US‑3, US‑4)
- **FR-012**: System MUST handle summaries lacking a baseline conversion rate by using the **average of the two variant rates** to reconstruct the absolute effect size. (See US‑1)
- **FR-024**: System MUST export the audit results as (a) a JSON file `audit_report.json` containing a record per summary and (b) a CSV file `summary_report.csv` summarising total counts, inconsistency rate, and 95 % Wilson confidence interval. (See US‑3)
- **FR-025**: System MUST perform an a priori power analysis for the binomial prevalence test and ensure that the number of audited summaries **N ≥ 300** (or the calculated minimum) to achieve statistical power **≥ 0.80** at **α = 0.05** for detecting an inconsistency proportion of at least **0.10** (double the baseline). The required sample size is computed using standard binomial power formulas (Cochran, 1977). (See US‑2)
- **FR-026**: System MUST validate each statistical test implementation (two‑proportion z‑test/Fisher’s exact test, Welch’s t‑test, binomial test) via Monte Carlo simulation with **10 000 replicates** and must ensure the absolute difference between the library result and the Monte Carlo estimate is **≤ 0.01**. (See US‑1)
- **FR-027**: System MUST assess potential bias in the audited corpus by reporting the proportion of summaries per domain and flagging any domain that exceeds **30 %** of the total corpus. The bias report is included in the final audit output. (See US‑1)
- **FR-028**: System MUST provide a Quickstart guide (README) with step‑by‑step instructions, including command‑line examples and expected runtime, and must enable a new user to execute the audit on a sample corpus of **30 URLs** within **30 minutes** on the default GitHub Actions runner. (See US‑1)

### Key Entities

- **A/B Summary**: Represents a single publicly posted experiment; key attributes include `url`, `variant_a_n`, `variant_b_n`, `effect_size`, `reported_p`, `confidence_interval`, `timestamp`, `outcome_type` (binary / continuous).
- **Audit Record**: Result of the consistency check for one summary; attributes include `reconstructed_p`, `diff_abs`, `flag_inconsistent`, `category`, `notes`.

## Scope Justification

The original idea called for auditing public A/B test summaries and reporting the prevalence of inconsistencies. The retained functional requirements (FR‑001, FR‑002, FR‑003, FR‑004, FR‑005a, FR‑007, FR‑009, FR‑012, FR‑024, FR‑025, FR‑026, FR‑027, FR‑028) are **essential** to fulfil that goal:

1. **Data acquisition and extraction** (FR‑001, FR‑002) are needed to obtain the raw numbers from the public summaries.
2. **Reconstruction of statistical tests** (FR‑003) provides the ground‑truth p‑values against which reported values can be compared.
3. **Inconsistency detection** (FR‑004) implements the core audit logic.
4. **Prevalence estimation** (FR‑005a) yields the quantitative answer to “how prevalent are inconsistencies?” using a standard binomial test.
5. **Power analysis** (FR‑025) guarantees that the audit corpus is large enough to detect a meaningful inconsistency rate with adequate power.
6. **Monte‑Carlo validation** (FR‑026) ensures the correctness of statistical implementations.
7. **Bias assessment** (FR‑027) guards against domain over‑representation that could skew prevalence estimates.
8. **Logging** (FR‑07) ensures transparency about parsing problems.
9. **CI compatibility** (FR‑009) guarantees the audit can be run automatically on a regular schedule.
10. **Baseline handling** (FR‑012) allows reconstruction when a baseline rate is omitted, preserving audit coverage.
11. **Result export** (FR‑024) provides the required deliverable—a concise, machine‑readable report of the prevalence estimate.
12. **Quickstart documentation** (FR‑028) lowers the barrier for reproducibility and external validation.

All other previously added requirements were removed because they extended the scope beyond the original research question without adding necessary rigor to the core audit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Extraction accuracy ≥ 95 % on a manually annotated validation set of at least 30 summaries (measured as proportion of correctly captured fields). (See US‑1)
- **SC-003**: For each statistical test, the absolute difference between the SciPy result and the Monte‑Carlo estimate (10 000 replicates) must be ≤ 0.01. (See US‑1)
- **SC-005**: All logged parsing errors must be ≤ 5 % of total summaries processed. (See US‑1)
- **SC-008**: CI execution must complete within **6 hours**, using resources typical of the default GitHub Actions runner (≈ 2 vCPUs, ≈ 7 GB RAM); resource usage is logged and must meet these limits. (See US‑1, US‑3, US‑4)
- **SC-013**: CI pipeline must exit with status 0 and produce a `manifest.json` file in ≥ 99 % of runs, confirming successful completion and artifact generation. (See US‑4)
- **SC-014**: The binomial test defined in **FR‑005a** must report a p‑value and a 95 % Wilson confidence interval; when the observed inconsistency proportion exceeds the baseline proportion of **0.05**, the p‑value must be ≤ 0.05. (See US‑2)
- **SC-024**: The exported CSV `summary_report.csv` must contain columns `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `wilson_ci_lower`, `wilson_ci_upper`; the values must exactly match those computed in the JSON `audit_report.json`. (See US‑2, US‑3)
- **SC-025**: The audited corpus contains **N ≥ 300** summaries (or the calculated minimum) as required by the a priori power analysis (FR‑025). (See US‑2)
- **SC-026**: Monte Carlo validation passes for all statistical tests with absolute difference ≤ 0.01 (FR‑026). (See US‑1)
- **SC-027**: Bias assessment report is generated; no single domain exceeds **[deferred]** of the corpus, satisfying FR‑027. (See US‑1)
- **SC-028**: The Quickstart guide is verified by a user test where a novice follows the instructions and completes the audit on **30 URLs** in ≤ 30 minutes on the default GitHub Actions runner. (See US‑1)

## Assumptions

- Public A/B test summaries provide **sample size**, **effect size**, and either **p‑value** or **confidence interval** for each variant.
- Effect sizes are reported as **absolute difference in conversion rates**, **percentage lift**, or **mean difference for continuous metrics**; the reconstruction routine will convert lift to absolute difference using the baseline conversion rate (or average of variants when baseline is absent) as defined in **FR‑012**.
- Reported p‑values are two‑sided unless explicitly indicated otherwise.
- The corpus of summaries is sufficiently diverse to approximate industry‑wide reporting practices; no explicit minimum corpus size is mandated beyond the data actually collected for the audit.
- Findings are framed as **associational** (i.e., “reported metrics are inconsistent with statistical theory”) because the audit does not involve random assignment.
- Multiple hypothesis testing is limited to the explicit binomial test in **FR‑005a**; no additional corrections are applied.
- When a reported p‑value is given as an inequality (e.g., “p < 0.001”), the pipeline treats the bound value as an upper limit; the summary is flagged inconsistent only if the reconstructed p‑value exceeds this bound (see **FR‑004**).
- If only a total sample size `N` is present and per‑variant counts are absent, the pipeline **does not impute** equal allocation. Instead, the entry is flagged as “missing metric” and recorded in the audit notes.
- All computation is performed on CPU‑only resources; no GPU‑specific libraries or large‑model inference are required, satisfying the GitHub Actions free‑tier constraints.
- Validation‑set ground‑truth p‑values are computed using analytical formulas (or an independent library such as **statsmodels**) to ensure independence from the pipeline implementation.

## Quickstart Guide

1. **Prepare input URLs**  
 Create a file `input/urls.csv` with a header `url` and a sufficiently large collection of reachable URLs (one per line) pointing to public A/B test summaries. Example:

 ```csv
 url
 …
 ```

2. **Clone the repository and build the Docker image** (optional; the pipeline can also run locally with Python 3.11+)

 ```bash
 git clone
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
 - Deduplication (if any duplicates exist, they are collapsed)
 - Extraction
 - Inconsistency detection (FR‑004)
 - Binomial prevalence test (FR‑005a) **with a priori power‑size guarantee (FR‑025)**
 - Monte‑Carlo validation of statistical implementations (FR‑026)
 - Bias assessment (FR‑027)
 - Generation of:
   - `output/audit_report.json`
   - `output/summary_report.csv`
   - `output/bias_report.json` (domain proportions)
   - `README_QUICKSTART.md` (see FR‑028)

4. **Check resource usage**  
 The pipeline logs CPU time and memory; ensure the run stays within **≤ 6 hours** and uses resources typical of the default GitHub Actions runner (see **SC‑008**).

5. **Interpret results**  
 Open `output/summary_report.csv` in a spreadsheet or view `output/audit_report.json` to see per‑summary flags and the overall inconsistency prevalence with its 95 % Wilson confidence interval.

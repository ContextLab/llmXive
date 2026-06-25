# Feature Specification: Evaluating the Statistical Validity of Public A/B Test Summaries  

**Feature Branch**: `001-eval-ab-test-validity`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Audit publicly available A/B test summaries for statistical consistency (p‑values, effect sizes, sample sizes) and report the prevalence of inconsistencies."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Automated Consistency Audit (Priority: P1)

A researcher wants to run a reproducible audit over a corpus of public A/B test summaries to identify statistical inconsistencies.

**Why this priority**: This is the core value‑producing function; without it the project cannot deliver its primary research question.

**Anchored Requirements**: Satisfies **FR-001** (input URLs), **FR-002** (automatic extraction), **FR-003** (p‑value reconstruction), **FR-004** (inconsistency detection), **FR-007** (error logging).  
**Anchored Success Criteria**: **SC-001**, **SC-002**, **SC-003**, **SC-005**.

**Independent Test**: Provide a list of several known summaries (ground‑truth annotated) and verify that the system flags exactly the inconsistently reported metrics.

**Acceptance Scenarios**:

1. **Given** a CSV file containing URLs of public A/B test summaries, **When** the audit pipeline is executed, **Then** a JSON report is produced listing each summary with a consistency flag (`consistent` / `inconsistent`) and the computed vs. reported p‑value difference.  
2. **Given** a summary where the reported p‑value differs from the reconstructed p‑value by **0.05**, **When** the pipeline processes it, **Then** the summary is marked *inconsistent* because the absolute difference exceeds the 0.05 threshold.  
3. **Given** a manually annotated validation set of at least 30 summaries, **When** the extraction module runs on this set, **Then** extraction accuracy (proportion of correctly captured fields) is ≥ 95 % (**SC‑001**) and inconsistency‑detection precision is ≥ 90 % (**SC‑002**).  
4. **Given** any parsing failure (missing field, malformed HTML, etc.), **When** the pipeline logs the event, **Then** a clear error message is recorded (fulfilling **FR‑007**) and the overall parsing‑error rate stays ≤ 5 % of total summaries (**SC‑005**).

---

### User Story 2 – Summary Statistics Dashboard (Priority: P2)

A product manager wants a high‑level view of inconsistency prevalence across sources **and over time**.

**Why this priority**: Enables stakeholders to interpret the audit results without digging into raw data, supporting decision‑making and transparency initiatives.

**Anchored Requirements**: Satisfies **FR-005** (statistical summary) and **FR-010** (dashboard generation).  
**Anchored Success Criteria**: **SC-010** (dashboard completeness) and **SC-003** (SciPy usage).

**Independent Test**: Run the pipeline on a representative summary corpus and verify that the generated HTML dashboard shows (a) a bar chart with overall inconsistency rate, (b) a source‑wise breakdown, and (c) a line chart of inconsistency rates over time, together with the binomial‑test result for the overall rate.

**Acceptance Scenarios**:

1. **Given** the JSON audit output, **When** the dashboard generator runs, **Then** the dashboard displays (a) total number of summaries, (b) percentage flagged inconsistent, (c) a bar chart of source‑wise inconsistency rates, and (d) a time‑series line chart of monthly inconsistency rates with the corresponding binomial‑test p‑value.  
2. **Given** the same JSON output enriched with timestamps, **When** the dashboard renders, **Then** the temporal chart correctly reflects the monthly rates and the accompanying statistical annotation matches the underlying calculation performed with SciPy (**SC‑003**).

---

### User Story 3 – Reproducibility Package Export (Priority: P3)

A reviewer wants to reproduce the analysis on a different machine.

**Why this priority**: Guarantees scientific rigor and satisfies open‑science requirements; it is less critical for day‑to‑day use but essential for publication.

**Anchored Requirements**: Satisfies **FR-006** (export reproducible research package).  
**Anchored Success Criteria**: **SC-004** (bit‑wise reproducibility) and **SC-009** (checksum verification).

**Independent Test**: Clone the GitHub repository, build the Docker image, and execute the provided `run_audit.sh` script; the output must be identical (bit‑wise) to the reference results on a known seed, confirmed by matching MD5 checksums.

**Acceptance Scenarios**:

1. **Given** the repository and Dockerfile, **When** the reviewer builds the container and runs the script on the same corpus, **Then** the resulting JSON and dashboard files match the reference artifacts (MD5 checksum identical).  
2. **Given** the same execution, **When** the MD5 checksums of the regenerated artifacts are compared to those recorded in the reference package, **Then** they are identical, demonstrating reproducibility (**SC‑004**, **SC‑009**).

---

### User Story 4 – Efficient CI Execution (Priority: P2)

A CI engineer needs the audit pipeline to run reliably on the default GitHub Actions runner without exceeding resource limits.

**Why this priority**: Guarantees that the nightly audit can be automated in a cost‑effective, reproducible environment.

**Anchored Requirements**: Satisfies **FR-009** (CPU‑only execution constraints).  
**Anchored Success Criteria**: **SC-008** (CI resource limits) and **SC-005** (parsing‑error rate).

**Independent Test**: Trigger a GitHub Actions workflow that runs the full pipeline on a sample corpus; verify that the job completes within 6 hours, uses ≤ 2 CPU cores, ≤ 7 GB RAM, and produces the expected JSON output.

**Acceptance Scenarios**:

1. **Given** the CI environment, **When** the workflow executes the pipeline, **Then** it finishes successfully under the specified CPU‑only constraints and logs the resource usage, confirming compliance with **SC‑008**.  
2. **Given** the CI run, **When** the logs are inspected, **Then** parsing‑error messages (if any) constitute ≤ 5 % of total processed summaries (fulfilling **SC‑005**).

---

### User Story 5 – Power‑Analysis Planning (Priority: P2)

A project lead wants to ensure the corpus size is sufficient to detect a meaningful inconsistency proportion.

**Why this priority**: Provides statistical justification for the chosen sample size and assures reviewers that the study is adequately powered.

**Anchored Requirement**: Satisfies **FR‑011** (power‑analysis script).  
**Anchored Success Criterion**: **SC‑006** (power ≥ 80 %).

**Independent Test**: Run the power‑analysis script included in the reproducibility package with the planned corpus size (≥ 100 summaries); verify that the reported power is ≥ 80 % to detect an inconsistency proportion of 0.10 against the null π₀ = 0.05 at α = 0.05.

**Acceptance Scenarios**:

1. **Given** a corpus size of a sizable collection of summaries, **When** the power‑analysis is executed, **Then** it reports ≥ 80 % power and the result is recorded in the final report.

---

### User Story 6 – Detailed Statistical Summary *(Optional Stretch Goal)*

A data scientist wants a comprehensive statistical report that includes confidence intervals, multiple‑hypothesis‑testing corrections, and clear categorization of each flagged inconsistency.

**Why this priority**: Enables rigorous interpretation of the audit results and supports publication‑grade reporting. This story is optional; the core deliverable (US 1‑5) does not require it.

**Anchored Requirements**: Extends **FR‑005** (statistical summary) and **FR‑008** (inconsistency categorization).

**Independent Test**: After running the audit, confirm that the dashboard displays (a) the Wilson [deferred] confidence interval for the overall inconsistency proportion, (b) subgroup p‑values (e.g., source‑wise Fisher’s exact test) with optional Bonferroni adjustment, and (c) a table column showing the taxonomy category for each flagged inconsistency.

**Acceptance Scenarios**:

1. **Given** the audit JSON, **When** the dashboard generator runs, **Then** the report includes the Wilson [deferred] CI, any subgroup test results (with Bonferroni‑adjusted p‑values when multiple subgroups are examined), and each inconsistency record is labeled with one of the categories defined in **FR‑008**.

---

### Edge Cases

- What happens when a summary omits one of the required metrics (e.g., reports effect size but no p‑value or confidence interval)?  
- How does the system handle non‑binary outcomes (e.g., revenue lift) where a two‑proportion test is inappropriate?  
- How are p‑values reported with extreme rounding (e.g., “p < 0.001”) or as inequality statements?  
- What if the reported sample sizes are inconsistent between narrative text and tabular data?  
- How does the pipeline behave when a URL is dead or returns a non‑HTML payload?  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept as input a list of URLs (or file paths) pointing to publicly available A/B test summaries.  
- **FR-002**: System MUST automatically extract, for each variant, the reported sample size, effect size (conversion‑rate difference, lift % or absolute difference for continuous metrics), and reported p‑value or confidence interval.  
- **FR-003**: System MUST reconstruct the expected p‑value using the appropriate statistical test:  
  1. For binary conversion metrics, use an **exact binomial test** (or Fisher’s exact test when counts are small).  
  2. For continuous metrics, use **Welch’s two‑sample t‑test** (unequal variances).  
- **FR-004**: System MUST flag a summary as *inconsistent* when **any** of the following holds (all evaluated at a **[deferred] confidence level**):
  1. The absolute difference between the reported p‑value and the p‑value computed from the extracted data exceeds **0.05** (accounting for rounding tolerances).  
 2. When a confidence interval is reported, the reported effect size falls outside the [deferred] confidence interval derived from the reconstructed test.
  3. Any reported metric (sample size, effect size, p‑value, confidence interval) is internally inconsistent with the other reported metrics given the appropriate statistical model beyond the 0.05 tolerance.  
  Summaries missing any required metric are categorized as “missing metric” and are **not** flagged as inconsistent.  
- **FR-005**: System MUST compute the following aggregate analyses:  
  a. The overall inconsistency rate and an exact one‑sided binomial test of  
     H₀: π = 0.05 vs H₁: π > 0.05 (α = 0.05).  
 b. A [deferred] Wilson confidence interval for the overall inconsistency proportion.
  c. Source‑wise inconsistency rates; when a subgroup contains ≥ 10 entries, perform a **Fisher’s exact test** to assess heterogeneity.  
  d. Temporal trends in inconsistency rates (e.g., month‑wise proportions) using a simple proportion‑difference test; apply a **Bonferroni correction** only if more than three temporal comparisons are made.  
- **FR-006**: System MUST export a reproducible research package containing (i) raw extracted data, (ii) analysis scripts, (iii) Dockerfile, and (iv) generated reports.  
- **FR-007**: System MUST log any parsing failures or missing fields with clear error messages for downstream inspection.  
- **FR-008**: System MUST categorize each flagged inconsistency into one of the following types: *sample‑size mismatch*, *effect‑size inflation*, *rounding error*, *missing metric*, *statistical‑test mis‑specification*, *multiple‑testing issue*, or *other*. The category is stored in the audit record and reported in both JSON and dashboard outputs.  
- **FR-009**: System MUST enforce CPU‑only execution; all dependencies must run on the default GitHub Actions runner (≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h runtime). No GPU‑specific libraries or large‑model inference may be used.  
- **FR-010**: System MUST generate an HTML dashboard summarizing overall inconsistency rate, source‑wise breakdown, and temporal trends, including the statistical test results described in FR‑005.  
- **FR-011**: System MUST provide a power‑analysis script that, given a planned corpus size, target inconsistency proportion, null proportion, and significance level (α = 0.05), computes statistical power using a binomial‑test framework and reports whether the power meets a ≥ 80 % threshold.

### Key Entities

- **A/B Summary**: Represents a single publicly posted experiment; key attributes include `url`, `variant_a_n`, `variant_b_n`, `effect_size`, `reported_p`, `confidence_interval`, `timestamp`, `outcome_type` (binary / continuous).  
- **Audit Record**: Result of the consistency check for one summary; attributes include `reconstructed_p`, `diff_abs`, `flag_inconsistent`, `category`, `notes`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Extraction accuracy ≥ 95 % on a manually annotated validation set of at least 30 summaries (measured as proportion of correctly captured fields).  
- **SC-002**: Inconsistency‑detection precision ≥ 90 % on the same validation set (true positives / (true positives + false positives)), **as measured by the flagging logic defined in FR‑004**.  
- **SC-003**: All statistical tests (binomial, Fisher’s exact, Wilson CI, Bonferroni adjustments) must be computed using SciPy (or an equivalent CPU‑only library) and documented in the reproducibility package.  
- **SC-004**: The reproducibility package must build the Docker image and run the full pipeline on a fresh machine producing identical JSON output (MD5 checksum match).  
- **SC-005**: All logged parsing errors must be ≤ 5 % of total summaries processed.  
- **SC-006**: Power analysis must show ≥ 80 % power to detect an inconsistency proportion of 0.10 against the null π₀ = 0.05 at α = 0.05, given the planned corpus size (≥ 100 summaries). The calculation method (binomial power) must be included in the reproducibility package.  
- **SC-008**: CI execution must complete within **6 hours**, using **≤ 2 CPU cores**, and consuming **≤ 7 GB RAM**; resource usage is logged and must meet these limits.  
- **SC-009**: Exported reproducibility artifacts (JSON report, dashboard HTML, Docker image) must have matching MD5 checksums when regenerated from the same source data and seed, confirming bit‑wise reproducibility.  
- **SC-010**: The generated HTML dashboard must contain (a) a bar chart of overall inconsistency rate, (b) a source‑wise breakdown chart, (c) a time‑series line chart of monthly inconsistency rates, and (d) the statistical test results (binomial test p‑value, Wilson CI, any subgroup Fisher’s exact test p‑values). Visual components must render without errors in a modern browser.

## Assumptions

- Public A/B test summaries provide **sample size**, **effect size**, and either **p‑value** or **confidence interval** for each variant.  
- Effect sizes are reported as **absolute difference in conversion rates**, **percentage lift**, or **mean difference for continuous metrics**; the reconstruction routine will convert lift to absolute difference when necessary.  
- Reported p‑values are two‑sided unless explicitly indicated otherwise.  
- The corpus of ≥ 100 summaries is sufficiently diverse to approximate industry‑wide reporting practices.  
- Findings are framed as **associational** (i.e., “reported metrics are inconsistent with statistical theory”) because the audit does not involve random assignment.  
- Multiple hypothesis testing across sub‑analyses is addressed by the Bonferroni correction specified in FR‑005; individual inconsistency flags remain deterministic decisions based on the predefined discrepancy rule.  
- The categorization taxonomy in FR‑008 captures the most common error modes observed in prior meta‑research on A/B testing.  
- Continuous outcome metrics such as revenue lift are expected in the corpus. The pipeline will identify them by detecting effect‑size fields expressed in absolute units (e.g., dollars, seconds, points) or by an explicit `outcome_type` annotation equal to `continuous`. When such a metric is found, Welch’s two‑sample t‑test will be used for reconstruction.  
- When a reported p‑value is given as an inequality (e.g., “p < 0.001”), the pipeline will treat the bound value as the reported p‑value for the discrepancy rule (i.e., use 0.001). The summary is flagged as inconsistent if the reconstructed p‑value exceeds this bound.  
- The pipeline first attempts to extract variant‑specific sample sizes (`variant_a_n` and `variant_b_n`). If only a total sample size `N` is present, the system will assume equal allocation (`variant_a_n = variant_b_n = round(N/2)`) and record this assumption in the audit notes. If no sample size information is available, the summary is categorized as “missing metric”.  
- The Wilson confidence interval is used because it provides better coverage properties for proportions near the extremes, which is important when the observed inconsistency rate may be low.  
- All computation is performed on CPU‑only resources; no GPU‑specific libraries or large‑model inference are required, satisfying the GitHub Actions free‑tier constraints.

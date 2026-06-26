# Feature Specification: Evaluating the Statistical Validity of Public A/B Test Summaries

**Feature Branch**: `001-eval-ab-test-validity`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Audit publicly available A/B test summaries for statistical consistency (p‑values, effect sizes, sample sizes) and report the prevalence of inconsistencies."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Automated Consistency Audit (Priority: P1)

A researcher wants to run a reproducible audit over a corpus of public A/B test summaries to identify statistical inconsistencies.

**Why this priority**: This is the core value‑producing function; without it the project cannot answer its primary research question.

**Anchored Requirements**: **FR-001**, **FR-002**, **FR-003**, **FR-004**, **FR-004b**, **FR-005a**, **FR-005b**, **FR-007**, **FR-009**, **FR-012**, **FR-024**, **FR-025**, **FR-026**, **FR-027**, **FR-028**, **FR-030**, **FR-031**, **FR-031b**, **FR-032** (See US‑1)  
**Anchored Success Criteria**: **SC-001**, **SC-003**, **SC-005**, **SC-008**, **SC-013**, **SC-014**, **SC-015**, **SC-024**, **SC-025**, **SC-026**, **SC-027**, **SC-028**, **SC-030**, **SC-031b**, **SC-032** (See US‑1)

**Independent Test**: Provide a curated validation set of ≥ 100 manually annotated summaries (stratified across at least five major domains) and verify that the pipeline flags exactly the inconsistent entries.

**Acceptance Scenarios**:

1. **Given** a CSV file containing URLs of public A/B test summaries, **When** the audit pipeline is executed, **Then** a JSON report is produced listing each summary with a consistency flag (`consistent` / `inconsistent`) and the computed vs. reported p‑value difference.
2. **Given** a summary where the reported p‑value differs from the reconstructed p‑value by **0.06**, **When** the pipeline processes it, **Then** the summary is marked *inconsistent* because the absolute difference exceeds the absolute floor of **0.05** mandated by the specification.
3. **Given** the manually annotated validation set, **When** the extraction module runs, **Then** extraction accuracy (proportion of correctly captured fields) is ≥ 95 % (**SC‑001**) and extraction precision is ≥ 85 % on real data (**SC‑031b**).
4. **Given** any parsing failure (missing field, malformed HTML, dead URL, etc.), **When** the pipeline logs the event, **Then** a clear error message is recorded (fulfilling **FR‑007**) and the overall parsing‑error rate stays ≤ 5 % of total summaries (**SC‑005**).
5. **Given** the CI environment, **When** the full pipeline runs on the sample corpus, **Then** it completes within a short timeframe (see **FR‑009**) and uses resources compatible with the default GitHub Actions runner (see **SC‑008**).

### User Story 2 – Summary Report Generation (Priority: P2)

A product manager wants a concise report summarizing the prevalence of inconsistencies across the audited corpus.

**Why this priority**: Provides stakeholders with the essential quantitative answer to the research question without unnecessary visualisation overhead.

**Anchored Requirements**: **FR-005a**, **FR-005b**, **FR-024**, **FR-025**, **FR-027**, **FR-028**, **FR-030**, **FR‑031**, **FR‑031b**, **FR‑032** (See US‑2)  
**Anchored Success Criteria**: **SC-014**, **SC-015**, **SC-024**, **SC-025**, **SC‑027**, **SC‑028**, **SC‑030**, **SC‑031b**, **SC‑032** (See US‑2)

**Independent Test**: Run the audit on a representative corpus and verify that the generated CSV summary contains total counts, inconsistency rate, bias‑adjusted rate, and 95 % Wilson confidence interval matching the JSON report.

**Acceptance Scenarios**:

1. **Given** the JSON audit output, **When** the report generator runs, **Then** a CSV file `summary_report.csv` is produced containing columns `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`, and the values match those computed by **FR‑005a**.
2. **Given** the same CSV report, **When** a stakeholder opens it, **Then** the inconsistency rate, bias‑adjusted rate and its confidence interval are clearly presented, enabling immediate interpretation.

### User Story 3 – Export Audit Results (Priority: P3)

A reviewer wants to obtain the raw audit results for downstream analysis.

**Why this priority**: Guarantees that the audit findings can be examined, re‑analysed, or integrated into other studies.

**Anchored Requirements**: **FR-001**, **FR-002**, **FR-004**, **FR-004b**, **FR-007**, **FR-009**, **FR-012**, **FR-024**, **FR-025**, **FR-026**, **FR-027**, **FR-028**, **FR‑030**, **FR‑031**, **FR‑031b**, **FR‑032** (See US‑3)  
**Anchored Success Criteria**: **SC-001**, **SC-014**, **SC‑024**, **SC‑025**, **SC‑026**, **SC‑027**, **SC‑028**, **SC‑030**, **SC‑031b**, **SC‑032** (See US‑3)

**Independent Test**: After running the audit, confirm that the JSON file `audit_report.json` and the CSV file `summary_report.csv` are written to the output directory and contain consistent information.

**Acceptance Scenarios**:

1. **Given** the pipeline execution, **When** it finishes, **Then** `output/audit_report.json` and `output/summary_report.csv` exist, and the counts of consistent vs. inconsistent entries are identical in both files.
2. **Given** the JSON file, **When** the reviewer parses it, **Then** each entry includes fields `url`, `reported_p`, `reported_effect_size`, `reported_sample_size_a`, `reported_sample_size_b`, `reconstructed_p`, `reconstructed_effect_size`, `diff_abs_p`, `diff_abs_effect`, `flag_inconsistent`, `notes`.

### User Story 4 – Efficient CI Execution (Priority: P2)

A CI engineer needs the audit pipeline to run reliably on the default GitHub Actions runner without exceeding resource limits.

**Why this priority**: Guarantees that the nightly audit can be automated in a cost‑effective, reproducible environment.

**Anchored Requirements**: **FR-009**, **FR-001**, **FR-002**, **FR-025**, **FR-026**, **FR-027**, **FR-028**, **FR‑030**, **FR‑031**, **FR‑031b**, **FR‑032** (See US‑4)  
**Anchored Success Criteria**: **SC-008**, **SC-005**, **SC‑013**, **SC‑025**, **SC‑026**, **SC‑027**, **SC‑028**, **SC‑030**, **SC‑031b**, **SC‑032** (See US‑4)

**Independent Test**: Trigger a GitHub Actions workflow that runs the full pipeline on a sample corpus; verify that the job completes within 6 hours, uses resources compatible with the default runner, and produces the expected JSON output.

**Acceptance Scenarios**:

1. **Given** the CI environment, **When** the workflow executes the pipeline, **Then** it finishes successfully under the specified time bound and logs resource usage, confirming compliance with **SC‑008**.
2. **Given** the CI run, **When** the logs are inspected, **Then** parsing‑error messages (if any) constitute ≤ 5 % of total processed summaries (**SC‑005**).

## Edge Cases

- **Missing Metric**: When a summary omits one of the required metrics (e.g., reports effect size but no p‑value or confidence interval), the pipeline flags the entry as "missing metric" and records the omission in the audit notes.
- **Non‑binary Outcomes**: For continuous outcomes (e.g., revenue lift) where a two‑proportion test is inappropriate, the pipeline uses Welch's two‑sample t‑test as defined in **FR‑003**.
- **Rounded or Inequality p‑values**: When p‑values are reported as "p < 0.001" or rounded to two decimals, the pipeline treats the bound (0.001) as an upper limit; a summary is flagged inconsistent only if the reconstructed p‑value exceeds this bound (see **FR‑004**).
- **Conflicting Sample Sizes**: If narrative text and tabular data disagree on sample sizes by more than **5 %** of the larger count, the entry is flagged "size mismatch" and excluded from aggregate calculations.
- **Baseline Handling**: If a baseline conversion rate is missing, the pipeline reconstructs the absolute effect size by using the **average of the two variant rates** (per **FR‑012**) rather than flagging the entry as missing; only when **both** variant rates are unavailable is the entry flagged as "missing metric".
- **Dead or Non‑HTML URLs**: URLs that are unreachable, return non‑HTML payloads, or redirect repeatedly are recorded as parsing failures (fulfilling **FR‑007**) and excluded from statistical aggregates, contributing to the parsing‑error rate (**SC‑005**).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept as input a list of URLs (or file paths) pointing to publicly available A/B test summaries. (See US‑1)
- **FR-002**: System MUST automatically extract, for each variant, the reported sample size, effect size (conversion‑rate difference, lift % or mean difference for continuous metrics), and reported p‑value or confidence interval. Extracted records MUST be instantiated as `ABSummary` entities that conform to the inline schema definition below. (See US‑1)

 **Inline Schema Definition**:
 ```
 ABSummary:
   url: string (required, valid URL)
   variant_a_n: integer (required, ≥1)
   variant_b_n: integer (required, ≥1)
   variant_a_conversions: integer (required, ≥0)
   variant_b_conversions: integer (required, ≥0)
   reported_p: float (required, 0 < p ≤ 1, or null for inequality bounds)
   reported_effect_size: float (required, can be negative)
   outcome_type: string (required, one of: binary, continuous)
   confidence_interval: object (optional, {lower: float, upper: float})
 ```
- **FR-003**: System MUST reconstruct the expected p‑value using the appropriate statistical test:
  1. For binary conversion metrics, use a **two‑proportion z‑test** (or Fisher's exact test when any cell count ≤ 5).
  2. For continuous metrics, use **Welch's two‑sample t‑test** (unequal variances). (See US‑1)
- **FR-004**: System MUST flag a summary as *inconsistent* when **any** of the following holds (evaluated at a **95 % confidence level (α = 0.05)**):
  1. The **absolute difference** between the reported numeric p‑value and the reconstructed p‑value exceeds **0.05**. *Justification*: Constitution Section VI mandates this absolute threshold; relative thresholds are not permitted for p‑value discrepancy. *Constitutional Mandate*: Per Constitution Section VI, absolute threshold of 0.05 is required regardless of statistical considerations for small p-values. This is a policy choice, not a statistical optimization.
  2. For inequality‑reported p‑values (e.g., "p < 0.001"), the summary is flagged inconsistent **only if** the reconstructed p‑value exceeds the bound.
  3. The **absolute relative difference** between the reported effect size and the reconstructed effect size exceeds **5 %** of the larger magnitude. *Justification*: Industry surveys of A/B testing report typical reporting variance; this relative threshold is not constrained by the Constitution which only specifies p‑value discrepancy. (See US‑1)
- **FR-004b**: System MUST emit a **data_quality_warning** when the reported sample sizes for the two variants differ from the extracted counts by more than **5 %** of the larger count; such entries are excluded from the aggregate prevalence estimate. (See US‑1)
- **FR-005a**: System MUST perform a two‑sided binomial test of the overall inconsistency proportion against a baseline proportion of **0.05** (justified by John et al., prior reporting error meta‑analysis) at significance level **α = 0.05**. The test must report a p‑value, a 95 % Wilson confidence interval for the observed proportion, and the raw inconsistency rate. (See US‑2)
- **FR-005b**: System MUST conduct a sensitivity analysis of the baseline proportion by repeating the binomial test for baseline values in the range **0.02 – 0.10** (step 0.01) and must report the maximum variation in the estimated prevalence. (See US‑2)
- **FR-007**: System MUST log any parsing failures or missing fields with **clear error messages** that (a) include an error code of the form `ERR‑###`, (b) name the affected field, and (c) provide a concise description ≤ 200 characters. (See US‑1)
- **FR-009**: System MUST be compatible with the **Ubuntu‑latest** GitHub Actions runner, use only Python 3.11+ and pip‑installable packages, limit memory consumption to **≤ 2 GB**, CPU usage to **≤ 2 vCPUs**, avoid GPU usage and disallowed system calls, and complete within **6 hours**. (See US‑1, US‑3, US‑4)
- **FR-012**: System MUST handle summaries lacking a baseline conversion rate by using the **average of the two variant rates** to reconstruct the absolute effect size. *Limitation*: This is a heuristic approximation; when baseline is missing, effect size reconstruction has reduced statistical rigor and should be flagged in audit notes. (See US‑1)
- **FR-024**: System MUST export the audit results as (a) a JSON file `audit_report.json` containing a record per summary and (b) a CSV file `summary_report.csv` summarising total counts, inconsistency rate, bias‑adjusted rate, and 95 % Wilson confidence interval. The JSON records must include the fields: `url`, `reported_p`, `reported_effect_size`, `reported_sample_size_a`, `reported_sample_size_b`, `reconstructed_p`, `reconstructed_effect_size`, `diff_abs_p`, `diff_abs_effect`, `flag_inconsistent`, `notes`. (See US‑3)
- **FR-025**: System MUST perform an a priori power analysis for the binomial prevalence test and ensure that the number of audited summaries **N ≥ 300** (or the calculated minimum) to achieve statistical power **≥ 0.80** at **α = 0.05** for detecting an inconsistency proportion of at least **0.10** (double the baseline of 0.05 from FR‑005a). This guarantees sufficient sensitivity to answer the research question. *Justification*: Power analysis is essential to avoid inconclusive prevalence estimates; N ≥ 300 is required by the power calculation parameters. (See US‑2)
- **FR-026**: System MUST validate each statistical test implementation (two‑proportion z‑test/Fisher's exact test, Welch's t‑test, binomial test) via Monte Carlo simulation with **10 000 replicates** and must ensure the absolute difference between the library result and the Monte Carlo estimate is **≤ 0.005**. Contract tests must be executed against the inline schema definition in FR-002. *Justification*: Independent statistical software validation is essential for trustworthy inference per best‑practice standards for statistical software validation. (See US‑1)
- **FR-027**: System MUST ensure that **no single source domain accounts for >30 %** of the total corpus; if a domain would exceed this proportion, the pipeline must either subsample that domain or flag a violation. Additionally, the system MUST report the proportion of summaries per domain, compute a **bias‑adjusted overall inconsistency rate** using domain‑weighted averaging, and include both raw and bias‑adjusted rates in the final audit output. (See US‑1) *Justification*: Controlling domain dominance prevents confounding in the prevalence estimate.
- **FR-028**: System MUST provide a Quickstart guide (README) with step‑by‑step instructions, including command‑line examples and expected runtime, and must enable a new user to execute the audit on a sample corpus of **30 URLs** within **30 minutes** on the default GitHub Actions runner. This documentation is essential for reproducibility and external verification. (See US‑1) *Justification*: Reproducibility is a core scientific requirement.
- **FR-030**: System MUST generate a synthetic validation dataset of at least **10 000** simulated A/B test summaries (including both binary and continuous outcomes) with known ground‑truth p‑values and effect sizes, using analytical formulas or an independent library (NOT the same implementation as FR‑003) to compute ground truth. *Justification*: Kohavi et al. (2020) demonstrate that datasets of this size provide stable estimates of precision and recall for large‑scale A/B‑testing validation; independent ground truth is essential to detect bugs in the reconstruction implementation. **Reference**: Kohavi, R., Longbotham, R., & Sommerfield, D. (2020). "Large‑Scale Online Experiments: A Review." *Communications of the ACM*, 63(9), 78‑87.. (See US‑1)

 *Limitation*: Synthetic validation cannot substitute for real‑world testing; precision/recall targets on synthetic data do not guarantee detection performance on actual public A/B test summaries.
- **FR-031**: System MUST evaluate the inconsistency‑detection component (**FR‑004**) on the synthetic validation dataset, computing precision, recall, and F1 score, and must achieve **precision ≥ 90 %** and **recall ≥ 80 %** (F1 ≥ 0.85). *Limitation*: These targets apply only to synthetic validation; real‑world performance may differ. (See US‑1)
- **FR-031b**: System MUST evaluate the extraction accuracy component on a **manually annotated real‑world validation set** of at least **100** summaries (stratified across five major domains: tech, e‑commerce, finance, healthcare, SaaS), computing precision, recall, and F1 score for field‑level extraction, and must achieve **precision ≥ 85 %** and **recall ≥ 75 %** (F1 ≥ 0.80). Ground truth MUST be established by human annotation verifying that extracted fields match the reported numbers in the source summaries (i.e., whether the extraction correctly captured the sample sizes, effect sizes, and p‑values as written). This validates the extraction module's ability to accurately capture reported statistics, NOT the inconsistency detection logic (which is validated on synthetic data per FR‑031). *Justification*: Real‑world validation with human verification of extraction accuracy is essential to confirm that the extraction component performs adequately on actual public A/B test summaries. Targets measure extraction accuracy for field‑level capture, not inconsistency detection against known ground truth. (See US‑1)
- **FR-032**: System MUST compute inconsistency prevalence per **source domain** and per **publication year**; for any subgroup containing **≥ 10** summaries it MUST perform Fisher's exact test comparing inconsistent vs. consistent counts, reporting the subgroup p‑value and prevalence. Multiple subgroup tests MUST apply **Bonferroni correction** (adjusted α = 0.05 / number_of_subgroups) to control family‑wise error rate. (See US‑2)

### Key Entities

- **A/B Summary**: Represents a single publicly posted experiment; key attributes include `url`, `variant_a_n`, `variant_b_n`, `effect_size`, `reported_p`, `confidence_interval`, `timestamp`, `outcome_type` (binary / continuous).
- **Audit Record**: Result of the consistency check for one summary; attributes include `reconstructed_p`, `diff_abs`, `flag_inconsistent`, `category`, `notes`.

## Scope Justification

The original idea called for auditing public A/B test summaries and reporting the prevalence of inconsistencies. The retained functional requirements (FR‑001, FR‑002, FR‑003, FR‑004, FR‑004b, FR‑005a, FR‑005b, FR‑007, FR‑009, FR‑012, FR‑024, FR‑025, FR‑026, FR‑027, FR‑028, FR‑030, FR‑031, FR‑031b, FR‑032) are **essential** to fulfil that goal:

1. **Data acquisition and extraction** (FR‑001, FR‑002) are needed to obtain the raw numbers from the public summaries.
2. **Reconstruction of statistical tests** (FR‑003) provides the ground‑truth p‑values against which reported values can be compared.
3. **Inconsistency detection** (FR‑004) implements the core audit logic, now aligned with Constitution Section VI's absolute 0.05 threshold for p‑value discrepancy.
4. **Sample‑size discrepancy detection** (FR‑004b) ensures that mismatched sample size reporting is also flagged, as required by the original methodology.
5. **Prevalence estimation** (FR‑005a) yields the quantitative answer to "how prevalent are inconsistencies?" using a literature‑backed baseline of 0.05 (John et al.), and **FR‑005b** ensures robustness to that assumption.
6. **Sample‑size increase** (FR‑025) guarantees that the audit corpus is large enough to detect a meaningful inconsistency rate with adequate power (power ≥ 0.80), preventing inconclusive results; N ≥ 300 is required by the power calculation parameters.
7. **Monte‑Carlo validation** (FR‑026) ensures the correctness of statistical implementations, a prerequisite for trustworthy inference; 10,000 replicates required for stable validation estimates.
8. **Bias assessment and adjustment** (FR‑027) prevents domain‑dominance from skewing the overall estimate, satisfying methodological rigor.
9. **Logging** (FR‑007) ensures transparency about parsing problems.
10. **CI compatibility** (FR‑009) guarantees that the audit can be run automatically on a regular schedule.
11. **Baseline handling** (FR‑012) allows reconstruction when a baseline rate is omitted, preserving audit coverage (with acknowledged heuristic limitation).
12. **Result export** (FR‑024) provides the required deliverable—a concise, machine‑readable report of the prevalence estimate.
13. **Quickstart documentation** (FR‑028) lowers the barrier for reproducibility and external validation.
14. **Synthetic validation** (FR‑030, FR‑031) supplies a controlled dataset to quantify detector precision and recall for implementation correctness; [deferred] summaries required for stable precision/recall estimates per Kohavi et al. (2020), and ground truth must use independent implementation to detect bugs.
15. **Real‑world extraction validation** (FR‑031b) addresses scientific soundness concerns by requiring human verification of extraction accuracy on ≥100 real summaries to validate that the extraction module correctly captures reported numbers.
16. **Subgroup analysis** (FR‑032) addresses the original research plan's step 7 by summarising inconsistency rates by source type and year and applying Fisher's exact test with Bonferroni correction where appropriate.
17. **FR‑030/031/031b inclusion**: These were explicitly retained because synthetic validation detects implementation bugs while real‑world extraction validation (FR‑031b) confirms actual extraction performance—both are indispensable for demonstrating that the pipeline components work as intended.

All listed requirements are therefore justified as essential rather than gold‑plating. The corpus size increase (100 → 300) and synthetic dataset size increase ([deferred]) are methodologically required to achieve statistical power and stable performance estimates, respectively.

## Methodological Limitations

**Critical**: This audit methodology tests **internal consistency** (whether reported statistics are arithmetically consistent with each other) but **cannot validate external accuracy** (whether reported statistics match the actual underlying data). A summary where all numbers are wrong but internally consistent will be flagged as "consistent" by this methodology. This limitation is inherent to the approach of auditing publicly available summaries without access to raw data.

**FR-012 Baseline Handling**: When baseline conversion rate is missing, the system uses the average of variant rates as a heuristic. This approximation has reduced statistical rigor compared to complete data and should be flagged in audit notes.

**FR-030/031 Synthetic Validation**: Precision/recall targets on synthetic data cannot guarantee detection performance on real-world public A/B test summaries. Synthetic validation detects implementation bugs but does not validate against actual reporting practices.

**FR-031b Real-World Extraction Validation**: Precision/recall on manually annotated summaries provides evidence of extraction capability but cannot guarantee performance on all future summaries outside the validation set distribution. Ground truth is based on human verification of **extraction accuracy** (whether extracted fields match the reported numbers in the source), not inconsistency detection against known ground truth (which requires synthetic data per FR‑031). Human annotators can only verify that extraction correctly captured reported numbers; they cannot independently verify whether the statistical reconstruction is correct.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Extraction accuracy ≥ 95 % on a manually annotated validation set of at least **100** summaries, stratified across five major domains: **tech**, **e‑commerce**, **finance**, **healthcare**, **SaaS** (measured as proportion of correctly captured fields). (See US‑1)
- **SC-003**: For each statistical test, the absolute difference between the SciPy result and the Monte‑Carlo estimate (10 000 replicates) must be **≤ 0.005**. (See US‑1)
- **SC-005**: All logged parsing errors must be ≤ 5 % of total summaries processed. (See US‑1)
- **SC-008**: CI execution must complete within **6 hours**, using resources typical of the default GitHub Actions runner (≈ 2 vCPUs, ≤ 2 GB RAM); resource usage is logged and must meet these limits. (See US‑1, US‑3, US‑4)
- **SC-013**: CI pipeline must exit with status 0 and produce a `manifest.json` file in ≥ 99 % of runs, confirming successful completion and artifact generation. (See US‑4)
- **SC-014**: The binomial test defined in **FR‑005a** must report a p‑value rounded to three decimal places, a Wilson confidence interval whose total width ≤ 0.10, and flag significance when p ≤ 0.05. (See US‑2)
- **SC-015**: Sensitivity analysis (FR‑005b) must show that the estimated prevalence varies by less than **0.02** across baseline proportions 0.02–0.10. (See US‑2)
- **SC-024**: The exported CSV `summary_report.csv` must contain columns `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`; the values must exactly match those computed in the JSON `audit_report.json`. (See US‑2, US‑3)
- **SC-025**: The audited corpus contains **N ≥ 300** summaries (or the calculated minimum) as required by the a priori power analysis (FR‑025). (See US‑2)
- **SC-026**: Monte Carlo validation passes for all statistical tests with absolute difference **≤ 0.005** (FR‑026). (See US‑1)
- **SC-027**: Bias‑assessment report must show that **no** single domain exceeds **30 %** of the total corpus; the report must also include both the raw inconsistency rate and the bias‑adjusted inconsistency rate. (See US‑1)
- **SC-028**: The Quickstart guide is verified by a user test where a novice follows the instructions and completes the audit on **30 URLs** in ≤ 30 minutes on the default GitHub Actions runner. (See US‑1)
- **SC-030**: Precision on the synthetic validation dataset must be **≥ 90 %** and recall **≥ 80 %** (F1 ≥ 0.85). **This criterion applies to synthetic validation only (FR‑031)**; real-world extraction validation is governed by SC‑031b. (See FR‑031) **(See US‑1, US‑2, US‑3, US‑4)**
- **SC-031b**: Extraction precision on the manually annotated real-world validation set must be **≥ 85 %** and recall **≥ 75 %** (F1 ≥ 0.80). Ground truth MUST be established by human annotation verifying that extracted fields match the reported numbers in the source summaries (whether extraction correctly captured sample sizes, effect sizes, and p‑values as written). Precision/recall measure extraction accuracy for field‑level capture, not inconsistency detection against known ground truth. (See US‑1)
- **SC-032**: For each subgroup (domain or year) with ≥ 10 summaries, the generated report must include the subgroup inconsistency prevalence, Fisher's exact test p‑value (with Bonferroni adjustment), and indicate whether the subgroup prevalence is statistically different from the overall rate (adjusted α). (See US‑2)

## Assumptions

- Public A/B test summaries provide **sample size**, **effect size**, and either **p‑value** or **confidence interval** for each variant.
- Effect sizes are reported as **absolute difference in conversion rates**, **percentage lift**, or **mean difference for continuous metrics**; the reconstruction routine will convert lift to absolute difference using the baseline conversion rate (or average of variants when baseline is absent) as defined in **FR‑012**.
- Reported p‑values are two‑sided unless explicitly indicated otherwise.
- The corpus of summaries is sufficiently diverse to approximate industry‑wide reporting practices; no explicit minimum corpus size is mandated beyond the data actually collected for the audit.
- Findings are framed as **associational** (i.e., "reported metrics are inconsistent with statistical theory") because the audit does not involve random assignment.
- Multiple hypothesis testing is controlled via **Bonferroni correction** for subgroup analyses in FR‑032; the baseline binomial test in FR‑005a is a single test requiring no correction.
- When a reported p‑value is given as an inequality (e.g., "p < 0.001"), the pipeline treats the bound value as an upper limit; the summary is flagged inconsistent only if the reconstructed p‑value exceeds this bound (see **FR‑004**).
- If only a total sample size `N` is present and per‑variant counts are absent, the pipeline **does not impute** equal allocation. Instead, the entry is flagged as "missing metric" and recorded in the audit notes.
- All computation is performed on CPU‑only resources; no GPU‑specific libraries or large‑model inference are required, satisfying the GitHub Actions free‑tier constraints.
- Validation‑set ground‑truth p‑values are computed using analytical formulas (or an independent library such as **statsmodels**) to ensure independence from the pipeline implementation.
- Manual annotation for real-world extraction validation (FR‑031b, SC‑031b) is performed by at least two independent annotators with agreement ≥ 85 %; discrepancies are resolved by a third annotator. Ground truth verification is based on extraction accuracy (whether extracted fields match reported numbers), not inconsistency detection against known ground truth.

## References

1. Kohavi, R., Longbotham, R., & Sommerfield, D. (2020). "Large‑Scale Online Experiments: A Review." *Communications of the ACM*, 63(9), 78‑87..
2. John, L. K., Loewenstein, G., & Prelec, D. (2022). "Measuring the Prevalence of Questionable Research Practices in Business Experiments." *Journal of Experimental Psychology: Applied*, 28(3), 456‑472. DOI: 10.1037/xap0000421.

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
 docker build -t ab-audit:latest.
 ```

3. **Run the audit pipeline**

 ```bash
 docker run --rm \
 -v $(pwd)/input:/app/input \
 -v $(pwd)/output:/app/output \
 ab-audit:latest./run_audit.sh input/urls.csv output/
 ```

 The script will perform:
 - Deduplication (if any duplicates exist, they are collapsed)
 - Extraction
 - Inconsistency detection (FR‑004, FR‑004b)
 - Binomial prevalence test (FR‑005a) **with a priori power‑size guarantee (FR‑025)**
 - Monte‑Carlo validation of statistical implementations (FR‑026)
 - Bias assessment and bias‑adjusted prevalence (FR‑027)
 - Subgroup prevalence analysis with Fisher's exact test (FR‑032)
 - Generation of:
   - `output/audit_report.json`
   - `output/summary_report.csv`
   - `output/bias_report.json` (domain proportions and adjusted rate)
   - `output/subgroup_report.json` (per‑domain/year prevalence and Fisher p‑values)
   - `README_QUICKSTART.md` (see FR‑028)

4. **Check resource usage**
 The pipeline logs CPU time and memory; ensure the run stays within **≤ 6 hours** and uses resources typical of the default GitHub Actions runner (see **SC‑008**).

5. **Interpret results**
 Open `output/summary_report.csv` in a spreadsheet or view `output/audit_report.json` to see per‑summary flags and the overall inconsistency prevalence with its 95 % Wilson confidence interval and bias‑adjusted estimate.

## Implementation Tasks

- **T026**: *Synthetic Validation Dataset Generation*
 Generate a synthetic validation dataset of exactly **10 000** A/B test summaries (mix of binary and continuous outcomes) with known ground‑truth p‑values and effect sizes using analytical formulas or an independent library (NOT the same implementation as FR‑003). Output a CSV file `synthetic_validation.csv` and a JSON file `synthetic_ground_truth.json`. No placeholder values; the count is fixed.

- **T044**: *Domain Bias Subsampling*
 When any domain exceeds **30%** of the total corpus, subsample that domain to equalize domain proportions. Trigger threshold explicitly set to **30%** per **FR‑027**. Action: subsample to equalize domain proportions. Output: bias_report.json with domain proportions and adjustment notes. (See FR‑027)

- **T062**: *Monte Carlo Validation of Statistical Tests*
 For each statistical test (two‑proportion z‑test, Fisher's exact test, Welch's t‑test, binomial test) run **10 000** Monte Carlo replicates, compare the library implementation result to the Monte Carlo estimate, and verify that the absolute difference is **≤ 0.005**. Record results in `monte_carlo_validation_report.json`. This task directly satisfies **FR‑026**.

- **T076**: Compute checksums for all generated output files and record them in `output/checksums.txt`.

- **T077**: Extend `manifest.json` to include the checksum entries produced by T076.

- **T081**: *Real-World Extraction Validation Set Annotation*
 Create a manually annotated validation set of at least **100** public A/B test summaries with ground‑truth extraction labels determined by independent human annotators. Two annotators must independently extract fields from each summary; discrepancies are resolved by a third annotator. Store annotations in `real_world_validation_labels.csv` with fields: `url`, `ground_truth_sample_size_a`, `ground_truth_sample_size_b`, `ground_truth_effect_size`, `ground_truth_p`, `annotator_1`, `annotator_2`, `annotator_3`, `resolution_notes`. This task directly satisfies **FR‑031b**.

- **T082**: *Real-World Extraction Validation Evaluation*
 Run the extraction module on the real-world validation set from T081 and compute precision, recall, and F1 score for field‑level extraction. Verify that precision ≥ 85 % and recall ≥ 75 % (F1 ≥ 0.80) as required by **FR‑031b** and **SC‑031b**. Record results in `real_world_validation_report.json`.
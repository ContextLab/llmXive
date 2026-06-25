# Feature Specification: Evaluating the Statistical Validity of Public A/B Test Summaries  

**Feature Branch**: `001-eval-ab-test-validity`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Audit publicly available A/B test summaries for statistical consistency (p‑values, effect sizes, sample sizes) and report the prevalence of inconsistencies."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Automated Consistency Audit (Priority: P1)

A researcher wants to run a reproducible audit over a corpus of public A/B test summaries to identify statistical inconsistencies.

**Why this priority**: This is the core value‑producing function; without it the project cannot deliver its primary research question.

**Independent Test**: Provide a list of several known summaries (ground‑truth annotated) and verify that the system flags exactly the inconsistently reported metrics.

**Acceptance Scenarios**:

1. **Given** a CSV file containing URLs of public A/B test summaries, **When** the audit pipeline is executed, **Then** a JSON report is produced listing each summary with a consistency flag (`consistent` / `inconsistent`) and the computed vs. reported p‑value difference.  
2. **Given** a summary where the reported p‑value differs from the reconstructed p‑value by 0.07, **When** the pipeline processes it, **Then** the summary is marked *inconsistent* because the absolute difference exceeds the 0.05 threshold.

---

### User Story 2 – Summary Statistics Dashboard (Priority: P2)

A product manager wants a high‑level view of inconsistency prevalence across sources **and over time**.

**Why this priority**: Enables stakeholders to interpret the audit results without digging into raw data, supporting decision‑making and transparency initiatives.

**Independent Test**: Run the pipeline on a representative summary corpus and verify that the generated HTML dashboard shows (a) a bar chart with overall inconsistency rate, (b) a source‑wise breakdown, **and** (c) a line chart of inconsistency rates over time with an accompanying Cochran‑Armitage trend‑test p‑value that matches the underlying JSON.

**Acceptance Scenarios**:

1. **Given** the JSON audit output, **When** the dashboard generator runs, **Then** the dashboard displays (a) total number of summaries, (b) percentage flagged inconsistent, (c) a **chi‑squared test of independence** result for source‑wise heterogeneity, and (d) the binomial‑test result for the overall inconsistency rate.  
2. **Given** the same JSON output enriched with timestamps for each summary, **When** the dashboard renders, **Then** it shows a time‑series line chart of monthly inconsistency rates and reports the Cochran‑Armitage trend‑test p‑value for the temporal pattern.

---

### User Story 3 – Reproducibility Package Export (Priority: P3)

A reviewer wants to reproduce the analysis on a different machine.

**Why this priority**: Guarantees scientific rigor and satisfies open‑science requirements; it is less critical for day‑to‑day use but essential for publication.

**Independent Test**: Clone the GitHub repository, build the Docker image, and execute the provided `run_audit.sh` script; the output must be identical (bit‑wise) to the reference results on a known seed.

**Acceptance Scenarios**:

1. **Given** the repository and Dockerfile, **When** the reviewer builds the container and runs the script on the same corpus, **Then** the resulting JSON and dashboard files match the reference artifacts (MD5 checksum identical).

---

### Edge Cases

- What happens when a summary omits one of the required metrics (e.g., reports effect size but no p‑value or confidence interval)?  
- How does the system handle non‑binary outcomes (e.g., revenue lift) where a two‑proportion test is inappropriate?  
- How are p‑values reported with extreme rounding (e.g., “p < 0.001”) or as inequality statements?  
- What if the reported sample sizes are inconsistent between the narrative text and the tabular data?  
- How does the pipeline behave when a URL is dead or returns a non‑HTML payload?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept as input a list of URLs (or file paths) pointing to publicly available A/B test summaries.  
- **FR-002**: System MUST automatically extract, for each variant, the reported sample size, effect size (conversion‑rate difference, lift % or absolute difference for continuous metrics), and reported p‑value or confidence interval.  
- **FR-003**: System MUST reconstruct the expected p‑value using the appropriate statistical test (two‑proportion Z‑test for binary conversion metrics, two‑sample t‑test for continuous metrics).  
- **FR-004**: System MUST flag a summary as *inconsistent* when the absolute difference between the reported p‑value and the reconstructed p‑value exceeds 0.05 **or** when the reported confidence interval does not contain the effect size implied by the reconstructed test.  
- **FR-005**: System MUST compute (a) the overall inconsistency rate and test the null hypothesis that the true proportion of inconsistencies equals 0.05 using an exact binomial test (one‑sided), (b) a chi‑squared goodness‑of‑fit test across the entire corpus to assess whether the observed inconsistency count exceeds what would be expected under random error, (c) source‑wise inconsistency rates and assess heterogeneity with a chi‑squared test of independence, (d) temporal trends in inconsistency rates using the Cochran‑Armitage trend test, and (e) apply a Bonferroni correction across all subgroup significance tests.  
- **FR-006**: System MUST export a reproducible research package containing (i) raw extracted data, (ii) analysis scripts, (iii) Dockerfile, and (iv) generated reports.  
- **FR-007**: System MUST log any parsing failures or missing fields with clear error messages for downstream inspection.  
- **FR-008**: System MUST categorize each flagged inconsistency into one of the following types: *sample‑size mismatch*, *effect‑size inflation*, *rounding error*, *missing metric*, *statistical‑test mis‑specification*, *multiple‑testing issue*, or *other*. The category is stored in the audit record and reported in both JSON and dashboard outputs.  
- **FR-009**: System MUST enforce CPU‑only execution; all dependencies must run on the default GitHub Actions runner (≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h runtime). No GPU‑specific libraries or large‑model inference may be used.  

### Key Entities

- **A/B Summary**: Represents a single publicly posted experiment; key attributes include `url`, `variant_a_n`, `variant_b_n`, `effect_size`, `reported_p`, `confidence_interval`, `timestamp`, `outcome_type` (binary / continuous).  
- **Audit Record**: Result of the consistency check for one summary; attributes include `reconstructed_p`, `diff_abs`, `flag_inconsistent`, `category`, `notes`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Extraction accuracy ≥ 95 % on a manually annotated validation set of at least 30 summaries (measured as proportion of correctly captured fields).  
- **SC-002**: Inconsistency‑detection precision ≥ 90 % on the same validation set (true positives / (true positives + false positives)).  
- **SC-003**: The binomial test, chi‑squared goodness‑of‑fit test, chi‑squared test of independence, Cochran‑Armitage trend test, and Bonferroni‑adjusted subgroup tests reported in the final dashboard must be computed using SciPy (or an equivalent CPU‑only library) and documented in the reproducibility package.  
- **SC-004**: The reproducibility package must build the Docker image and run the full pipeline on a fresh machine producing identical JSON output (MD5 checksum match).  
- **SC-005**: All logged parsing errors must be ≤ 5 % of total summaries processed.  
- **SC-006**: Power analysis must show ≥ 80 % power to detect an inconsistency proportion of [deferred] against the null π₀ = 0.05 at α = 0.05, given the planned corpus size (≥ 100 summaries). The calculation method (binomial power) must be included in the reproducibility package.
- **SC-007**: After Bonferroni correction, any subgroup significance claim must have an adjusted p‑value ≤ 0.05; the adjusted p‑values must be reported alongside raw p‑values in the dashboard.

## Assumptions

- Public A/B test summaries provide **sample size**, **effect size**, and either **p‑value** or **confidence interval** for each variant.  
- Effect sizes are reported as **absolute difference in conversion rates**, **percentage lift**, or **mean difference for continuous outcomes**; the reconstruction routine will convert lift to absolute difference when necessary.  
- Reported p‑values are two‑sided unless explicitly indicated otherwise.  
- The corpus of ≥ 100 summaries is sufficiently diverse to approximate industry‑wide reporting practices.  
- Findings are framed as **associational** (i.e., “reported metrics are inconsistent with statistical theory”) because the audit does not involve random assignment.  
- Multiple hypothesis testing across sub‑analyses is addressed by the Bonferroni correction specified in FR‑005; individual inconsistency flags remain unadjusted because they are deterministic decisions based on a predefined discrepancy rule.  
- The categorization taxonomy in FR‑008 captures the most common error modes observed in prior meta‑research on A/B testing (see Nielsen et al., 2022, *J. of Data Science*).  
- The analysis will run on the default GitHub Actions free‑tier runner (≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h total runtime); all code must be CPU‑only and avoid GPU‑specific libraries.  
- **[NEEDS CLARIFICATION: Are continuous outcome metrics (e.g., revenue lift) present in the corpus, and if so, how should they be identified for selection of the two‑sample t‑test?]**  
- **[NEEDS CLARIFICATION: How should inequality‑formatted p‑values (e.g., “p < 0.001”) be interpreted for the discrepancy rule?]**  
- **[NEEDS CLARIFICATION: Do all summaries consistently report sample sizes for both variants, or are there cases where only a total sample size is given?]**  

---

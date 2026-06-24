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

1. **Given** a CSV file containing URLs of public A/B test summaries, **When** the audit pipeline is executed, **Then** a JSON report is produced listing each summary with a consistency flag (consistent / inconsistent) and the computed vs. reported p‑value difference.  
2. **Given** a summary where the reported p‑value differs from the reconstructed p‑value by 0.07, **When** the pipeline processes it, **Then** the summary is marked *inconsistent* because the absolute difference exceeds the 0.05 threshold.

---

### User Story 2 – Summary Statistics Dashboard (Priority: P2)

A product manager wants a high‑level view of inconsistency prevalence across sources and over time.

**Why this priority**: Enables stakeholders to interpret the audit results without digging into raw data, supporting decision‑making and transparency initiatives.

**Independent Test**: Run the pipeline on a representative summary corpus and verify that the generated HTML dashboard shows a bar chart with overall inconsistency rate and source‑wise breakdown that matches the underlying JSON.

**Acceptance Scenarios**:

1. **Given** the JSON audit output, **When** the dashboard generator runs, **Then** the dashboard displays (a) total number of summaries, (b) percentage flagged inconsistent, and (c) a chi‑squared goodness‑of‑fit test result with its p‑value.

---

### User Story 3 – Reproducibility Package Export (Priority: P3)

A reviewer wants to reproduce the analysis on a different machine.

**Why this priority**: Guarantees scientific rigor and satisfies open‑science requirements; it is less critical for day‑to‑day use but essential for publication.

**Independent Test**: Clone the GitHub repository, build the Docker image, and execute the provided `run_audit.sh` script; the output must be identical (bit‑wise) to the reference results on a known seed.

**Acceptance Scenarios**:

1. **Given** the repository and Dockerfile, **When** the reviewer builds the container and runs the script on the same corpus, **Then** the resulting JSON and dashboard files match the reference artifacts (MD5 checksum identical).

---

### Edge Cases

- What happens when a summary omits one of the required metrics (e.g., reports effect size but no p‑value)?  
- How does the system handle non‑binary outcomes (e.g., revenue lift) where a two‑proportion test is inappropriate?  
- How are p‑values reported with extreme rounding (e.g., “p < 0.001”)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept as input a list of URLs (or file paths) pointing to publicly available A/B test summaries.  
- **FR-002**: System MUST automatically extract, for each variant, the reported sample size, effect size (conversion‑rate difference or lift %), and reported p‑value or confidence interval.  
- **FR-003**: System MUST reconstruct the expected p‑value using the appropriate statistical test (two‑proportion Z‑test for binary conversion metrics, two‑sample t‑test for continuous metrics).  
- **FR-004**: System MUST flag a summary as *inconsistent* when the absolute difference between reported and reconstructed p‑values exceeds **0.05**.  
- **FR-005**: System MUST compute and report (a) overall inconsistency rate, (b) source‑wise rates, and (c) a chi‑squared goodness‑of‑fit test comparing observed inconsistency counts to the uniform‑error null hypothesis.  
- **FR-006**: System MUST export a reproducible research package containing (i) raw extracted data, (ii) analysis scripts, (iii) Dockerfile, and (iv) generated reports.  
- **FR-007**: System MUST log any parsing failures or missing fields with clear error messages for downstream inspection.  

*Clarification needed*:

- **FR-002**: [NEEDS CLARIFICATION: Should the extractor also capture confidence intervals when p‑values are not reported?]  
- **FR-003**: [NEEDS CLARIFICATION: Which statistical test should be used for non‑binary outcomes such as revenue lift?]  
- **FR-004**: [NEEDS CLARIFICATION: How should “p < 0.001” style reports be treated in the inconsistency calculation?]

### Key Entities

- **A/B Summary**: Represents a single publicly posted experiment; key attributes include `url`, `variant_a_n`, `variant_b_n`, `effect_size`, `reported_p`, `confidence_interval`.  
- **Audit Record**: Result of the consistency check for one summary; attributes include `reconstructed_p`, `diff_abs`, `flag_inconsistent`, `notes`.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Extraction accuracy ≥ 95 % on a manually annotated validation set of 20 summaries (measured as proportion of correctly captured fields).  
- **SC-002**: Inconsistency‑detection precision ≥ 90 % on the same validation set (true positives / (true positives + false positives)).  
- **SC-003**: The chi‑squared goodness‑of‑fit test reported in the final dashboard must have a p‑value computed using a standard library (e.g., SciPy) and documented in the reproducibility package.  
- **SC-004**: The reproducibility package must build the Docker image and run the full pipeline on a fresh machine producing identical JSON output (MD5 checksum match).  
- **SC-005**: All logged parsing errors must be ≤ 5 % of total summaries processed.

## Assumptions

- Public A/B test summaries provide **sample size**, **effect size**, and either **p‑value** or **confidence interval** for each variant.  
- Effect sizes are reported as **absolute difference in conversion rates** or **percentage lift**; the reconstruction routine will convert lift to absolute difference when necessary.  
- Reported p‑values are two‑sided unless explicitly indicated otherwise.  
- The corpus of 100 + summaries is sufficiently diverse to approximate the broader industry reporting practice.  
- No random assignment is performed by the audit itself; findings are framed as **associational** (i.e., “reported metrics are inconsistent with statistical theory”) rather than causal.  
- Multiple hypothesis testing across summaries will be addressed by the chi‑squared test; individual inconsistency flags are not corrected for multiplicity beyond the 0.05 absolute‑difference threshold.  

---

# Feature Specification: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences"

## User Scenarios & Testing

### User Story 1 - Meta-Analysis Data Extraction and Synthesis (Priority: P1)

As a research analyst, I need to extract effect sizes (correlation coefficients, t-values, F-statistics), sample sizes, and tract regions from selected studies and compute a weighted mean effect size using a random-effects model, so that I can determine the aggregate relationship between white matter integrity and music preference.

**Research Feasibility Note**: This analysis assumes the existence of primary studies reporting direct correlation coefficients (r) between diffusion MRI metrics (FA/MD) and quantitative music preference ratings. If the literature search yields no studies with direct (r, n) pairs for this specific relationship, the system must pivot to a narrative synthesis of qualitative findings regarding "neural circuitry" and "preference" as distinct but related constructs.

**Why this priority**: This is the core scientific deliverable. Without the ability to extract data and perform the primary statistical synthesis, the study produces no quantitative results.

**Independent Test**: Can be fully tested by running the extraction script on a small, synthetic CSV of 3 mock studies with known effect sizes and verifying the output JSON contains the correct weighted mean and confidence intervals calculated via `statsmodels` or `metafor` logic.

**Acceptance Scenarios**:

1. **Given** a CSV file containing 3 mock studies with valid `r`, `n`, and `tract_name` columns, **When** the extraction and synthesis module is executed, **Then** the output JSON must contain a `weighted_mean_r` value matching the manual calculation within a tolerance of 0.001.
2. **Given** a dataset where one study has a missing `t-value` but a valid `r`, **When** the module processes the data, **Then** it must correctly utilize the `r` value for the meta-analysis without raising a runtime error.
3. **Given** a dataset with fewer than 10 unique studies (defined as unique (Author, Year) pairs), **When** the system runs, **Then** it must flag the `synthesis_mode` as "narrative" and skip the quantitative aggregation step.

---

### User Story 2 - Heterogeneity and Bias Assessment (Priority: P2)

As a methodologist, I need to calculate I² statistics for heterogeneity and perform Egger's regression test for publication bias, so that I can validate the robustness of the meta-analytic findings and determine if the pooled effect is reliable.

**Why this priority**: A meta-analysis without heterogeneity or bias checks is methodologically unsound. This ensures the "Methodological Soundness" requirement is met before results are considered valid.

**Independent Test**: Can be tested by providing a synthetic dataset with high variance between study effect sizes and verifying the I² statistic output is >50%, and by providing a dataset with skewed effect sizes to verify the Egger's test p-value is reported correctly.

**Acceptance Scenarios**:

1. **Given** a synthetic dataset with 15 studies where effect sizes are explicitly set to r values ranging from 0.1 to 0.8, **When** the heterogeneity module runs, **Then** the output must report an I² statistic ≥ 50% indicating substantial heterogeneity.
2. **Given** a synthetic dataset of 15 studies where small studies (n < 20) have r > 0.6 and large studies (n > 100) have r < 0.2 (simulating publication bias), **When** the bias detection module runs, **Then** the Egger's regression test must return a p-value < 0.05.
3. **Given** a dataset with only 5 studies, **When** the bias detection module runs, **Then** it must SKIP the Egger's test and report "Skipped: Insufficient studies (N < 10) for Egger's regression."

---

### User Story 3 - Visualization and Reporting (Priority: P3)

As a researcher, I need to generate forest plots, funnel plots, and summary correlation plots using `matplotlib` and `seaborn`, so that I can visually communicate the meta-analytic results and heterogeneity to the review panel.

**Why this priority**: Visualizations are required for the final report and are essential for interpreting the statistical outputs, but they are secondary to the calculation logic.

**Independent Test**: Can be tested by running the plotting module on a static dataset and verifying that the generated PNG files exist, are under 5MB, and contain the correct axis labels and data points.

**Acceptance Scenarios**:

1. **Given** the synthesized effect size data, **When** the forest plot generator runs, **Then** it must produce a PNG file where the summary diamond aligns with the calculated `weighted_mean_r`.
2. **Given** the bias assessment data, **When** the funnel plot generator runs, **Then** it must plot standard error against effect size on the correct axes and render a vertical symmetry reference line at the pooled effect size.
3. **Given** a standard GitHub Actions runner environment, **When** the plotting module generates high-resolution figures, **Then** the process must complete without exceeding the runner's default memory limits.

### Edge Cases

- **Study Counting**: A "study" is defined as a unique (Author, Year) pair. Multiple tracts reported in a single paper count as one study for the N < 10 threshold, but as distinct comparisons for correction logic if N ≥ 10.
- **Missing Effect Sizes**: If studies report only p-values without effect sizes, the system must attempt to convert p-values to effect sizes using standard formulas (e.g., Fisher's z) or exclude the study with a log entry.
- **Model Convergence**: If the `statsmodels` or `metafor` library fails to converge on a random-effects model, the system must fall back to a fixed-effects model and log the divergence.
- **Data Scarcity**: If the literature search yields an insufficient number of eligible studies with direct (r, n) data, the system MUST pivot to a narrative systematic review of qualitative findings.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract correlation coefficients (`r`), sample sizes (`n`), and specific tract identifiers from input study data. If direct (r, n) pairs for dMRI vs. Preference are unavailable, the system MUST extract qualitative descriptors of "neural circuitry" and "preference" for narrative synthesis. (See US-1)
- **FR-002**: System MUST calculate the I² statistic to quantify between-study heterogeneity and report the percentage of variance due to heterogeneity rather than chance. (See US-2)
- **FR-003**: System MUST perform Egger's linear regression test to detect potential publication bias AND report the intercept and p-value ONLY if the number of studies N ≥ 10. If N < 10, the system MUST skip the test and report the reason. (See US-2)
- **FR-004**: System MUST generate a forest plot visualizing individual study effect sizes with 95% confidence intervals and the pooled estimate. (See US-3)
- **FR-005**: System MUST apply Bonferroni correction for multiple tract comparisons ONLY if the number of distinct tracts (k) ≥ 2 AND the number of studies (N) ≥ 10. The correction must be applied across the set of distinct tracts (e.g., arcuate fasciculus, cingulum bundle, uncinate fasciculus) identified in the input data. If N < 10, the system MUST skip correction and default to narrative synthesis. (See US-1)
- **FR-006**: System MUST detect if the number of eligible studies (unique Author-Year pairs) is < 10 and automatically switch the output mode from quantitative meta-analysis to narrative systematic review. (See US-1)

### Key Entities

- **StudyRecord**: Represents a single literature entry containing metadata (author, year), methodological details (tract name, MRI metric), and statistical outcomes (effect size, sample size).
- **MetaAnalysisResult**: Represents the aggregated output including pooled effect size, heterogeneity metrics (I²), bias test results, and confidence intervals.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The meta-analysis pipeline MUST successfully process a dataset of 10+ studies and output a valid JSON report with a pooled effect size and 95% CI within 15 minutes on a GitHub Actions default runner (2 vCPU, 7GB RAM). (See US-1)
- **SC-002**: The heterogeneity assessment MUST report an I² statistic with a precision of at least two decimal places. (See US-2)
- **SC-003**: The visualization module MUST generate all required plots (forest, funnel, correlation) in PNG format with file sizes optimized for efficient storage and transmission, without exceeding the runner's default memory limits. (See US-3)
- **SC-004**: The system MUST successfully apply Bonferroni correction to at least 5 distinct tract comparisons (defined as unique tract names in the input) and report the adjusted significance threshold, provided N ≥ 10. (See US-1)
- **SC-005**: The narrative synthesis fallback MUST generate a structured text summary if the eligible study count is < 10. (See US-1)

## Assumptions

- The primary dataset sources (PubMed, Web of Science) MAY yield a sufficient number of studies containing both diffusion MRI metrics (FA/MD) and behavioral music preference data.; however, if such direct correlation data is scarce, the project will proceed via a narrative systematic review of related neural circuitry findings.
- The `statsmodels` and `scipy` Python libraries are available in the standard CI/CD runner environment and can perform random-effects meta-analysis and Egger's regression without GPU acceleration.
- The "auditory-reward pathway" is defined strictly as the connection between the primary auditory cortex (Heschl's gyrus) and the ventral striatum/nucleus accumbens, and studies reporting these specific tracts will be prioritized.
- All extracted effect sizes are assumed to be two-tailed; one-tailed values will be converted or excluded if the directionality is ambiguous.
- The analysis is computationally lightweight enough to run within standard CI/CD runner limits (e.g., modest vCPU and RAM configurations).
- If the literature search yields insufficient data for quantitative synthesis, the pivot to a narrative systematic review is an acceptable outcome that satisfies the project's research goals.
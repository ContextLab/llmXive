# Feature Specification: Mindfulness Components and Delivery Formats in ASD Social Skills

**Feature Branch**: `001-mindfulness-asd-social-skills`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "The Role of Mindfulness in Improving Social Skills Among Children with Autism"

## User Scenarios & Testing

### User Story 1 - Data Collection and Cleaning Pipeline (Priority: P1)

The system MUST ingest raw study data from ClinicalTrials.gov, OSF, Semantic Scholar, arXiv, and OpenAlex, where data is retrieved via API queries or manual exports, validate it against the inclusion criteria (children aged 6-12 with ASD, explicit social skill outcomes), and extract standardized variables (intervention component, delivery format, outcome measure scores, sample size, follow-up duration, social skill domain) into a clean CSV.

**Why this priority**: Without a reliable, validated dataset from diverse sources, no statistical analysis can be performed. This is the foundational step that determines the validity of all downstream results and addresses the risk of zero studies from primary registries.

**Independent Test**: The pipeline can be tested by running it against a known set of 5 mock study records with predefined inclusion/exclusion flags and verifying that the output CSV contains exactly the expected 3 included records with correctly parsed numeric fields and categorical labels.

**Acceptance Scenarios**:

1. **Given** a CSV export from ClinicalTrials.gov containing 10 studies, **When** the pipeline processes the file, **Then** exactly 3 studies meeting the age (6-12) and diagnosis (ASD) criteria are retained, and the others are logged to `excluded_studies.log` with the specific reason (e.g., "Age > 12", "No social skill outcome").
2. **Given** a study record with missing "follow-up duration" but valid baseline and post-intervention scores, **When** the pipeline processes the record, **Then** the record is retained with `follow_up_months` set to `null` and a warning is logged, allowing the meta-analysis to proceed using available data points.
3. **Given** a study where the intervention description lists "breath awareness and body scan", **When** the pipeline processes the record, **Then** the intervention component is tagged as "combined" and the record is retained for subgroup analysis.

---

### User Story 2 - Effect Size Calculation and Meta-Analysis (Priority: P2)

The system MUST calculate Hedges' *g* effect sizes for each included study using the extracted means, standard deviations, and sample sizes, then perform a random-effects meta-analysis to estimate the pooled effect size and conduct subgroup analyses (using Cochran's Q-test) comparing mindfulness components and delivery formats, with meta-regression only if N ≥ 10.

**Why this priority**: This is the core analytical engine that answers the primary research question regarding which components and formats are most effective, while ensuring statistical validity by conditioning complex models on sample size.

**Independent Test**: The calculation module can be tested by providing a synthetic dataset of 3 studies with known means and standard deviations, verifying that the calculated Hedges' *g* matches the manual calculation within a tolerance of 0.001, and that the random-effects model produces a pooled estimate consistent with a standard reference implementation (e.g., `metafor` in R).

**Acceptance Scenarios**:

1. **Given** a dataset of 5 studies with complete pre/post means and standard deviations, **When** the analysis runs, **Then** Hedges' *g* is calculated for each study, and the random-effects pooled effect size is reported with a 95% confidence interval.
2. **Given** a dataset where studies are tagged by delivery format (caregiver-mediated vs. child-led), **When** the subgroup analysis runs, **Then** the output includes a Cochran's Q statistic and p-value comparing the effect sizes between the two formats.
3. **Given** a dataset with heterogeneous effect sizes (I² > 50%), **When** the analysis runs, **Then** the heterogeneity statistics (Q, I², τ²) are calculated and reported, and the random-effects model is used instead of a fixed-effects model.

---

### User Story 3 - Visualization and Publication Bias Assessment (Priority: P3)

The system MUST generate forest plots for the overall effect and subgroup analyses, and a funnel plot (if N ≥ 10) to assess publication bias, saving these as high-resolution PNG files and including them in the final report.

**Why this priority**: Visualizations are essential for interpreting the meta-analysis results and assessing the robustness of the findings against publication bias, which is critical for the validity of the review, while avoiding invalid tests on small samples.

**Independent Test**: The visualization module can be tested by running it on a small dataset and verifying that the forest plot correctly displays the study-specific effect sizes and confidence intervals, and that the funnel plot is suppressed if N < 10.

**Acceptance Scenarios**:

1. **Given** a dataset of 10 studies with calculated effect sizes, **When** the forest plot is generated, **Then** the plot displays each study's effect size with its 95% CI, the pooled effect size diamond, and a clear legend distinguishing between mindfulness components.
2. **Given** a dataset with potential publication bias (missing small studies with negative effects) and N ≥ 10, **When** the funnel plot is generated, **Then** the plot visually shows asymmetry, and Egger's test reports a significant p-value (< 0.10).
3. **Given** a dataset with N < 10, **When** the report is generated, **Then** the funnel plot and Egger's test are suppressed, and a warning is included in the final report.

---

### Edge Cases

- What happens when a study reports only p-values or confidence intervals instead of means and standard deviations? The system MUST attempt to reconstruct the necessary statistics or exclude the study with a detailed log entry explaining the reconstruction failure.
- How does the system handle studies with multiple intervention arms (e.g., both breath awareness and body scan tested separately)? The system MUST either split the control group proportionally or select the most relevant arm based on predefined rules, documenting the choice in the analysis log.
- What happens if the number of included studies is less than 10? The system MUST still perform the meta-analysis but suppress the funnel plot and Egger's test, as these are unreliable with small sample sizes, and issue a warning in the final report. If N < 10, subgroup analyses (Cochran's Q) are also suppressed in favor of descriptive statistics and narrative synthesis.

## Requirements

### Functional Requirements

- **FR-001**: System MUST query ClinicalTrials.gov (endpoint: /study/v2), OSF (API v2), Semantic Scholar, arXiv, and OpenAlex APIs for completed trials involving "mindfulness" and "autism" or "ASD" published between 2015–2024, with rate-limit handling (max 10 requests/sec, exponential backoff), and return a list of study identifiers (See US-1).
- **FR-002**: System MUST parse study metadata and extract inclusion criteria (age 6-12, ASD diagnosis, social skill outcome measures) to filter the candidate studies, mapping 'age' to 'enrollment_age_min/max' fields and 'ASD diagnosis' to 'conditions' field containing 'Autism Spectrum Disorder' or 'ASD' (See US-1).
- **FR-003**: System MUST extract numeric data (means, standard deviations, sample sizes) and categorical variables (intervention component, delivery format, follow-up duration, social skill domain) from the included studies, using regex patterns for 'breath', 'body scan', 'loving-kindness' and keywords 'caregiver', 'parent', 'child-led', 'self-directed' for classification (See US-1).
- **FR-004**: System MUST calculate Hedges' *g* effect sizes for each study using the extracted means, standard deviations, and sample sizes, correcting for small sample bias (See US-2).
- **FR-005**: System MUST perform a random-effects meta-analysis to estimate the pooled effect size and conduct subgroup analyses using Cochran's Q-test comparing mindfulness components (breath, body scan, loving-kindness) and delivery formats (caregiver-mediated vs. child-led), with meta-regression only if N ≥ 10; studies with missing subgroup tags are excluded from that specific subgroup analysis (See US-2).
- **FR-006**: System MUST generate forest plots for the overall effect and subgroup analyses, and a funnel plot to assess publication bias (unless N < 10), saving them as PNG files (See US-3).
- **FR-007**: System MUST log all excluded studies with specific reasons (e.g., age range, missing outcome measure) and all data extraction decisions in a structured log file (See US-1).
- **FR-008**: System MUST handle studies with multiple intervention arms by either splitting the control group proportionally or selecting the most relevant arm, and document the approach in the analysis log (See US-2).
- **FR-009**: System MUST attempt data reconstruction from full-text PDFs if registry data is incomplete, using OCR and text extraction tools (See US-1).
- **FR-010**: System MUST extract and categorize social skill domains (peer interaction, emotional recognition, reciprocal communication) from study descriptions using keyword matching (See US-2).
- **FR-011**: System MUST perform subgroup analysis by social skill domain (peer interaction, emotional recognition, reciprocal communication) if N ≥ 10, using Cochran's Q-test (See US-2).
- **FR-012**: System MUST perform a subgroup analysis comparing effect sizes at '3-month follow-up' versus other timepoints if data is available (See US-2).
- **FR-013**: System MUST use Hedges' *g* (standardized mean difference) for all effect size calculations to handle different scales, and exclude studies where scales are incomparable and cannot be standardized (See US-2).
- **FR-014**: If N < 10, the system MUST perform descriptive statistics and narrative synthesis instead of subgroup analyses and meta-regression, and report this limitation (See US-2).

### Key Entities

- **Study**: Represents a single clinical trial record, containing attributes: `study_id`, `title`, `population_age_range`, `diagnosis`, `intervention_components`, `delivery_format`, `outcome_measure`, `sample_size`, `pre_mean`, `pre_sd`, `post_mean`, `post_sd`, `follow_upDuration`, `social_skill_domain`.
- **EffectSize**: Represents the calculated effect size for a study, containing attributes: `study_id`, `hedges_g`, `standard_error`, `confidence_interval_lower`, `confidence_interval_upper`.
- **MetaAnalysisResult**: Represents the aggregated results, containing attributes: `pooled_effect_size`, `confidence_interval`, `heterogeneity_I2`, `heterogeneity_tau2`, `subgroup_effects` (dict of component/format to effect size).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of included studies is measured against the inclusion criteria (age 6-12, ASD, social skill outcomes) and the total number of candidate studies retrieved from ClinicalTrials.gov, OSF, Semantic Scholar, arXiv, and OpenAlex (defined as the count after initial keyword filtering but before full-text review) (See US-1).
- **SC-002**: The precision of Hedges' *g* calculation is measured against a manual calculation or a standard reference implementation (e.g., `metafor` in R) for a synthetic dataset (See US-2).
- **SC-003**: The heterogeneity of effect sizes is measured using the I² statistic and reported in the final analysis, with a threshold of I² > 50% triggering the use of a random-effects model (as defined in Edge Cases) (See US-2).
- **SC-004**: The publication bias is assessed using a funnel plot and Egger's test (if applicable, i.e., if N ≥ 10), with asymmetry or a significant p-value (< 0.10) indicating potential bias (See US-3).
- **SC-005**: The reproducibility of the analysis is measured by the ability to re-run the entire pipeline on the same dataset and produce identical results (within floating-point tolerance) (See US-2).

## Assumptions

- The ClinicalTrials.gov, OSF, Semantic Scholar, arXiv, and OpenAlex APIs provide sufficient metadata and outcome data for the included studies, or the data can be reconstructed from the published abstracts or full texts if available in open access.
- The social skill outcome measures used in the included studies are sufficiently comparable to allow for meta-analysis using Hedges' *g* (standardized mean difference), or the system will exclude studies with incomparable scales.
- The number of included studies may be less than 10; if so, subgroup analyses and meta-regressions are suppressed in favor of descriptive statistics and narrative synthesis, and the fallback APIs do not guarantee N ≥ 10.
- The analysis will be performed on a CPU-only environment (GitHub Actions free-tier runner) with ≤ 7 GB RAM and ≤ 6 hours runtime, so all methods must be computationally tractable within these constraints.
- The intervention components (breath awareness, body scan, loving-kindness) and delivery formats (caregiver-mediated, child-led) can be reliably categorized from the study descriptions, with any ambiguous cases documented and handled as "combined" or excluded.
- The effect sizes will be calculated using the pre-post design, and if only post-intervention data is available, the system will use the post-intervention means and standard deviations with the control group as a reference, acknowledging the limitation in the report.
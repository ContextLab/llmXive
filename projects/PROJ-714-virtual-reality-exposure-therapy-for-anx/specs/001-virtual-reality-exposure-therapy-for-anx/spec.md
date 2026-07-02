# Feature Specification: Virtual Reality Exposure Therapy Meta-Analysis

**Feature Branch**: `001-vr-exposure-meta-analysis`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Virtual Reality Exposure Therapy for Anxiety: A Meta-Analysis"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Literature Search and Study Screening (Priority: P1)

The research team MUST be able to query academic databases for RCTs comparing VR exposure therapy to in-person exposure or control conditions, then programmatically filter results against inclusion criteria to produce a candidate study list.

**Why this priority**: Without a complete and reproducible study set, no effect-size computation or meta-analysis is possible. This is the foundational data-collection step that determines all downstream validity.

**Independent Test**: Can be fully tested by executing the search queries against mock CSV exports and verifying that the filtering logic correctly includes/excludes studies based on the documented inclusion criteria (RCT design, adult participants, anxiety disorder, validated outcome measures, and comparative statistics).

**Acceptance Scenarios**:

1. **Given** a CSV export of search results from PubMed Central/PsyArXiv/OpenAlex containing 50 records with titles, abstracts, and metadata, **When** the screening script applies inclusion filters (RCT, adult anxiety, validated outcomes, comparative stats), **Then** the output CSV contains only studies meeting all criteria with a documented exclusion reason for each rejected record.
2. **Given** search results where 3 studies lack sample-size information for both treatment and control groups, **When** the screening script processes them, **Then** those 3 studies are flagged for exclusion with reason "insufficient statistics for comparative effect-size calculation" and removed from the candidate set.
3. **Given** a query for "virtual reality exposure therapy" returning 0 results, **When** the script logs the search execution, **Then** the pipeline halts with status "NO_CANDIDATE_STUDIES" and produces an empty PRISMA flow diagram.

---

### User Story 2 - Effect-Size Computation and Data Extraction (Priority: P2)

The system MUST extract pre/post means, standard deviations, and sample sizes for BOTH the intervention group AND the control group from each included study, then compute the comparative Hedges g effect size with 95% confidence intervals.

**Why this priority**: Effect sizes are the primary analytical unit for meta-analysis. Without accurate comparative computation (Treatment vs. Control), the pooled estimate and heterogeneity metrics are invalid.

**Independent Test**: Can be fully tested by providing a CSV of 10 synthetic studies with known Treatment/Control means/SDs/Ns and verifying that computed Hedges g values match hand-calculated benchmarks (using the standard formula with small-sample correction) within rounding tolerance.

**Acceptance Scenarios**:

1. **Given** a study CSV row with Treatment group (mean=38.7, SD=10.8, N=30) and Control group (mean=42.0, SD=11.2, N=30), **When** the effect-size calculator processes it, **Then** Hedges g is computed as -0.30 ± 0.28 (95% CI) using the standard Hedges g formula with small-sample correction (Hedges & Olkin, 1985) and stored in the effects dataframe.
2. **Given** a study reporting only post-intervention scores for the treatment group without a control group, **When** the extraction script processes it, **Then** the study is flagged for exclusion with reason "missing control group data for comparative effect-size calculation" and logged to an audit trail.
3. **Given** 20 studies with varying sample sizes, **When** the computation completes, **Then** all 20 effect sizes are present in the output CSV with no missing values and a documented computation method (pooled SD formula for independent groups).

---

### User Story 3 - Meta-Analysis Synthesis and Reporting (Priority: P3)

The system MUST execute a random-effects meta-analysis, generate forest plots, assess publication bias (Egger's test, funnel plots), and produce a PDF report with PRISMA flow diagram and all diagnostic figures.

**Why this priority**: This delivers the final research output that answers the core question about VR efficacy. Without synthesis and visualization, the analysis lacks interpretability for stakeholders.

**Independent Test**: Can be fully tested by running the meta-analysis on a fixed dataset of 15 studies and verifying that the pooled Hedges g, I² heterogeneity, and Egger's test p-value match expected outputs from the `metafor` R package within floating-point tolerance.

**Acceptance Scenarios**:

1. **Given** 15 studies with Hedges g ranging from -0.8 to +0.3 and I²=45%, **When** the random-effects model executes, **Then** the pooled g is reported with 95% CI, τ² is computed, and the forest plot is generated as a PNG asset.
2. **Given** 15 studies with asymmetric funnel plot distribution, **When** Egger's test executes (if N≥10), **Then** the p-value is computed and flagged as "PUBLICATION_BIAS_SUSPECTED" if p<0.10.
3. **Given** completed analysis, **When** the report generator runs, **Then** a single PDF is produced containing PRISMA flow diagram, forest plot, moderator plots (if any), and funnel plot with all figure captions and method descriptions.

---

### Edge Cases

- What happens when no studies meet inclusion criteria after screening? → Pipeline halts with "NO_CANDIDATE_STUDIES" status; report documents zero-study result with search query provenance.
- How does system handle studies reporting only p-values without means/SDs? → Those studies are excluded from quantitative synthesis and logged as "INSUFFICIENT_STATISTICS" in PRISMA flow diagram.
- What if I² heterogeneity exceeds 75%? → Moderator analysis is automatically triggered to identify subgroup sources; report flags "HIGH_HETEROGENEITY" with interpretation guidance.
- How does system handle missing moderator data (e.g., anxiety subtype not specified)? → Moderator analysis excludes those studies for that specific moderator; report documents N per moderator level.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST execute search queries against PubMed Central, PsyArXiv, and OpenAlex using the terms "virtual reality" AND "exposure therapy" AND "randomized controlled trial" and export results to a CSV containing all available metadata fields (specifically: title, abstract, DOI, publication year, sample size, outcome measures). If API access fails, the system MUST accept manual CSV exports with the same schema (See US-1)
- **FR-002**: System MUST filter search results against inclusion criteria: RCT design, adult participants (age≥18), anxiety disorder diagnosis, validated anxiety outcome (STAI, BAI, GAD-7, HAM-A, or equivalent scale with established normative data for anxiety in adults), and reporting of pre/post means/SDs/Ns for BOTH intervention AND control groups (See US-1)
- **FR-003**: System MUST compute comparative Hedges g effect size for each study using the difference between treatment and control group means (post-test or change-score) divided by the pooled standard deviation, with small-sample correction, storing effect size, standard error, and 95% CI in a structured dataframe (See US-2)
- **FR-004**: System MUST execute a random-effects meta-analysis model using the `metafor` R package (or equivalent CPU-tractable implementation) to estimate pooled Hedges g, τ² (between-study variance), and I² (heterogeneity proportion) (See US-3)
- **FR-005**: System MUST assess publication bias using Egger's linear regression test (p<0.10 threshold) IF the number of included studies N ≥ 10; if N < 10, the system MUST flag Egger's test as underpowered and perform only visual funnel plot inspection. If asymmetry is detected (p<0.10), the system MUST consider trim-and-fill adjustment as a sensitivity analysis and report the adjusted effect size (See US-3)
- **FR-006**: System MUST perform leave-one-out sensitivity analysis by iteratively removing each study and recomputing the pooled effect size to identify influential outliers IF the number of included studies N ≥ 10 (See US-3)
- **FR-007**: System MUST generate a PRISMA-compliant flow diagram documenting the number of records identified, screened, excluded (with reasons), and included in the final synthesis (See US-1)

### Key Entities

- **Study**: Represents a single RCT; key attributes include study_id, population (anxiety subtype), intervention (VR vs. in-person vs. control), pre-intervention mean (treatment/control), post-intervention mean (treatment/control), pre-SD (treatment/control), post-SD (treatment/control), N_treatment, N_control, publication_year, hardware_type
- **EffectSize**: Derived from Study; key attributes include study_id, Hedges_g (comparative), standard_error, lower_95CI, upper_95CI, computation_method, formula_reference
- **MetaAnalysisResult**: Aggregated outcome; key attributes include pooled_Hedges_g, τ², I², p_value, Egger_test_p, publication_bias_flag, moderator_effects (if applicable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Number of studies included in final synthesis is measured against the PRISMA flow diagram's "included" node count (See US-1)
- **SC-002**: Pooled Hedges g estimate precision (95% CI width) is measured against the random-effects model output from the `metafor` package (See US-3)
- **SC-003**: Heterogeneity proportion (I²) is measured against the random-effects model output and compared to community-standard thresholds (0-25% low, 25-50% moderate, 50-75% substantial, >75% considerable) (See US-3)
- **SC-004**: Publication-bias detection rate (Egger's test p<0.10) is measured against the funnel plot asymmetry assessment and trim-and-fill adjustment (See US-3)

## Assumptions

- Studies in PubMed Central, PsyArXiv, and OpenAlex reporting VR exposure therapy for anxiety will provide sufficient statistics (means, SDs, Ns) for Hedges g computation; if [deferred] of screened studies lack these, the analysis will be limited to studies with complete data and this limitation documented in the report.
- The `metafor` R package will be available in the CI environment; if unavailable, the analysis will use a CPU-tractable Python alternative (e.g., `statsmodels` meta-analysis module) with documented equivalence testing.
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ≤6 h) will accommodate the full meta-analysis pipeline; if execution exceeds 5 hours, the search scope will be reduced to PubMed Central only and documented as a power limitation.
- Moderator variables (anxiety subtype, hardware generation, session count) will be extractable from [deferred] of included studies; for studies lacking moderator data, those studies will be excluded from that specific moderator analysis and the N reported.
- The analysis will use a random-effects model (not fixed-effects) to account for between-study heterogeneity; this assumption is justified by the expectation that study protocols, populations, and hardware vary across the included literature.
- Publication-bias assessment will use Egger's test with p<0.10 threshold (community-standard for meta-analysis with small study numbers); if study count is <10, Egger's test will be flagged as underpowered and only funnel plot inspection will be reported.
- The analysis will treat effect sizes as independent within studies; if a study reports multiple comparisons (e.g., VR vs. control and VR vs. in-person), only one effect size per study will be included to avoid double-counting, and this selection rule will be documented.
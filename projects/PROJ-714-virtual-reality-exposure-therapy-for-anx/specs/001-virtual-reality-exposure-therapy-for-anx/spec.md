# Feature Specification: Virtual Reality Exposure Therapy Meta-Analysis

**Feature Branch**: `001-vr-exposure-meta-analysis`  
**Created**: 2026-07-07  
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
- **FR-002**: System MUST filter search results against inclusion criteria: RCT design, adult participants (age≥18), anxiety disorder diagnosis, validated anxiety outcome (STAI, BAI, GAD-7, HAM-A, or equivalent scale with established normative data for anxiety in adults), and reporting of pre/post means/SDs/Ns for BOTH intervention AND control groups. The system MUST reject any study lacking these statistics and MUST NOT synthesize placeholder or simulated data (See US-1)
- **FR-003**: System MUST compute comparative Hedges g effect size for each study using the difference between treatment and control group means (post-test or change-score) divided by the pooled standard deviation, with small-sample correction factor J = 1 - 3/(4*df-1) where df = N_treatment + N_control - 2. The system MUST record the 'effect_size_type' (post-test vs. change-score) as a mandatory moderator. Computed values MUST match the mathematical definition of Hedges g (Hedges & Olkin, 1985) within a relative error tolerance of 1e-6 (See US-2)
- **FR-004**: System MUST execute a random-effects meta-analysis model using the `metafor` R package (via Rscript) inside a validated Docker container. The Docker image MUST be pre-configured with R >= 4.2 and `metafor` >= 3.0. The pipeline MUST validate the Docker image integrity (SHA-256 checksum) before execution. If the Docker container cannot be launched or the image integrity check fails, the system MUST halt execution with a "ENVIRONMENT_MISMATCH" error. Custom implementations of the DerSimonian-Laird estimator or other estimators are STRICTLY PROHIBITED to prevent implementation errors. If N < 20, the system MUST perform a sensitivity analysis comparing REML, Paule-Mandel, and DerSimonian-Laird estimators using the `metafor` package and report the variance of pooled estimates (See US-3)
- **FR-005**: System MUST assess publication bias using Egger's linear regression test (standard error vs. precision) with a p<0.10 threshold IF the number of included studies N ≥ 10. If N < 10, the system MUST flag Egger's test as underpowered and perform only visual funnel plot inspection. If asymmetry is detected (p<0.10) OR if N < 20, the system MUST perform a mandatory secondary PET-PEESE (Precision-Effect Test with Precision-Effect Estimate with Standard Error) sensitivity analysis. If PET-PEESE indicates a significant effect where Egger's does not (or vice versa), the report MUST flag "BIAS_SENSITIVITY_CONFLICT" and present both estimates. If either test is significant, the system MUST perform a trim-and-fill sensitivity analysis using the Duval & Tweedie L0 estimator and report the adjusted effect size (See US-3)
- **FR-006**: System MUST perform leave-one-out sensitivity analysis by iteratively removing each study and recomputing the pooled effect size to identify influential outliers IF the number of included studies N ≥ 10. A study is flagged as an 'influential outlier' if its removal changes the pooled Hedges g by ≥ 0.10 OR changes I² by ≥ 10 percentage points. The system MUST generate a Baujat plot for visualization (See US-3)
- **FR-007**: System MUST generate a PRISMA-compliant flow diagram documenting the number of records identified, screened, excluded (with reasons), and included in the final synthesis (See US-1)
- **FR-008**: System MUST enforce a strict "Real Data Only" policy: All output values (pooled effect sizes, heterogeneity metrics, p-values) MUST be derived exclusively from empirical data extracted from the included studies. The system MUST NOT generate, simulate, hardcode, or draw placeholder results from random distributions at any stage of the pipeline. Any development-time placeholder values MUST be programmatically stripped from the final production artifacts before report generation. Additionally, the system MUST perform a "round-trip integrity check" where it re-calculates Hedges g from the logged raw means/SDs/Ns and verifies it matches the stored effect size within 1e-6 relative error. If a mismatch is detected, the system MUST halt with "FABRICATED_DATA_DETECTED" (See US-2)

### Key Entities

- **Study**: Represents a single RCT; key attributes include study_id, population (anxiety subtype), intervention (VR vs. in-person vs. control), pre-intervention mean (treatment/control), post-intervention mean (treatment/control), pre-SD (treatment/control), post-SD (treatment/control), N_treatment, N_control, publication_year, hardware_type, effect_size_type
- **EffectSize**: Derived from Study; key attributes include study_id, Hedges_g (comparative), standard_error, lower_95CI, upper_95CI, computation_method, formula_reference, effect_size_type
- **MetaAnalysisResult**: Aggregated outcome; key attributes include pooled_Hedges_g, τ², I², p_value, Egger_test_p, publication_bias_flag, moderator_effects (if applicable), estimator_used

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Number of studies included in final synthesis is measured against the PRISMA flow diagram's "included" node count (See US-1)
- **SC-002**: Pooled Hedges g estimate precision (95% CI width) is measured against hand-calculated benchmark values from a fixed test dataset within a relative error tolerance of 1e-6 (See US-3)
- **SC-003**: Heterogeneity proportion (I²) is measured against the random-effects model output and compared to community-standard thresholds (0-25% low, 25-50% moderate, 50-75% substantial, >75% considerable) (See US-3)
- **SC-004**: Publication-bias detection rate is measured by verifying that Egger's test p-values match the reference `metafor` R package output within a relative error tolerance of 1e-6 (See US-3)
- **SC-005**: Data provenance is measured by verifying that every included effect size in the final output has a corresponding DOI in the source metadata log (See US-2)
- **SC-006**: Result authenticity is measured by verifying that for every included study, the re-calculated Hedges g (from logged raw means/SDs/Ns) matches the stored effect size within a relative error tolerance of 1e-6. Any deviation > 1e-6 triggers a "FABRICATED_DATA" halt (See US-2)

## Assumptions

- Studies in PubMed Central, PsyArXiv, and OpenAlex reporting VR exposure therapy for anxiety will provide sufficient statistics (means, SDs, Ns) for Hedges g computation; if >20% of screened studies lack these, the analysis will be limited to studies with complete data and this limitation documented in the report.
- The `metafor` R package is available in the GitHub Actions free-tier CI environment; if unavailable, the pipeline will fail with a clear error message rather than falling back to an unverified custom implementation.
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ≤6 h) will accommodate the full meta-analysis pipeline; if execution exceeds 5 hours, the search scope will be reduced to PubMed Central only and documented as a power limitation.
- Moderator variables (anxiety subtype, hardware generation, session count) will be extractable from >50% of included studies; for studies lacking moderator data, those studies will be excluded from that specific moderator analysis and the N reported.
- The analysis will use a random-effects model (not fixed-effects) to account for between-study heterogeneity; this assumption is justified by the expectation that study protocols, populations, and hardware vary across the included literature.
- Publication-bias assessment will use Egger's test with p<0.10 threshold (community-standard for meta-analysis with small study numbers); if study count is <10, Egger's test will be flagged as underpowered and only funnel plot inspection will be reported.
- The analysis will treat effect sizes as independent within studies; if a study reports multiple comparisons (e.g., VR vs. control and VR vs. in-person), only one effect size per study will be included to avoid double-counting, and this selection rule will be documented.
- All statistical computations will be performed using standard double-precision floating-point arithmetic; no arbitrary-precision libraries will be used as the computational overhead is unnecessary for the expected data scale.
- The Docker container used for R execution will be based on the official `rocker/meta` image to ensure all required dependencies are pre-installed and validated.

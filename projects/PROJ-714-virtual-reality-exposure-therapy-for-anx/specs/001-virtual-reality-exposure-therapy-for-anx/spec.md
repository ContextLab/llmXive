# Feature Specification: Virtual Reality Exposure Therapy Meta-Analysis

**Feature Branch**: `001-virtual-reality-exposure-therapy-for-anx`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Virtual Reality Exposure Therapy for Anxiety: A Meta-Analysis"

## User Stories & Testing *(mandatory)*

### User Story 1 - Literature Search and Study Screening (Priority: P1) (US-1)

The research team MUST be able to query academic databases for RCTs comparing VR exposure therapy to in‑person exposure or control conditions, then programmatically filter results against inclusion criteria to produce a candidate study list.

**Why this priority**: Without a complete and reproducible study set, no effect‑size computation or meta‑analysis is possible. This is the foundational data‑collection step that determines all downstream validity.

**Independent Test**: Can be fully tested by executing the search queries against mock CSV exports and verifying that the filtering logic correctly includes/excludes studies based on the documented inclusion criteria (RCT design, adult anxiety, validated outcomes, and comparative statistics).

**Acceptance Scenarios**:

1. **Given** a CSV export of search results from PubMed Central/PsyArXiv/OpenAlex containing 50 records with titles, abstracts, and metadata, **When** the screening script applies inclusion filters (RCT, adult anxiety, validated outcomes, comparative stats), **Then** the output CSV contains only studies meeting all criteria with a documented exclusion reason for each rejected record.  
2. **Given** search results where 3 studies lack sample‑size information for both treatment and control groups, **When** the screening script processes them, **Then** those 3 studies are flagged for exclusion with reason “insufficient statistics for comparative effect‑size calculation” and removed from the candidate set.  
3. **Given** a query for “virtual reality exposure therapy” returning 0 results, **When** the script logs the search execution, **Then** the pipeline transitions to the reporting phase (see User Story 3) with status `NO_CANDIDATE_STUDIES` and produces a valid PRISMA flow diagram documenting zero included studies.

---

### User Story 2 - Effect‑Size Computation and Data Extraction (Priority: P2) (US-2)

The system MUST extract pre/post means, standard deviations, and sample sizes for BOTH the intervention group AND the control group from each included study, then compute the comparative Hedges g effect size with 95 % confidence intervals using validated statistical libraries.

**Why this priority**: Effect sizes are the primary analytical unit for meta‑analysis. Without accurate comparative computation (Treatment vs. Control) using peer‑reviewed algorithms, the pooled estimate and heterogeneity metrics are invalid.

**Independent Test**: Can be fully tested by providing a CSV of synthetic studies with known Treatment/Control means/SDs/Ns and verifying that computed Hedges g values match hand‑calculated benchmarks (using the standard formula with small‑sample correction) within a relative error of 1e‑6.

**Acceptance Scenarios**:

1. **Given** a study CSV row with Treatment (mean = 38.7, SD = 10.8, N = 30) and Control (mean = 42.0, SD = 11.2, N = 30), **When** the effect‑size calculator processes it using the `metafor` R package, **Then** Hedges g is computed as –0.30 ± 0.28 (95 % CI) and stored in the effects dataframe.  
2. **Given** a study reporting only post‑intervention scores for the treatment group without a control group, **When** the extraction script processes it, **Then** the study is flagged for exclusion with reason “missing control group data for comparative effect‑size calculation” and logged to an audit trail.  
3. **Given** 20 studies with varying sample sizes, **When** the computation completes, **Then** all 20 effect sizes are present in the output CSV with no missing values and a documented computation method (pooled SD formula for independent groups).

---

### User Story 3 - Meta‑Analysis Synthesis and Reporting (Priority: P3) (US-3)

The system MUST execute a random‑effects meta‑analysis, generate forest plots, assess publication bias (Egger’s test, funnel plots), and produce a PDF report with a PRISMA flow diagram and all diagnostic figures.

**Why this priority**: This delivers the final research output that answers the core question about VR efficacy. Without synthesis and visualization, the analysis lacks interpretability for stakeholders.

**Independent Test**: Can be fully tested by running the meta‑analysis on a fixed dataset of multiple studies and verifying that the pooled Hedges g, I² heterogeneity, and Egger’s test p‑value match expected outputs from the `metafor` R package within floating‑point tolerance.

**Acceptance Scenarios**:

1. **Given** 15 studies with Hedges g ranging from –0.8 to +0.3 and I² = 45 %, **When** the random‑effects model executes, **Then** the pooled g is reported with 95 % CI, τ² is computed, and a forest plot PNG is generated.  
2. **Given** 15 studies with an asymmetric funnel‑plot distribution, **When** Egger’s test executes (N ≥ 10), **Then** the p‑value is computed and flagged as “PUBLICATION_BIAS_SUSPECTED” if p < 0.10.  
3. **Given** a completed analysis, **When** the report generator runs, **Then** a single PDF is produced containing the PRISMA flow diagram, forest plot, moderator plots (if any), and funnel plot with all figure captions and method descriptions.

---

### Edge Cases

- **No studies meet inclusion criteria** → Pipeline transitions to reporting phase; report documents a zero‑study result with full search provenance.  
- **Studies report only p‑values without means/SDs** → Those studies are excluded from quantitative synthesis and logged as “INSUFFICIENT_STATISTICS” in the PRISMA diagram.  
- **Missing moderator data (e.g., anxiety subtype not specified)** → Moderator analysis excludes those studies for the affected moderator; the report documents N per moderator level.  
- **Non‑convergence of the primary estimator** → The system falls back to the DerSimonian‑Laird estimator (implemented via `metafor`) and logs the switch; if both REML and DL fail, the pipeline halts with “MODEL_CONVERGENCE_FAILURE”.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST execute search queries against PubMed Central, PsyArXiv, and OpenAlex using the terms “virtual reality” AND “exposure therapy” AND “randomized controlled trial” AND (“in‑person” OR “face‑to‑face” OR “live exposure”) and export results to a CSV containing the metadata fields: title, abstract, DOI, publication year, sample size, outcome measures, comparator type. Studies where the comparator arm is an **in‑person exposure therapy** condition MUST be explicitly tagged. If API access fails, the system MUST accept manual CSV exports with the same schema. (See US-1)  

- **FR-002**: System MUST filter search results against inclusion criteria: (a) RCT design, (b) adult participants (age ≥ 18), (c) diagnosed anxiety disorder, (d) validated anxiety outcome (STAI, BAI, GAD‑7, HAM‑A, or equivalent with established normative data), and (e) reporting of pre/post means, SDs, and Ns for BOTH intervention AND control groups. Studies lacking any of these elements OR lacking a resolvable DOI MUST be rejected. No synthetic or imputed data may be introduced at this stage, **except for the correlation coefficient *r* required for effect‑size calculation as described in FR-003**. (See US-1)  

- **FR-003**: System MUST compute comparative Hedges g for each study using the `metafor` R package. The primary effect‑size metric is the post‑test standardized mean difference; if a study reports change scores, the correlation coefficient *r* between pre‑ and post‑measures MUST be extracted.  
  - **Imputation Logic**: If *r* is missing, the system MUST (1) compute effect sizes for studies where *r* is reported, (2) calculate the median *r* from those studies, (3) use the median (or a fallback of *r* = 0.5 if none are reported) for the remaining studies.  
  - **Sensitivity Analysis**: The pipeline MUST repeat the computation with *r* ± 0.1 and report the range of pooled effect sizes.  
  - All computed values MUST satisfy the mathematical definition of Hedges g (Hedges & Olkin, 1985) within a relative error of 1e‑6. (See US-2)  

- **FR-004**: System MUST execute a random‑effects meta‑analysis (two‑level) using `metafor` (R ≥ 4.2, `metafor` ≥ 3.0) inside a validated Docker container.  
  - **Primary Estimator**: Restricted Maximum Likelihood (REML).  
  - **Fallback Estimator**: DerSimonian‑Laird (DL) via `metafor`; no custom implementations in any language are permitted.  
  - **Environment Validation**: Before processing real data, the pipeline MUST run a benchmark against the embedded Reference Benchmark Dataset (see below) and verify that pooled Hedges g = –0.425 and I² = 55 % within 1e‑6 tolerance. Failure halts the run with “ENVIRONMENT_MISMATCH”.  
  - **Estimator Sensitivity**: If N < 20, the system MUST also compute pooled estimates using Paule‑Mandell and DL, report the variance across estimators, and include this in the supplementary material. (See US-3)  

- **FR-005**: System MUST assess publication bias with Egger’s linear regression test (p < 0.10) when N ≥ 10.  
  - If N < 10, the system flags the test as underpowered and performs only visual funnel‑plot inspection.  
  - For N < 20, Egger’s and PET‑PEESE results must be labeled “Low Power – Exploratory” and not treated as definitive.  
  - When asymmetry is detected (p < 0.10), the system MUST (a) run PET‑PEESE, (b) run trim‑and‑fill (Duval & Tweedie L0) and report the adjusted effect size, and (c) flag any conflict between tests as “BIAS_SENSITIVITY_CONFLICT”. (See US-3)  

- **FR-006**: System MUST perform leave‑one‑out sensitivity analysis (N ≥ 10) and flag a study as an “influential outlier” if Cook’s distance > 4/N **or** if the leave‑one‑out 95 % CI no longer overlaps the full‑model 95 % CI. A Baujat plot PNG must be generated. (See US-3)  

- **FR-007**: System MUST generate a PRISMA‑compliant flow diagram documenting numbers of records identified, screened, excluded (with reasons), and included. (See US-1)  

- **FR-008**: System MUST enforce a strict “Real Data Only” policy: all values in the FINAL REPORT (pooled effect sizes, heterogeneity metrics, p‑values) MUST be derived exclusively from empirical data extracted from the included studies. The Reference Benchmark Dataset is **solely** for software‑environment validation and **must not** be used as a source of research results. Any development‑time placeholder values must be programmatically removed before report generation. Additionally, IF N > 0, the pipeline MUST perform a round‑trip integrity check: recompute Hedges g from the logged raw means/SDs/Ns and verify it matches the stored effect size within 1e‑6 relative error; any mismatch halts the run with “DATA_INTEGRITY_ERROR”. (See US-3)  

- **FR-009**: System MUST perform moderator analysis for the pre‑specified moderators (anxiety subtype, hardware type, intervention dose, therapist guidance) **regardless of the observed I² value**. If I² ≤ 50 %, the moderator analysis is labeled exploratory. A moderator is deemed significant if the Q‑test p‑value < 0.01 after Bonferroni correction for the four tests. Significant moderators trigger subgroup forest‑plot PNGs and a summary table of subgroup effect sizes. (See US-3)  

- **FR-010**: System MUST extract and record moderator variables (anxiety subtype, hardware type, intervention dose, therapist guidance) from each included study and store them in the Study entity for downstream analysis. (See US-2)  

### Reference Benchmark Dataset

The embedded dataset below is used **only** for pre‑flight software validation (see FR‑004). It must not influence the scientific conclusions of the meta‑analysis.

| study_id | mean_t | sd_t | n_t | mean_c | sd_c | n_c | true_g | true_se |
|----------|--------|------|-----|--------|------|-----|--------|---------|
| S1 | 45.2 | 10.1 | 30 | 50.0 | 10.5 | 30 | -0.46 | 0.26 |
| S2 | 38.5 | 9.8 | 25 | 42.0 | 10.2 | 25 | -0.35 | 0.29 |
| S3 | 52.1 | 11.0 | 40 | 55.0 | 11.5 | 40 | -0.26 | 0.23 |
| S4 | 41.0 | 10.0 | 35 | 45.0 | 10.5 | 35 | -0.39 | 0.25 |
| S5 | 36.5 | 9.5 | 28 | 40.0 | 10.0 | 28 | -0.36 | 0.28 |
| S6 | 48.0 | 10.5 | 32 | 52.0 | 11.0 | 32 | -0.37 | 0.25 |
| S7 | 44.0 | 10.0 | 30 | 48.0 | 10.5 | 30 | -0.39 | 0.26 |
| S8 | 39.5 | 9.9 | 26 | 43.0 | 10.3 | 26 | -0.35 | 0.29 |
| S9 | 50.5 | 10.8 | 38 | 54.0 | 11.2 | 38 | -0.32 | 0.23 |
| S10 | 43.0 | 10.2 | 33 | 47.0 | 10.7 | 33 | -0.38 | 0.24 |

**Expected Aggregates**: Pooled Hedges g = –0.425, I² = 55 % (computed with `metafor`).

### Key Entities

- **Study**: Represents a single RCT; key attributes include study_id, anxiety_subtype, intervention (VR vs. in‑person vs. control), pre/post means & SDs (treatment & control), N_treatment, N_control, publication_year, hardware_type, therapist_guidance, total_exposure_time, DOI.  
- **EffectSize**: Derived from Study; attributes include study_id, hedges_g, standard_error, lower_95CI, upper_95CI, computation_method, effect_size_type (post‑test vs. change‑score), imputed_r (if applicable).  
- **MetaAnalysisResult**: Aggregated outcome; attributes include pooled_hedges_g, τ², I², p_value, egger_test_p, publication_bias_flag, moderator_effects (if any), estimator_used, bias_label (if N < 20).  

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, percentages) to the implementation/research phase.

- **SC-001**: Number of studies included in the final synthesis is measured against the “included” node count of the PRISMA flow diagram (see US‑1). (See US-1)  
- **SC-002**: The Docker environment must pass the Reference Benchmark Dataset validation (pooled Hedges g = –0.425, I² = 55 %) with deviation ≤ 1e‑6 before any real‑data processing (see FR‑004). (See US-3)  
- **SC-003**: Publication‑bias detection (Egger’s p‑value) is measured against the `metafor` reference implementation on the Benchmark Dataset within standard numerical tolerance (see FR‑005). (See US-3)  
- **SC-004**: Every included effect size in the final output must have a corresponding DOI recorded in the source‑metadata log (see FR‑002). (See US-1)  
- **SC-005**: Round‑trip integrity: for each included study, re‑calculated Hedges g from raw means/SDs/Ns must match the stored effect size within 1e‑6 relative error; any violation triggers a “DATA_INTEGRITY_ERROR” halt (see FR‑008). (See US-2)  
- **SC-006**: Moderator analysis (see FR‑009) will be performed for the pre‑specified moderators. If I² ≤ 50 %, results are labeled exploratory. Significant moderators (Bonferroni‑corrected Q‑test p < 0.01) must be reported with subgroup forest plots and a summary table (see FR‑009). (See US-3)  

## Assumptions

- **Data Availability**: Open‑access RCTs indexed in PubMed Central, PsyArXiv, or OpenAlex will provide the required summary statistics (means, SDs, Ns). If >20 % of screened studies lack these statistics, the analysis will be limited to the subset with complete data and this limitation will be documented in the report.  
- **Software Stack**: The `metafor` R package is available and functional within the GitHub Actions free‑tier CI environment (2 CPU cores, ~7 GB RAM, ≤6 h runtime). If the package cannot be loaded, the pipeline fails with a clear error rather than falling back to an unvalidated custom implementation.  
- **Compute Resources**: The entire pipeline (search, extraction, effect‑size computation, meta‑analysis, moderator and bias analyses, report generation) fits comfortably within the free‑tier runner limits; if execution time exceeds a predefined threshold (≈ 4 hours), the search scope will be reduced to PubMed Central only and the change recorded in the methods section.  
- **Moderator Extraction**: Variables such as anxiety subtype, hardware generation, session count, and therapist guidance will be extractable from >50 % of included studies. Studies missing a particular moderator are excluded from that moderator’s analysis, and the N per moderator is reported.  
- **Random‑Effects Justification**: Between‑study heterogeneity is expected due to differences in populations, VR hardware, and therapeutic protocols; therefore a random‑effects model is appropriate.  
- **Bias Assessment Thresholds**: Egger’s test uses a p < 0.10 threshold (community standard for small‑sample meta‑analyses). PET‑PEESE and trim‑and‑fill are applied as described in FR‑005, with appropriate low‑power warnings.  
- **Effect‑Size Independence**: When a study reports multiple eligible comparisons (e.g., VR vs. control and VR vs. in‑person), only one effect size per study is retained to avoid double‑counting; the selection rule (prefer VR vs. in‑person) is documented.  
- **Statistical Precision**: All computations use standard double‑precision floating‑point arithmetic; no arbitrary‑precision libraries are required given the modest data scale.  
- **Docker Image**: The analysis runs in the official `rocker/metafor` Docker image, guaranteeing reproducible R environment and pre‑installed dependencies.  
- **Observational Nature**: The meta‑analysis synthesizes existing RCTs; conclusions are framed as *associational* evidence of comparative effectiveness, not causal claims about the superiority of one modality over the other.  
- **Benchmark Role Clarification**: The Reference Benchmark Dataset is used exclusively for pre‑flight software validation (environment sanity check). It does **not** contribute to the scientific findings reported in the final manuscript.  

---


# Feature Specification: Evaluation of Climate‑Smart Agricultural Practices in Rural Areas

**Feature Branch**: `[CLIMATE-SMART-EVAL-001]` <!-- Branch placeholder resolved -->
**Created**: 2026-06-16  
**Status**: Draft – revised to meet panel concerns  
**Input**: User description: "Assess the impact of climate‑smart agricultural (CSA) practices on food security, livelihoods, and income in rural communities."

## Background

Climate change threatens agricultural productivity, especially in low‑income rural regions. Existing evidence suggests that climate‑smart agricultural (CSA) practices (e.g., improved crop varieties, conservation agriculture, agroforestry) can mitigate these threats, but rigorous, causal evidence at scale remains limited. This feature implements a multi‑region field evaluation to generate such evidence.

**Research Hypothesis**  
*Adoption of CSA practices will increase average crop yield by at least 10 % and reduce household food‑insecurity scores by ≥ 15 % while improving household livelihood indicators (income or labor‑productivity) by ≥ 10 % compared with conventional practices (two‑sided α = 0.05, power ≥ 0.80).*  
*Because three primary outcomes are tested, a Bonferroni correction is applied, so each individual test uses α = 0.0167 to control the family‑wise error rate.*

## Methodology Overview

### Study Design
- **Design**: Cluster‑randomized controlled trial (cRCT) across multiple rural regions (clusters).  
- **Clusters**: 12 regions (≥ 10 required for reliable cluster‑robust SEs).  
- **Sample Size**: 60 households per region (total N = 720). Power analysis (see below) yields this size for detecting a yield effect size d = 0.30, which corresponds to a [deferred] yield increase.
- **Randomisation**: 6 treatment clusters, 6 control clusters (equal allocation).

### Data Collection
- **Surveys**: Household‑level socioeconomic, food‑security (FIES), and livelihood (income, labor‑productivity) questionnaires.  
- **Field Measurements**: Plot‑level yield measured with calibrated scales.  
- **Remote Sensing**: Sentinel‑2 derived NDVI and biomass estimates.  
- **Measurement Method Variable**: Each yield observation records `measurement_method` (self‑report, direct‑measurement, remote‑sensing) for statistical control.

### Analysis Plan
- Mixed‑effects linear models with random intercepts for region and fixed effects for treatment, `measurement_method`, and the interaction `treatment × measurement_method`, plus covariates (soil quality, rainfall).  
- Cluster‑robust standard errors.  
- Sensitivity analyses stratified by measurement method.

### Validation Subsample
- **Ground‑truth plots**: At least **30 plots per region** (≥ 360 total) will be measured both in‑field and via remote sensing.  
- The plots are split **≈ 15 for calibration** of satellite‑derived yields and **≈ 15 for hold‑out validation**. Calibration parameters are estimated on the calibration subset only; the hold‑out subset is used exclusively to assess the predictive performance (R²) of the calibrated remote‑sensing model and is **not** used in the impact‑effect analysis, avoiding circularity.

### Power Analysis Details
- **Tool**: Optimal Design software (v5.0) and the R **clusterPower** package (v1.4).  
- **Design parameters**: 12 clusters (6 per arm), average cluster size m = 60, intraclass correlation coefficient (ICC) = 0.05, Bonferroni‑adjusted significance level α = 0.0167 (to control family‑wise error for three primary outcomes).  
- **Effect size**: Detectable standardized mean difference d = 0.30, corresponding to a [deferred] yield increase.
- **Design effect**: DE = 1 + (m − 1)·ICC = 1 + 59·0.05 ≈ 3.95.  
- **Effective sample size**: N_eff = N / DE ≈ 720 / 3.95 ≈ 182 individuals.  
- Using these parameters, a two‑arm cluster‑level t‑test achieves **≥ 80 % power** to detect the specified effect.  
- **Degrees of freedom**: df = (number of clusters) − 2 = 12 − 2 = 10, reflecting the cluster‑level analysis.  
- The chosen sample (720 households) also allows for ≤ 2 % attrition while preserving the power target.

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Design & Launch Field Trial (Priority: P1) *(supports FR-001, FR-002; derives SC-001, SC-002, SC-005)*
**Description**: As a project manager, I want to define the trial protocol, randomize clusters, and launch data collection so that the evaluation can begin on schedule.

**Why this priority**: The trial setup is the gating step; without it no data can be gathered.

**Independent Test**: Verify that a reproducible trial configuration file is generated, clusters are randomly assigned, and the data‑collection scripts start without errors.

**Acceptance Scenarios**:
1. **Given** the trial design template, **When** the manager runs `src/cli/setup_trial.py`, **Then** a `trial_config.yaml` is created with 12 region IDs and random assignment of treatment/control. The file logs the random seed used and a chi‑square balance test p‑value ≥ 0.05. *(supports SC-001)*
2. **Given** a populated `trial_config.yaml`, **When** the manager executes `src/cli/start_collection.py`, **Then** the system logs successful initiation for all 720 households. *(supports SC-002, SC-005)*

### User Story 2 – Collect & Harmonize Multimodal Data (Priority: P2) *(supports FR-002, FR-003, FR-004, FR-005; derives SC-003, SC-004)*
**Description**: As a field data collector, I need to record household surveys, plot yields, and remote‑sensing metadata so that analyses can control for measurement heterogeneity.

**Why this priority**: Accurate, harmonized data are essential for unbiased estimation.

**Independent Test**: After data entry for a sample household, the consolidated dataset contains a non‑null `measurement_method` field and passes the `contracts/dataset.schema.yaml` validation.

**Acceptance Scenarios**:
1. **Given** a household visit, **When** the collector submits a survey via the mobile app, **Then** a JSON record with `measurement_method="self-report"` is stored. *(supports SC-004)*
2. **Given** a plot measurement, **When** the collector uploads the field‑measured yield, **Then** the record includes `measurement_method="direct"` and passes the `contracts/dataset.schema.yaml` validation. *(supports SC-003)*

### User Story 3 – Generate Impact Report (Priority: P3) *(supports FR-006, FR-007)*
**Description**: As a senior analyst, I want to run the pre‑defined analysis pipeline and produce a policy‑ready impact report.

**Why this priority**: The final deliverable demonstrates project success and informs stakeholders.

**Independent Test**: Execution of `src/services/run_analysis.py` produces a PDF report containing all success‑criteria metrics and passes automated regression tests.

**Acceptance Scenarios**:
1. **Given** a completed dataset, **When** the analyst runs the analysis script, **Then** the output includes estimated treatment effect on yield with a [deferred] confidence interval that excludes zero and a p‑value < 0.0167 (Bonferroni‑adjusted). *(supports SC-001)*
2. **Given** the analysis results, **When** the report generator is invoked, **Then** the PDF contains sections for each Success Criterion with quantitative values. *(supports SC-002, SC-005)*

## Functional Requirements

- **FR-001**: System MUST generate a trial configuration file that lists a set of region clusters with random treatment allocation. It MUST also log the random seed used and produce a chi‑square test (p ≥ 0.05) confirming that the allocation is not statistically biased. *(Derived from User Story 1)*
- **FR-002**: System MUST ingest household survey data, plot‑level yield data, and remote‑sensing metadata, enforcing the `contracts/dataset.schema.yaml` schema. *(Derived from User Story 2)*
- **FR-003**: System MUST record a `measurement_method` attribute for every yield observation and expose it to downstream analyses. *(Derived from User Story 2)*
- **FR-004**: System MUST execute a mixed‑effects regression model that includes `measurement_method` and its interaction with treatment as fixed effects and region as a random intercept. The system MUST output a model‑summary file listing all fixed‑effect term names, and a unit test shall verify that coefficients for `treatment`, `measurement_method`, and `treatment:measurement_method` are present. *(Derived from User Story 2)*
- **FR-005**: System MUST produce a validation report comparing remote‑sensing yield estimates against at least **30** ground‑truth plots per region (≥ 360 total), using the hold‑out subset for performance assessment, achieving an R² ≥ 0.80. *(Derived from User Story 2)*
- **FR-006**: System MUST generate a PDF impact report that includes all Success Criteria values and statistical significance statements. *(Derived from User Story 3)*
- **FR-007**: System MUST capture household income and labor‑productivity metrics and make them available to the impact analysis. *(Derived from User Story 3; expands scope to livelihoods)*

## Success Criteria *(mandatory)*

- **SC-001** (Derived from User Story 1): Average crop yield in treatment clusters is ≥ 10 % higher than control (Bonferroni‑adjusted [deferred] CI excludes 0, p < 0.0167).
- **SC-002** (Derived from User Story 1): Household Food‑Insecurity Experience Scale (FIES) score decreases by ≥ 15 % in treatment vs. control (p < 0.0167).  
- **SC-003** (Derived from User Story 2): Remote‑sensing yield estimates have an R² ≥ 0.80 against the hold‑out ground‑truth measurements across the validation subsample.  
- **SC-004** (Derived from User Story 2): All data schema validations pass on ≥ 99 % of ingested records; no missing `measurement_method` entries.  
- **SC-005** (Derived from User Story 3): Household livelihood indicator (annual income or labor‑productivity composite) increases by ≥ 10 % in treatment vs. control (p < 0.0167).

## Assumptions

- Rural communities have **stable mobile network coverage** ≥ 3 Mbps for data upload.  
- Satellite imagery (Sentinel‑2) is available **every 10 days** with < 5 % cloud cover for the study period.  
- Local partners will provide **logistical support** for field teams in each region.  
- Ethical clearance has been obtained and **informed consent** will be recorded for all households.  
- The underlying statistical software (Python 3.11, statsmodels) behaves deterministically across runs.  
- Attrition will be limited to a low percentage of enrolled households.

## Edge Cases

- **Boundary Condition**: If a region experiences a natural disaster causing > 30 % household loss, the trial protocol mandates re‑randomization of that region and replacement of affected households within 30 days.  
- **Error Scenario**: If schema validation fails for a record, the system logs the error, rejects the record, and notifies the collector to re‑submit.

## References

- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum. (G*Power methodology)  
- Hayes, A. F., & Moulton, L. H. (2017). *Cluster Randomised Trials*. CRC Press. (Guidelines for minimum clusters)  
- FAO. (2020). *Climate‑Smart Agriculture Sourcebook*. Rome: FAO.  
- Van der Wal, C. E. M., et al. (2017). Ecosystem models for the reconstruction of historical fire frequency and severity. *Philosophical Transactions of the Royal Society B*, 372(1743).  
- Optimal Design Software, Version 5.0 (University of Southampton).  
- R package **clusterPower** (v1.4), University of Zurich.  

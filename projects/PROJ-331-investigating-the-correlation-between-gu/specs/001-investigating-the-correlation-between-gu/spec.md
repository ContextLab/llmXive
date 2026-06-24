# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Feature Branch**: `[###-feature-name]`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Which specific gut microbial taxa are significantly correlated with longitudinal progression rates of Parkinson’s Disease (PD) severity, after controlling for age, sex, and medication status?"  

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify Progression‑Associated Taxa (Priority: P1)

A biomedical researcher runs the analysis pipeline on the PPMI longitudinal cohort to discover gut microbial taxa whose abundances correlate with the rate of UPDRS motor score change over a longitudinal follow‑up period.

**Why this priority**: This story delivers the core scientific value—producing the hypothesis‑generating biomarkers that the project set out to find.

**Independent Test**: Execute the end‑to‑end pipeline on a curated subset of the PPMI data (≥30 patients with ≥2 visits) and verify that a results table is produced containing taxa, correlation coefficients, and adjusted p‑values.

**Acceptance Scenarios**:

1. **Given** a cleaned ASV table and matching clinical metadata with at least two timepoints per patient, **When** the pipeline is launched, **Then** a CSV file `taxa_correlations.csv` is generated containing one row per taxon with Spearman ρ, raw p‑value, and Benjamini‑Hochberg adjusted p‑value.  
2. **Given** the same input data, **When** the pipeline finishes, **Then** **at least two taxa have BH‑adjusted p < 0.05** in `taxa_correlations.csv`.

---

### User Story 2 - Model Covariate‑Adjusted Effects (Priority: P2)

The researcher requires a Linear Mixed‑Effects Model that adjusts taxon‑specific slopes for age, sex, and levodopa equivalent dose, providing effect size estimates that account for key confounders.

**Why this priority**: This story operationalizes FR‑005, ensuring that identified associations are not driven by demographic or medication variables.

**Independent Test**: Run the mixed‑effects modeling module on the same dataset used in Story 1 and confirm that a results file `mixed_effects_summary.csv` is produced with coefficients, standard errors, and p‑values for each taxon.

**Acceptance Scenarios**:

1. **Given** the per‑patient taxon slope data and clinical covariates, **When** the mixed‑effects model is executed, **Then** `mixed_effects_summary.csv` contains a row per taxon with the fixed‑effect coefficient for the slope, its standard error, and a BH‑adjusted p‑value.  
2. **Given** the output, **When** the researcher filters for BH‑adjusted p < 0.05, **Then** at least two taxa meet this criterion, matching the findings from Story 1.

---

### User Story 3 - Validate Statistical Robustness (Priority: P3)

The researcher performs permutation testing to confirm that identified associations are not artifacts of the data structure.

**Why this priority**: Robustness validation protects against false discoveries and aligns with the methodology sketch.

**Independent Test**: Run the permutation module with **1000 iterations** and confirm that the empirical p‑value for each reported taxon deviates from the parametric p‑value by ≤0.02.

**Acceptance Scenarios**:

1. **Given** the output `taxa_correlations.csv`, **When** the permutation test is executed, **Then** a file `permutation_pvalues.csv` is produced and for every taxon with BH‑adjusted p < 0.05 the permutation‑derived p ≤ 0.07 (i.e., ≤0.02 absolute difference from the parametric p).

---

### User Story 4 - Performance and Resource Constraints (Priority: P3)

The pipeline must complete within defined computational limits to be usable on typical research compute nodes.

**Why this priority**: Guarantees that the analysis can be run reproducibly without exhausting resources, directly supporting SC‑003.

**Independent Test**: Execute the full pipeline (including the **1000‑iteration** permutation step) on an 8‑core, 32 GB RAM node and verify that wall‑clock time does not exceed **6 hours** and that the permutation step alone does not exceed **4 hours**.

**Acceptance Scenarios**:

1. **Given** the full dataset, **When** the pipeline runs, **Then** the total runtime reported in the log is ≤ 6 hours.  
2. **Given** the same run, **When** the permutation module completes, **Then** its runtime logged is ≤ 4 hours.

---

### User Story 5 - Generate Publication‑Ready Summary (Priority: P4)

The researcher exports a concise report summarizing the top correlated taxa, effect sizes, and model diagnostics for inclusion in a manuscript.

**Why this priority**: The PDF report is a required deliverable (FR‑008) and accelerates downstream manuscript preparation.

**Independent Test**: Invoke the reporting utility and verify that a PDF `PD_microbiome_progression_report.pdf` contains a ranked table of taxa, **[deferred] confidence intervals** for mixed‑effects coefficients (computed via 1000‑bootstrap resamples), and a brief methods paragraph.

**Acceptance Scenarios**:

1. **Given** the analysis outputs, **When** the report generator is called, **Then** the PDF includes at least the top three taxa with their Spearman ρ, BH‑adjusted p‑values, mixed‑effects model coefficients (with [deferred] CIs), plus a methods section matching the methodology sketch.

---

### Edge Cases

- **Boundary condition**: What happens when a patient has only one longitudinal visit?  
  *The pipeline must exclude that patient and log the exclusion count.*

- **Error scenario**: How does the system handle taxa with zero counts across all samples?  
  *Those taxa are dropped prior to CLR transformation; a warning is emitted.*

- **Resource limit**: What if the permutation step exceeds the **4‑hour** wall‑time limit?  
  *The pipeline aborts gracefully, writes a partial results file, and reports the runtime breach.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest pre‑processed 16S rRNA ASV tables and associated clinical metadata from the PPMI database in CSV/TSV format.  
- **FR-002**: System MUST filter samples to retain only PD patients with **≥ 2** distinct timepoints and record the number of excluded subjects.  
- **FR-003**: System MUST apply centered log‑ratio (CLR) transformation to all retained taxa abundances before any statistical testing.  
- **FR-004**: System MUST compute, for each taxon, the per‑patient linear slope of CLR‑transformed abundance over time, then calculate a Spearman rank correlation across patients between those taxon‑specific slopes and each patient’s UPDRS Part III score change per month.  
- **FR-005**: System MUST fit a Linear Mixed‑Effects Model (random intercept per patient) that includes age, sex, and levodopa equivalent dose as fixed covariates, and output model coefficients and p‑values for each taxon.  
- **FR-006**: System MUST perform Benjamini‑Hochberg false discovery rate correction across all taxa and annotate each taxon with the adjusted p‑value.  
- **FR-007**: System MUST execute a permutation test with **1000 iterations**, shuffling patient identifiers while preserving within‑patient time structure, and must complete this step within a **4‑hour** wall‑time budget on a standard 8‑core, 32 GB RAM compute node.  
- **FR-008**: System MUST generate three deliverables: `taxa_correlations.csv`, `permutation_pvalues.csv`, and a PDF summary report `PD_microbiome_progression_report.pdf` (mandatory).

### Key Entities *(include if feature involves data)*

- **PatientRecord**: Represents an individual study participant; key attributes include `patient_id`, `age`, `sex`, `levodopa_eq_dose`, and a list of `Visit` objects.  
- **Visit**: Captures a single timepoint; attributes include `visit_date`, `UPDRS_partIII`, and a vector of CLR‑transformed taxa abundances.  
- **TaxonResult**: Stores analysis outcomes per taxon; attributes include `taxon_name`, `spearman_rho`, `raw_p`, `bh_adj_p`, `mixed_effect_coef`, `permutation_p`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least **2** taxa achieve Benjamini‑Hochberg adjusted p < 0.05 while controlling for age, sex, and medication dose.  
- **SC-002**: Permutation‑derived empirical p‑values for those taxa differ from the parametric p‑values by no more than **0.02** (absolute difference).  
- **SC-003**: Total wall‑time for the complete pipeline (including permutation testing) does not exceed **6 hours** on an 8‑core, 32 GB RAM node.  
- **SC-004**: The generated PDF report contains a ranked table of the top **3** taxa with **[deferred] confidence intervals** for mixed‑effects coefficients (computed via 1000‑bootstrap resamples).

## Assumptions

- Access to the PPMI database is granted and the researcher can download the pre‑processed ASV table and metadata in CSV/TSV format.  
- The ASV table is already quality‑controlled (e.g., chimeric sequences removed) and compatible with CLR transformation.  
- A Python 3.11 environment with `pandas`, `scikit‑bio`, `statsmodels`, and `matplotlib` is available; no additional proprietary software is required.  
- The compute environment provides at least 8 CPU cores and 32 GB RAM; network latency is negligible for local file I/O.  
- The study cohort contains a minimum of **30** PD patients meeting the longitudinal inclusion criteria, providing sufficient statistical power for correlation analysis.
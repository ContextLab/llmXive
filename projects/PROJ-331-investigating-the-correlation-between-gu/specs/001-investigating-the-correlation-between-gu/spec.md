# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Feature Branch**: `001-gut-microbiome-pd-progression`  
**Created**: 2026-07-18  
**Status**: Draft  
**Input**: User description: "Which specific gut microbial taxa are significantly correlated with longitudinal progression rates of Parkinson’s Disease (PD) severity, after controlling for age, sex, and medication status?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify Progression‑Associated Taxa (Priority: P1)

A biomedical researcher runs the analysis pipeline on the PPMI longitudinal cohort to discover gut microbial taxa whose abundances correlate with the rate of UPDRS motor score change over a longitudinal follow‑up period.

**Why this priority**: This story delivers the core scientific value—producing the hypothesis‑generating biomarkers that the project set out to find. It directly addresses the research question regarding specific taxa and progression rates.

**Independent Test**: Execute the end‑to‑end pipeline on a curated subset of the PPMI data (≥30 patients with ≥2 visits) and verify that a results table is produced containing taxa, correlation coefficients, and adjusted p‑values.

**Acceptance Scenarios**:

1. **Given** a cleaned ASV table and matching clinical metadata with at least two timepoints per patient (referencing `PatientRecord` and `Visit` entities), **When** the pipeline is launched, **Then** a CSV file `taxa_correlations.csv` is generated containing one row per taxon with Spearman ρ, raw p‑value, and Benjamini‑Hochberg adjusted p‑value.  
2. **Given** the same input data, **When** the pipeline finishes, **Then** the system correctly calculates and reports BH‑adjusted p‑values for all tested taxa in `taxa_correlations.csv`.

---

### User Story 2 - Model Covariate‑Adjusted Effects (Priority: P2)

The researcher requires a Linear Mixed‑Effects Model that adjusts taxon‑specific slopes for age, sex, and levodopa equivalent dose, providing effect size estimates that account for key confounders. The model explicitly tests the interaction between Time and Taxon abundance to determine if taxon levels predict the rate of progression.

**Why this priority**: This story operationalizes the requirement for confounder control, ensuring that identified associations are not driven by demographic or medication variables. It refines the P1 findings into statistically robust estimates using a scientifically sound longitudinal model.

**Independent Test**: Run the mixed‑effects modeling module on the same dataset used in Story 1 and confirm that a results file `mixed_effects_summary.csv` is produced with coefficients, standard errors, and p‑values for each taxon.

**Acceptance Scenarios**:

1. **Given** the longitudinal clinical data and taxon abundances linked to `PatientRecord` and `Visit` entities, **When** the mixed‑effects model is executed, **Then** `mixed_effects_summary.csv` contains a row per taxon with the fixed‑effect coefficient for the `Time * Taxon` interaction, its standard error, and a BH‑adjusted p‑value.  
2. **Given** the output, **When** the researcher inspects the file, **Then** the system correctly reports BH‑adjusted p‑values for all taxa, demonstrating the statistical procedure was applied regardless of the significance outcome.

---

### User Story 3 - Validate Statistical Robustness (Priority: P3)

The researcher performs permutation testing to confirm that identified associations are not artifacts of the data structure or outliers.

**Why this priority**: Robustness validation protects against false discoveries and aligns with the methodology sketch's requirement for a stability check. It ensures the findings are not driven by specific sample configurations.

**Independent Test**: Run the permutation module with **1,000 iterations** and confirm that a valid empirical p-value distribution is generated.

**Acceptance Scenarios**:

1. **Given** the output `mixed_effects_summary.csv`, **When** the permutation test is executed, **Then** a file `permutation_pvalues.csv` is produced containing valid p-values (0 ≤ p ≤ 1) for all tested taxa, confirming the robustness check completed successfully.

---

### User Story 4 - Performance and Resource Constraints (Priority: P3)

The pipeline must complete within defined computational limits to be usable on typical research compute nodes (GitHub Actions free tier).

**Why this priority**: Guarantees that the analysis can be run reproducibly without exhausting resources, directly supporting SC‑003. This is critical for the "free CPU-only CI" constraint.

**Independent Test**: Execute the full pipeline (including the **1,000‑iteration** permutation step) on a 2‑core, 7 GB RAM node and verify that wall‑clock time does not exceed **6 hours**.

**Acceptance Scenarios**:

1. **Given** the full dataset (subsampled to top 100 taxa if necessary), **When** the pipeline runs, **Then** the total runtime reported in the log is ≤ 6 hours.  
2. **Given** the same run, **When** the permutation module completes, **Then** its runtime logged is ≤ 4 hours.

---

### User Story 5 - Generate Publication‑Ready Summary (Priority: P4)

The researcher exports a concise report summarizing the top correlated taxa, effect sizes, and model diagnostics for inclusion in a manuscript.

**Why this priority**: The PDF report is a required deliverable (FR‑008) and accelerates downstream manuscript preparation.

**Independent Test**: Invoke the reporting utility and verify that a PDF `PD_microbiome_progression_report.pdf` contains a ranked table of taxa, confidence intervals (values computed via bootstrap resamples at runtime) for mixed‑effects coefficients, and a brief methods paragraph.

**Acceptance Scenarios**:

1. **Given** the analysis outputs, **When** the report generator is called, **Then** the PDF includes at least the top three taxa with their Spearman ρ, BH‑adjusted p‑values, mixed‑effects model coefficients (with confidence intervals computed via 1,000 bootstrap resamples at runtime), plus a methods section matching the methodology sketch.

---

### Edge Cases

- **Boundary condition**: What happens when a patient has only one longitudinal visit?  
  *The pipeline must exclude that patient and log the exclusion count.*

- **Error scenario**: How does the system handle taxa with zero counts across all samples?  
  *Those taxa are dropped prior to CLR transformation; a warning is emitted.*

- **Resource limit**: What if the permutation step exceeds the **4‑hour** wall‑time limit?  
  *The pipeline aborts gracefully, writes a partial results file, and reports the runtime breach.*

- **Data sparsity**: What happens if the PPMI dataset lacks sufficient variation in levodopa dosage?  
  *The system detects zero-variance covariates and excludes them from the model, logging a warning.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest pre‑processed 16S rRNA ASV tables and associated clinical metadata from the PPMI database in CSV/TSV format. (See US‑1)
- **FR-002**: System MUST filter samples to retain only PD patients with **≥ 2** distinct timepoints (referencing `PatientRecord` and `Visit` entities) and record the number of excluded subjects. (See US‑1)
- **FR-003**: System MUST apply centered log‑ratio (CLR) transformation to all retained taxa abundances before any statistical testing to handle compositional data bias. (See US‑1)
- **FR-004**: System MUST compute, for each taxon, the per‑patient linear slope of CLR‑transformed abundance over time, and the per‑patient linear slope of UPDRS Part III score change over time, then calculate a Spearman rank correlation across patients between these two slopes. (See US‑1)
- **FR-005**: System MUST fit a Linear Mixed‑Effects Model (random intercept per patient) with the fixed effects formula `UPDRS ~ Time * Taxon + Age + Sex + Levodopa_Dose`, outputting the interaction coefficient, standard error, and p‑value for each taxon. (See US‑2)
- **FR-006**: System MUST perform Benjamini‑Hochberg false discovery rate correction across all taxa and annotate each taxon with the adjusted p‑value. (See US‑2)
- **FR-007**: System MUST execute a permutation test with **1,000 iterations**, shuffling patient identifiers while preserving within‑patient time structure, and must complete this step within a **4‑hour** wall‑time budget on a standard 2‑core, 7 GB RAM compute node. (Justification: [deferred] iterations is the minimum standard for stable empirical p-value estimation (SE ≈ 0.01) in high-dimensional data; the 4-hour limit is derived from the 6-hour total pipeline budget minus data loading and reporting overhead). (See US‑3)
- **FR-008**: System MUST generate three deliverables: `taxa_correlations.csv`, `mixed_effects_summary.csv`, `permutation_pvalues.csv`, and a PDF summary report `PD_microbiome_progression_report.pdf` (mandatory). (See US‑5)
- **FR-009**: System MUST frame all reported associations as **associational** rather than causal, explicitly stating that no randomization was performed in the observational PPMI cohort. (See US‑2)
- **FR-010**: System MUST subsample the analysis to the **top 100 most abundant taxa** if the full feature set exceeds **7 GB** of RAM usage during the modeling phase. (See US‑4)

### Key Entities *(include if feature involves data)*

- **PatientRecord**: Represents an individual study participant; key attributes include `patient_id`, `age`, `sex`, `levodopa_eq_dose`, and a list of `Visit` objects.
- **Visit**: Captures a single timepoint; attributes include `visit_date`, `UPDRS_partIII`, and a vector of CLR‑transformed taxa abundances.
- **TaxonResult**: Stores analysis outcomes per taxon; attributes include `taxon_name`, `spearman_rho`, `raw_p`, `bh_adj_p`, `mixed_effect_coef`, `permutation_p`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system outputs `mixed_effects_summary.csv` containing BH‑adjusted p‑values for all tested taxa, with correct Benjamini‑Hochberg correction applied to the `Time * Taxon` interaction term. (See FR‑006, US‑2)
- **SC-002**: Permutation test execution completes successfully and generates `permutation_pvalues.csv` with valid p-values (0 ≤ p ≤ 1) for all taxa. (See FR‑007, US‑3)
- **SC-003**: Total wall‑time for the complete pipeline (including permutation testing) does not exceed **6 hours** on a 2‑core, 7 GB RAM node. (See FR‑007, US‑4)
- **SC-004**: The generated PDF report contains a ranked table of the top **3** taxa with confidence intervals (values computed via 1,000 bootstrap resamples at runtime) for mixed‑effects coefficients. (See FR‑008, US‑5)
- **SC-005**: All reported correlations are explicitly labeled as "associational" in the final report, with no causal language used regarding the microbiome's effect on disease progression. (See FR‑009, US‑2)

## Assumptions

- Access to the PPMI database is granted and the researcher can download the pre‑processed ASV table and metadata in CSV/TSV format.
- The ASV table is already quality‑controlled (e.g., chimeric sequences removed) and compatible with CLR transformation.
- A Python 3.11 environment with `pandas`, `scikit‑bio`, `statsmodels`, and `matplotlib` is available; no additional proprietary software is required.
- The compute environment provides at least 2 CPU cores and 7 GB RAM; network latency is negligible for local file I/O.
- The study cohort contains a minimum of **30** PD patients meeting the longitudinal inclusion criteria, providing sufficient statistical power for correlation analysis.
- The PPMI dataset contains the necessary variables (age, sex, levodopa equivalent dose, UPDRS Part III scores at multiple timepoints) to perform the requested analysis.
- The analysis focuses on **associational** relationships only, as the observational nature of the PPMI cohort precludes causal inference without randomization.
- The top 100 most abundant taxa represent a sufficient subset of the microbiome to detect significant correlations with disease progression, given the memory constraints of the GitHub Actions runner.
- The CLR transformation is appropriate for the compositional nature of 16S rRNA data and does not introduce significant bias in the presence of zero counts (handled via imputation or filtering).
- The permutation test with 1,000 iterations provides a robust estimate of empirical p‑values without exceeding the 6‑hour runtime limit.
- **Scientific Expectation**: While the system is designed to handle any outcome, the research hypothesis anticipates identifying a limited number of microbial taxa significantly associated with PD progression. This is a scientific hypothesis, not a software requirement; the system must function correctly even if zero significant taxa are found.
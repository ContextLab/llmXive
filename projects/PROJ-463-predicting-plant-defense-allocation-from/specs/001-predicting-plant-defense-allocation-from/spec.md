# Feature Specification: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

**Feature Branch**: `001-plant-defense-allocation`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "How does tissue‑specific transcriptomic response to chewing versus piercing‑sucking herbivores predict differential allocation of chemical versus physical defense traits across plant species?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to automatically acquire publicly available RNA‑seq datasets from NCBI GEO/SRA involving plant herbivory experiments and preprocess them into normalized transcript counts, so that I have a standardized, analysis‑ready dataset for downstream differential expression and modeling.

**Why this priority**: This is the foundational step without which no analysis is possible. All subsequent user stories depend on having clean, batch‑corrected expression data.

**Independent Test**: Can be fully tested by running the pipeline on a subset of GEO studies and verifying that output TPM matrices have ≥95% of genes with non‑zero counts and batch‑corrected samples show reduced variance across studies (ComBat‑seq output metrics).

**Acceptance Scenarios**:

1. **Given** 3+ GEO/SRA studies with plant herbivory RNA‑seq data and tissue metadata, **When** the pipeline runs, **Then** FASTQ files are downloaded, quality‑trimmed with fastp, aligned with HISAT2, and quantified with featureCounts into TPM matrices
2. **Given** multiple studies with batch effects, **When** ComBat‑seq batch correction is applied, **Then** the coefficient of variation across batches decreases by ≥20% for housekeeping genes
3. **Given** studies lacking tissue information or biological replicates, **When** filtering is applied, **Then** those studies are excluded and a log reports the exclusion reason

---

### User Story 2 - Differential Expression and Feature Derivation (Priority: P2)

As a researcher, I want to compute differential expression between herbivore treatments and controls for each species‑tissue pair, and derive a standardized herbivore‑response vector from the top DE genes, so that I have comparable features for predictive modeling across species.

**Why this priority**: This transforms raw expression data into the predictor variables for the research question. It is the core analytical step that enables US‑3.

**Independent Test**: Can be fully tested by running DESeq2 on a single species‑tissue pair with known chewing vs control samples and verifying that ≥150 of the top 200 DE genes match published herbivory response genes (Jaccard similarity ≥0.75).

**Acceptance Scenarios**:

1. **Given** normalized TPM matrices with ≥2 biological replicates per condition, **When** DESeq2 is run with FDR < 0.05 and |log₂FC| > 1 thresholds, **Then** a list of DE genes with signed log₂FC values is produced for each herbivore type (chewing vs piercing‑sucking)
2. **Given** DE genes across multiple studies, **When** the top 200 common DE genes are selected, **Then** a herbivore‑response vector is derived with consistent gene ordering across species
3. **Given** species with insufficient replicates (<2 per condition), **When** filtering is applied, **Then** those species are excluded and the exclusion is logged for traceability

---

### User Story 3 - Predictive Modeling and Statistical Evaluation (Priority: P3)

As a researcher, I want to train regularized linear models (Elastic Net) and random‑forest regressors to map herbivore‑response vectors to a defense allocation index, and evaluate predictive performance using leave‑one‑species‑out cross‑validation with permutation‑based significance testing, so that I can determine whether transcriptomic signatures reliably forecast defense allocation.

**Why this priority**: This delivers the final research output (the prediction model and its validation). It depends on US‑1 and US‑2 being complete.

**Independent Test**: Can be fully tested by running leave‑one‑species‑out CV on ≥5 species and verifying that the model achieves Spearman correlation ≥0.3 between predicted and observed defense allocation indices with permutation p < 0.05.

**Acceptance Scenarios**:

1. **Given** herbivore‑response vectors and defense allocation indices for ≥5 species, **When** Elastic Net and random‑forest models are trained with leave‑one‑species‑out CV, **Then** test‑set R² and Spearman correlation are computed for each fold
2. **Given** 10,000 permutations of the defense allocation index, **When** the null distribution is generated, **Then** the observed correlation's p‑value is calculated and reported with 95% CI via bootstrapping
3. **Given** multiple tissue‑specific models, **When** results are compared, **Then** a tissue‑specificity effect size (ΔR² between leaf‑only and multi‑tissue models) is reported

---

### Edge Cases

- What happens when a species has RNA‑seq data for chewing herbivores but not piercing‑sucking herbivores (or vice versa)? → The species is excluded from the paired analysis and logged; a sensitivity analysis is run on the subset with both herbivore types.
- How does the system handle batch effects that exceed ComBat‑seq correction capacity (e.g., different sequencing platforms)? → Batch is recorded as a covariate; if residual batch variance >15% after correction, the study is flagged for manual review and may be excluded.
- What happens when the defense trait database (TRY) lacks data for a species included in the RNA‑seq analysis? → That species is excluded from the prediction model; the exclusion rate is tracked and if >30% of species lack defense traits, a `[NEEDS CLARIFICATION: can alternative trait sources be integrated?]` is raised.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download FASTQ files from NCBI GEO/SRA for ≥3 plant herbivory studies with tissue metadata and ≥2 biological replicates per condition (See US-1)
- **FR-002**: System MUST perform quality trimming with fastp, alignment with HISAT2, and transcript quantification with featureCounts to produce TPM matrices (See US-1)
- **FR-003**: System MUST apply ComBat‑seq batch correction and verify that batch variance reduction ≥20% for housekeeping genes (See US-1)
- **FR-004**: System MUST run DESeq2 with FDR < 0.05 and |log₂FC| > 1 to identify DE genes for each herbivore type (See US-2)
- **FR-005**: System MUST derive a herbivore‑response vector from the top 200 common DE genes with consistent gene ordering across species (See US-2)
- **FR-006**: System MUST compile a defense allocation index = (sum of standardized chemical traits) / (sum of standardized physical traits) from TRY database and literature (See US-3)
- **FR-007**: System MUST train Elastic Net and random‑forest regressors with leave‑one‑species‑out cross‑validation (See US-3)
- **FR-008**: System MUST calculate Spearman correlation between predicted and observed defense allocation indices with 10,000 permutations for significance (See US-3)
- **FR-009**: System MUST perform sensitivity analysis varying the number of DE genes in the response vector (across multiple levels) and report how R² varies (See US-3)
- **FR-010**: System MUST apply family‑wise error correction (Bonferroni or Holm) when testing >1 hypothesis (See US-3)

### Key Entities *(include if feature involves data)*

- **RNA‑seq Study**: Represents a single GEO/SRA experiment; key attributes include accession ID, plant species, tissue type, herbivore treatment (chewing/piercing‑sucking/control), sequencing platform, replicate count
- **Herbivore‑Response Vector**: Represents the predictor feature for a species‑tissue pair; key attributes include gene identifiers (top 200 common DE genes), signed log₂FC values, herbivore type (chewing or piercing‑sucking)
- **Defense Allocation Index**: Represents the outcome variable for a species; key attributes include standardized chemical trait sum, standardized physical trait sum, ratio value, data sources (TRY/literature)
- **Species**: Represents a plant taxon with both transcriptomic and defense trait data; key attributes include species name, tissue types available, herbivore types tested, defense trait values

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Batch variance reduction is measured against pre‑correction housekeeping gene CV (See US-1)
- **SC-002**: DE gene reproducibility is measured against published herbivory response gene lists (Jaccard similarity ≥0.75) (See US-2)
- **SC-003**: Predictive model performance (R², Spearman correlation) is measured against leave‑one‑species‑out test sets (See US-3)
- **SC-004**: Statistical significance (p‑value) is measured against 10,000‑permutation null distribution (See US-3)
- **SC-005**: Sensitivity to DE gene count is measured by R² variation across {100, 150, 200, 250} genes (See US-3)

## Assumptions

- Public RNA‑seq studies in GEO/SRA contain ≥2 biological replicates per herbivore treatment condition for at least 5 plant species with both chewing and piercing‑sucking herbivore data
- The TRY plant trait database or supplementary tables of the RNA‑seq studies contain standardized chemical defense (e.g., glucosinolates, alkaloids) and physical defense (e.g., trichome density, leaf tensile strength) metrics for ≥5 of the species in the transcriptomic dataset
- All required data (FASTQ files, reference genomes, trait databases) fit within 7 GB RAM and 14 GB disk on a GitHub Actions free‑tier runner; larger datasets will be sampled to ≤1 GB before processing
- The analysis will complete within ≤6 hours of CPU time on a 2‑core, ~7 GB RAM runner without GPU acceleration
- Tissue metadata in GEO/SRA submissions are sufficiently accurate to distinguish leaf, stem, and root samples for tissue‑specific analysis
- Herbivore treatment annotations (chewing vs piercing‑sucking) in the original studies are correctly labeled and do not require manual curation beyond automated keyword matching
- The 200‑gene threshold for the herbivore‑response vector is based on community‑standard top‑DE gene cutoffs in plant transcriptomics; this will be validated via the sensitivity analysis in FR-009
- Findings are framed as associational (not causal) because the design is observational with no random assignment of herbivore treatments
- Family‑wise error correction uses Holm‑Bonferroni method as a standard choice for ≤10 hypothesis tests in ecological meta‑analyses

# Feature Specification: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

**Feature Branch**: `001-plant-defense-allocation`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "How does tissue‑specific transcriptomic response to chewing versus piercing‑sucking herbivores predict differential allocation of chemical versus physical defense traits across plant species?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to automatically acquire publicly available RNA‑seq datasets from NCBI GEO/SRA involving plant herbivory experiments and preprocess them into normalized transcript counts, so that I have a standardized, analysis‑ready dataset for downstream differential expression and modeling.

**Why this priority**: This is the foundational step without which no analysis is possible. All subsequent user stories depend on having clean, batch‑corrected expression data.

**Independent Test**: Can be fully tested by running the pipeline on a subset of GEO studies and verifying that:
1. Output files match the expected FASTA/TPM format specifications.
2. The batch correction module executes successfully and reports a variance reduction metric for the defined housekeeping gene set.
3. The pipeline correctly flags samples with coverage below the configurable threshold.

**Acceptance Scenarios**:

1. **Given** 3+ GEO/SRA studies with plant herbivory RNA‑seq data and tissue metadata, **When** the pipeline runs, **Then** FASTQ files are downloaded, quality‑trimmed with fastp, aligned with HISAT2, and quantified with featureCounts into TPM matrices
2. **Given** multiple studies with batch effects, **When** ComBat‑seq batch correction is applied, **Then** the coefficient of variation across batches decreases by ≥20% for the defined housekeeping gene set
3. **Given** studies lacking tissue information or biological replicates, **When** filtering is applied, **Then** those studies are excluded and a log reports the exclusion reason

---

### User Story 2 - Differential Expression and Feature Derivation (Priority: P2)

As a researcher, I want to compute differential expression between herbivore treatments and controls for each species‑tissue pair, and derive a standardized herbivore‑response vector from the top DE genes, so that I have comparable features for predictive modeling across species.

**Why this priority**: This transforms raw expression data into the predictor variables for the research question. It is the core analytical step that enables US‑3.

**Independent Test**: Can be fully tested by running DESeq2 on a single species‑tissue pair with known chewing vs control samples and verifying that the pipeline correctly identifies DE genes and constructs the response vector using the specified aggregation logic.

**Acceptance Scenarios**:

1. **Given** normalized TPM matrices with ≥2 biological replicates per condition, **When** DESeq2 is run with FDR < 0.05 and |log₂FC| > 1 thresholds, **Then** a list of DE genes with signed log₂FC values is produced for each herbivore type (chewing vs piercing‑sucking)
2. **Given** DE genes across multiple studies, **When** a subset of common differentially expressed (DE) genes is selected. (based on aggregate significance within the training fold), **Then** a herbivore‑response vector is derived with consistent gene ordering across species
3. **Given** species with insufficient replicates (<2 per condition), **When** filtering is applied, **Then** those species are excluded and the exclusion is logged for traceability

---

### User Story 3 - Predictive Modeling and Statistical Evaluation (Priority: P3)

As a researcher, I want to train regularized linear models (Elastic Net) and random‑forest regressors to map herbivore‑response vectors to a defense allocation index, and evaluate predictive performance using leave‑one‑species‑out cross‑validation with permutation‑based significance testing, so that I can determine whether transcriptomic signatures reliably forecast defense allocation.

**Why this priority**: This delivers the final research output (the prediction model and its validation). It depends on US‑1 and US‑2 being complete.

**Independent Test**: Can be fully tested by running the modeling pipeline on a dataset of ≥5 species and verifying that:
1. The dimensionality reduction step (pathway aggregation) is executed, reducing features to ≤50.
2. The model training executes the specified leave-one-species-out cross-validation loop.
3. The permutation test executes the specified number of iterations and calculates p-values.
4. The output includes all required performance metrics (R², Spearman correlation) and confidence intervals.

**Acceptance Scenarios**:

1. **Given** pathway-level herbivore-response vectors and defense allocation indices for ≥5 species, **When** Elastic Net and random‑forest models are trained with leave‑one‑species‑out CV, **Then** test‑set R² and Spearman correlation are computed for each fold
2. **Given** N=10,000 permutations of the defense allocation index, **When** the null distribution is generated, **Then** the observed correlation's p‑value is calculated and reported with 95% CI via bootstrapping
3. **Given** multiple tissue‑specific models, **When** results are compared, **Then** a tissue‑specificity effect size (ΔR² between leaf‑only and multi‑tissue models) is reported

---

### Edge Cases

- What happens when a species has RNA‑seq data for chewing herbivores but not piercing‑sucking herbivores (or vice versa)? → The species is excluded from the paired analysis and logged; a sensitivity analysis is run on the subset with both herbivore types.
- How does the system handle batch effects that exceed ComBat‑seq correction capacity (e.g., different sequencing platforms)? → Batch is recorded as a covariate; if residual batch variance >15% after correction, the study is flagged for manual review and may be excluded.
- What happens when the defense trait database (TRY) lacks data for a species included in the RNA‑seq analysis? → The system attempts fallback sources (Phenoscape, GBIF). If data remains missing for >30% of the target species (post-QC set), the modeling phase halts and raises `human_input_needed`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download FASTQ files from NCBI GEO/SRA for ≥3 plant herbivory studies with tissue metadata and ≥2 biological replicates per condition (See US-1)
- **FR-002**: System MUST perform quality trimming with fastp, alignment with HISAT2, and transcript quantification with featureCounts to produce TPM matrices (See US-1)
- **FR-003**: System MUST apply ComBat‑seq batch correction and verify that batch variance reduction ≥20% for the top 50 most stable genes selected from a fixed list of 50 housekeeping genes: ACT2, ACT7, GAPDH, UBQ10, EF1a, TUB6, TUB1, PP2A, SAND, CYP79D16, CYP79D15, CYP79D17, CYP83A1, CYP83B1, CYP96A1, CYP96A2, CYP96A3, CYP71A1, CYP71A2, CYP71A3, CYP71A4, CYP71A5, CYP71A6, CYP71A7, CYP71A8, CYP71A9, CYP71A10, CYP71A11, CYP71A12, CYP71A13, CYP71A14, CYP71A15, CYP71A16, CYP71A17, CYP71A18, CYP71A19, CYP71A20, CYP71A21, CYP71A22, CYP71A23, CYP71A24, CYP71A25, CYP71A26, CYP71A27, CYP71A28, CYP71A29, CYP71A30, CYP71A31, CYP71A32 (See US-1). Selection order is determined by lowest GeNorm M-value within this fixed set.
- **FR-004**: System MUST run DESeq2 with FDR < 0.05 and |log₂FC| > 1 to identify DE genes for each herbivore type (See US-2)
- **FR-005**: System MUST derive a herbivore‑response vector from a set of common DE genes ranked by aggregate significance (mean transformed p-value) across the training set within each Leave-One-Species-Out fold, ensuring no data leakage (See US-2)
- **FR-006**: System MUST compile a defense allocation index = (mean of standardized chemical traits) / (mean of standardized physical traits) using a fixed list of chemical and physical traits: Chemical = [Glucosinolates, Alkaloids, Phenolics]; Physical = [Trichome Density, Leaf Tensile Strength] from TRY database, Phenoscape, GBIF trait extensions, or specific literature repositories (See US-3)
- **FR-007**: System MUST train Elastic Net and random‑forest regressors with leave‑one‑species‑out cross‑validation where feature selection and model training occur strictly within the training fold. To address phylogenetic non-independence, the system MUST also perform a Phylogenetic Generalized Least Squares (PGLS) validation or a clade-stratified LOSO (See US-3)
- **FR-008**: System MUST calculate Spearman correlation between predicted and observed defense allocation indices with N=10,000 permutations (or until convergence within p-value tolerance of 0.001 for 3 consecutive runs) for significance (See US-3)
- **FR-009**: System MUST perform sensitivity analysis varying the number of DE genes in the response vector (across multiple levels) and report how R² varies (See US-3)
- **FR-010**: System MUST apply family‑wise error correction (Holm-Bonferroni) when testing >1 hypothesis (See US-3)
- **FR-011**: System MUST attempt to integrate alternative public sources (e.g., Phenoscape, GBIF trait extensions, or specific literature repositories) via a fallback lookup if the primary source (TRY) lacks data for a species. "Target species" is defined as the set of unique plant species present in the final RNA-seq dataset after initial QC filtering (US-1). If the total number of species missing data from *all* sources (primary + fallback) exceeds 30% of the target species, the system MUST halt the modeling phase, log the exclusion count, and raise a `human_input_needed` flag (See US-3)
- **FR-012**: System MUST perform pathway-level aggregation (e.g., KEGG/GO) to reduce the herbivore-response vector from 200 genes to ≤50 pathway-level features before model training to address the small-n, large-p problem (See US-3)
- **FR-016**: System MUST perform a power analysis prior to modeling. If the available number of species is relatively small… (calculated to detect R²=0.3 with α=0.05 and β=0.2), the system MUST halt and report "Insufficient statistical power for reliable prediction" (See US-3)
- **FR-017**: System MUST validate the predictive model against a phylogenetic null model. The system MUST generate a null distribution of R² values by shuffling species labels across the phylogenetic tree (sufficient iterations) and report if the observed R² exceeds the 95th percentile of this null distribution (See US-3)

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
- **SC-004**: Statistical significance (p‑value) is measured against N=10,000 permutation null distribution (See US-3)
- **SC-005**: Sensitivity to DE gene count is measured by R² variation across a range of gene counts. (See US-3)
- **SC-006**: Phylogenetic independence is measured by comparing observed R² against the 95th percentile of the phylogenetic null distribution (See US-3)

## Assumptions

- Public RNA‑seq studies in GEO/SRA contain ≥2 biological replicates per herbivore treatment condition for at least 15 plant species with both chewing and piercing‑sucking herbivore data
- The TRY plant trait database or supplementary tables of the RNA‑seq studies contain standardized chemical defense (e.g., glucosinolates, alkaloids, phenolics) and physical defense (e.g., trichome density, leaf tensile strength) metrics for ≥70% of the species in the transcriptomic dataset
- All required data (FASTQ files, reference genomes, trait databases) fit within 16GB RAM and 50GB disk on a GitHub Actions free‑tier runner; larger datasets will be sampled to 15 species before processing
- The analysis will complete within 24 hours of CPU time on a 4-core runner without GPU acceleration
- Tissue metadata in GEO/SRA submissions are sufficiently accurate to distinguish leaf, stem, and root samples for tissue‑specific analysis
- Herbivore treatment annotations (chewing vs piercing‑sucking) in the original studies are correctly labeled and do not require manual curation beyond automated keyword matching
- The 200-gene threshold for the herbivore‑response vector is based on community‑standard top‑DE gene cutoffs in plant transcriptomics; this will be validated via the sensitivity analysis in FR-009
- The Defense Allocation Index (ratio of means) is justified as a robust, interpretable metric for comparative analysis, avoiding the instability of summing standardized traits across small sample sizes
- Findings are framed as associational (not causal) because the design is observational with no random assignment of herbivore treatments
- Family‑wise error correction uses Holm‑Bonferroni method as a standard choice for ≤10 hypothesis tests in ecological meta‑analyses
- The phylogenetic tree used for null modeling is constructed from the Open Tree of Life API with a bootstrap support threshold of ≥70%
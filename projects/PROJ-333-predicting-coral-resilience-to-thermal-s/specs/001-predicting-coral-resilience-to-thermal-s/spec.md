# Feature Specification: Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

**Feature Branch**: `001-predict-coral-resilience`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Quality Filtering (Priority: P1)

The researcher downloads publicly available *Acropora millepora* genomic variant files (VCF) and associated metadata from NCBI BioProject PRJNA292777, then applies strict quality filters to ensure the dataset fits within the 7 GB RAM constraint and removes low-confidence variants.

**Why this priority**: Without a clean, memory-tractable dataset, no downstream statistical analysis can be performed. This is the foundational step that enables the entire research pipeline.

**Independent Test**: The pipeline can be executed end-to-end starting from raw download links, producing a filtered PLINK binary file set (`.bed`, `.bim`, `.fam`) and a summary report of removed variants, without requiring any association testing logic.

**Acceptance Scenarios**:
1. **Given** the raw VCF and metadata files from NCBI PRJNA292777, **When** the ingestion script runs, **Then** the output must be a filtered dataset where all variants with Minor Allele Frequency (MAF) ≤ 0.05 or missingness > 10% are excluded.
2. **Given** a corrupted or incomplete VCF file in the input directory, **When** the ingestion script runs, **Then** the system must halt with a clear error message identifying the specific file and the nature of the corruption, preventing partial data processing.
3. **Given** the metadata file, **When** the system checks for individual-level survival labels, **Then** if individual survival data is missing, the system must either derive a population-level proxy (e.g., mean temperature tolerance) or halt with a specific error indicating the data source does not support individual-level GWAS.

---

### User Story 2 - Genome-Wide Association Analysis (Priority: P2)

The researcher executes a genome-wide association study (GWAS) using PLINK to statistically correlate filtered SNPs with the binary survival phenotype (survived/died) under thermal stress, applying multiple-comparison corrections and population stratification controls to identify significant hits.

**Why this priority**: This is the core scientific inquiry of the project. It directly addresses the research question by identifying specific genetic variants linked to thermal tolerance.

**Independent Test**: The analysis script can be run on the filtered dataset from User Story 1, producing a list of significant SNPs (p-values), a Manhattan plot, and a QQ-plot, independent of the pathway enrichment step.

**Acceptance Scenarios**:
1. **Given** the filtered dataset and survival metadata, **When** the PLINK logistic regression runs, **Then** the output must include a p-value for every tested SNP and apply a False Discovery Rate (FDR) correction (q < 0.05) to control family-wise error.
2. **Given** a dataset where no SNPs meet the significance threshold (q < 0.05), **When** the analysis completes, **Then** the system must explicitly report "No significant associations found" and generate a null result report rather than crashing or returning empty files.
3. **Given** the filtered dataset, **When** Principal Component Analysis (PCA) is run, **Then** the top 3 Principal Components must be output as covariates to correct for population stratification.

---

### User Story 3 - Pathway Enrichment and Visualization (Priority: P3)

The researcher takes the list of significant SNPs from the GWAS and performs pathway enrichment analysis to determine if these variants cluster in heat-shock protein or oxidative stress pathways, visualizing the results via a Manhattan plot and pathway summary.

**Why this priority**: This step provides biological context and interpretability to the statistical hits, transforming raw p-values into actionable biological insights for conservationists.

**Independent Test**: The enrichment script can be run on a pre-defined list of significant SNPs (simulated or from a previous run) to produce the final visualization and biological interpretation report.

**Acceptance Scenarios**:
1. **Given** a list of significant SNPs (q < 0.05), **When** the enrichment analysis runs against a standard reference database (e.g., g:Profiler) and a homologous species database (e.g., *Nematostella vectensis*), **Then** the output must identify over-represented biological pathways (e.g., "Heat Shock Protein binding") with a reported adjusted p-value < 0.05.
    *Note: The p < 0.05 threshold for enrichment is a standard community convention for exploratory analysis.*
2. **Given** a list of significant SNPs that do not map to any known pathway, **When** the analysis runs, **Then** the system must report "No significant pathway enrichment found" and list the specific SNPs that could not be annotated.

### Edge Cases

- What happens when the metadata lacks a clear "survival" binary label (e.g., continuous temperature exposure data only)? The system must flag this as a critical data quality issue, attempt to derive a population-level proxy, or halt with a specific error preventing invalid GWAS execution.
- How does the system handle a situation where the number of significant SNPs is zero after correction? The system must treat this as a valid scientific outcome (polygenic trait or environmental plasticity) and generate a "Null Result" report rather than failing.
- What if the VCF file contains variants with missing genotype calls exceeding the 10% threshold for a specific individual? That individual must be excluded from the analysis to prevent bias.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download variant call files (VCF) and metadata from NCBI BioProject PRJNA292777 and parse them into a standard format. (See US-1)
- **FR-002**: System MUST filter variants to retain only those with Minor Allele Frequency (MAF) > 0.05 and missingness < 10%. (See US-1)
- **FR-003**: System MUST perform genome-wide association testing using logistic regression (PLINK) linking SNPs to the binary survival phenotype, including population stratification correction. (See US-2)
- **FR-004**: System MUST apply a False Discovery Rate (FDR) correction (q < 0.05) to all p-values to control family-wise error rate. (See US-2)
- **FR-005**: System MUST conduct pathway enrichment analysis on significant hits (q < 0.05) using a standard reference database (e.g., g:Profiler) and a homologous species database to identify heat-shock or oxidative stress pathways. (See US-3)
- **FR-006**: System MUST generate a Manhattan plot visualizing p-values across all chromosomes. (See US-2)
- **FR-007**: System MUST report a definitive "No significant associations found" status if no SNPs meet the corrected significance threshold, rather than failing silently. (See US-2)
- **FR-008**: System MUST validate pathway annotations by cross-referencing with a homologous species database (e.g., *Nematostella vectensis*) and report the annotation confidence level. (See US-3)
- **FR-009**: System MUST perform Principal Component Analysis (PCA) to identify the top 3 Principal Components and use them as covariates in the GWAS model to correct for population stratification. (See US-2)

### Key Entities

- **Variant Record**: A genomic position containing allele frequency, genotype data, and chromosome location.
- **Phenotype Record**: A sample identifier linked to a binary survival status (1=Survived, 0=Died) and temperature exposure metadata.
- **Significant Hit**: A Variant Record that meets the statistical significance threshold (q < 0.05 after correction).
- **Pathway**: A biological functional group (e.g., "Oxidative Stress Response") containing a set of genes.
- **Principal Component**: A derived covariate representing genetic ancestry variation used to correct for population stratification.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The total dataset size after filtering is measured against the 7 GB RAM limit to ensure memory feasibility. (See US-1)
- **SC-002**: The genomic inflation factor (lambda) is measured against the threshold 1.05 to validate that the population stratification correction (FR-009) was successful. (See US-2)
- **SC-003**: The pathway enrichment analysis successfully reports either a list of pathways with adjusted p < 0.05 OR a definitive null result, ensuring the output is never ambiguous. (See US-3)
- **SC-004**: The computation time for the full GWAS pipeline is measured against a target of ≤ 5 hours to provide a 1-hour buffer before the 6-hour GitHub Actions free-tier timeout. (See US-2)
- **SC-005**: The presence of the top 3 Principal Components in the GWAS covariate file is measured against the requirement for population stratification correction. (See US-2)
- **SC-006**: The annotation confidence of pathway mappings is measured against the requirement for cross-species validation (FR-008). (See US-3)

## Assumptions

- The NCBI BioProject PRJNA292777 contains VCF files for *Acropora millepora*. If individual-level survival metadata is missing, the system will attempt to derive a population-level proxy or halt with a specific error, as individual-level GWAS requires individual phenotypes.
- The thermal stress phenotype is observational; therefore, all findings will be framed as associational correlations, not causal effects, unless the metadata explicitly indicates a randomized experimental design.
- The analysis will rely on standard, CPU-tractable statistical methods (PLINK logistic regression) rather than deep learning or GPU-accelerated models, as the compute environment is limited to a small number of CPU cores and no GPU.
- The g:Profiler or equivalent pathway database may contain sparse annotation mappings for *Acropora millepora* genes; therefore, the system will map to the closest homologous model organism (e.g., *Nematostella vectensis* or *Homo sapiens*) and report this mapping confidence as part of the results.
- The "survival" phenotype is binary (Survived/Died) in the metadata; if the data provides continuous temperature tolerance metrics, a threshold of "survival" will be defined as the median survival temperature of the cohort for binarization, or a population-level proxy will be used if individual labels are absent.
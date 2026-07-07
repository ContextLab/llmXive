# Feature Specification: Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

**Feature Branch**: `001-coral-resilience-prediction`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data"

## User Scenarios & Testing

### User Story 1 - RNA-seq Data Ingestion and Preprocessing Pipeline (Priority: P1)

A researcher needs to download raw RNA-seq reads (FASTQ) for *Acropora millepora* from an NCBI BioProject., map them to a reference transcriptome, and quantify gene expression to ensure data quality and fit within the limited RAM constraint of the free-tier CI runner.

**Why this priority**: Without clean, memory-tractable expression data, no differential expression analysis can occur. This is the foundational step that enables all subsequent hypothesis testing.

**Independent Test**: Can be fully tested by running the download and quantification script on a local machine or CI runner and verifying that peak memory usage (RSS) remains < 7 GB and that the output expression matrix contains only samples with valid treatment metadata.

**Acceptance Scenarios**:

1. **Given** the NCBI BioProject ID PRJNA292777 is provided, **When** the ingestion script executes, **Then** it successfully downloads the FASTQ files and logs the total file size.
2. **Given** raw FASTQ files, **When** the quantification step runs (using Salmon/DESeq2), **Then** the output expression matrix is generated with valid gene counts, and peak memory usage does not exceed 7 GB.
3. **Given** metadata with treatment status (Heat vs. Control), **When** the script parses the phenotype file, **Then** it correctly maps sample IDs from the FASTQ files to treatment conditions.

---

### User Story 2 - Differential Gene Expression Analysis (Priority: P2)

A researcher needs to run a differential gene expression (DGE) analysis using DESeq2 to identify genes significantly upregulated or downregulated under thermal stress, ensuring the analysis respects the observational nature of the data.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question by testing the correlation between gene expression and thermal stress conditions.

**Independent Test**: Can be fully tested by executing the DESeq2 pipeline with the quantified data and verifying that a results table is generated containing log2-fold changes and adjusted p-values for all tested genes.

**Acceptance Scenarios**:

1. **Given** the quantified expression matrix and phenotype file are ready, **When** the DESeq2 analysis runs, **Then** it outputs a result table with log2-fold changes and adjusted p-values for every gene tested.
2. **Given** the analysis is based on experimental conditions, **When** the results are generated, **Then** the output includes a clear header or metadata note stating that findings are associational, not causal.
3. **Given** multiple hypothesis tests are performed, **When** the analysis completes, **Then** the results include a column for multiple-comparison corrected p-values (FDR).

---

### User Story 3 - Pathway Enrichment and Visualization (Priority: P3)

A researcher needs to visualize the differentially expressed genes via a volcano plot and perform pathway enrichment analysis to identify if the hits cluster in heat-shock protein or oxidative stress pathways.

**Why this priority**: This transforms raw statistical hits into biological insight, allowing the researcher to interpret *why* certain genes are associated with thermal stress response.

**Independent Test**: Can be fully tested by running the enrichment script on the top 100 significant genes and verifying that a volcano plot image and an enrichment report (listing pathways) are generated.

**Acceptance Scenarios**:

1. **Given** a list of significant genes (FDR < 0.05), **When** the visualization script runs, **Then** it generates a volcano plot saved as a PNG file.
2. **Given** significant genes are mapped to gene IDs, **When** the enrichment analysis runs against g:Profiler, **Then** it outputs a list of enriched pathways with p-values, and explicitly notes whether heat-shock or oxidative stress pathways are among the enriched results.
3. **Given** the analysis completes, **When** the final report is generated, **Then** it includes a summary stating whether the observed enrichment for stress pathways is statistically significant (FDR < 0.05).

---

### Edge Cases

- What happens when the NCBI download fails due to network timeout? (System retries up to 3 times with exponential backoff, then logs a fatal error).
- How does the system handle a dataset where no genes pass the expression threshold? (The pipeline halts with a clear error message indicating insufficient data for this specific cohort).
- What happens if the phenotype metadata is missing treatment status for a subset of samples? (Those samples are excluded from the DGE, and a warning log reports the exclusion count).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download FASTQ files and phenotype metadata from NCBI BioProject [Identifier] and verify file integrity (SHA256) before processing. (See US-1)
- **FR-002**: System MUST quantify gene expression and filter results to ensure the resulting dataset size is compatible with a constrained RAM environment. (See US-1)
- **FR-003**: System MUST execute a differential gene expression test using DESeq2 (or equivalent) to correlate gene expression levels with thermal stress treatment conditions. (See US-2)
- **FR-004**: System MUST apply a multiple-comparison correction (Benjamini-Hochberg FDR) to all p-values to control family-wise error rate. (See US-2)
- **FR-005**: System MUST generate a volcano plot and a pathway enrichment report using g:Profiler or equivalent for genes with FDR < 0.05. (See US-3)
- **FR-006**: System MUST explicitly label all statistical findings as "associational" in the output report, acknowledging the lack of random assignment. (See US-2)

### Key Entities

- **Expression Matrix**: A filtered collection of gene counts derived from *Acropora millepora* RNA-seq data, mapped to treatment conditions.
- **Phenotype Record**: A mapping of sample IDs to experimental treatment status (Heat vs. Control).
- **DGE Result**: A dataset linking each gene to a log2-fold change, p-value, and adjusted significance status.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Peak memory usage (RSS) measured via system profiler during execution is measured against the available RAM limit to ensure the analysis completes without memory overflow on the free-tier runner. (See US-1)
- **SC-002**: Number of significant genes (FDR < 0.05) is measured against the expected count under the null hypothesis; success requires observed count > expected count at p < 0.05. (See US-2)
- **SC-003**: Enrichment p-value for at least one pathway from the predefined list [HSP, Oxidative] is measured against the threshold FDR < 0.1 to validate biological plausibility. (See US-3)
- **SC-004**: The computational runtime is measured against the free-tier job limit of GitHub Actions to ensure feasibility. (See US-1)
- **SC-005**: The False Discovery Rate (FDR) of reported significant hits is measured against the threshold FDR <= 0.05. (See US-2)

## Assumptions

- The NCBI BioProject contains raw RNA-seq reads (FASTQ) that can be mapped to a reference transcriptome within a feasible CI time limit using standard tools (e.g., Salmon, DESeq2).
- The experimental treatment metadata (Heat vs. Control) is available in a machine-readable format (e.g., CSV, TSV) linked to the sample IDs in the genomic files.
- The dataset size, after quantification and filtering, will fit within the RAM and disk constraints of the free-tier runner.
- The analysis is purely observational; therefore, no causal claims regarding specific genes causing thermal resilience will be made, only associations.
- The g:Profiler API or a local equivalent is accessible and functional during the pipeline execution for pathway enrichment.
- The "heat-shock protein" and "oxidative stress" pathways are adequately represented in the reference genome annotation used for the analysis.
- If the dataset lacks specific variables required for covariate adjustment (e.g., specific environmental covariates), the analysis will proceed with available metadata only, noting this limitation in the final report.
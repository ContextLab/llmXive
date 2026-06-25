# Feature Specification: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast  

**Feature Branch**: `001-yeast-cre-analysis`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description:  
> Which cis‑regulatory elements (CREs) show condition‑specific activity that drives the transcriptional responses underlying phenotypic plasticity of *Saccharomyces cerevisiae* across heat‑shock, osmotic, and oxidative stress?  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Generate a ranked CRE catalog for stress‑specific activity (Priority: P1)

A computational biologist wants to run the full analysis pipeline and obtain a markdown table ranking CREs (including genomic coordinates, associated TFs, log₂FC, β₁ estimate, and adjusted q‑value) for each of the three stress conditions.

**Why this priority**: This delivers the core scientific output—identifying candidate regulatory elements—without which downstream validation cannot proceed.

**Independent Test**: Execute the pipeline on the supplied GEO ChIP‑seq and 1002 Yeast Genomes eQTL datasets and verify that a markdown table with ≥200 entries is produced for each stress condition.

**Acceptance Scenarios**:

1. **Given** the raw ChIP‑seq FASTQ files and the processed eQTL summary statistics are present in the repository, **when** the `run_pipeline.sh` script finishes successfully, **then** a file `results/CRE_ranked_<stress>.md` exists containing at least 200 rows (excluding header) and includes the required columns.  

2. **Given** the pipeline has completed, **when** the user opens the markdown file, **then** the top 10 CREs show a log₂FC ≥ 1.0 and an adjusted q‑value ≤ 0.05.

---

### User Story 2 – Provide statistical evidence of CRE contribution beyond promoters (Priority: P2)

A reviewer needs a concise statistical report demonstrating that CRE activity explains a significant fraction of gene‑expression variance after accounting for promoter‑proximal TF binding.

**Why this priority**: The claim of “regulatory rewiring” hinges on robust statistical validation; without it the catalog lacks credibility.

**Independent Test**: Run the pipeline and inspect the generated PDF report `results/Statistical_summary.pdf` for the presence of (i) likelihood‑ratio test results, (ii) FDR‑corrected p‑values, and (iii) a statement of variance explained (ΔR²) that is >0.

**Acceptance Scenarios**:

1. **Given** the mixed‑model analysis is completed, **when** the reviewer reads the PDF, **then** the report contains a table where the fixed‑effect β₁ for ΔPeakSignal is significant (adjusted p < 0.05) for at least one stress condition.  

2. **Given** the permutation test (10 000 shuffles) has been performed, **when** the reviewer examines the empirical null plot, **then** the observed test statistic lies in the extreme tail of the null distribution, indicating a statistically significant deviation.

---

### User Story 3 – Visualize top CREs in a genome browser (Priority: P3)

A lab member wishes to load the most promising CREs into IGV to plan follow‑up functional assays.

**Why this priority**: Visualization bridges computational results with experimental design, enabling hypothesis‑driven bench work.

**Independent Test**: After pipeline execution, confirm that bigWig files `tracks/<stress>_CRE_signal.bw` are generated and can be loaded into IGV without errors, displaying peaks at the coordinates listed in the top‑10 of the markdown table.

**Acceptance Scenarios**:

1. **Given** the bigWig tracks are present, **when** the user opens IGV and adds the track, **then** the signal intensity aligns with the reported log₂FC values for the top‑5 CREs.  

2. **Given** the user navigates to a CRE annotated as “distal (>500 bp)”, **when** the track is displayed, **then** the peak shape matches the MACS2 narrowPeak file (same summit position).

---

### Edge Cases

- **No peaks survive MACS2 q < 0.01**: The pipeline must abort with a clear error message and suggest relaxing the q‑threshold (e.g., to 0.05).  
- **Missing eQTL effect sizes for a gene**: The gene is excluded from the mixed‑model analysis; a warning is logged indicating how many genes were dropped.  
- **Dataset variable gap**: `[NEEDS CLARIFICATION: Does the selected GEO series contain ChIP‑seq for all listed TFs (Hsf1, Msn2/4, Hog1) under each stress condition?]`  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw ChIP‑seq FASTQ files for each TF‑condition pair from GEO and verify integrity via MD5 checksums. (See US-1)  
- **FR-002**: System MUST trim adapters with `fastp`, align reads with `bowtie2` (≤2 threads), and retain only uniquely mapped reads (MAPQ ≥ 30). (See US-1)  
- **FR-003**: System MUST call peaks with `MACS2` using a **q‑threshold = 0.01** (community‑standard for stringent peak calling) **and** perform a sensitivity sweep over q ∈ {0.01, 0.05, 0.10}, reporting how the number of peaks and downstream β₁ estimates change. (See US-1)  
- **FR-004**: System MUST merge overlapping peaks across TFs/conditions, annotate genomic context (promoter ≤ 500 bp upstream vs. distal > 500 bp), and store the result in a BED file. (See US-1)  
- **FR-005**: System MUST fit a linear mixed‑model per stress condition as specified, test the fixed effect β₁ with a likelihood‑ratio test, and output both raw and Benjamini–Hochberg FDR‑adjusted p‑values. (See US-2)  
- **FR-006**: System MUST perform 10 000 permutation shuffles of peak signals to generate an empirical null distribution and report the empirical p‑value for the observed β₁. (See US-2)  
- **FR-007**: System MUST apply Benjamini–Hochberg correction across all CRE‑gene pairs and enforce **FDR < 0.05** as the significance cutoff. (See US-2)  
- **FR-008**: System MUST produce a markdown table ranking CREs by adjusted q‑value and absolute β₁ magnitude, limited to the top 500 entries per stress. (See US-1)  
- **FR-009**: System MUST generate bigWig tracks (`deepTools bamCoverage`) for each stress condition to enable IGV visualization of peak signal intensity. (See US-3)  
- **FR-010**: System MUST log a concise summary report (PDF) containing (i) number of peaks per TF/condition, (ii) variance explained (ΔR²) by CRE signal, (iii) enrichment test results for GO stress‑response genes using `clusterProfiler` (hypergeometric, FDR < 0.05). (See US-2)  

*Methodological safeguards*:

- **FR-011**: System MUST verify that the eQTL dataset contains (a) effect sizes for each gene, (b) expression fold‑changes under the same stress conditions, and raise a `[NEEDS CLARIFICATION]` if any variable is missing. (See US-1)  
- **FR-012**: System MUST diagnose multicollinearity among TF peak signals for a given CRE (variance inflation factor > 5) and, if present, report the CRE as “collinear” and exclude it from independent effect testing. (See US-2)  

### Key Entities

- **CRE (cis‑regulatory element)**: Genomic interval derived from merged MACS2 peaks; attributes include coordinates, associated TF(s), context (promoter/distal), normalized RPKM per condition, log₂FC, β₁ estimate, adjusted q‑value.  
- **Gene**: Yeast ORF; attributes include nearest CRE (≤10 kb), eQTL effect size, expression fold‑change per stress, random intercept term *u₍g₎* used in the mixed model.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ≥ 200 CREs per stress condition achieve adjusted q‑value ≤ 0.05 and absolute β₁ ≥ 0.2 (See US-1).  
- **SC-002**: The mixed‑model fixed effect β₁ is statistically significant (FDR‑adjusted p < 0.05) for at least one stress condition, demonstrating that CRE activity explains additional variance beyond promoter‑proximal binding (See US-2).  
- **SC-003**: Enrichment analysis yields a hypergeometric odds ratio ≥ 1.5 with FDR < 0.05 for GO stress‑response categories among the top‑100 CREs (See US-2).  
- **SC-004**: Sensitivity sweep over MACS2 q‑thresholds shows that the ranking of the top‑20 CREs is stable (≥ 80% overlap) across q = 0.01, 0.05, 0.10 (See FR-003).  
- **SC-005**: Generated bigWig tracks load into IGV without error and display signal peaks whose summit positions match the narrowPeak summit coordinates within ±5 bp for ≥ 90% of the top‑10 CREs (See US-3).  

## Assumptions

- The GEO series identified (placeholder `GSE####`) contains raw ChIP‑seq data for **all listed TFs** (Hsf1, Msn2/4, Hog1) under **control** and **each stress** condition.  
- The 1002 Yeast Genomes eQTL dataset provides **both** effect sizes and stress‑specific expression fold‑changes for the same set of genes examined in the ChIP‑seq analysis.  
- All command‑line tools (`fastp`, `bowtie2`, `MACS2`, `bedtools`, `BEDOPS`, `deepTools`, `lme4` in R, `clusterProfiler`) run within the **2‑core, 7 GB RAM, ≤5 h** limits of the GitHub Actions free‑tier runner.  
- No GPU or CUDA‑based acceleration is required; all steps use CPU‑only implementations.  
- Sample size (number of genes with paired CRE and eQTL data) is assumed sufficient for mixed‑model inference; a formal power analysis will be performed later (deferred).  
- The chosen q‑threshold of 0.01 for MACS2 is a widely accepted standard for stringent peak detection in yeast ChIP‑seq studies.  
- Collinearity diagnostics (VIF) are appropriate for the modest number of TF predictors per CRE; VIF > 5 is treated as problematic.  
- All external URLs cited in the idea (arXiv papers) are reachable and correctly formatted; no additional citations are introduced.

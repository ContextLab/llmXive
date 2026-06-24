# Feature Specification: Evolutionary Pressure on Alternative Splicing in Primates

**Feature Branch**: `PROJ-002-001-evolutionary-pressure`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “Investigate how alternative splicing divergence in primate cortex correlates with positive selection on splicing regulatory elements by analysing RNA‑seq data from human, chimpanzee, macaque and marmoset and integrating genomic selection metrics.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Quantify lineage‑specific splicing events (Priority: P1)

A researcher wants to download publicly available cortex RNA‑seq datasets for the four primate species, align the reads, and compute percent‑spliced‑in (PSI) values so that lineage‑specific splicing events can be identified.

**Why this priority**: This is the core data‑generation step; without reliable PSI estimates no downstream evolutionary analysis is possible.

**Independent Test**: Execute the pipeline on a single sample per species and verify that a PSI table is produced and that at least one splice junction is reported per sample.

**Acceptance Scenarios**:

1. **Given** a list of SRA accession IDs (e.g., GSE123456 for human), **When** the pipeline is run, **Then** FASTQ files are downloaded and stored in a designated `raw/` folder.
2. **Given** downloaded FASTQ files, **When** STAR alignment is invoked, **Then** each sample produces a sorted BAM file within ≤2 h on an 8‑core CPU node.

---

### User Story 2 – Annotate regulatory regions surrounding splicing events (Priority: P2)

A researcher needs the ±500 bp intronic sequences flanking each identified alternatively spliced exon and wants to attach phyloP conservation scores and dN/dS ratios for nearby coding regions.

**Why this priority**: Annotation provides the genomic context required to test for positive selection.

**Independent Test**: Run the annotation module on a pre‑filtered list of 50 splicing events and confirm that a BED file with sequence coordinates and a CSV file with phyloP & dN/dS values are generated.

**Acceptance Scenarios**:

1. **Given** a list of exon coordinates, **When** `bedtools getfasta` is executed, **Then** a FASTA file containing the ±500 bp flanking sequences is created for every exon.
2. **Given** the FASTA file, **When** phyloP scores are queried from the UCSC 100‑way alignment, **Then** each sequence receives an average phyloP score recorded in the annotation table.

---

### User Story 3 – Test enrichment of splicing events in positively selected regions (Priority: P3)

A researcher wants to statistically assess whether lineage‑specific splicing events are enriched in regions showing signatures of positive selection and visualise the results.

**Why this priority**: This delivers the primary scientific answer to the research question.

**Independent Test**: Perform the enrichment analysis on the full dataset and verify that a Manhattan‑style plot is produced with a significance line at *p* < 0.05 (Bonferroni‑corrected).

**Acceptance Scenarios**:

1. **Given** the annotated event table, **When** a Fisher’s exact test is run, **Then** an enrichment *p*‑value and odds ratio are reported for each lineage.
2. **Given** the test results, **When** the plotting script is executed, **Then** a PNG image showing chromosomes on the x‑axis and –log₁₀(*p*) on the y‑axis is saved, with peaks exceeding the corrected threshold highlighted.

---

### Edge Cases

- What happens when a species has fewer than 3 RNA‑seq samples meeting the minimum read‑depth requirement?  
- How does the system handle flanking intronic regions that overlap assembly gaps or lack phyloP scores?  
- What is the behaviour if STAR alignment fails for a sample (e.g., due to corrupted FASTQ)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download RNA‑seq FASTQ files from NCBI SRA given a user‑provided list of accession IDs.  
- **FR-002**: System MUST align reads to the appropriate reference genome (GRCh38, panTro6, rheMac10, calJac4) using STAR with default parameters, completing each alignment within **≤ 2 hours** on an 8‑core CPU node.  
- **FR-003**: System MUST quantify splice junction usage and compute PSI values with SUPPA2, outputting a unified TSV file containing `gene_id`, `event_id`, `PSI_sample1…PSI_sampleN`.  
- **FR-004**: System MUST identify lineage‑specific splicing events using **ΔPSI > 0.1** and **Benjamini‑Hochberg FDR < 0.05**; results are stored in `lineage_specific_events.tsv`.  
- **FR-005**: System MUST extract **±500 bp** flanking intronic sequences for each event using bedtools and retrieve average phyloP scores from the UCSC 100‑way alignment.  
- **FR-006**: System MUST calculate **dN/dS** ratios for the nearest coding region of each event using PAML’s codeml, recording the ratio in the annotation table.  
- **FR-007**: System MUST perform a Fisher’s exact test for enrichment of events overlapping regions with **phyloP ≥ 2.0** *and* **dN/dS < 0.5**, applying a **Bonferroni‑corrected p < 0.05** threshold.  
- **FR-008**: System MUST generate a Manhattan‑style plot (PNG, 1200 × 800 px) visualising –log₁₀(*p*) per chromosome, with a horizontal line indicating the significance threshold.  
- **FR-009**: System MUST log all major steps (download, alignment, quantification, annotation, statistical test) to a `pipeline.log` file with timestamps and exit codes.  

*Clarification needed*:

- **FR-010**: System MUST retain raw FASTQ files for **[NEEDS CLARIFICATION: retention period – e.g., 30 days, 90 days, indefinite?]**.  
- **FR-011**: System MUST allow the user to specify the **[NEEDS CLARIFICATION: number of replicates per species – default 3‑5 as sketched]**.  
- **FR-012**: System MUST report multiple‑testing correction method as **[NEEDS CLARIFICATION: Bonferroni or Benjamini‑Hochberg for enrichment?]** (default set to Bonferroni in FR‑007).

### Key Entities *(include if feature involves data)*

- **RNASeqSample**: Represents a single SRA run; attributes include `accession_id`, `species`, `fastq_path`.  
- **SplicingEvent**: Represents an alternative splicing locus; attributes include `event_id`, `gene_id`, `delta_psi`, `fdr`, `flank_seq`, `phyloP_score`, `dN_dS`.  
- **EnrichmentResult**: Stores statistical outcome per lineage; attributes include `lineage`, `odds_ratio`, `p_value`, `p_adj`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The end‑to‑end pipeline processes **≥ 90 %** of supplied samples without fatal errors (as recorded in `pipeline.log`).  
- **SC-002**: At least **100** lineage‑specific splicing events are identified per primate lineage meeting the ΔPSI/FDR thresholds.  
- **SC-003**: Enrichment analysis yields a **statistically significant (Bonferroni‑adjusted p < 0.05)** association for **≥ 30 %** of lineages, confirming a non‑random overlap with positively selected regions.  
- **SC-004**: The generated Manhattan plot correctly displays chromosome positions and includes a visible significance line; visual inspection by a domain expert rates the plot as *interpretable* (≥ 4/5 on a 5‑point Likert scale).  

## Assumptions

- SRA datasets for each species contain **≥ 10 million paired‑end reads** per sample, providing sufficient coverage for splice‑junction detection.  
- Reference genome FASTA and annotation GTF files for GRCh38, panTro6, rheMac10, and calJac4 are publicly accessible and compatible with STAR and SUPPA2.  
- PhyloP 100‑way conservation scores are available for all intronic regions of interest via the UCSC Table Browser.  
- The computational environment offers **≥ 8 CPU cores**, **≥ 32 GB RAM**, and **≥ 200 GB** of disk space for intermediate files.  
- Users have basic command‑line proficiency and can install required third‑party tools (STAR, SUPPA2, bedtools, PAML, R/Python for statistics).  
- The project will be executed within a **single‑node** HPC allocation; distributed computing is out of scope for v1.

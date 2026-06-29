# Feature Specification: Evolutionary Pressure on Alternative Splicing in Primates

**Feature Branch**: `PROJ-002-001-evolutionary-pressure`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “Investigate how alternative splicing divergence in primate cortex correlates with positive selection on splicing regulatory elements by analysing RNA‑seq data from human, chimpanzee, macaque and marmoset and integrating genomic selection metrics.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Quantify lineage‑specific splicing events (Priority: P1) (See US-1)

A researcher wants to download publicly available cortex RNA‑seq datasets for the four primate species, align the reads, and compute percent‑spliced‑in (PSI) values so that lineage‑specific splicing events can be identified.

**Why this priority**: This is the core data‑generation step; without reliable PSI estimates no downstream evolutionary analysis is possible.

**Independent Test**: Execute the pipeline on a single sample per species and verify that a PSI table is produced and that at least one splice junction is reported per sample.

**Acceptance Scenarios**:

1. **Given** a list of SRA accession IDs (e.g., GSE123456 for human), **When** the pipeline is run, **Then** FASTQ files are downloaded and stored in a designated `raw/` folder.
2. **Given** downloaded FASTQ files, **When** STAR alignment is invoked, **Then** each sample produces a sorted BAM file within ≤2 h on an 8‑core CPU node.

*(Serves FR-001, FR-002, FR-003, FR-004, FR-010, FR-011)*

---

### User Story 2 – Annotate regulatory regions surrounding splicing events (Priority: P2) (See US-2)

A researcher needs the ±500 bp intronic sequences flanking each identified alternatively spliced exon and wants to attach phyloP conservation scores and an accelerated‑evolution flag for the flanking region.

**Why this priority**: Annotation provides the genomic context required to test for accelerated evolution in regulatory elements.

**Independent Test**: Run the annotation module on a pre‑filtered list of 50 splicing events and confirm that a BED file with sequence coordinates and a CSV file with phyloP scores and acceleration flags are generated.

**Acceptance Scenarios**:

1. **Given** a list of exon coordinates, **When** `bedtools getfasta` is executed, **Then** a FASTA file containing the ±500 bp flanking sequences is created for every exon.
2. **Given** the FASTA file, **When** phyloP scores are queried from the UCSC 100‑way alignment, **Then** each sequence receives an average phyloP score and an “accelerated” boolean recorded in the annotation table.

*(Serves FR-005, FR-006)*

---

### User Story 3 – Test enrichment of splicing events in accelerated regulatory regions (Priority: P3) (See US-3)

A researcher wants to statistically assess whether lineage‑specific splicing events are enriched in regions showing signatures of accelerated evolution and visualise the results.

**Why this priority**: This delivers the primary scientific answer to the research question.

**Independent Test**: Perform the enrichment analysis on the full dataset and verify that a Manhattan‑style plot is produced with a significance line at *p* < 0.05 (Bonferroni‑corrected) and that the automated validation script passes.

**Acceptance Scenarios**:

1. **Given** the annotated event table, **When** a Fisher’s exact test is run, **Then** an enrichment *p*‑value and odds ratio are reported for each lineage, after phylogenetic correction (FR-013).
2. **Given** the test results, **When** the plotting script is executed, **Then** a PNG image showing chromosomes on the x‑axis and –log₁₀(*p*) on the y‑axis is saved, with peaks exceeding the corrected threshold highlighted.

*(Serves FR-007, FR-008, FR-012, FR-013)*

---

### Edge Cases

- What happens when a species has fewer than 3 RNA‑seq samples meeting the minimum read‑depth requirement?  
  *The pipeline aborts with an informative error (enforced by FR-011).*
- How does the system handle flanking intronic regions that overlap assembly gaps or lack phyloP scores?  
  *Missing scores are recorded as `NA`; such events are excluded from the enrichment test.*
- What is the behaviour if STAR alignment fails for a sample (e.g., due to corrupted FASTQ)?  
  *The failure is logged (FR-009) and the pipeline halts, allowing the user to correct the input.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download RNA‑seq FASTQ files from NCBI SRA given a user‑provided list of accession IDs. (See US-1)
- **FR-002**: System MUST align reads to the appropriate reference genome (GRCh38, panTro6, rheMac10, calJac4) using STAR with default parameters, completing each alignment within **≤ 2 hours** on an 8‑core CPU node. (See US-1)
- **FR-003**: System MUST quantify splice junction usage and compute PSI values with SUPPA, outputting a unified TSV file containing `gene_id`, `event_id`, `PSI_sample1…PSI_sampleN`. (See US-1)
- **FR-004**: System MUST identify lineage‑specific splicing events using **ΔPSI > 0.1** and **Benjamini‑Hochberg FDR < 0.05**; results are stored in `lineage_specific_events.tsv`. (See US-1)
- **FR-005**: System MUST extract **±500 bp** flanking intronic sequences for each event using bedtools and retrieve the **average phyloP score** from the UCSC 100‑way alignment. (See US-2)
- **FR-006**: System MUST compute an **accelerated‑evolution flag** for each flanking region: flag = TRUE if the average phyloP ≤ ‑2.0 (indicative of accelerated evolution); otherwise FALSE. (See US-2)
- **FR-007**: System MUST perform a Fisher’s exact test for enrichment of lineage‑specific events that have the accelerated‑evolution flag TRUE. The raw *p*‑values are corrected across lineages using **Benjamini‑Hochberg FDR ≤ 0.05** (FR-012) and within each lineage using **Bonferroni correction**; subsequently, phylogenetic correction is applied as described in FR-013. Significant results are those with corrected *p* < 0.05. (See US-3)
- **FR-008**: System MUST generate a Manhattan‑style plot (PNG, **≥ 1200 × 800 px**) visualising –log₁₀(*p*) per chromosome, with a horizontal line indicating the significance threshold. (See US-3)
- **FR-009**: System MUST log all major steps (download, alignment, quantification, annotation, statistical test) to a `pipeline.log` file with timestamps and exit codes.  
- **FR-010**: System MUST retain raw FASTQ files for **≥ 90 days** on local storage; after this period the files are **compressed and deposited to Zenodo** (recorded DOI stored in `metadata.json`), and the local copies are **deleted**. Metadata (accession IDs, checksums, DOI) must be retained for **5 years** to satisfy reproducibility requirements (see Constitution Principle II). (See US-1)
- **FR-011**: System MUST enforce a **minimum of 3 biological replicates per species**; if fewer are provided the pipeline aborts with error code 101. An optional flag `--max-replicates 5` allows up to 5 replicates when computational resources are sufficient, otherwise the default is 3. This ensures **≥ 80 % power at α = 0.05** for detecting **ΔPSI ≥ 0.1** (see Love et al., 2014). (See US-1)
- **FR-012**: System MUST apply **Benjamini‑Hochberg FDR ≤ 0.05** for the set of enrichment tests *across* lineages (4 tests) and **Bonferroni correction** (α = 0.05 / N_events) for the set of tests *within* each lineage. The corrected *p*‑values are stored in the results table. (See US-3)
- **FR-013**: System MUST adjust enrichment *p*‑values for phylogenetic non‑independence using **Phylogenetic Generalized Least Squares (PGLS)** as implemented in the R package **caper**. The primate species tree (Newick file `primate_tree.nwk`) is supplied; the model regresses the binary presence/absence of accelerated events on lineage while accounting for shared ancestry. Adjusted *p*‑values replace the raw Fisher’s test *p*‑values before multiple‑testing correction. (See US-3)

### Key Entities *(include if feature involves data)*

- **RNASeqSample**: Represents a single SRA run; attributes include `accession_id`, `species`, `fastq_path`.  
- **SplicingEvent**: Represents an alternative splicing locus; attributes include `event_id`, `gene_id`, `delta_psi`, `fdr`, `flank_seq`, `phyloP_score`, `accelerated_flag`.  
- **EnrichmentResult**: Stores statistical outcome per lineage; attributes include `lineage`, `odds_ratio`, `p_raw`, `p_corrected_phylo`, `p_adj`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The end‑to‑end pipeline processes **≥ 90 %** of supplied samples without fatal errors (as recorded in `pipeline.log`).  
- **SC-002**: Number of lineage‑specific splicing events identified per lineage will be measured (deferred to analysis phase).  
- **SC-003**: Enrichment analysis significance (fraction of lineages with adjusted *p* < 0.05) will be measured (deferred to analysis phase).  
- **SC-004**: The generated Manhattan plot must satisfy automated validation: PNG dimensions **≥ 1200 × 800 px**, X‑axis labeled “Chromosome”, Y‑axis labeled “–log₁₀(p)”, a title present, and a horizontal line at the Bonferroni‑corrected significance threshold. Validation is performed by the script `validate_plot.py`; passing the script constitutes meeting SC‑004.

## Assumptions

- SRA datasets for each species contain **≥ 10 million paired‑end reads** per sample, providing sufficient coverage for splice‑junction detection.  
- Reference genome FASTA and annotation GTF files for GRCh38, panTro6, rheMac10, and calJac4 are publicly accessible and compatible with STAR and SUPPA2.  
- PhyloP 100‑way conservation scores are available for all intronic regions of interest via the UCSC Table Browser.  
- The computational environment offers **≥ 8 CPU cores**, **≥ 32 GB RAM**, and **≥ 200 GB** of disk space for intermediate files.  
- Users have basic command‑line proficiency and can install required third‑party tools (STAR, SUPPA2, bedtools, R/Python for statistics).  
- The project will be executed within a **single‑node** HPC allocation; distributed computing is out of scope for v1.  

## References

- Dobin, A. *et al.* (2013). STAR: Ultrafast universal RNA‑seq aligner. *Bioinformatics*, 29(1), 15‑21.  
- Trincado, J. L. *et al.* (2018). SUPPA2: Fast, accurate, and uncertainty‑aware differential splicing analysis across multiple conditions. *Genome Biology*, 19, 40.  
- Siepel, A. *et al.* (2005). Evolutionarily conserved elements in vertebrate genomes. *Genome Research*, 15(8), 1034‑1050.  
- Love, M. I., Huber, W., & Anders, S. (2014). Moderated estimation of fold change and dispersion for RNA‑seq data with DESeq2. *Genome Biology*, 15, 550.  
- Pagel, M. (1999). Inferring the historical patterns of biological evolution. *Nature*, 401, 877‑884. (PGLS methodology)  
- R package **caper** (Orme, D. *et al.*, 2023). Comparative analysis of phylogenetics and evolution in R.

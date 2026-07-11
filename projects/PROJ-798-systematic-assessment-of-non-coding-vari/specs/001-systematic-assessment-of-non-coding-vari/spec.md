# Feature Specification: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Regulatory Context Filtering (Priority: P1)

The researcher must be able to download common human SNPs (MAF > 1%) from dbSNP build 155 and filter them to those located within annotated regulatory regions (promoters/enhancers) using specific ENCODE/Roadmap BED files, while also generating a GC-matched non-regulatory control set for baseline comparison.

**Why this priority**: This is the foundational data preparation step. Without a clean, context-filtered dataset of SNPs and their corresponding motif models, no affinity scoring or statistical analysis can occur. It delivers a validated input dataset for downstream steps and establishes a baseline to control for ascertainment bias.

**Independent Test**: Can be fully tested by verifying the output of the filtering script: a list of SNPs with genomic coordinates that overlap at least one regulatory region BED interval, a list of GC-matched non-regulatory control SNPs, and a log confirming the exact source URLs and build versions used.

**Acceptance Scenarios**:

1. **Given** a raw dbSNP VCF file (build 155) and a set of ENCODE promoter BED files (v4), **When** the filtering pipeline is executed, **Then** the output contains only SNPs with coordinates overlapping the provided BED regions, and a separate file of GC-matched non-regulatory control SNPs.
2. **Given** a JASPAR 2024 PWM file, **When** the system loads it, **Then** all human TF matrices are parsed and stored with their unique IDs and sequence lengths ready for dynamic scoring.
3. **Given** a SNP with MAF < 1% or from a non-human species, **When** the pipeline processes it, **Then** it is excluded from the downstream analysis dataset.

---

### User Story 2 - Allele-Specific Binding Affinity Scoring (Priority: P2)

The researcher must be able to calculate the difference in binding affinity ($\Delta Score$) between reference and alternate alleles for every SNP-TF pair using a dynamic context window that matches the PWM length.

**Why this priority**: This is the core computational engine of the study. It transforms raw sequence data into the quantitative metric ($\Delta Score$) required to test the hypothesis about TF sensitivity. It can be tested independently of the statistical aggregation or GWAS overlap.

**Independent Test**: Can be fully tested by running the scorer on a small, manually verified subset of SNPs and comparing the calculated $\Delta Score$ against a manual calculation or a known reference tool (e.g., FIMO) using the exact PWM length, ensuring mathematical correctness.

**Acceptance Scenarios**:

1. **Given** a SNP with known reference 'A' and alternate 'G' at a specific coordinate, **When** the scorer processes a window equal to the PWM length (centered on the variant) for a specific TF PWM, **Then** it outputs a numeric $\Delta Score$ reflecting the change in log-odds score.
2. **Given** a SNP where the alternate allele perfectly matches the consensus motif, **When** scored, **Then** the $\Delta Score$ is positive and significant compared to the reference.
3. **Given** a SNP where the reference allele matches the consensus and the alternate disrupts it, **When** scored, **Then** the $\Delta Score$ is negative.

---

### User Story 3 - Statistical Enrichment and GWAS Overlap Analysis (Priority: P3)

The researcher must be able to aggregate $\Delta Score$ distributions per TF, perform a label-shuffling permutation test to generate a null distribution, and cross-reference the full distribution of $\Delta Scores$ with GWAS Catalog lead SNPs using a Kolmogorov-Smirnov test to assess enrichment, applying a West-Stephens max-T permutation FDR correction for multiple testing.

**Why this priority**: This step synthesizes the individual scores into a biological conclusion, testing the main hypothesis (enrichment in disease loci). It relies on the output of US-2 and is the final analytical deliverable.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset where the enrichment status is known (e.g., a subset of SNPs artificially injected into GWAS loci) and verifying the Kolmogorov-Smirnov test correctly identifies the enrichment with a p-value < 0.05 after correction.

**Acceptance Scenarios**:

1. **Given** a distribution of $\Delta Scores$ for TF-X and a null distribution from 100 label shuffles (swapping ref/alt scores within the same SNP), **When** the test runs, **Then** it outputs a p-value indicating if TF-X is significantly more disrupted than random.
2. **Given** the full distribution of $\Delta Scores$ and a GWAS Catalog lead SNP BED file, **When** the enrichment analysis runs, **Then** it reports the Kolmogorov-Smirnov statistic and a p-value indicating the shift in the distribution towards GWAS loci.
3. **Given** a TF known to be associated with a disease (e.g., TCF7L2 for Type 2 Diabetes), **When** analyzed, **Then** the enrichment test returns a significant p-value (< 0.05 corrected), validating the system's ability to detect true positives.

### Edge Cases

- **What happens when** a SNP falls exactly on the boundary of a regulatory region? (System must include it if the overlap is ≥ 1bp).
- **How does the system handle** SNPs where the reference or alternate allele is not A/C/G/T (e.g., N or indels)? (System must exclude these from scoring to avoid NaN errors).
- **How does the system handle** TFs with very few PWM matches in the regulatory regions? (System must flag them as having insufficient data for statistical testing rather than crashing).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download common human SNPs (MAF > 1%) from dbSNP build 155 (GRCh38) via the explicit FTP path `ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/` and filter them to those located within annotated regulatory regions (promoters/enhancers) using ENCODE v4 (URL: `https://www.encodeproject.org/files/ENCFF000...`) and Roadmap Epigenomics BED files. Additionally, the system MUST generate a non-regulatory control set of SNPs from random genomic regions matched for GC content (within ±2% of the matched SNP's GC%) to establish a valid baseline and mitigate ascertainment bias. (See US-1)
- **FR-002**: System MUST load JASPAR 2024 PWMs for human TFs and calculate binding affinity scores for both reference and alternate alleles of each filtered SNP using a **dynamic context window** where the window size equals the PWM length (centered on the variant). (See US-2)
- **FR-003**: System MUST compute the difference in binding affinity ($\Delta Score = Score_{alt} - Score_{ref}$) for every valid SNP-TF pair, and ONLY flag results as 'biologically significant' if the absolute $\Delta Score$ is ≥ 2 bits. (See US-2)
- **FR-004**: System MUST perform a permutation test (n=100) by **shuffling SNP labels** (swapping ref/alt scores within the same SNP) to generate a null distribution for each TF's $\Delta Score$ distribution, preserving the local sequence context and GC content. (See US-3)
- **FR-005**: System MUST assess the enrichment of $\Delta Scores$ in GWAS loci using a **Kolmogorov-Smirnov (KS) test** on the FULL distribution of scores (not a top-k subset) against the null distribution, cross-referencing with GWAS Catalog lead SNPs from `ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/` (downloaded on [DATE]), ensuring the test accounts for the baseline regulatory enrichment. (See US-3)
- **FR-006**: System MUST apply a **West-Stephens max-T permutation FDR** method to the p-values generated from the permutation tests across all TFs. This method MUST preserve the joint distribution of scores across correlated TF motifs by permuting SNP labels across all TFs simultaneously, and MUST use the Benjamini-Hochberg procedure for initial correction if West-Stephens is not fully implemented, to control the false discovery rate. (See US-3)
- **FR-007**: System MUST calculate and output a p-value for each TF indicating the statistical significance of the enrichment test (KS statistic) derived from the comparison of the observed distribution against the null distribution. (See US-3)
- **FR-008**: System MUST apply a significance threshold of α = 0.05 (corrected for multiple testing) to the output p-values to determine which TFs are significantly enriched. (See US-3)

### Non-Functional Requirements

- **NFR-001**: The full analysis pipeline (data fetch to final report) MUST complete within 6 hours on a standard free-tier CI runner (2 CPU, 7GB RAM) by utilizing batched processing and limiting permutation counts to 100 per TF. (See Assumptions)
- **NFR-002**: The memory usage of the affinity scoring and permutation steps MUST remain within the available RAM limits of standard CI runners to ensure no OOM failures. (See Assumptions)

### Key Entities

- **SNP**: A genomic variant characterized by chromosome, position, reference allele, alternate allele, minor allele frequency (MAF), quality score, and GC content of the local context.
- **RegulatoryRegion**: A genomic interval (start, end, strand, type) annotated as a promoter or enhancer.
- **PWM**: A Position Weight Matrix representing the binding preference of a specific Transcription Factor, with an explicit length attribute (base pairs).
- **AffinityScore**: A numeric value representing the log-odds probability of a sequence matching a PWM.
- **DeltaScore**: The numeric difference between the affinity score of the alternate allele and the reference allele.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of SNPs successfully scored (valid alleles, valid context) is measured against the total number of input SNPs to ensure data integrity. (See FR-001, FR-002)
- **SC-002**: The deviation of the observed $\Delta Score$ distribution from the null distribution is measured against the p-value threshold (α = 0.05, corrected using West-Stephens max-T) to determine statistical significance. This includes a distinct validation step applying the threshold to the final p-values. (See FR-004, FR-006, FR-007, FR-008)
- **SC-003**: The enrichment ratio of high-impact SNPs in GWAS loci is measured against the expected random overlap count to validate the hypothesis. (See FR-005)

## Assumptions

- **Assumption about data availability**: The dbSNP FTP server (build 155) and JASPAR database are accessible and provide the required datasets (common SNPs, human PWMs) in a format parseable by standard Python libraries (biopython, pandas) without requiring proprietary credentials.
- **Assumption about computational constraints**: The total dataset of common SNPs (MAF > 1%) from dbSNP build 155 (source: dbSNP Common release, size [deferred]) will fit within the 7 GB RAM limit of the free-tier CI runner when processed in batches or via memory-mapped files; no GPU is required or available for this analysis.
- **Assumption about methodology**: The use of Position Weight Matrices (PWMs) from JASPAR is an accepted and valid proxy for TF binding affinity changes, despite ignoring chromatin accessibility and cooperative binding effects, as per the study's scope.
- **Assumption about threshold justification**: The "2 bits" cutoff for biological significance is a standard threshold in the field for log-odds score changes; a sensitivity analysis sweeping this cutoff over {1.5, 2.0, 2.5} bits will be performed to verify result robustness.
- **Assumption about inference framing**: Since this is an observational study using existing GWAS data, all conclusions regarding "disruption" and "enrichment" will be framed as associational, not causal, in the final report.
- **Assumption about dataset-variable fit**: The ENCODE/Roadmap BED files provided contain the necessary regulatory annotations to accurately define the "regulatory regions" for the SNPs; if a specific tissue context is required but missing, the analysis will default to a union of all available enhancer/promoter annotations.
- **Assumption about runtime**: The reduction of permutation counts to 100 per TF and the use of batched processing will ensure the analysis completes within the 6-hour runtime constraint on a 2-CPU runner.
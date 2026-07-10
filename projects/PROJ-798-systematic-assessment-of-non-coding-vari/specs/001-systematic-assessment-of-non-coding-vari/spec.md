# Feature Specification: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Regulatory Context Filtering (Priority: P1)

The researcher must be able to download common human SNPs (MAF > 1%) from dbSNP and JASPAR PWMs, then filter SNPs to those located within annotated regulatory regions (promoters/enhancers) using ENCODE/Roadmap BED files.

**Why this priority**: This is the foundational data preparation step. Without a clean, context-filtered dataset of SNPs and their corresponding motif models, no affinity scoring or statistical analysis can occur. It delivers a validated input dataset for downstream steps.

**Independent Test**: Can be fully tested by verifying the output of the filtering script: a list of SNPs with genomic coordinates that overlap at least one regulatory region BED interval, with no SNPs outside these regions included.

**Acceptance Scenarios**:

1. **Given** a raw dbSNP VCF file and a set of ENCODE promoter BED files, **When** the filtering pipeline is executed, **Then** the output contains only SNPs with coordinates overlapping the provided BED regions.
2. **Given** a JASPAR 2024 PWM file, **When** the system loads it, **Then** all human TF matrices are parsed and stored with their unique IDs and sequence logos ready for scoring.
3. **Given** a SNP with MAF < 1%, **When** the pipeline processes it, **Then** it is excluded from the downstream analysis dataset.

---

### User Story 2 - Allele-Specific Binding Affinity Scoring (Priority: P2)

The researcher must be able to calculate the difference in binding affinity ($\Delta Score$) between reference and alternate alleles for every SNP-TF pair within a ±10bp context window using the loaded PWMs.

**Why this priority**: This is the core computational engine of the study. It transforms raw sequence data into the quantitative metric ($\Delta Score$) required to test the hypothesis about TF sensitivity. It can be tested independently of the statistical aggregation or GWAS overlap.

**Independent Test**: Can be fully tested by running the scorer on a small, manually verified subset of SNPs and comparing the calculated $\Delta Score$ against a manual calculation or a known reference tool (e.g., FIMO or PWM-Scan) to ensure mathematical correctness.

**Acceptance Scenarios**:

1. **Given** a SNP with known reference 'A' and alternate 'G' at a specific coordinate, **When** the scorer processes the ±10bp window for a specific TF PWM, **Then** it outputs a numeric $\Delta Score$ reflecting the change in log-odds score.
2. **Given** a SNP where the alternate allele perfectly matches the consensus motif, **When** scored, **Then** the $\Delta Score$ is positive and significant compared to the reference.
3. **Given** a SNP where the reference allele matches the consensus and the alternate disrupts it, **When** scored, **Then** the $\Delta Score$ is negative.

---

### User Story 3 - Statistical Enrichment and GWAS Overlap Analysis (Priority: P3)

The researcher must be able to aggregate $\Delta Score$ distributions per TF, perform a permutation test against a shuffled null distribution (constrained to regulatory regions), and cross-reference high-impact SNPs (top [deferred] by absolute $|\Delta Score|$) with GWAS Catalog lead SNPs (converted to BED format) to assess enrichment.

**Why this priority**: This step synthesizes the individual scores into a biological conclusion, testing the main hypothesis (enrichment in disease loci). It relies on the output of US-2 and is the final analytical deliverable.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset where the enrichment status is known (e.g., a subset of SNPs artificially injected into GWAS loci) and verifying the permutation test correctly identifies the enrichment with a p-value < 0.05.

**Acceptance Scenarios**:

1. **Given** a distribution of $\Delta Scores$ for TF-X and a null distribution from 1000 permutations (shuffled within regulatory regions), **When** the test runs, **Then** it outputs a p-value indicating if TF-X is significantly more disrupted than random.
2. **Given** a set of high-impact SNPs (top [deferred] by $|\Delta Score|$) and a GWAS Catalog lead SNP BED file, **When** the overlap analysis runs, **Then** it reports the observed vs. expected overlap count and an enrichment ratio.
3. **Given** a TF with no known disease association, **When** analyzed, **Then** the enrichment test returns a non-significant p-value (e.g., > 0.05) unless a false positive occurs.

### Edge Cases

- **What happens when** a SNP falls exactly on the boundary of a regulatory region? (System must include it if the overlap is ≥ 1bp).
- **How does the system handle** SNPs where the reference or alternate allele is not A/C/G/T (e.g., N or indels)? (System must exclude these from scoring to avoid NaN errors).
- **How does the system handle** TFs with very few PWM matches in the regulatory regions? (System must flag them as having insufficient data for statistical testing rather than crashing).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download common human SNPs (MAF > 1%) from dbSNP and filter them to those located within annotated regulatory regions (promoters/enhancers) using provided BED files. (See US-1)
- **FR-002**: System MUST load JASPAR 2024 PWMs for human TFs and calculate binding affinity scores for both reference and alternate alleles of each filtered SNP within a ±10bp context window. (See US-2)
- **FR-003**: System MUST compute the difference in binding affinity ($\Delta Score = Score_{alt} - Score_{ref}$) for every valid SNP-TF pair. (See US-2)
- **FR-004**: System MUST perform a permutation test (n=1000) by shuffling SNP positions within the same annotated regulatory regions to generate a null distribution for each TF's $\Delta Score$ distribution, preserving the genomic context. (See US-3)
- **FR-005**: System MUST identify high-impact SNPs (top [deferred] by absolute $|\Delta Score|$, configurable) and calculate the statistical enrichment of these SNPs within GWAS Catalog lead SNP loci, ensuring the enrichment test accounts for the baseline regulatory enrichment. (See US-3)
- **FR-006**: System MUST apply a permutation-based FDR estimation method (e.g., Storey-Tibshirani or custom permutation FDR) to the p-values generated from the permutation tests across all TFs to control the false discovery rate, accounting for the dependence structure between correlated TF motifs. (See US-3)

### Non-Functional Requirements

- **NFR-001**: The full analysis pipeline (data fetch to final report) MUST complete within 6 hours on a standard free-tier CI runner. (See Assumptions)
- **NFR-002**: The memory usage of the affinity scoring and permutation steps MUST remain within the available RAM limits of standard CI runners to ensure no OOM failures. (See Assumptions)

### Key Entities

- **SNP**: A genomic variant characterized by chromosome, position, reference allele, alternate allele, and minor allele frequency (MAF).
- **RegulatoryRegion**: A genomic interval (start, end, strand, type) annotated as a promoter or enhancer.
- **PWM**: A Position Weight Matrix representing the binding preference of a specific Transcription Factor.
- **AffinityScore**: A numeric value representing the log-odds probability of a sequence matching a PWM.
- **DeltaScore**: The numeric difference between the affinity score of the alternate allele and the reference allele.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of SNPs successfully scored (valid alleles, valid context) is measured against the total number of input SNPs to ensure data integrity. (See FR-001, FR-002)
- **SC-002**: The deviation of the observed $\Delta Score$ distribution from the null distribution is measured against the p-value threshold (α = 0.05, corrected) to determine statistical significance. (See FR-004)
- **SC-003**: The enrichment ratio of high-impact SNPs in GWAS loci is measured against the expected random overlap count to validate the hypothesis. (See FR-005)

## Assumptions

- **Assumption about data availability**: The dbSNP FTP server and JASPAR database are accessible and provide the required datasets (common SNPs, human PWMs) in a format parseable by standard Python libraries (biopython, pandas) without requiring proprietary credentials.
- **Assumption about computational constraints**: The total dataset of common SNPs (MAF > 1%) and their context sequences will fit within the 7 GB RAM limit of the free-tier CI runner when processed in batches or via memory-mapped files; no GPU is required or available for this analysis.
- **Assumption about methodology**: The use of Position Weight Matrices (PWMs) from JASPAR is an accepted and valid proxy for TF binding affinity changes, despite ignoring chromatin accessibility and cooperative binding effects, as per the study's scope.
- **Assumption about threshold justification**: The "top [deferred]" cutoff for high-impact SNPs is a standard exploratory threshold for prioritization in this domain; a sensitivity analysis sweeping this cutoff across top [deferred], [deferred], and [deferred] will be performed to verify result robustness.
- **Assumption about inference framing**: Since this is an observational study using existing GWAS data, all conclusions regarding "disruption" and "enrichment" will be framed as associational, not causal, in the final report.
- **Assumption about dataset-variable fit**: The ENCODE/Roadmap BED files provided contain the necessary regulatory annotations to accurately define the "regulatory regions" for the SNPs; if a specific tissue context is required but missing, the analysis will default to a union of all available enhancer/promoter annotations.
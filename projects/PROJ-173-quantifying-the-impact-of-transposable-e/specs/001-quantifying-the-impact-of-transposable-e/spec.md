# Feature Specification: Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core TE-Gene Association Analysis Pipeline (Priority: P1)

A researcher downloads DGRP genotype and expression data, runs the association analysis pipeline, and obtains a table of significant TE-gene pairs with effect sizes and FDR-corrected p-values.

**Why this priority**: This is the minimum viable product that answers the core research question. Without this pipeline, the project cannot produce any scientific results.

**Independent Test**: Can be fully tested by running the pipeline on a sample subset of DGRP lines (e.g., 50 genotypes) and verifying that the output table contains TE-gene pairs with proper statistical metrics.

**Acceptance Scenarios**:

1. **Given** DGRP genotype VCF and RNA-seq expression data for ≥50 lines, **When** the pipeline executes the linear model association analysis, **Then** the output table contains ≥1 TE-gene pair with FDR < 0.05 or explicitly reports null findings with complete test statistics.
2. **Given** population structure PCs computed from genome-wide SNPs, **When** the linear model `gene_expression ~ TE_presence + PC1 + PC2 + PC3` is fit, **Then** the output includes effect size (log₂-fold change), 95% confidence interval, unadjusted p-value, and adjusted p-value for each tested pair.
3. **Given** ≥5,000 TE-gene pairs tested, **When** Benjamini–Hochberg correction is applied, **Then** the adjusted p-values are computed and the false discovery rate is ≤0.05 for retained pairs.

---

### User Story 2 - Independent Dataset Replication (Priority: P2)

A researcher validates significant TE-gene associations by testing them on an independent DGRP expression dataset from a different tissue or developmental stage.

**Why this priority**: Replication strengthens the reliability of findings and distinguishes true biological signals from dataset-specific artifacts.

**Independent Test**: Can be fully tested by running the association analysis on a second expression dataset (e.g., modENCODE) and calculating the replication concordance rate (proportion of significant associations with consistent direction) to assess robustness against random chance.

**Acceptance Scenarios**:

1. **Given** ≥10 significant TE-gene pairs from the primary analysis (FDR < 0.05), **When** the same associations are tested on an independent expression dataset, **Then** the system reports the proportion of pairs showing consistent direction of effect with p < 0.05 in the replication dataset.
2. **Given** replication test results, **When** the system generates a comparison table, **Then** the table includes original effect size, replication effect size, direction concordance flag, and replication p-value for each pair.
3. **Given** missing expression data for a line in the replication dataset, **When** the analysis pipeline encounters the missing value, **Then** the line is excluded from that specific test without crashing the entire replication run.

---

### User Story 3 - Permutation Testing for Robustness Validation (Priority: P3)

A researcher performs permutation testing to confirm that observed TE-gene associations exceed random expectation, providing evidence that signals are not artifacts of population structure or multiple testing.

**Why this priority**: Permutation testing adds a layer of robustness validation but is not strictly required to answer the core research question.

**Independent Test**: Can be fully tested by running multiple permutations of TE presence labels and verifying that the observed raw test statistic exceeds the 95th percentile of the null distribution generated from permuted data.

**Acceptance Scenarios**:

1. **Given** 100 permutation runs where TE presence labels are shuffled, **When** the association analysis is re-run on each permuted dataset to generate a null distribution of raw t-statistics, **Then** the observed raw t-statistic for significant pairs exceeds the 95th percentile of the null distribution.
2. **Given** permutation results, **When** the system generates a null distribution plot, **Then** the plot shows the observed statistic as a vertical line with the 95th percentile threshold clearly marked.
3. **Given** a permutation run that exceeds the 6-hour CI time limit, **When** the job is interrupted, **Then** the system saves intermediate results and reports the number of completed permutations without data loss.

---

### Edge Cases

- What happens when a TE insertion is present in ≥95% or ≤5% of DGRP lines (monomorphic or nearly monomorphic variants cannot be tested for association)?
- How does the system handle gene expression values of zero or near-zero (TPM < 0.001) in the linear model?
- What if the TE annotation VCF contains coordinates that overlap multiple genes (ambiguous TE-gene proximity assignment)?
- How does the pipeline behave when RNA-seq data for a DGRP line is missing from the public repository?
- What if population structure PCs show high collinearity with TE presence (variance inflation factor > 5)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download DGRP genotype VCF including TE genotype calls and RNA-seq expression data for ≥50 DGRP lines from public repositories (See US-1)
- **FR-002**: System MUST define proximal TE-gene pairs as those where TE insertion site lies ≤5 kb upstream or downstream of gene transcription start/end using Drosophila release 6 gene models (See US-1)
- **FR-003**: System MUST compute population structure PCs from genome-wide SNP genotypes and include PC1, PC2, PC3 as covariates in the linear model to control for population stratification (See US-1)
- **FR-004**: System MUST fit linear model `gene_expression ~ TE_presence + PC1 + PC2 + PC3` for each TE-gene pair and output effect size, 95% CI, unadjusted p-value, and Benjamini-Hochberg adjusted p-value (See US-1)
- **FR-005**: System MUST apply Benjamini–Hochberg correction across all tested TE-gene pairs and retain pairs with adjusted p-value < 0.05 (See US-1)
- **FR-006**: System MUST perform permutation testing with ≥100 random shuffles of TE presence labels to establish null distribution of raw test statistics (See US-3)
- **FR-007**: System MUST compute collinearity diagnostics (variance inflation factor) for TE presence and population structure PCs; if VIF > 5, flag the pair for descriptive reporting only (See US-1)
- **FR-008**: System MUST exclude monomorphic TEs (presence frequency < 5% or > 95%) from association testing (See US-1)
- **FR-009**: System MUST handle missing expression data by excluding affected lines from individual tests without crashing the pipeline (See US-2)
- **FR-010**: System MUST generate comparison table for replication analysis including original effect size, replication effect size, direction concordance, and replication p-value (See US-2)

### Key Entities

- **TE Insertion**: Genomic coordinate, TE family, presence/absence genotype per DGRP line, frequency across lines
- **Gene Expression**: Gene identifier, TPM or log₂-transformed expression value per DGRP line, tissue/developmental stage metadata
- **TE-Gene Pair**: TE identifier, gene identifier, genomic distance (bp), proximal flag (≤5 kb threshold), association statistics
- **Population Structure**: PC1, PC2, PC3 values per DGRP line derived from genome-wide SNPs

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Number of significant TE-gene associations (FDR < 0.05) is measured against the null expectation from permutation testing to confirm signal exceeds random chance (See US-1)
- **SC-002**: Replication concordance rate (proportion of significant associations with consistent direction in independent dataset) is measured against the null expectation of random chance to assess robustness (See US-2)
- **SC-003**: False discovery rate is measured against the Benjamini–Hochberg adjusted p-value threshold of < 0.05 to control for multiple testing across ≥5,000 TE-gene pairs (See US-1)
- **SC-004**: Population structure control efficacy is measured by comparing model fit (R²) with and without PC covariates; the reduction in residual variance is reported to indicate confounding control (See US-1)
- **SC-005**: Permutation null distribution 95th percentile is measured against observed raw test statistics; observed statistic must exceed null 95th percentile for valid associations (See US-3)
- **SC-006**: Collinearity diagnostic VIF is measured against threshold of 5; pairs exceeding this threshold are flagged for descriptive reporting only rather than causal inference claims (See US-1)

## Assumptions

- DGRP genotype VCF from ftp://ftp.flybase.net/genomes/Drosophila/DGRP/ contains all polymorphic TE genotype calls needed for the analysis
- RNA-seq expression data from NCBI SRA accession SRPXXXXX or modENCODE covers ≥50 DGRP lines with sufficient read depth for reliable TPM quantification
- Drosophila release 6 gene models provide accurate transcription start/end coordinates for defining the ≤5 kb proximal window
- Population structure PCs derived from genome-wide SNPs adequately capture stratification; if not, additional PCs may be needed
- Benjamini–Hochberg correction is appropriate for the dependency structure among TE-gene tests; if tests are highly correlated, family-wise error rate control may be more conservative
- The 6-hour CI time limit on GitHub Actions free-tier is sufficient for ≥100 permutation runs on a CPU-only 2-core runner with ~7 GB RAM
- STAR 2-pass alignment and featureCounts/TEtranscripts quantification can run within the CPU-only, memory-constrained environment when processing ≤100 samples
- No GPU acceleration is available or required; all statistical modeling uses CPU-tractable methods (linear regression via MatrixEQTL)
- TE presence is treated as a binary predictor; insertion copy number variation is not modeled due to data limitations
- If the DGRP VCF lacks explicit TE genotype calls, the system MUST fail gracefully with an error message indicating missing input data; de novo calling is out of scope for this feature.
- If RNA-seq data for specific DGRP lines is unavailable, the system MUST exclude affected lines from individual tests. Imputation from similar genotypes is explicitly prohibited for expression data to prevent introducing synthetic bias into the association statistics; only lines with actual measured expression values are included in the linear model fit for any given gene.
- If population structure PCs show high collinearity with TE presence (VIF > 5), findings for those pairs will be framed as associational only, not causal (See FR-007)
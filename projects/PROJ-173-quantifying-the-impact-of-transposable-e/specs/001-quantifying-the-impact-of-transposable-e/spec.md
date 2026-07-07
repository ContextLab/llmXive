# Feature Specification: Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core TE-Gene Association Analysis Pipeline (Priority: P1)

A researcher runs the association analysis pipeline on a Mock/Synthetic Dataset (as no verified public dataset exists) and obtains a table of TE-gene pairs with effect sizes, FDR-corrected p-values, and diagnostic flags.

**Why this priority**: This is the minimum viable product that answers the core research question. Without this pipeline, the project cannot produce any scientific results.

**Independent Test**: Can be fully tested by running the pipeline on a Mock/Synthetic Dataset and verifying that the output table contains TE-gene pairs with proper statistical metrics and diagnostic flags.

**Acceptance Scenarios**:

1. **Given** a Mock/Synthetic Dataset for ≥50 lines, **When** the pipeline executes the linear model association analysis, **Then** the output table contains TE-gene pairs with columns: effect_size, ci_lower, ci_upper, p_value, adj_p_value, vif_flag, proximity_flag, ambiguous_flag, and a 'significance_status' flag indicating 'significant' or 'null'. The system MUST NOT require a biological signal to be present; it must successfully output the table even if all pairs are 'null'.
2. **Given** population structure PCs computed from genome-wide SNPs (or Mock PCs), **When** the linear model `gene_expression ~ TE_presence + PC1 + PC2 + PC3` is fit, **Then** the output includes effect size (log₂-fold change), 95% confidence interval (calculated via Wald method assuming normality of residuals, or bootstrap if normality is violated), unadjusted p-value, and adjusted p-value for each tested pair.
3. **Given** ≥5,000 TE-gene pairs tested, **When** Benjamini–Hochberg correction is applied, **Then** the adjusted p-values are computed and the false discovery rate is ≤0.05 for retained pairs.

---

### User Story 2 - Independent Dataset Replication (Priority: P2)

A researcher validates significant TE-gene associations by testing them on an independent dataset (Mock) from a different tissue or developmental stage, ensuring coordinate mapping is handled.

**Why this priority**: Replication strengthens the reliability of findings and distinguishes true biological signals from dataset-specific artifacts.

**Independent Test**: Can be fully tested by running the association analysis on a second Mock dataset and calculating the replication concordance rate to assess robustness against random chance.

**Acceptance Scenarios**:

1. **Given** ≥10 significant TE-gene pairs from the primary analysis (FDR < 0.05), **When** the same associations are tested on an independent expression dataset (after coordinate mapping), **Then** the system reports the proportion of pairs showing consistent direction of effect and performs a binomial test against a null expectation of 0.5.
2. **Given** replication test results, **When** the system generates a comparison table, **Then** the table includes original effect size, replication effect size, direction concordance flag, and replication p-value for each pair.
3. **Given** missing expression data for a line in the replication dataset, **When** the analysis pipeline encounters the missing value, **Then** the line is excluded from that specific test without crashing the entire replication run.

---

### User Story 3 - Permutation Testing for Robustness Validation (Priority: P3)

A researcher performs permutation testing to confirm that observed TE-gene associations exceed random expectation, providing evidence that signals are not artifacts of population structure or multiple testing.

**Why this priority**: Permutation testing adds a layer of robustness validation but is not strictly required to answer the core research question.

**Independent Test**: Can be fully tested by running multiple Freedman-Lane permutations of residuals and verifying that the observed raw test statistic exceeds the 95th percentile of the null distribution generated from permuted data.

**Acceptance Scenarios**:

1. **Given** 1000 permutation runs using the Freedman-Lane method (shuffling residuals of the null model `gene_expression ~ PC1 + PC2 + PC3`, adding to fitted values, and refitting the full model), **When** the association analysis is re-run on each permuted dataset to generate a null distribution of raw t-statistics, **Then** the observed raw t-statistic for significant pairs exceeds the 95th percentile of the null distribution.
2. **Given** permutation results, **When** the system generates a null distribution plot, **Then** the plot shows the observed statistic as a vertical line with the 95th percentile threshold clearly marked.
3. **Given** a permutation run that exceeds the 6-hour CI time limit, **When** the job is interrupted, **Then** the system saves intermediate results and reports the number of completed permutations without data loss.

---

### Edge Cases

- What happens when a TE insertion is present in ≥95% or ≤5% of DGRP lines (monomorphic or nearly monomorphic variants cannot be tested for association)? **System MUST exclude these TEs from testing (FR-008).**
- How does the system handle gene expression values of zero or near-zero (TPM < 0.001) in the linear model? **System MUST add a small constant (e.g., 1e-6) to avoid log(0) or zero-variance issues.**
- What if the TE annotation VCF contains coordinates that overlap multiple genes (ambiguous TE-gene proximity assignment)? **System MUST flag these pairs with 'ambiguous_flag' = true and exclude them from primary association testing (FR-011).**
- How does the pipeline behave when RNA-seq data for a DGRP line is missing from the public repository? **System MUST exclude affected lines from individual tests (FR-009).**
- What if population structure PCs show high collinearity with TE presence (variance inflation factor > 5)? **System MUST flag these pairs with 'vif_flag' = true and exclude them from causal inference claims (FR-007).**

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a Mock/Synthetic Dataset for testing because no verified public dataset containing both TE genotype calls and matched RNA-seq expression for the same DGRP lines exists. The Mock dataset MUST simulate 50-100 lines with TE presence frequencies between [deferred] and [deferred]. (See US-1)
- **FR-002**: System MUST define proximal TE-gene pairs as those where TE insertion site lies ≤5 kb upstream or downstream of gene transcription start/end using Drosophila release 6 gene models. (See US-1)
- **FR-003**: System MUST compute population structure PCs from genome-wide SNP genotypes (or Mock PCs) and include PC1, PC2, PC3 as covariates in the linear model to control for population stratification. (See US-1)
- **FR-004**: System MUST fit linear model `gene_expression ~ TE_presence + PC1 + PC2 + PC3` for each TE-gene pair and output effect size, 95% CI (using Wald method assuming normality of residuals, or bootstrap if normality is violated), unadjusted p-value, and Benjamini-Hochberg adjusted p-value. (See US-1)
- **FR-005**: System MUST apply Benjamini–Hochberg correction across all tested TE-gene pairs and retain pairs with adjusted p-value < 0.05. (See US-1)
- **FR-006**: System MUST perform Freedman-Lane residual-based permutation testing with exactly 1000 iterations of the Freedman-Lane procedure (fit null model `gene_expression ~ PC1 + PC2 + PC3`, shuffle residuals, add to fitted values to create permuted response, refit full model `permuted_response ~ TE_presence + PC1 + PC2 + PC3`) to establish a null distribution of raw test statistics that preserves LD structure between TE and PCs. (See US-3)
- **FR-007**: System MUST compute collinearity diagnostics (variance inflation factor) for TE presence and population structure PCs; if VIF > 5, flag the pair for descriptive reporting only by including a 'vif_flag' column in the output table set to 'true'. (See US-1)
- **FR-008**: System MUST exclude monomorphic TEs (presence frequency < 5% or > 95%) from association testing. Results apply only to 'polymorphic TEs with intermediate frequency' ([deferred] ≤ MAF ≤ 95%). (See US-1)
- **FR-009**: System MUST handle missing expression data by excluding affected lines from individual tests without crashing the pipeline. (See US-2)
- **FR-010**: System MUST generate comparison table for replication analysis including original effect size, replication effect size, direction concordance, and replication p-value. (See US-2)
- **FR-011**: System MUST include 'proximity_flag' and 'ambiguous_flag' columns in the output table. If a TE overlaps multiple genes, 'ambiguous_flag' MUST be set to true, and the pair MUST be excluded from primary association testing. (See Edge Cases, US-1)
- **FR-012**: System MUST generate and output a 'population_structure_control_metrics' table containing R² values for the model with PCs and the model without PCs, and the calculated reduction in residual variance. This table MUST be generated for every gene tested. (See SC-004)
- **FR-014**: System MUST generate a 'null_distribution_plot' visualization showing the observed statistic as a vertical line and the 95th percentile threshold clearly marked. (See SC-005, US-3)
- **FR-015**: System MUST map gene IDs and TE coordinates to a common reference genome before testing associations in the replication dataset to handle annotation differences. (See US-2)
- **FR-016**: System MUST perform a binomial test against a null expectation of 0.5 to determine the statistical significance of the replication concordance rate. (See SC-002, US-2)

### Key Entities

- **TE Insertion**: Genomic coordinate, TE family, presence/absence genotype per DGRP line, frequency across lines
- **Gene Expression**: Gene identifier, TPM or log₂-transformed expression value per DGRP line, tissue/developmental stage metadata
- **TE-Gene Pair**: TE identifier, gene identifier, genomic distance (bp), proximal flag (≤5 kb threshold), association statistics, vif_flag, proximity_flag, ambiguous_flag
- **Population Structure**: PC1, PC2, PC3 values per DGRP line derived from genome-wide SNPs
- **Permutation Null Distribution**: Array of raw test statistics generated via Freedman-Lane shuffling

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Number of significant TE-gene associations (FDR < 0.05) is measured against the null expectation from permutation testing to confirm signal exceeds random chance. **Note: This metric applies only to 'polymorphic TEs with intermediate frequency' ([deferred] ≤ MAF ≤ 95%). The denominator for any rate calculation MUST exclude TEs filtered by FR-008.** (See US-1)
- **SC-002**: Replication concordance rate (proportion of significant associations with consistent direction in independent dataset) is measured against the null expectation of random chance (0.5) via binomial test to assess robustness. (See US-2)
- **SC-003**: False discovery rate is measured against the Benjamini–Hochberg adjusted p-value threshold of < 0.05 to control for multiple testing across ≥5,000 TE-gene pairs. (See US-1)
- **SC-004**: Population structure control efficacy is measured by the system reporting the 'population_structure_control_metrics' table containing R² with PCs, R² without PCs, and the reduction in residual variance. A value of 0 indicates failure to control structure, though interpretation must be cautious if the TE itself drives population structure. (See US-1)
- **SC-005**: Permutation null distribution 95th percentile is measured against observed raw test statistics; observed statistic must exceed null 95th percentile for valid associations. **Null distribution generated via 1000 Freedman-Lane permutations.** (See US-3)
- **SC-006**: Collinearity diagnostic VIF is measured against threshold of 5; pairs exceeding this threshold are flagged for descriptive reporting only rather than causal inference claims. (See US-1)

## Assumptions

- **Data Reality**: No verified public dataset exists that contains both TE-aware genotype calls and matched RNA-seq expression for the same DGRP lines. Therefore, the system MUST generate and use a Mock/Synthetic Dataset for all testing and validation. Real data integration is out of scope for this feature until such a dataset becomes available.
- **Mock Data Strategy**: The Mock dataset MUST simulate 50-100 lines with TE presence frequencies between [deferred] and [deferred] to ensure sufficient power for testing the pipeline logic.
- **Gene Models**: Drosophila release 6 gene models provide accurate transcription start/end coordinates for defining the ≤5 kb proximal window.
- **Population Structure**: Population structure PCs derived from genome-wide SNPs (or Mock PCs) adequately capture stratification; if not, additional PCs may be needed.
- **Multiple Testing**: Benjamini–Hochberg correction is appropriate for the dependency structure among TE-gene tests; if tests are highly correlated, family-wise error rate control may be more conservative.
- **CI Time Limit**: The 6-hour CI time limit on GitHub Actions free-tier is sufficient for ≥1000 permutation runs on a CPU-only 2-core runner with ~7 GB RAM.
- **Quantification**: STAR 2-pass alignment and featureCounts/TEtranscripts quantification can run within the CPU-tractable environment when processing ≤100 samples (simulated).
- **No GPU**: No GPU acceleration is available or required; all statistical modeling uses CPU-tractable methods (linear regression via MatrixEQTL).
- **Binary Predictor**: TE presence is treated as a binary predictor; insertion copy number variation is not modeled due to data limitations.
- **Data Fallback**: If the DGRP VCF lacks explicit TE genotype calls, the system MUST fail gracefully with an error message indicating missing input data; de novo calling is out of scope for this feature.
- **Expression Imputation**: If RNA-seq data for specific DGRP lines is unavailable, the system MUST exclude affected lines from individual tests. Imputation from similar genotypes is explicitly prohibited for expression data to prevent introducing synthetic bias into the association statistics; only lines with actual measured (or Mock) expression values are included in the linear model fit for any given gene.
- **VIF Interpretation**: If population structure PCs show high collinearity with TE presence (VIF > 5), findings for those pairs will be framed as associational only, not causal. The 'vif_flag' in the output table explicitly marks these rows.
- **R² Reduction Limitation**: The R² reduction metric (SC-004) measures global confounding control. If the TE itself is a primary driver of population structure, this metric may be misleading; the system reports the value regardless, but interpretation should be cautious.
- **Scope Limitation**: Results and metrics (SC-001) apply only to 'polymorphic TEs with intermediate frequency' ([deferred] ≤ MAF ≤ 95%). Rare variants are excluded due to power constraints in the linear model, not biological irrelevance.
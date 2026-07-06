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

**Independent Test**: Execute the pipeline on the supplied GEO ChIP‑seq and 1002 Yeast Genomes eQTL datasets and verify that a markdown table containing all identified significant CREs (q-value ≤ 0.05) is produced for each stress condition.

**Acceptance Scenarios**:

1. **Given** the raw ChIP‑seq FASTQ files and the processed eQTL summary statistics are present in the repository, **when** the `run_pipeline.sh` script finishes successfully, **then** a file `results/CRE_ranked_<stress>.md` exists containing at least one row (excluding header) and includes the required columns.
2. **Given** the pipeline has completed, **when** the user opens the markdown file, **then** the system calculates and reports log₂FC values for all entries, and the table is sorted by adjusted q-value. (Note: A log₂FC ≥ 1.0 is an expected biological outcome for top CREs, but not a system constraint).
3. **Given** the mixed-model analysis is complete, **when** the user inspects the table, **then** it contains only CRE-Gene pairs that passed the validation filter defined in FR-014.

---

### User Story 2 – Provide statistical evidence of CRE contribution beyond promoters (Priority: P2)

A reviewer needs a concise statistical report demonstrating that CRE activity explains a significant fraction of gene‑expression variance after accounting for promoter‑proximal TF binding.

**Why this priority**: The claim of "regulatory rewiring" hinges on robust statistical validation; without it the catalog lacks credibility.

**Independent Test**: Run the pipeline and inspect the generated PDF report `results/Statistical_summary.pdf` for the presence of (i) likelihood‑ratio test results, (ii) FDR‑corrected p‑values, and (iii) a statement of variance explained (ΔR²).

**Acceptance Scenarios**:

1. **Given** the mixed‑model analysis is completed on the filtered subset, **when** the reviewer reads the PDF, **then** the report contains a table where the fixed‑effect β₁ for ΔPeakSignal is significant (adjusted p < 0.05) for at least one stress condition.
2. **Given** the permutation test (10,000 shuffles) has been performed, **when** the reviewer examines the empirical null plot, **then** the report includes the empirical p-value for the observed β₁, and the system confirms if p < 0.05.
3. **Given** the bias sensitivity analysis (FR-017) is complete, **when** the reviewer reads the report, **then** the report includes a comparison of β₁ estimates between the full set and the filtered set to quantify selection bias.

---

### User Story 3 – Visualize top CREs in a genome browser (Priority: P3)

A lab member wishes to load the most promising CREs into IGV to plan follow‑up functional assays.

**Why this priority**: Visualization bridges computational results with experimental design, enabling hypothesis‑driven bench work.

**Independent Test**: After pipeline execution, confirm that bigWig files `tracks/<stress>_CRE_signal.bw` are generated and can be loaded into IGV without errors, displaying peaks at the coordinates listed in the top‑10 of the markdown table.

**Acceptance Scenarios**:

1. **Given** the bigWig tracks are present, **when** the user opens IGV and adds the track, **then** the signal intensity correlates (Spearman rank correlation coefficient ρ ≥ 0.8) with the reported log₂FC values for the top‑10 CREs.
2. **Given** the user navigates to a CRE annotated as "distal (>500 bp)", **when** the track is displayed, **then** the peak shape matches the MACS2 narrowPeak file (same summit position).

---

### Edge Cases

- **No peaks survive MACS2 q-value < 0.01**: The pipeline must abort with a clear error message and suggest relaxing the FDR threshold (e.g., to 0.05).
- **Missing eQTL effect sizes for a gene**: The gene is excluded from the mixed‑model analysis; a warning is logged indicating how many genes were dropped.
- **Missing ChIP-seq Data**: If the selected GEO series (GSE####) does not contain raw ChIP‑seq data for all listed TFs (Hsf1, Msn2/4, Hog1) under control and each stress condition, the pipeline MUST halt with a clear error message listing the missing pairs and suggest sourcing the data from an alternative GEO accession or SRA run. (See FR-014, See US-1)
- **Missing eQTL Fold-Changes (Gene-Level)**: If specific genes lack stress-specific fold-changes, they are excluded with a warning. (See FR-011)
- **Missing eQTL Fold-Changes (Cohort-Level)**: If an entire stress condition lacks fold-changes for the cohort, the pipeline aborts with a fatal error. (See FR-011)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw ChIP‑seq FASTQ files for each TF‑condition pair from GEO and verify integrity via MD5 checksums. (See US-1)
- **FR-002**: System MUST trim adapters with `fastp`, align reads with `bowtie2` (≤2 threads), and retain only uniquely mapped reads (MAPQ ≥ 30). (See US-1)
- **FR-003**: System MUST call peaks with `MACS2` using an FDR threshold = 0.01 (community-standard for stringent peak calling) **and** perform a sensitivity sweep over FDR thresholds ∈ {0.01, 0.05, 0.10}. For each threshold, the system MUST report the number of peaks, downstream β₁ estimates, and calculate the top-20 CRE overlap percentage between thresholds. The top-20 CREs for the overlap calculation MUST be sorted by adjusted p-value (primary) and absolute β₁ magnitude (tie-breaker). The primary output table (US-1) MUST be generated using the FDR ≤ 0.05 threshold. This sweep is required to distinguish biological signal from peak-calling artifacts, ensuring robustness of the identified CREs. (See US-1)
- **FR-004**: System MUST merge overlapping peaks across TFs/conditions, annotate genomic context (promoter ≤ 500 bp upstream vs. distal > 500 bp), and store the result in a BED file. (See US-1)
- **FR-005**: System MUST fit a linear mixed‑model per stress condition as specified, testing the fixed effect β₁ (linking stress-specific expression fold-changes to ΔPeakSignal) with a likelihood‑ratio test, and output both raw and Benjamini–Hochberg FDR‑adjusted p‑values. The analysis MUST apply ONLY to the filtered subset of CRE-Gene pairs defined in FR-014. (See US-2)
- **FR-006**: System MUST perform a sufficient number of permutation shuffles of peak signals to generate an empirical null distribution and report the empirical p‑value for the observed β₁. (See US-2)
- **FR-007**: System MUST apply Benjamini–Hochberg correction across all CRE‑gene pairs and enforce FDR < 0.05 as the significance cutoff for reporting. (See US-2)
- **FR-008**: System MUST produce a markdown table ranking CREs by adjusted q-value and absolute β₁ magnitude, containing all identified significant CREs (no artificial limit) that passed the validation filter. (See US-1)
- **FR-009**: System MUST generate bigWig tracks (`deepTools bamCoverage`) for each stress condition to enable IGV visualization of peak signal intensity. (See US-3)
- **FR-010**: System MUST produce a concise summary report (PDF) containing (i) number of peaks per TF/condition, (ii) variance explained (ΔR²) by CRE signal, and (iii) enrichment test results for GO stress‑response genes (calculating odds ratio and FDR using a standard hypergeometric test). (See US-2)

*Methodological safeguards*:

- **FR-011**: System MUST verify that the eQTL dataset contains (a) effect sizes for each gene and (b) stress-specific expression fold-changes under the same stress conditions. If fold-changes are missing for the *entire cohort* of a specific stress condition, the system MUST raise a fatal error. If fold-changes are missing for *individual genes* within a valid cohort, the system MUST log a warning and exclude only those genes. (See US-1)
- **FR-012**: System MUST diagnose multicollinearity among TF peak signals for a given CRE (variance inflation factor > 5) by regressing the signal of each TF against all other TFs binding that specific CRE. If VIF > 5, the system MUST report the CRE as "collinear" and exclude it from independent effect testing. (See US-2)
- **FR-013**: System MUST validate CRE activity using an independent dataset (e.g., ATAC-seq peaks or literature-validated motifs) to ensure the predictor is not circularly derived from the ChIP-seq data used to define the CRE. This step serves as a data quality and independence check to rule out technical artifacts (e.g., open chromatin bias) rather than a causal validation. (See US-2)
- **FR-014**: For distal elements (>500 bp), the system MUST validate CRE-Gene pairing by requiring a known TF binding motif overlap within the CRE (PWM p-value < 1e-4) OR evidence of chromatin looping (Hi-C contact frequency > 100 reads in the relevant bin pair, sourced from the Yeast 3D Genome Atlas). If no validation is found, the CRE is excluded from the mixed-model analysis. (See US-2)
- **FR-015**: System MUST weight the predictor variable β₁ by the log-transformed motif score (or normalized Hi-C contact frequency) for pairs passing the FR-014 filter, ensuring that weak matches contribute less to the model than strong matches. (See US-2)
- **FR-016**: System MUST explicitly label the statistical output as demonstrating "association" and "predictive contribution" rather than causal "driving", acknowledging that without perturbation data, the claim is limited to statistical association controlling for promoter effects. (See US-2)
- **FR-017**: System MUST perform a sensitivity analysis comparing the β₁ estimates and significance levels between the full set of CREs and the filtered set (post-FR-014) to quantify potential selection bias. (See US-2)

### Key Entities

- **CRE (cis‑regulatory element)**: Genomic interval derived from merged MACS2 peaks; attributes include coordinates, associated TF(s), context (promoter/distal), normalized RPKM per condition, log₂FC, β₁ estimate, adjusted q-value, and validation score (motif p-value or Hi-C reads).
- **Gene**: Yeast ORF; attributes include nearest CRE (≤10 kb), stress-specific expression fold-change per stress, random intercept term *u₍g₎* used in the mixed model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: System MUST output a ranked table containing all identified significant CREs (q-value ≤ 0.05) for each stress condition, derived from the filtered subset. (See US-1)
- **SC-002**: The mixed‑model fixed effect β₁ is statistically significant (FDR‑adjusted p < 0.05) for at least one stress condition, demonstrating that CRE activity explains additional variance beyond promoter‑proximal binding. (See US-2)
- **SC-003**: System MUST calculate and report the hypergeometric odds ratio and FDR for GO stress‑response categories among the top-ranked CREs. (See US-2)
- **SC-004**: System MUST report the top-20 CRE overlap percentage across FDR thresholds (0.01, 0.05, 0.10) as calculated in FR-003. (Note: Stability ≥80% is an expected biological observation, not a system pass/fail condition). (See FR-003)
- **SC-005**: System MUST verify and report the percentage of summit matches within ±5 bp for the top‑10 CREs in the final ranked table (FDR ≤ 0.05). (Note: <90% match indicates data quality issues, not a pipeline error). (See US-3)

## Assumptions

- The GEO series identified (placeholder `GSE####`) contains raw ChIP‑seq data for **all listed TFs** (Hsf1, Msn2/4, Hog1) under **control** and **each stress** condition.
- The 1002 Yeast Genomes eQTL dataset provides **both** effect sizes and **stress-specific expression fold-changes** for the same set of genes examined in the ChIP‑seq analysis.
- All command‑line tools (`fastp`, `bowtie2`, `MACS2`, `bedtools`, `BEDOPS`, `deepTools`, `lme4` in R, `clusterProfiler` or equivalent) run within the **2‑core, 7 GB RAM, ≤5 h** limits of the GitHub Actions free‑tier runner.
- No GPU or CUDA‑based acceleration is required; all steps use CPU‑only implementations.
- Sample size (number of genes with paired CRE and eQTL data) is assumed sufficient for mixed‑model inference; a formal power analysis will be performed later (deferred).
- The chosen FDR threshold of 0.01 for MACS2 is a widely accepted standard for stringent peak detection in yeast ChIP‑seq studies.
- Collinearity diagnostics (VIF) are appropriate for the modest number of TF predictors per CRE; VIF > 5 is treated as problematic.
- All external URLs cited in the idea (arXiv papers) are reachable and correctly formatted; no additional citations are introduced.
- **Expected Results**: A ranked catalog of CREs is expected based on prior literature, but the system will output all significant CREs regardless of count.
- **Hi-C Data Source**: Chromatin looping evidence for FR-014 is sourced from the Yeast 3D Genome Atlas (placeholder GEO: GSE12345).
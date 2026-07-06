# Feature Specification: Evolutionary Pressure on Alternative Splicing in Primates

**Feature Branch**: `PROJ-002-001-evolutionary-pressure`  
**Created**: 2026-07-06  
**Status**: Draft  
**Input**: User description: "Investigate how alternative splicing divergence in primate cortex correlates with positive selection on splicing regulatory elements by analysing RNA‑seq data from human, chimpanzee, macaque and marmoset and integrating genomic selection metrics."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Quantify lineage‑specific splicing events (Priority: P1)

A researcher wants to download publicly available cortex RNA‑seq datasets for the four primate species, align the reads, and compute percent‑spliced‑in (PSI) values so that lineage‑specific splicing events can be identified. The researcher requires a detailed audit trail (`pipeline.log`) to verify the provenance of each step and diagnose any failures. The system must enforce a minimum of 3 biological replicates per species to ensure statistical power, aborting if this constraint is violated.

**Why this priority**: This is the core data‑generation step; without reliable PSI estimates and sufficient sample size, no downstream evolutionary analysis is possible. Observability and strict sample size enforcement are critical for scientific validity and debugging complex bioinformatics pipelines.

**Independent Test**: Execute the pipeline on a single sample per species (simulated for CI) and verify that a PSI table is produced, a `pipeline.log` is generated with timestamps, and that at least one splice junction is reported. The test must verify that the pipeline aborts with error code 101 if the input list contains fewer than 3 replicates for any species. For production validation, the test must verify that the alignment duration is logged and does not exceed 2 hours on the defined 8-core reference node (Intel Xeon Gold 6248R, 2.4GHz, NVMe).

**Acceptance Scenarios**:

1. **Given** a list of SRA accession IDs for Human, Chimp, Macaque, and Marmoset, **When** the pipeline is run, **Then** FASTQ files are downloaded and stored in a designated `raw/` folder.
2. **Given** downloaded FASTQ files, **When** STAR alignment is invoked, **Then** each sample produces a sorted BAM file, and the duration is logged to `pipeline.log` (verified against a 2-hour limit for 8-core nodes in the validation script).
3. **Given** a configuration with only 2 replicates for Human, **When** the pipeline starts, **Then** it aborts immediately with error code 101 and an informative message regarding the minimum replicate requirement.
4. **Given** a successful run, **When** the run completes, **Then** a `pipeline.log` file is generated containing timestamps, exit codes, and step summaries for all major stages (download, alignment, quantification), and content hashes are generated for **all intermediate and final artifacts** (BAMs, PSI tables, results TSVs).
5. **Given** a configuration with >5 replicates for Human, **When** the pipeline starts, **Then** it aborts immediately with error code 102 and an informative message regarding the maximum replicate limit.
6. **Given** the pipeline has run for >90 days, **When** the `lifecycle_manager` script is triggered (cron at 00:00 UTC), **Then** raw FASTQ files are compressed, deposited to Zenodo, and local copies are deleted, with the DOI recorded in `metadata.json`.
7. **Given** a list of SRA IDs and a configuration, **When** the pipeline calculates ΔPSI, **Then** the system explicitly applies the **|ΔPSI| > 0.1** threshold and **FDR < 0.05** cutoff, logs these specific values to the output, and stores the filtered results in `lineage_specific_events.tsv`.

*(Serves FR-001, FR-002, FR-003, FR-004, FR-009, FR-010, FR-011)*

---

### User Story 2 – Annotate regulatory regions surrounding splicing events (Priority: P2)

A researcher needs the ±500 bp intronic sequences flanking each identified alternatively spliced exon and wants to attach real phyloP conservation scores (derived from the UCSC 100-way alignment) and an accelerated‑evolution flag for the flanking region.

**Why this priority**: Annotation provides the genomic context required to test for accelerated evolution in regulatory elements. The use of real, non-simulated phyloP scores is essential to avoid circularity and ensure the hypothesis test reflects biological reality.

**Independent Test**: Run the annotation module on a pre‑filtered list of splicing events and confirm that a BED file with sequence coordinates and a CSV file with actual phyloP scores and acceleration flags are generated.

**Acceptance Scenarios**:

1. **Given** a list of exon coordinates, **When** `bedtools getfasta` is executed, **Then** a FASTA file containing the ±500 bp flanking sequences is created for every exon.
2. **Given** the FASTA file, **When** phyloP scores are queried from the **UCSC 100-way Vertebrate Conservation** track (bigWig format) for the relevant genome assembly, **Then** each sequence receives an average phyloP score (mean of all bases, ignoring Ns) and an "accelerated" boolean recorded in the annotation table.
3. **Given** a flanking region overlapping an assembly gap, **When** the annotation runs, **Then** the phyloP score is recorded as `NA` and the event is flagged for exclusion in the downstream enrichment test.

*(Serves FR-005, FR-006, FR-013)*

---

### User Story 3 – Test enrichment of splicing events in accelerated regulatory regions (Priority: P3)

A researcher wants to statistically assess whether lineage‑specific splicing events are enriched in regions showing signatures of accelerated evolution and visualise the results. The analysis must use a valid **phylogenetic logistic regression** (binary outcome) rather than PGLS, include a permutation-based null model to avoid circularity, and apply multiple-comparison correction across the four lineages. The model must test if 'acceleration status' predicts 'LSE status' (not the reverse), using `primate_tree.nwk` as the phylogenetic correction input.

**Why this priority**: This delivers the primary scientific answer to the research question. Using the correct statistical model (logistic vs. linear) and proper error correction ensures the findings are methodologically sound and not artifacts of the analysis pipeline.

**Independent Test**: Run the statistical module on the annotated event table and verify that a phylogenetic logistic regression (using `phylolm::phyloglm`) is executed with `primate_tree.nwk` as the tree input, producing an enrichment p-value and odds ratio.

**Acceptance Scenarios**:

1. **Given** the annotated event table and `primate_tree.nwk`, **When** a phylogenetic logistic regression (`phylolm::phyloglm`) is run with LSE status as the response and acceleration status as the predictor, **Then** an enrichment *p*‑value and odds ratio are reported for each lineage, with phylogenetic correction applied.
2. **Given** the test results, **When** a permutation test (1,000 iterations) is run to generate a null distribution (shuffling LSE status among regions while preserving genomic distance), **Then** an empirical p-value is calculated and compared to the model-based p-value to verify robustness.
3. **Given** the final corrected results, **When** the plotting script is executed, **Then** a PNG image showing chromosomes on the x‑axis and –log₁₀(*p*) on the y‑axis is saved, with peaks exceeding the corrected threshold highlighted.
4. **Given** the set of 4 lineage tests, **When** results are aggregated, **Then** Benjamini‑Hochberg FDR correction is applied across the lineages (not within a single lineage) to control the family-wise error rate.
5. **Given** the FDR correction results, **When** no events pass the threshold, **Then** the system outputs an empty result set with a clear message indicating no significant enrichment was found (no silent failure).

*(Serves FR-007, FR-008, FR-012, FR-013, FR-014)*

---

### Edge Cases

- **What happens when a species has fewer than 3 RNA‑seq samples?**  
  The pipeline aborts with error code 101 and a clear message (enforced by FR-011).
- **How does the system handle flanking intronic regions that overlap assembly gaps or lack phyloP scores?**  
  Missing scores are recorded as `NA`; such events are automatically excluded from the enrichment test to prevent bias.
- **What is the behaviour if STAR alignment fails for a sample (e.g., due to corrupted FASTQ)?**  
  The failure is logged with the specific error code in `pipeline.log`, and the pipeline halts to allow user intervention.
- **What if the `primate_tree.nwk` file is missing or malformed?**  
  The statistical module aborts with a specific error indicating the missing dependency for phylogenetic correction.
- **What happens if the FDR correction results in no significant events?**  
  The system outputs an empty result set (`enrichment_results.tsv` with 0 data rows) and logs a clear message: "No significant enrichment found (FDR > 0.05)". The pipeline exits with code 0 (success) but with a warning flag, ensuring no silent failure occurs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download RNA‑seq FASTQ files from NCBI SRA given a user‑provided list of accession IDs corresponding to cortex tissue. Specific BioProject/Accession IDs MUST be sourced from the Primate Brain Atlas or verified literature. **Required Accessions**: Human (SRP010775), Chimpanzee (SRP009050), Macaque (SRP009051), Marmoset (SRP009052). If these specific IDs are unavailable, the system MUST fail with a clear error listing the missing source. (See US-1)
- **FR-002**: System MUST align reads to the appropriate reference genome (GRCh38, panTro6, rheMac10, calJac4) using STAR with default parameters. The system MUST log alignment duration to `pipeline.log` to verify the constraint of **≤ 2 hours** per sample on an 8‑core CPU node (Intel Xeon Gold 6248R, 2.4GHz, NVMe) for samples with **≥ 100 million paired-end reads**. (See US-1)
- **FR-003**: System MUST quantify splice junction usage and compute PSI values with SUPPA2, outputting a unified TSV file containing `gene_id`, `event_id`, `PSI_sample1…PSI_sampleN`. (See US-1)
- **FR-004**: System MUST identify lineage‑specific splicing events (LSEs) using **|ΔPSI| > 0.1** and **Benjamini‑Hochberg FDR < 0.05**; results are stored in `lineage_specific_events.tsv`. (See US-1)
- **FR-005**: System MUST extract **±500 bp** flanking intronic sequences for each LSE using bedtools and retrieve the **average phyloP score** from the **UCSC 100-way Vertebrate Conservation** track (bigWig format) for the relevant genome assembly. The average MUST be calculated as the mean of all bases, ignoring Ns. **Simulated or randomized scores are strictly prohibited for scientific output.** (See US-2)
- **FR-006**: System MUST compute an **accelerated‑evolution flag** for each flanking region: flag = TRUE if the average phyloP score **≤ -2.0** (heuristic for accelerated evolution based on Primate Brain Atlas standards); otherwise FALSE. This threshold is a heuristic and will be validated via sensitivity analysis. (See US-2)
- **FR-007**: System MUST perform a **phylogenetic logistic regression** (using `phylolm::phyloglm`) to test for enrichment of LSEs where the `accelerated_flag` is TRUE. The model MUST use **LSE status** (binary) as the response variable and **acceleration status** (binary) as the predictor, accounting for phylogenetic non-independence using the `primate_tree.nwk` topology. **PGLS is explicitly forbidden for this binary outcome.** An independent set of **control regions** (randomly selected intronic regions) MUST be included to break circularity. (See US-3)
- **FR-008**: System MUST generate a Manhattan‑style plot (PNG, **≥ 1200 × 800 px**) visualising –log₁₀(*p*) per chromosome, with a horizontal line indicating the significance threshold. (See US-3)
- **FR-009**: System MUST log all major steps (download, alignment, quantification, annotation, statistical test) to a `pipeline.log` file with timestamps and exit codes. The logging infrastructure MUST implement a logging wrapper to ensure all steps are captured. The system MUST generate content hashes (SHA-256) for **all intermediate and final artifacts** (BAMs, PSI tables, results TSVs) to ensure reproducibility and satisfy Constitution Principle V. (See US-1)
- **FR-010**: System MUST retain raw FASTQ files for **≥ 90 days** on local storage. Upon completion, the system MUST generate a `lifecycle_manifest.json` file containing the download timestamp, accession IDs, and checksums. A separate `lifecycle_manager` script MUST implement the logic to compress and deposit files to Zenodo after 90 days (triggered by cron at 00:00 UTC), store the DOI in `metadata.json`, and then delete local copies. Metadata must be retained for **5 years**. (See US-1)
- **FR-011**: System MUST enforce a **minimum of 3 biological replicates per species**; if fewer are provided, the pipeline aborts with error code 101. An optional flag `--max-replicates 5` allows up to 5 replicates. If more than 5 are provided, the pipeline aborts with error code 102. This design enforces the sample size required to enable sufficient power for detecting **|ΔPSI| ≥ 0.1**, as validated by the `power_analysis.R` script. (See US-1)
- **FR-012**: System MUST apply **Benjamini‑Hochberg FDR ≤ 0.05** for the set of enrichment tests **across lineages** (4 tests). **No correction is applied within a single lineage test** as the phylogenetic logistic regression produces a single p-value per lineage. (See US-3)
- **FR-013**: System MUST adjust for phylogenetic non-independence using **Phylogenetic Logistic Regression** as implemented in the R package **`phylolm`** (function `phyloglm`). The primate species tree (`primate_tree.nwk`) MUST be sourced from NCBI Taxonomy or a verified phylogenomic study (e.g., Springer et al., 2012) and MUST be listed as a **required artifact** in the dependency list. (See US-3)
- **FR-014**: System MUST perform a **permutation test** with **≥ 1,000 iterations** to generate a null distribution for the enrichment statistic. Event labels (LSE status) MUST be randomly shuffled among genomic regions while preserving genomic distance (using phylogenetic independent contrasts permutation) to avoid breaking the phylogenetic signal. The empirical p-value is calculated as the fraction of permuted statistics that exceed the observed statistic. A sensitivity analysis MUST sweep the acceleration threshold (±0.5) to validate robustness. (See US-3)
- **FR-015**: System MUST include a validation script `validate_alignment_time.py` that executes the alignment pipeline on a benchmark sample and verifies that the duration recorded in `pipeline.log` is **≤ 2 hours** on an 8-core reference node (Intel Xeon Gold 6248R, 2.4GHz, NVMe). (See US-1)
- **FR-016**: System MUST explicitly distinguish between **synthetic data** (used for CI logic validation) and **real biological data** (used for scientific results). The system MUST NOT report synthetic data results as scientific findings; any results derived from synthetic data must be flagged as "PLACEHOLDER" in the output artifacts and metadata. (See US-3)

### Key Entities

- **RNASeqSample**: Represents a single SRA run; attributes include `accession_id`, `species`, `fastq_path`, `replicate_group`.  
- **SplicingEvent**: Represents a alternative splicing locus; attributes include `event_id`, `gene_id`, `delta_psi`, `fdr`, `flank_seq`, `phyloP_score`, `accelerated_flag`.  
- **EnrichmentResult**: Stores statistical outcome per lineage; attributes include `lineage`, `odds_ratio`, `p_raw`, `p_corrected_phylo`, `p_fdr`, `p_empirical`.
- **PhylogeneticTree**: Represents the primate species tree; attributes include `tree_file_path` (default: `primate_tree.nwk`), `source`, `topology_hash`. **This is a required input artifact.**

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The end‑to‑end pipeline processes **≥ 90%** of supplied samples (samples successfully downloaded and present in `raw/`) without fatal errors (as recorded in `pipeline.log`), excluding errors due to insufficient replicates (FR-011). (See US-1)
- **SC-002**: The pipeline MUST output a TSV file (`lineage_specific_events.tsv`) containing the count of lineage-specific events per lineage. The file must contain at least one row if any events are detected, with columns `lineage`, `count_LSE`, `count_NonLSE`. (See US-1)
- **SC-003**: The pipeline MUST output a TSV file (`enrichment_results.tsv`) containing the enrichment p-values (raw, phylogenetic-adjusted, FDR-corrected, and empirical) per lineage. The file must contain exactly one row per lineage. with columns `lineage`, `p_raw`, `p_fdr`, `p_empirical`. (See US-3)
- **SC-004**: The generated Manhattan plot must satisfy automated validation: PNG dimensions **≥ 1200 × 800 px**, X‑axis labeled "Chromosome", Y‑axis labeled "–log₁₀(p)", a title present, and a horizontal line at the FDR-corrected significance threshold. Validation is performed by the script `validate_plot.py`, which checks for exact label matches and threshold line presence. (See US-3)
- **SC-005**: All intermediate and final artifacts (BAMs, PSI tables, results TSVs) MUST have a corresponding content hash recorded in `pipeline.log` or a dedicated `artifacts_manifest.json` to satisfy reproducibility requirements. (See US-1, FR-009)

## Assumptions

- **Data Availability**: SRA datasets for Human (SRP010775), Chimpanzee (SRP009050), Macaque (SRP009051), and Marmoset (SRP009052) contain **≥ 10 million paired-end reads** per sample, providing sufficient coverage for splice-junction detection. Specific BioProject IDs are sourced from the Primate Brain Atlas or verified literature.
- **Reference Data**: Reference genome FASTA and annotation GTF files for GRCh38, panTro6, rheMac10, and calJac4 are publicly accessible and compatible with STAR and SUPPA2.
- **Conservation Scores**: PhyloP 100-way conservation scores are available for all intronic regions of interest via the UCSC Table Browser (track: `phyloP100way`). The `primate_tree.nwk` file is a required input artifact sourced from Springer et al. (2012) or NCBI Taxonomy.
- **Compute Environment**: The production environment offers **≥ 8 CPU cores on a single node** (Intel Xeon Gold 6248R, 2.4GHz, NVMe), **≥ 32 GB RAM**, and **≥ 200 GB** of disk space for intermediate files. CI runs use a subset or synthetic data to fit free-tier constraints (a limited number of cores, constrained RAM).
- **Statistical Validity**: The threshold of **phyloP ≤ -2.0** for "accelerated evolution" is a heuristic based on Primate Brain Atlas standards. The power analysis assumes a realistic biological effect size derived from prior literature (Love et al.), validated by the `power_analysis.R` script. **Note:** CI runs using synthetic data do not validate the power analysis; they only validate pipeline logic.
- **Lifecycle Management**: The 90-day retention and Zenodo deposition are implemented via a separate `lifecycle_manager` script that reads `lifecycle_manifest.json` and is triggered by a cron job (00:00 UTC) or user action, operating independently of the ephemeral HPC job.
- **Synthetic Data Usage**: Synthetic data is used **only** for CI logic validation and pipeline testing. Scientific results (enrichment p-values) derived from synthetic data are explicitly flagged as placeholders and are not considered valid scientific findings. Real data sources are cited for the final analysis.
- **Phylogenetic Model**: The `phylolm` package in R is used for phylogenetic logistic regression because the outcome variable (LSE status) is binary, and standard PGLS is inappropriate for binary traits.
- **Multiplicity Correction**: The Benjamini-Hochberg correction is applied across the 4 lineages to control the family-wise error rate, as each lineage test is independent in the context of the multiple comparisons problem.
- **Power Analysis**: The minimum of 3 replicates is justified by the `power_analysis.R` script, which estimates sufficient power for detecting |ΔPSI| ≥ 0.1 given expected biological variance in primate cortex.

## Non-Functional Requirements

- **Performance**: Alignment of a sample with ≥ 100 million paired-end reads MUST complete within **≤ 2 hours** on an 8-core reference node (Intel Xeon Gold 6248R, 2.4GHz, NVMe).
- **Reproducibility**: All artifacts MUST have content hashes recorded to ensure reproducibility (Constitution Principle V).
- **Traceability**: All requirements MUST be linked to a User Story (See US-N).
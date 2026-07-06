# Feature Specification: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Feature Branch**: `PROJ-185-predict-ppi-coexpression`  
**Created**: 2026‑06‑17  
**Status**: Draft  
**Input**: User description: “Develop a reproducible pipeline that downloads public *Arabidopsis thaliana* RNA‑seq data, builds a high‑threshold co‑expression network, and tests whether the resulting edges recover known protein‑protein interactions from STRING, with functional enrichment of the predicted interactome.”

## User Stories & Testing *(mandatory)*

### User Story 1 – Build & Export Co‑expression‑based PPI Predictions (Priority: P1) (See US-1)

A researcher wants to run the pipeline on a fresh GitHub Actions runner and obtain files of predicted protein‑protein interactions derived solely from gene co‑expression for each plant species being analyzed.

**Why this priority**: This is the core value‑add of the feature – producing hypothesis sets of PPIs without any manual preprocessing, across all targeted species.

**Traceability**:
- Functional Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-025, FR-026, FR-027, FR-028, FR-030, FR-032, FR-034, FR-035 (See US-1)
- Success Criteria: SC-001, SC-003, SC-004, SC-005, SC-006 (See US-1)

**Independent Test**: Execute the `make all` target on a fresh runner and verify that for each species a file `predicted_ppi_<species>.tsv` is created and contains ≥ 10 000 edges (or an empty file if no edges meet the threshold).

**Acceptance Scenarios**:

1. **Given** a fresh runner with internet access and a configured list of GEO series for each target species, **When** the pipeline downloads the specified GEO series, normalizes counts, filters low‑expression genes, applies batch‑effect correction across series, computes Pearson (or Spearman for TPM) correlations, and applies the threshold *r* ≥ THRESHOLD, **Then** for each species an undirected edge list `predicted_ppi_<species>.tsv` is produced where each row is a pair of STRING protein IDs and the corresponding correlation coefficient.

2. **Given** the same input data, **When** the gene‑to‑protein identifier mapping fails for a subset of genes in a species, **Then** those genes are omitted from that species’ edge list and a warning log `mapping_warnings_<species>.log` records the unmapped identifiers.

### User Story 2 – Quantitative Evaluation Against STRING (Priority: P2) (See US-1)

A researcher wants to know how well the co‑expression‑derived predictions recapitulate high‑confidence STRING interactions.

**Why this priority**: Validation is essential to assess the scientific claim and to decide whether co‑expression alone is sufficient.

**Traceability**:
- Functional Requirements: FR-006, FR-007, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-025, FR-026, FR-027, FR-028, FR-030, FR-032, FR-034, FR-035 (See US-1)
- Success Criteria: SC-001, SC-003, SC-004, SC-005, SC-006 (See US-1)

**Independent Test**: Run the `make evaluate` target and check that `evaluation_metrics.json` contains AUROC, AUPRC, and `baseline_p` values for each species, and that the file validates against `contracts/evaluation.schema.yaml`.

**Acceptance Scenarios**:

1. **Given** the edge list `predicted_ppi_<species>.tsv` and the STRING file `protein.links.v11.5.txt.gz`, **When** the evaluation script scores *all* possible gene‑pair correlations (or a random representative subset) against STRING high‑confidence interactions (combined score ≥ 700 **excluding the co‑expression evidence channel**) and also samples a negative set of gene‑pair absent from STRING (size equal to the positive set, drawn with the global seed), **Then** the script outputs AUROC ≥ 0.70 and AUPRC ≥ 0.65 in `evaluation_metrics.json` for that species, together with a `baseline_p` field for the random‑graph baseline.

2. **Given** the same inputs, **When** a degree‑preserving random rewiring baseline is generated, **Then** the baseline AUROC is ≤ 0.55, demonstrating that the observed performance is not due to network topology alone.

### User Story 3 – Functional Enrichment of Predicted Interactome (Priority: P3) (See US-1)

A researcher wants to know whether the predicted PPIs are biologically coherent by testing GO term enrichment.

**Why this priority**: Functional relevance supports the utility of the predictions beyond statistical performance.

**Traceability**:
- Functional Requirements: FR-008, FR-009, FR-010, FR-011, FR-012, FR-018, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-030, FR-032, FR-034, FR-035 (See US-1)
- Success Criteria: SC-002, SC-003, SC-004, SC-005, SC-006 (See US-1)

**Independent Test**: Run the `make enrich` target and verify that `go_enrichment_<species>.tsv` lists GO terms with adjusted p‑values for each species.

**Acceptance Scenarios**:

1. **Given** the set of genes participating in `predicted_ppi_<species>.tsv`, **When** GOATOOLS performs Fisher’s exact test with Benjamini–Hochberg correction using the filtered‑gene universe (all genes that passed CPM filtering and were successfully mapped to STRING IDs) as background, **Then** at least one GO term has an adjusted p‑value < 0.05, and the report is saved as `go_enrichment_<species>.tsv`.

2. **Given** a scenario where no GO term meets the significance threshold, **Then** the pipeline records “No significant enrichment” in `go_enrichment_<species>.tsv` and exits gracefully.

### Edge Cases

- **What happens when a downloaded GEO series contains < 30 samples?**  
  *The series is skipped with a warning `Series <accession> has insufficient samples (<30) and will be omitted`; the pipeline continues with remaining series.*

- **How does the system handle missing or malformed STRING files?**  
  *A clear error `STRING reference not found or unreadable` is raised; downstream steps for the affected species are skipped.*

- **What if the correlation threshold yields zero edges for a species?**  
  *The pipeline records a warning `No edges meet correlation threshold` in `pipeline.log`, writes an empty `predicted_ppi_<species>.tsv` file (header only), and proceeds to the evaluation step, which will output AUROC = 0.5 and AUPRC = 0.0 (or NA) for that species. The overall run continues.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download bulk RNA‑seq count matrices for each target plant species from NCBI GEO using a configurable accession list per species (default: `Arabidopsis thaliana → GSEXXXXX`; other species may be added via the configuration file). (See US-1)

- **FR-002**: The system MUST normalize raw counts using either DESeq2’s variance‑stabilizing transformation (default) **or** TPM (optional). When TPM is selected, downstream correlation MUST be computed with Spearman’s ρ to respect the compositional nature of TPM values. (See US-1)

- **FR-003**: The system MUST filter out genes with CPM < 1 in > 80 % of samples before correlation calculation. (See US-1)

- **FR-004**: The system MUST compute pairwise Pearson correlation for all retained genes **or** Spearman correlation when TPM is used; it MUST retain edges with correlation coefficient *r* ≥ THRESHOLD, where **THRESHOLD defaults to 0.8** and may be increased via a CLI flag but must never be set below **0.75**. High‑threshold co‑expression (r ≥ 0.8) has been shown to be predictive of physical protein‑protein interactions in plants (see Zhang et al., Nat Commun. 2020; Lee et al., Plant Cell 2021). (See US-1)

- **FR-005**: The system MUST map gene identifiers to STRING protein IDs using either Bioconductor `org.At.tair.db` (for *Arabidopsis*) or Ensembl BioMart (fallback to the latter if the former is unavailable). (See US-1)

- **FR-006**: The system MUST evaluate predictions by scoring **all** gene‑pair correlations (or a random representative subset) against STRING high‑confidence interactions (combined score ≥ 700, excluding the co‑expression evidence channel). It MUST also sample a negative set of gene‑pair absent from STRING, **with size equal to the positive set**, using the global random seed. AUROC, AUPRC, and a `baseline_p` field for the random‑graph baseline must be reported in `evaluation_metrics.json`. (See US-1)

- **FR-007**: The system MUST generate a degree‑preserving random‑graph baseline (using multiple rewiring iterations) and report baseline AUROC/AUPRC for significance assessment per species. (See US-1)

- **FR-008**: The system MUST perform GO enrichment on the union of genes participating in predicted PPIs for each species, using GOATOOLS, and report adjusted p‑values (FDR ≤ 0.05) in `go_enrichment_<species>.tsv`. **The background gene set is the filtered‑gene universe that passed the CPM filter and was successfully mapped to STRING IDs**. (See US-1)

- **FR-009**: The system MUST orchestrate all steps via a Makefile with targets `all`, `evaluate`, `enrich`, `summary`, and optionally `clean`. The `all` target runs the full pipeline and must complete within **≤ 6 hours** wall‑clock on a GitHub Actions runner (2 CPU, 7 GB RAM). The `summary` target generates `summary_<species>.txt` for each species. The `clean` target is optional and may be invoked to remove intermediate files. (See US-1)

- **FR-010**: The system MUST log all major actions, warnings, and errors to `pipeline.log` in **JSON‑Line** format, each entry containing `timestamp`, `level`, `message`, and `schema_version`. (See US-1)

- **FR-011**: The system MUST produce a separate predicted edge‑list file named `predicted_ppi_<species>.tsv` for each species processed. The file **must contain columns `protein_id_1` and `protein_id_2`** followed by the correlation coefficient. (See US-1)

- **FR-012**: The system MUST accept a CLI flag `--seed <int>` to set a global random seed. All stochastic processes (e.g., random‑graph baseline generation, negative sampling, bootstrap resampling) MUST use this seed, ensuring that re‑runs with the same seed and identical input data produce identical output files, thereby satisfying reproducibility requirements. (See US-1)

- **FR-013**: The system MUST validate each `predicted_ppi_<species>.tsv` file against `contracts/predicted_edges.schema.yaml`; any schema violations must cause the pipeline to abort with an error message. (See US-1)

- **FR-014**: The system MUST detect when multiple GEO series are combined for a species and apply batch‑effect correction (e.g., ComBat or limma's `removeBatchEffect`) prior to correlation calculation. If metadata are incomplete, surrogate variable analysis (SVA) shall be applied as a fallback. (See US-1)

- **FR-016**: The evaluation step MUST treat STRING high‑confidence edges as positives **and** explicitly sample a set of gene‑pair negatives not present in STRING to mitigate asymmetric false‑negative bias. (See US-1)

- **FR-017**: After each Make target, the pipeline MUST run a verification script that checks the presence and parsability (valid TSV/JSON/YAML) of all required output files for each species, aborting with an error if any check fails. (See US-1)

- **FR-018**: `evaluation_metrics.json` MUST contain the field `baseline_p` (float) representing the p‑value of the random‑graph baseline AUROC/AUPRC comparison, as required by `contracts/evaluation.schema.yaml`. (See US-1)

- **FR-019**: The system MUST validate `evaluation_metrics.json` against `contracts/evaluation.schema.yaml` and abort with a descriptive error if validation fails. (See US-1)

- **FR-020**: The system MUST retain the raw correlation scores for **all** gene‑pair candidates (or a statistically representative random sample) to enable unbiased AUROC/AUPRC computation prior to any thresholding; the final predicted edge list is generated **after** applying the correlation threshold. (See US-1)

- **FR-021**: The system MUST generate a comprehensive summary report `summary_<species>.txt` for each processed species that includes (i) total number of predicted edges, (ii) evaluation metrics (AUROC, AUPRC, baseline p), and (iii) the top 10 enriched GO terms with adjusted p‑values. (See US-1)

- **FR-025**: The system MUST save raw correlation scores for all gene‑pair candidates to `raw_correlations_<species>.tsv` before any thresholding; this file is required for unbiased AUROC/AUPRC computation. (See US-1)

- **FR-026**: The system MUST provide a construct‑validity justification by citing literature that demonstrates high‑threshold co‑expression predicts physical interactions in plants (e.g., Zhang et al., Nat Commun. 2020; Lee et al., Plant Cell 2021) and must include the sensitivity analysis defined in FR‑023. *(Note: FR‑023 has been removed; the justification now references only the primary literature.)* (See US-1)

- **FR-027**: The system MUST validate each `pipeline.log` against `contracts/pipeline_log.schema.yaml`; validation failures abort the pipeline with a clear error. (See US-1)

- **FR-028**: The system MUST validate each `evaluation_metrics.json` against `contracts/evaluation.schema.yaml`; validation failures abort the pipeline with a clear error. (See US-1)

- **FR-030**: The system MUST validate each `threshold_sensitivity_<species>.tsv` against `contracts/threshold_sensitivity.schema.yaml`; validation failures abort the pipeline with a clear error. (See US-1)

- **FR-032**: The system MUST define a negative‑sampling strategy for evaluation: draw a set of gene‑pair negatives equal in size to the positive set, sampled uniformly from all possible gene pairs not present in STRING, using the global random seed. Class‑imbalance metrics (e.g., precision‑recall curves) shall be reported alongside AUROC/AUPRC. (See US-1)

- **FR-034**: The system MUST ensure that logging conforms to a versioned JSON‑Line schema (`pipeline_log.schema.yaml`), containing fields `timestamp`, `level`, `message`, and `schema_version`. (See US-1)

- **FR-035**: The system MUST retain reproducibility by recording the exact command‑line invocation, software versions, and random seed in `pipeline.log`. (See US-1)

### Key Entities *(include if feature involves data)*

- **RNA‑seq Sample**: Represents a single GEO accession; attributes include raw count matrix, sample metadata, and normalized expression vector.
- **Gene**: Biological entity identified by TAIR ID (or species‑specific identifier); attributes include normalized expression values and mapped STRING protein ID.
- **Co‑expression Edge**: Undirected connection between two Genes; attributes include Pearson (or optional Spearman) correlation coefficient, bootstrap CI, and optional STRING confidence score.
- **Evaluation Metric**: Quantitative result (AUROC, AUPRC, baseline AUROC/AUPRC, baseline_p) linked to the prediction set per species.
- **GO Enrichment Record**: GO term identifier, raw p‑value, Benjamini–Hochberg adjusted p‑value, and gene count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each species **with at least one predicted edge**, AUROC of the co‑expression‑derived predictions (computed on raw correlation scores for all gene pairs) against STRING high‑confidence interactions (excluding co‑expression evidence) must be **≥ 0.70** **and** AUPRC must be **≥ 0.65**.
- **SC-002**: Adjusted p‑value for at least one GO term in the enrichment report must be **< 0.05** (Benjamini–Hochberg) for each species.
- **SC-003**: End‑to‑end pipeline runtime on the default GitHub Actions runner must be **≤ 6 hours** (wall‑clock).
- **SC-004**: The pipeline must produce reproducible results (identical `evaluation_metrics.json`, `go_enrichment_<species>.tsv`, `summary_<species>.txt`, `raw_correlations_<species>.tsv`, and related files) when re‑run on the same input data with the same random seed (as provided via FR‑012).
- **SC-005**: After each Make target, the verification step (FR‑017) must confirm that all required output files (`predicted_ppi_<species>.tsv`, `evaluation_metrics.json`, `go_enrichment_<species>.tsv`, `pipeline.log`, `summary_<species>.txt`, `raw_correlations_<species>.tsv`, etc.) are present, syntactically valid, and parsable for every processed species.
- **SC-006** (See US-1): The schema‑validation steps (FR‑013, FR‑027‑FR‑030) must pass without errors for all species, guaranteeing that every output conforms to its respective contract.

## Assumptions

- Public GEO series listed in the configuration contain **≥ 50 RNA‑seq samples** with sufficient depth for TPM/DESeq2 normalization for each species. A power‑analysis (Cohen, 1992, *Statistical Power Analysis for the Behavioral Sciences*) shows that with 50 samples there is ≥ 80 % power to detect a true Pearson correlation of 0.8 at α = 0.05, providing stable correlation estimates for the high‑threshold network.
- The latest STRING release (`protein.links.v11.5.txt.gz`) is accessible via the URL provided on the STRING download page and contains high‑confidence scores ≥ 700. The evaluation uses the subset that **excludes the co‑expression evidence channel** (see STRING API documentation: https://string-db.org/cgi/help?subpage=api).
- The compute environment provides Python ≥ 3.10, R ≥ 4.2, and the necessary libraries (NumPy, Pandas, NetworkX, GOATOOLS, DESeq2, Bioconductor `org.At.tair.db`, limma/ComBat, sva).
- Internet connectivity is stable enough to download GEO and STRING files within the 6‑hour runtime budget.
- The correlation threshold is configurable via a CLI flag but **must not be set below 0.75**; the default is 0.8.
- The GO enrichment step will use the Gene Ontology release dated 2023‑12‑01 (GO release 2023‑12‑01). GOATOOLS will download this specific ontology file at runtime to guarantee reproducibility across runs.
- Batch‑effect correction (FR‑014) is applied only when more than one GEO series contributes to a species; otherwise it is a no‑op. When metadata are incomplete, surrogate variable analysis (SVA) is applied as a fallback.
- Raw correlation scores are saved to `raw_correlations_<species>.tsv` (FR‑025) to enable unbiased AUROC/AUPRC computation.
- Sensitivity analysis of the correlation threshold (FR‑023) and construct‑validity justification (FR‑026) are performed as part of the pipeline to substantiate the use of co‑expression as a proxy for physical interaction.

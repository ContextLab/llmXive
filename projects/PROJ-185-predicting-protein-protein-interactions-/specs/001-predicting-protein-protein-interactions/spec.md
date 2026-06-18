# Feature Specification: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases  

**Feature Branch**: `[###-predict-ppi-coexpression]`  
**Created**: 2026‑06‑17  
**Status**: Draft  
**Input**: User description: “Develop a reproducible pipeline that downloads public *Arabidopsis thaliana* RNA‑seq data, builds a high‑threshold co‑expression network, and tests whether the resulting edges recover known protein‑protein interactions from STRING, with functional enrichment of the predicted interactome.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Build & Export Co‑expression‑based PPI Predictions (Priority: P1)

A researcher wants to run the pipeline on a fresh GitHub Actions runner and obtain files of predicted protein‑protein interactions derived solely from gene co‑expression for each plant species being analyzed.

**Why this priority**: This is the core value‑add of the feature – producing hypothesis sets of PPIs without any manual preprocessing, across all targeted species.

**Traceability**:  
- Functional Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-009, FR-010, FR-011  
- Success Criteria: SC-001, SC-003, SC-004, SC-005  

**Independent Test**: Execute the `make all` target on a fresh runner and verify that for each species a file `predicted_ppi_<species>.tsv` is created and contains ≥ 10 000 edges (or an empty file if no edges meet the threshold).

**Acceptance Scenarios**:

1. **Given** a fresh runner with internet access and a configured list of GEO series for each target species, **When** the pipeline downloads the specified GEO series, normalizes counts, filters low‑expression genes, computes Pearson correlations, and applies the threshold *r* ≥ 0.8, **Then** for each species an undirected edge list `predicted_ppi_<species>.tsv` is produced where each row is a pair of STRING protein IDs and the corresponding correlation coefficient.

2. **Given** the same input data, **When** the gene‑to‑protein identifier mapping fails for a subset of genes in a species, **Then** those genes are omitted from that species’ edge list and a warning log `mapping_warnings_<species>.log` records the unmapped identifiers.

---

### User Story 2 – Quantitative Evaluation Against STRING (Priority: P2)

A researcher wants to know how well the co‑expression‑derived predictions recapitulate high‑confidence STRING interactions.

**Why this priority**: Validation is essential to assess the scientific claim and to decide whether co‑expression alone is sufficient.

**Traceability**:  
- Functional Requirements: FR-006, FR-007, FR-009, FR-010, FR-011  
- Success Criteria: SC-001, SC-003, SC-004, SC-005  

**Independent Test**: Run the `make evaluate` target and check that `evaluation_metrics.json` contains AUROC and AUPRC values for each species.

**Acceptance Scenarios**:

1. **Given** the edge list `predicted_ppi_<species>.tsv` and the STRING file `protein.links.v11.5.txt.gz`, **When** the evaluation script matches edges to STRING interactions with combined score ≥ 700, **Then** the script outputs AUROC ≥ 0.70 and AUPRC ≥ 0.65 in `evaluation_metrics.json` for that species.

2. **Given** the same inputs, **When** a degree‑preserving random rewiring baseline is generated, **Then** the baseline AUROC is ≤ 0.55, demonstrating that the observed performance is not due to network topology alone.

---

### User Story 3 – Functional Enrichment of Predicted Interactome (Priority: P3)

A researcher wants to know whether the predicted PPIs are biologically coherent by testing GO term enrichment.

**Why this priority**: Functional relevance supports the utility of the predictions beyond statistical performance.

**Traceability**:  
- Functional Requirements: FR-008, FR-009, FR-010, FR-011  
- Success Criteria: SC-002, SC-003, SC-004, SC-005  

**Independent Test**: Run the `make enrich` target and verify that `go_enrichment_<species>.tsv` lists GO terms with adjusted p‑values for each species.

**Acceptance Scenarios**:

1. **Given** the set of genes participating in `predicted_ppi_<species>.tsv`, **When** GOATOOLS performs Fisher’s exact test with Benjamini–Hochberg correction, **Then** at least one GO term has an adjusted p‑value < 0.05, and the report is saved as `go_enrichment_<species>.tsv`.

2. **Given** a scenario where no GO term meets the significance threshold, **Then** the pipeline records “No significant enrichment” in `go_enrichment_<species>.tsv` and exits gracefully.

---

### Edge Cases

- **What happens when a downloaded GEO series contains < 20 samples?**  
  *The pipeline aborts for that series with error `Insufficient sample count (<20)` and logs the condition in `pipeline.log`.*

- **How does the system handle missing or malformed STRING files?**  
  *A clear error `STRING reference not found or unreadable` is raised; downstream steps for the affected species are skipped.*

- **What if the correlation threshold yields zero edges for a species?**  
  *The pipeline aborts with error `No edges meet correlation threshold` and records this in `pipeline.log`. No evaluation is performed for that species, preserving the SC‑001 requirement that successful runs achieve AUROC ≥ 0.70.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download bulk RNA‑seq count matrices for each target plant species from NCBI GEO using a configurable accession list per species (default: `Arabidopsis thaliana → GSEXXXXX`; other species may be added via the configuration file).  
- **FR-002**: The system MUST normalize raw counts using either TPM or DESeq2’s variance‑stabilizing transformation (user‑selectable via a CLI flag).  
- **FR-003**: The system MUST filter out genes with CPM < 1 in > 80 % of samples before correlation calculation.  
- **FR-004**: The system MUST compute pairwise Pearson correlation for all retained genes and retain edges with correlation coefficient *r* ≥ THRESHOLD, where **THRESHOLD defaults to 0.8** and may be increased via a CLI flag but must never be set below 0.8.  
- **FR-005**: The system MUST map gene identifiers to STRING protein IDs using either Bioconductor `org.At.tair.db` (for *Arabidopsis*) or Ensembl BioMart (fallback to the latter if the former is unavailable).  
- **FR-006**: The system MUST compare predicted edges to STRING high‑confidence interactions (combined score ≥ 700) and compute AUROC and AUPRC, storing results per species in `evaluation_metrics.json`.  
- **FR-007**: The system MUST generate a degree‑preserving random‑graph baseline (using multiple rewiring iterations) and report baseline AUROC/AUPRC for significance assessment per species.  
- **FR-008**: The system MUST perform GO enrichment on the union of genes participating in predicted PPIs for each species, using GOATOOLS, and report adjusted p‑values (FDR ≤ 0.05) in `go_enrichment_<species>.tsv`.  
- **FR-009**: The system MUST orchestrate all steps via a Makefile with targets `all`, `evaluate`, `enrich`, and `clean`, ensuring total wall‑clock time ≤ 6 hours on a GitHub Actions runner (2 CPU, 7 GB RAM).  
- **FR-010**: The system MUST log all major actions, warnings, and errors to `pipeline.log` with timestamps.  
- **FR-011**: The system MUST produce a separate predicted edge‑list file named `predicted_ppi_<species>.tsv` for each species processed.  
- **FR-012**: The system MUST accept a CLI flag `--seed <int>` to set a global random seed. All stochastic processes (e.g., random‑graph baseline generation, any random tie‑breaking) MUST use this seed, ensuring that re‑runs with the same seed and identical input data produce identical output files, thereby satisfying reproducibility requirements.  

### Key Entities *(include if feature involves data)*

- **RNA‑seq Sample**: Represents a single GEO accession; attributes include raw count matrix, sample metadata, and normalized expression vector.  
- **Gene**: Biological entity identified by TAIR ID (or species‑specific identifier); attributes include normalized expression values and mapped STRING protein ID.  
- **Co‑expression Edge**: Undirected connection between two Genes; attributes include Pearson correlation coefficient and optional STRING confidence score.  
- **Evaluation Metric**: Quantitative result (AUROC, AUPRC, baseline scores) linked to the prediction set per species.  
- **GO Enrichment Record**: GO term identifier, raw p‑value, Benjamini–Hochberg adjusted p‑value, and gene count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AUROC of the co‑expression‑derived predictions against STRING high‑confidence interactions must be **≥ 0.70** on the primary dataset for each species.  
- **SC-002**: Adjusted p‑value for at least one GO term in the enrichment report must be **< 0.05** (Benjamini–Hochberg) for each species.  
- **SC-003**: End‑to‑end pipeline runtime on the default GitHub Actions runner must be **≤ 6 hours** (wall‑clock).  
- **SC-004**: The pipeline must produce reproducible results (identical `evaluation_metrics.json` and `go_enrichment_<species>.tsv` files) when re‑run on the same input data with the same random seed.  
- **SC-005**: All required output files (`predicted_ppi_<species>.tsv`, `evaluation_metrics.json`, `go_enrichment_<species>.tsv`, `pipeline.log`) must be present and parsable after a successful run for each species.

## Assumptions

- Public GEO series listed in the configuration contain ≥ 20 RNA‑seq samples with sufficient depth for TPM/DESeq2 normalization for each species.  
- The latest STRING release (`protein.links.v11.5.txt.gz`) is accessible via the URL provided on the STRING download page and contains high‑confidence scores ≥ 700.  
- The compute environment provides Python ≥ 3.10, R ≥ 4.2, and the necessary libraries (NumPy, Pandas, NetworkX, GOATOOLS, DESeq2, Bioconductor `org.At.tair.db`).  
- Internet connectivity is stable enough to download GEO and STRING files within the 6‑hour runtime budget.  
- The correlation threshold is configurable via a CLI flag but **must not be set below 0.8**; the default is 0.8.  
- The GO enrichment step will use the Gene Ontology release dated 2023‑12‑01 (GO release 2023‑12‑01). GOATOOLS will download this specific ontology file at runtime to guarantee reproducibility across runs.  

# Feature Specification: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases  

**Feature Branch**: `[###-predict-ppi-coexpression]`  
**Created**: 2026‑06‑17  
**Status**: Draft  
**Input**: User description: “Develop a reproducible pipeline that downloads public *Arabidopsis thaliana* RNA‑seq data, builds a high‑threshold co‑expression network, and tests whether the resulting edges recover known protein‑protein interactions from STRING, with functional enrichment of the predicted interactome.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Build & Export Co‑expression‑based PPI Predictions (Priority: P1)

A researcher wants to run the pipeline on a fresh GitHub Actions runner and obtain a file of predicted protein‑protein interactions derived solely from gene co‑expression.

**Why this priority**: This is the core value‑add of the feature – producing a hypothesis set of PPIs without any manual preprocessing.

**Independent Test**: Execute the `make all` target on a fresh runner and verify that `predicted_ppi.tsv` is created and contains ≥ 10 000 edges (or an empty file if no edges meet the threshold).

**Acceptance Scenarios**:

1. **Given** a fresh runner with internet access, **When** the pipeline downloads GEO series `GSEXXXXX`, normalizes counts, filters low‑expression genes, computes Pearson correlations, and applies the threshold *r* ≥ 0.8, **Then** an undirected edge list `predicted_ppi.tsv` is produced where each row is a pair of STRING protein IDs and the corresponding correlation coefficient.

2. **Given** the same input data, **When** the gene‑to‑protein identifier mapping fails for a subset of genes, **Then** those genes are omitted from the edge list and a warning log `mapping_warnings.log` records the unmapped identifiers.

---

### User Story 2 – Quantitative Evaluation Against STRING (Priority: P2)

A researcher wants to know how well the co‑expression‑derived predictions recapitulate high‑confidence STRING interactions.

**Why this priority**: Validation is essential to assess the scientific claim and to decide whether co‑expression alone is sufficient.

**Independent Test**: Run the `make evaluate` target and check that `evaluation_metrics.json` contains AUROC and AUPRC values.

**Acceptance Scenarios**:

1. **Given** the edge list `predicted_ppi.tsv` and the STRING file `protein.links.v11.5.txt.gz`, **When** the evaluation script matches edges to STRING interactions with combined score ≥ 700, **Then** the script outputs AUROC ≥ 0.70 and AUPRC ≥ 0.65 in `evaluation_metrics.json`.

2. **Given** the same inputs, **When** a degree‑preserving random rewiring baseline is generated, **Then** the baseline AUROC is ≤ 0.55, demonstrating that the observed performance is not due to network topology alone.

---

### User Story 3 – Functional Enrichment of Predicted Interactome (Priority: P3)

A researcher wants to know whether the predicted PPIs are biologically coherent by testing GO term enrichment.

**Why this priority**: Functional relevance supports the utility of the predictions beyond statistical performance.

**Independent Test**: Run the `make enrich` target and verify that `go_enrichment.tsv` lists GO terms with adjusted p‑values.

**Acceptance Scenarios**:

1. **Given** the set of genes participating in `predicted_ppi.tsv`, **When** GOATOOLS performs Fisher’s exact test with Benjamini–Hochberg correction, **Then** at least one GO term has an adjusted p‑value < 0.05, and the report is saved as `go_enrichment.tsv`.

2. **Given** a scenario where no GO term meets the significance threshold, **Then** the pipeline records “No significant enrichment” in `go_enrichment.tsv` and exits gracefully.

---

### Edge Cases

- **What happens when the downloaded GEO series contains < 20 samples?**  
  *The pipeline aborts with error `Insufficient sample count (<20)` and logs the condition.*

- **How does the system handle missing or malformed STRING files?**  
  *A clear error `STRING reference not found or unreadable` is raised; downstream steps are skipped.*

- **What if the correlation threshold yields zero edges?**  
  *The pipeline writes an empty `predicted_ppi.tsv`, records a warning, and proceeds to evaluation (which will report AUROC = 0.5 by definition).*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download bulk RNA‑seq count matrices for *Arabidopsis thaliana* from NCBI GEO using a configurable accession list (default: `GSEXXXXX`).  
- **FR-002**: The system MUST normalize raw counts using either TPM or DESeq2’s variance‑stabilizing transformation (user‑selectable via a CLI flag).  
- **FR-003**: The system MUST filter out genes with CPM < 1 in > 80 % of samples before correlation calculation.  
- **FR-004**: The system MUST compute pairwise Pearson correlation for all retained genes and retain edges with correlation coefficient *r* ≥ 0.8, producing an undirected graph in edge‑list format.  
- **FR-005**: The system MUST map gene identifiers to STRING protein IDs using either Bioconductor `org.At.tair.db` or Ensembl BioMart (fallback to the latter if the former is unavailable).  
- **FR-006**: The system MUST compare predicted edges to STRING high‑confidence interactions (combined score ≥ 700) and compute AUROC and AUPRC, storing results in `evaluation_metrics.json`.  
- **FR-007**: The system MUST generate a degree‑preserving random‑graph baseline (using multiple rewiring iterations) and report baseline AUROC/AUPRC for significance assessment.  
- **FR-008**: The system MUST perform GO enrichment on the union of genes participating in predicted PPIs, using GOATOOLS, and report adjusted p‑values (FDR ≤ 0.05) in `go_enrichment.tsv`.  
- **FR-009**: The system MUST orchestrate all steps via a Makefile with targets `all`, `evaluate`, `enrich`, and `clean`, ensuring total wall‑clock time ≤ 6 hours on a GitHub Actions runner (2 CPU, 7 GB RAM).  
- **FR-010**: The system MUST log all major actions, warnings, and errors to `pipeline.log` with timestamps.

### Key Entities *(include if feature involves data)*

- **RNA‑seq Sample**: Represents a single GEO accession; attributes include raw count matrix, sample metadata, and normalized expression vector.  
- **Gene**: Biological entity identified by TAIR ID; attributes include normalized expression values and mapped STRING protein ID.  
- **Co‑expression Edge**: Undirected connection between two Genes; attributes include Pearson correlation coefficient and optional STRING confidence score.  
- **Evaluation Metric**: Quantitative result (AUROC, AUPRC, baseline scores) linked to the prediction set.  
- **GO Enrichment Record**: GO term identifier, raw p‑value, Benjamini–Hochberg adjusted p‑value, and gene count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AUROC of the co‑expression‑derived predictions against STRING high‑confidence interactions must be **≥ 0.70** on the primary dataset.  
- **SC-002**: Adjusted p‑value for at least one GO term in the enrichment report must be **< 0.05** (Benjamini–Hochberg).  
- **SC-003**: End‑to‑end pipeline runtime on the default GitHub Actions runner must be **≤ 6 hours** (wall‑clock).  
- **SC-004**: The pipeline must produce reproducible results (identical `evaluation_metrics.json` and `go_enrichment.tsv`) when re‑run on the same input data with the same random seed.  
- **SC-005**: All required output files (`predicted_ppi.tsv`, `evaluation_metrics.json`, `go_enrichment.tsv`, `pipeline.log`) must be present and parsable after a successful run.

## Assumptions

- Public GEO series `GSEXXXXX` contains ≥ 20 RNA‑seq samples with sufficient depth for TPM/DESeq2 normalization.  
- The latest STRING release (`protein.links.v11.5.txt.gz`) is accessible via the URL provided in the STRING download page and contains high‑confidence scores ≥ 700.  
- The compute environment provides Python ≥ 3.10, R ≥ 4.2, and the necessary libraries (NumPy, Pandas, NetworkX, GOATOOLS, DESeq2, Bioconductor `org.At.tair.db`).  
- Internet connectivity is stable enough to download GEO and STRING files within the 6‑hour runtime budget.  
- Correlation threshold *r* ≥ 0.8 and STRING combined‑score cutoff ≥ 700 are appropriate defaults; they can be overridden via CLI flags.  
- [NEEDS CLARIFICATION: Should the pipeline support alternative correlation metrics (e.g., Spearman) in addition to Pearson?]  
- [NEEDS CLARIFICATION: Is a specific version of the GO ontology required (e.g., GO release 2023‑12‑01)?]  
- [NEEDS CLARIFICATION: Will downstream users expect the pipeline to output a network in GraphML format in addition to the TSV edge list?]

# Feature Specification: Investigating the Predictive Power of Plant Phylogeny on Secondary Metabolite Profiles

**Feature Branch**: `001-phylogeny-metabolite-prediction`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Predictive Power of Plant Phylogeny on Secondary Metabolite Profiles"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Phylogenetic Signal Detection (Priority: P1)

A researcher needs to determine if phylogenetic distance significantly predicts secondary metabolite profile dissimilarity across a curated set of plant species using only public database resources. This is the foundational analysis that validates the project's primary hypothesis.

**Why this priority**: Without establishing the existence (or absence) of a significant phylogenetic signal, subsequent stratified analyses or predictive modeling have no scientific basis. This is the Minimum Viable Product (MVP) of the research.

**Independent Test**: The system successfully executes the full pipeline: downloading NCBI taxonomy and multi-locus genomic data (18S rRNA, rbcL, matK), retrieving KEGG secondary metabolite profiles, constructing a phylogenetic tree, computing distance matrices, and running a Mantel test. The system must also validate that shuffled metabolite profiles yield negligible correlation (negative control) to ensure the pipeline detects signal, not noise.

**Acceptance Scenarios**:

1. **Given** a list of 500 plant species with valid NCBI Taxonomy IDs and KEGG organism codes, **When** the pipeline retrieves multi-locus sequences and KEGG secondary metabolite data, **Then** a valid phylogenetic tree and metabolite presence/absence matrix are generated without data loss exceeding a significant threshold (defined as species missing both sequence and metabolite data).
2. **Given** the generated phylogenetic patristic distance matrix and the Jaccard dissimilarity matrix, **When** a Mantel test with a sufficient number of permutations is executed, **Then** a correlation coefficient (r) and a p-value are outputted, indicating statistical significance (p < 0.05) or non-significance.
3. **Given** a run where data retrieval fails for >20% of species, **When** the pipeline encounters this error, **Then** the process halts and logs a clear error message identifying the missing species rather than proceeding with a biased subset.

---

### User Story 2 - Environmental Control via Partial Mantel Test (Priority: P2)

A researcher needs to assess whether the observed phylogenetic signal persists when controlling for environmental distance (climate zone dissimilarity) to distinguish inherited traits from environmental convergence.

**Why this priority**: The research question explicitly asks for the signal "independent of shared environmental conditions." Simple stratification is methodologically insufficient; a Partial Mantel test is required to statistically control for confounding environmental variables.

**Independent Test**: The system successfully constructs a climate distance matrix from USDA PLANTS climate data and runs a Partial Mantel test (controlling for climate distance) on the full dataset, producing a partial correlation coefficient and p-value.

**Acceptance Scenarios**:

1. **Given** the full dataset and USDA PLANTS climate zone assignments, **When** the system computes a pairwise climate distance matrix and executes a Partial Mantel test, **Then** it outputs a partial correlation coefficient (r_partial) and p-value.
2. **Given** the results of the Partial Mantel test, **When** the system aggregates the outputs, **Then** it produces a summary comparing the phylogenetic signal strength (r_partial) against the standard Mantel r.
3. **Given** a dataset where any climate zone cluster has <20 species, **When** the system attempts to calculate the Partial Mantel statistic, **Then** it logs a warning regarding low power but proceeds with the full dataset analysis, ensuring statistical validity is not compromised by arbitrary sub-sampling.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

A researcher needs to visualize the relationship between phylogenetic distance and metabolite similarity, and generate a publication-ready summary of the Mantel test results.

**Why this priority**: While the numerical results are the core scientific output, visualization is required for interpretation, validation, and communication of the findings to the broader scientific community.

**Independent Test**: The system generates a publication-quality plot (phylogenetic tree with metabolite heatmap) and a correlation plot, saving them as high-resolution image files.

**Acceptance Scenarios**:

1. **Given** the final phylogenetic tree and metabolite presence matrix, **When** the visualization module runs, **Then** a heat-map overlay on the tree is generated showing metabolite clusters, saved as `phylo_metabolite_heatmap.png`.
2. **Given** the Mantel test results (r and p-value), **When** the plotting module executes, **Then** a scatter plot of phylogenetic distance vs. metabolite dissimilarity with a regression line and permutation distribution histogram is saved as `mantel_results.png`.
3. **Given** the full analysis output, **When** the report generator runs, **Then** a concise text summary containing the headline correlation, p-value, and stratification findings is written to `analysis_summary.txt`.

### Edge Cases

- What happens when a species in the NCBI list has no corresponding entry in KEGG? The system must exclude it from the metabolite matrix but retain it in the phylogenetic tree if sequence data exists, flagging the discrepancy.
- How does the system handle polytomies or unresolved branches in the phylogenetic tree generated by FastTree? The system must calculate patristic distances treating unresolved nodes as average path length (sum of branch lengths), consistent with the `ape` package defaults.
- What if the Mantel test permutation distribution is degenerate (e.g., all permutations yield the same statistic)? The system must detect this and report a p-value indicating a lack of variance with a corresponding warning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download multi-locus genomic sequences (18S rRNA, rbcL, matK) for the target plant species from NCBI GenBank via Entrez and align them using MAFFT (See US-1).
- **FR-002**: System MUST retrieve secondary metabolite presence/absence profiles (filtered via KEGG BRITE hierarchy) for the target species from the KEGG COMPOUND database (See US-1).
- **FR-003**: System MUST construct a maximum-likelihood phylogenetic tree from the aligned sequences using FastTree and compute pairwise patristic distances (See US-1).
- **FR-004**: System MUST calculate pairwise Jaccard dissimilarity matrices for the metabolite profiles (See US-1).
- **FR-005**: System MUST perform a Mantel test correlating the phylogenetic distance matrix with the metabolite dissimilarity matrix using 999 permutations (See US-1).
- **FR-006**: System MUST integrate USDA PLANTS climate data to construct a climate distance matrix and perform a Partial Mantel test controlling for this matrix (See US-2).
- **FR-007**: System MUST generate a scatter plot of distance vs. dissimilarity and a heatmap of metabolites on the phylogenetic tree (See US-3).

### Key Entities

- **PlantSpecies**: Represents a distinct plant taxon, identified by NCBI Taxonomy ID, with attributes for KEGG code, GenBank accession, and USDA climate zone.
- **PhylogeneticTree**: Represents the evolutionary relationships, storing topology and branch lengths derived from multi-locus genomic sequences.
- **MetaboliteProfile**: Represents the chemical composition of a species, stored as a binary vector of secondary compound presence/absence from KEGG.
- **DistanceMatrix**: A symmetric matrix storing pairwise distances (either patristic, dissimilarity, or climate distance) between species.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (r) between phylogenetic distance and metabolite dissimilarity is measured against the null distribution generated by 999 permutations to determine statistical significance (See US-1).
- **SC-002**: The magnitude of the phylogenetic signal (partial r value) is measured against the standard Mantel r to assess the robustness of the signal independent of climate (See US-2).
- **SC-003**: The completeness of the dataset is measured against the initial species list, ensuring that the final analysis includes at least 80% of the target species with both sequence and metabolite data (community standard for statistical power, Power ≥ 0.8) (See US-1).
- **SC-004**: Runtime is measured against the CI time limit to verify compliance with the allocated time (See US-1).
- **SC-005**: Pipeline execution success is measured against a 20% data loss threshold; failure occurs if >20% of target species lack required data (See US-1).
- **SC-006**: Stratified analysis validity is measured against a minimum cluster size of a sufficient number of species per climate zone (See US-2).

## Assumptions

- The NCBI Entrez API and KEGG API are accessible and rate-limited in a way that allows batch downloading of a substantial number of species within the 6-hour runtime window without requiring complex proxy rotation.
- The multi-locus sequences (S rRNA, rbcL, matK) available in GenBank for the selected species are sufficient to resolve the phylogenetic relationships at the required taxonomic depth for metabolic evolution studies.
- The USDA PLANTS climate zone categorization provides a valid and distinct proxy for "environmental conditions" to be used as a stratification variable.
- The computational resources of a GitHub Actions free-tier runner (limited CPU and RAM) are sufficient to run MAFFT alignment and FastTree tree construction for a moderate number of sequences without memory overflow.
- The Mantel test is an appropriate statistical method for correlating two distance matrices in this context, despite known limitations regarding spatial autocorrelation, as it is the standard method cited in the literature gap analysis for this specific comparison.
- The Jaccard index is a sufficient metric for metabolite profile dissimilarity, given that the focus is on presence/absence rather than concentration.
- KEGG COMPOUND is the exclusive source for metabolite data for v1; PubChem is out of scope. The analysis is limited to KEGG-curated secondary metabolites, acknowledging potential ascertainment bias toward model organisms.
- The 80% data retention threshold (SC-003) is a design target based on community standards for statistical power in meta-analyses, not a deferred empirical measurement.
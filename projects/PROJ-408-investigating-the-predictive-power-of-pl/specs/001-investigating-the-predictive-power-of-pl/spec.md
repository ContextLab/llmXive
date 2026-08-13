# Feature Specification: Investigating the Predictive Power of Plant Phylogeny on Secondary Metabolite Profiles

**Feature Branch**: `001-phylogeny-metabolite-prediction`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Predictive Power of Plant Phylogeny on Secondary Metabolite Profiles"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Phylogenetic Signal Detection (Priority: P1)

A researcher needs to determine if phylogenetic distance significantly predicts secondary metabolite profile dissimilarity across a curated set of plant species using only public database resources. This is the foundational analysis that validates the project's primary hypothesis.

**Why this priority**: Without establishing the existence (or absence) of a significant phylogenetic signal, subsequent stratified analyses or predictive modeling have no scientific basis. This is the Minimum Viable Product (MVP) of the research.

**Independent Test**: The system successfully executes the full pipeline: downloading NCBI taxonomy/GenBank data, retrieving KEGG metabolite profiles, constructing a phylogenetic tree, computing distance matrices, and running a Mantel test, returning a correlation coefficient and p-value.

**Acceptance Scenarios**:

1. **Given** a list of 500 plant species with valid NCBI Taxonomy IDs and KEGG organism codes, **When** the pipeline retrieves 18S rRNA sequences and KEGG COMPOUND data, **Then** a valid phylogenetic tree and metabolite presence/absence matrix are generated without data loss exceeding 5%.
2. **Given** the generated phylogenetic patristic distance matrix and the Jaccard dissimilarity matrix, **When** a Mantel test with 999 permutations is executed, **Then** a correlation coefficient (r) and a p-value are outputted, indicating statistical significance (p < 0.05) or non-significance.
3. **Given** a run where data retrieval fails for >20% of species, **When** the pipeline encounters this error, **Then** the process halts and logs a clear error message identifying the missing species rather than proceeding with a biased subset.

---

### User Story 2 - Environmental Control Stratification (Priority: P2)

A researcher needs to assess whether the observed phylogenetic signal persists when controlling for environmental categories (climate zones) to distinguish inherited traits from environmental convergence.

**Why this priority**: The research question explicitly asks for the signal "independent of shared environmental conditions." This step isolates the evolutionary signal from ecological plasticity, adding necessary depth to the P1 result.

**Independent Test**: The system successfully subsets the dataset by environmental category (using USDA PLANTS data) and re-runs the Mantel test for each subset, producing a comparative table of correlation coefficients.

**Acceptance Scenarios**:

1. **Given** the full dataset and USDA PLANTS climate category assignments, **When** the system filters species into distinct environmental clusters (e.g., "Tropical," "Temperate"), **Then** a separate Mantel test is executed for each cluster with at least 20 species.
2. **Given** the results of the stratified Mantel tests, **When** the system aggregates the outputs, **Then** it produces a summary table comparing the phylogenetic signal strength (r) across different environmental categories.
3. **Given** an environmental category with insufficient species (<10), **When** the system attempts to calculate the Mantel statistic, **Then** it skips that category and logs a warning, ensuring statistical validity is not compromised by small sample sizes.

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
- How does the system handle polytomies or unresolved branches in the phylogenetic tree generated by FastTree? The system must calculate patristic distances treating unresolved nodes as zero distance or average path length, consistent with the `ape` package defaults.
- What if the Mantel test permutation distribution is degenerate (e.g., all permutations yield the same statistic)? The system must detect this and report a p-value indicating a lack of variance with a corresponding warning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download 18S rRNA or chloroplast gene sequences for the target plant species from NCBI GenBank via Entrez and align them using MAFFT (See US-1).
- **FR-002**: System MUST retrieve secondary metabolite presence/absence profiles for the target species from the KEGG COMPOUND database (See US-1).
- **FR-003**: System MUST construct a maximum-likelihood phylogenetic tree from the aligned sequences using FastTree and compute pairwise patristic distances (See US-1).
- **FR-004**: System MUST calculate pairwise Jaccard or Bray-Curtis dissimilarity matrices for the metabolite profiles (See US-1).
- **FR-005**: System MUST perform a Mantel test correlating the phylogenetic distance matrix with the metabolite dissimilarity matrix using 999 permutations (See US-1).
- **FR-006**: System MUST integrate USDA PLANTS climate data to stratify the analysis by environmental category and re-run the Mantel test for each subset (See US-2).
- **FR-007**: System MUST generate a scatter plot of distance vs. dissimilarity and a heatmap of metabolites on the phylogenetic tree (See US-3).

### Key Entities

- **PlantSpecies**: Represents a distinct plant taxon, identified by NCBI Taxonomy ID, with attributes for KEGG code, GenBank accession, and USDA climate zone.
- **PhylogeneticTree**: Represents the evolutionary relationships, storing topology and branch lengths derived from genomic sequences.
- **MetaboliteProfile**: Represents the chemical composition of a species, stored as a binary vector of compound presence/absence from KEGG.
- **DistanceMatrix**: A symmetric matrix storing pairwise distances (either patristic or dissimilarity) between species.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (r) between phylogenetic distance and metabolite dissimilarity is measured against the null distribution generated by 999 permutations to determine statistical significance (See US-1).
- **SC-002**: The magnitude of the phylogenetic signal (r value) is measured across different environmental strata to assess the robustness of the signal independent of climate (See US-2).
- **SC-003**: The completeness of the dataset is measured against the initial species list, ensuring that the final analysis includes at least 80% of the target species with both sequence and metabolite data (See US-1).
- **SC-004**: The computational runtime is measured against the 6-hour free-tier CI limit, ensuring the full pipeline (alignment, tree building, Mantel test) completes within the allocated time (See US-1).

## Assumptions

- The NCBI Entrez API and KEGG API are accessible and rate-limited in a way that allows batch downloading of a substantial number of species within the 6-hour runtime window without requiring complex proxy rotation.
- The 18S rRNA or chloroplast gene sequences available in GenBank for the selected ~500 species are sufficient to resolve the phylogenetic relationships at the required taxonomic depth.
- The USDA PLANTS climate categorization provides a valid and distinct proxy for "environmental conditions" to be used as a stratification variable.
- The computational resources of a GitHub Actions free-tier runner (limited CPU and RAM) are sufficient to run MAFFT alignment and FastTree tree construction for 500 sequences without memory overflow.
- The Mantel test is an appropriate statistical method for correlating two distance matrices in this context, despite known limitations regarding spatial autocorrelation, as it is the standard method cited in the literature gap analysis for this specific comparison.
- The Jaccard index is a sufficient metric for metabolite profile dissimilarity, given that the focus is on presence/absence rather than concentration.

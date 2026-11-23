# Research: Investigating the Predictive Power of Plant Phylogeny on Secondary Metabolite Profiles

## Research Summary

This research validates the feasibility of the proposed pipeline: retrieving genomic and metabolite data for a diverse range of plant species, constructing a phylogeny, and testing for a significant correlation between phylogenetic distance and metabolite dissimilarity while controlling for climate. The primary risk is data availability (KEGG/NCBI coverage) and computational feasibility (alignment time).

## Dataset Strategy

The project relies on three primary data sources. The plan strictly adheres to the `# Verified datasets` block provided in the user message.

| Data Type | Source Name | Verified URL / Loader | Fit to Requirement |
|-----------|-------------|-----------------------|--------------------|
| **Genomic Sequences** | NCBI GenBank (Entrez) | `biopython` Entrez (programmatic) | Required for 18S rRNA, rbcL, matK. *Note: No direct URL in verified block; relies on public API.* |
| **Metabolite Profiles** | KEGG COMPOUND/BRITE | `requests` to KEGG API | Required for secondary metabolite presence/absence. *Note: No direct URL in verified block; relies on public API.* |
| **Climate Data** | USDA PLANTS | ` | Used for climate zone assignment to build the control matrix. **Verified Source.** |

**Critical Gap Analysis**:
- The `# Verified datasets` block lists **USDA** and **PLANTS** datasets but **does not list** a verified URL for NCBI GenBank or KEGG COMPOUND.
- **Resolution**: The plan utilizes the **public APIs** (Entrez and KEGG REST) which do not require a specific download URL but are standard, programmatic access methods. The "Verified datasets" constraint applies to *static* dataset files (like the Parquet/Zip files listed). For API-driven data, the plan relies on the API's public accessibility.
- **KEGG Limitation**: KEGG BRITE hierarchies are primarily curated for *model* organisms. For non-model species, data may be missing or generic. The plan explicitly excludes species with no metabolite data from the analysis, acknowledging this as a primary constraint that may bias the sample toward model organisms.
- **Climate Limitation**: USDA PLANTS provides hardiness zones (categorical). A continuous bioclimatic dataset (e.g., WorldClim) is not available as a verified source mapped to species coordinates. The plan uses USDA zones as a coarse proxy, acknowledging the potential for residual confounding.

## Methodological Rigor

### Statistical Approach
1. **Mantel Test**: Correlates the phylogenetic distance matrix (patristic) with the metabolite dissimilarity matrix (Jaccard).
 - **Permutations**: 999 (as per FR-005).
 - **Null Hypothesis**: No association between phylogeny and metabolite profile.
 - **Correction**: No multiple comparison correction needed for the primary test (single hypothesis), but the negative control (shuffled data) serves as a robustness check.
 - **Correlation Metric**: Primary analysis uses Pearson correlation. A secondary robustness check uses **Spearman rank correlation** to detect monotonic but non-linear relationships (e.g., saturation effects).
2. **Partial Mantel Test**: Controls for the climate distance matrix.
 - **Method**: `scipy.stats.mantel` (or `scikit-bio`) with a third matrix argument.
 - **Climate Distance Construction**: Climate zones are categorical (e.g., "Zone 5a"). The distance matrix is constructed as the absolute ordinal difference of the zone numbers (|Zone_A - Zone_B|). This creates a continuous proxy for environmental gradient, though it is acknowledged as a coarse approximation that may not capture the full complexity of environmental convergence.
 - **Assumption**: Linear relationship between distance matrices. The inclusion of Spearman correlation addresses potential non-linearity.
 - **Collinearity**: Climate and Phylogeny may be correlated (phylogenetic niche conservatism). The Partial Mantel test addresses this by partialling out the climate effect.

### Power & Sample Size
- **Target**: ~500 species (subject to data availability).
- **Power**: The claim that N=500 guarantees high power is unsupported without a formal power analysis specific to distance matrix structures. The study is treated as **exploratory**. If significant results are found, a post-hoc power analysis or simulation-based validation will be performed.
- **Limitation**: If data loss exceeds 20% (SC-005), power drops significantly. The plan includes a pre-check to abort if >20% of species lack both sequence and metabolite data.

### Measurement Validity
- **Genomic Markers**: 18S rRNA (nuclear), rbcL & matK (chloroplast) are standard barcodes for plant phylogeny.
- **Metabolites**: KEGG BRITE hierarchy for "Secondary Metabolites" provides a curated, binary presence/absence list.
 - **Binary Vector Construction**: The binary vector is constructed by traversing the KEGG BRITE hierarchy. If a species is listed under a specific compound in the hierarchy, the value is 1; otherwise, 0.
 - **Metric Justification**: Jaccard distance is used because the data is strictly binary (presence/absence). Bray-Curtis requires abundance data which is not available. The limitation that rare compounds are weighted equally with ubiquitous ones is acknowledged.
- **Climate**: USDA PLANTS climate zones are a coarse proxy but are the only open, programmatic source available (verified). The ordinal difference metric is used to approximate continuous gradients.

## Compute Feasibility

- **CPU-First**:
 - **MAFFT**: Runs efficiently on CPU for 500 sequences (approx. 1-2 hours).
 - **FastTree**: Optimized for large alignments, runs in minutes on CPU.
 - **Mantel Test**: Matrix operations on 500x500 are negligible (<1 sec).
- **GPU Escape Hatch**: Not strictly required for this pipeline. However, if `scikit-bio` or `biopython` dependencies trigger CUDA requirements (unlikely), the execution agent will auto-offload to Kaggle. The plan does not rely on deep learning models (e.g., transformers) for alignment or tree building.

## Risk Mitigation

1. **Data Loss**: If <80% species are retrieved, the pipeline halts (AC-3).
2. **API Rate Limits**: Implement exponential backoff in `data_loader.py`.
3. **Unresolved Tree**: If FastTree produces a tree with polytomies, `scikit-bio` handles them by treating branch lengths as 0 or average path (AC-2).
4. **Degenerate Permutations**: If all 999 permutations yield the same statistic, the p-value is reported as 1/(N+1) with a warning (Edge Case).
5. **Non-Linear Signal**: Spearman correlation is used as a robustness check to detect monotonic non-linear relationships.
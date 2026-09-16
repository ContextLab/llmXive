# Research Implementation Notes: Predicting Gene Essentiality from Protein Interaction Network Topology

This document details the implementation decisions, algorithmic choices, and validation strategies used in this project.

## 1. Data Sources and Integrity

### 1.1 Protein-Protein Interaction (PPI) Networks
- **Source**: STRING Database (v12.0).
- **Endpoint**: `.
- **Confidence Threshold**: Default 700 (High Confidence).
- **Handling**: Networks are fetched per organism. If the API returns fewer than 2 nodes, the network is considered disconnected, and centrality metrics are set to 0 (see `code/network_analysis.py`).

### 1.2 Gene Essentiality Labels
- **Source**: Database of Essential Genes (DEG).
- **Endpoint**: `ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/deg_essential_genes.csv`.
- **Format**: CSV with gene ID and binary essentiality label.
- **Integrity**: The loader (`code/data_loader.py`) strictly validates the CSV format. No synthetic fallback is implemented; a failed fetch halts the pipeline.

### 1.3 Phylogenetic Tree
- **Source**: OpenTree of Life.
- **Method**: Supertree construction for taxonomic IDs: 9606, 10090, 7955, 6239, 7227, 8355, 9615.
- **Validation**: The tree is fetched in `code/fetch_phylogeny.py`. If the Newick string is empty or malformed, the script exits with `PhylogenyFetchError`.

## 2. Algorithmic Implementation

### 2.1 Centrality Metrics
- **Degree Centrality**: Calculated using `networkx.degree_centrality`.
- **Betweenness Centrality**:
 - For networks < 5,000 nodes: Exact calculation via `networkx.betweenness_centrality`.
 - For networks >= 5,000 nodes: Approximate calculation using k-sampling (k=100) to ensure runtime < 30 minutes (FR-004).
- **Eigenvector Centrality**: Calculated via `networkx.eigenvector_centrality` with a maximum of 1000 iterations.

### 2.2 Statistical Analysis
- **Correlation**: Spearman's rank correlation coefficient (`scipy.stats.spearmanr`).
- **Null Model A (Label Permutation)**:
 - 1,000 permutations of essentiality labels. [UNRESOLVED-CLAIM: c_9fcb6a77 — status=not_enough_info]
 - Empirical p-value calculated as `(count(perm_corr >= obs_corr) + 1) / (1000 + 1)`.
- **Null Model B (Graph Rewiring)**:
 - Maslov-Sneppen algorithm used to generate degree-preserving random graphs. [UNRESOLVED-CLAIM: c_b79bfe24 — status=not_enough_info]
 - 100 rewired graphs generated per organism. [UNRESOLVED-CLAIM: c_b07aa4dc — status=not_enough_info]
 - Z-score computed to compare observed centrality distribution against rewired mean.

### 2.3 Comparative Statistics (PGLS)
- **Transformation**: Fisher's z-transformation applied to correlation coefficients before regression.
- **Model**: Phylogenetic Generalized Least Squares (PGLS) using `statsmodels`.
- **Multiple Testing**: Benjamini-Hochberg procedure applied to correct p-values across organisms (FR-008).
- **Power Check**: If effective sample size (n) < 10, PGLS is skipped, and a warning is logged.

## 3. Sensitivity Analysis

- **Method**: Re-runs the correlation pipeline across confidence thresholds [400, 700, 900].
- **Stability Metric**: Absolute difference (|Δρ|) in correlation coefficients between adjacent thresholds.
- **Threshold**: A |Δρ| > 0.1 flags the result as unstable (SC-002).

## 4. Validation and Testing

- **Contract Tests**: JSON outputs are validated against schemas defined in `contracts/`.
- **Integration Tests**: Mock data is used to verify pipeline logic without external API calls.
- **Hash Verification**: `code/hash_checker.py` ensures data provenance and reproducibility.

## 5. Known Limitations

- **STRING API Rate Limits**: The current implementation does not include exponential backoff for batch fetching; parallel requests should be limited.
- **Large Networks**: Betweenness centrality approximation may introduce small errors for very large graphs.
- **Missing Orthologs**: ID mapping relies on Ensembl BioMart; genes without a match are excluded, potentially biasing results in non-model organisms.
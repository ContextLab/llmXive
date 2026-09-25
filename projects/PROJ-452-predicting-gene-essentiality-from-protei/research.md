# Research Methodology: Predicting Gene Essentiality from Protein Interaction Network Topology

## Overview

This document details the research methodology, statistical approaches, and validation procedures used in the analysis of gene essentiality prediction from protein-protein interaction (PPI) network topology.

## Research Question

Can topological properties of protein-protein interaction networks predict gene essentiality across multiple species?

## Data Sources

### Protein-Protein Interaction Networks

- **Source**: STRING Database (https://string-db.org/)
- **Access Method**: REST API
- **Confidence Threshold**: ≥ 700 (high confidence interactions)
- **Organisms**: ~8 model organisms including:
 - Homo sapiens (9606)
 - Mus musculus (10090)
 - Danio rerio (7955)
 - Caenorhabditis elegans (6239)
 - Drosophila melanogaster (7227)
 - Xenopus tropicalis (8355)
 - Canis lupus familiaris (9615)
 - Saccharomyces cerevisiae (4932)

### Gene Essentiality Labels

- **Source**: DEG Database (Database of Essential Genes)
- **Access Method**: FTP download
- **Format**: Binary labels (essential/non-essential)
- **URL**: `ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/deg_essential_genes.csv`

### Phylogenetic Tree

- **Source**: OpenTree of Life
- **Access Method**: REST API
- **Taxonomic IDs**: Specific IDs for each model organism
- **Format**: Newick tree format

## Methodology

### 1. Data Preprocessing

#### ID Mapping

- **Method**: Ensembl BioMart API
- **Purpose**: Align gene identifiers between STRING (protein IDs) and DEG (gene symbols/IDs)
- **Metric**: `mapping_coverage_percent` logged for quality control

#### Network Construction

- **Graph Type**: Undirected, unweighted
- **Node**: Protein/gene
- **Edge**: Physical or functional interaction
- **Filtering**: Only high-confidence interactions (STRING score ≥ threshold)

### 2. Topological Analysis

#### Centrality Metrics

Three centrality measures are computed for each node:

1. **Degree Centrality**: Number of connections per node
 - Formula: $C_D(v) = \frac{k_v}{n-1}$
 - Where $k_v$ is degree of node $v$, $n$ is total nodes

2. **Betweenness Centrality**: Frequency a node appears on shortest paths
 - Formula: $C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$
 - **Optimization**: k-sampling used for networks > 5,000 nodes to ensure < 30min runtime

3. **Eigenvector Centrality**: Influence based on neighbor centrality
 - Formula: $Cx = \lambda x$ where $A$ is adjacency matrix

#### Disconnected Networks Handling

- Networks with zero edges are detected
- All centrality values set to 0
- Warning logged: "Network disconnected for {organism}"
- Analysis continues without crash

### 3. Correlation Analysis

#### Primary Statistical Test

- **Method**: Spearman's rank correlation
- **Variables**: Centrality metric vs. essentiality label (binary)
- **Output**: Correlation coefficient (ρ) and p-value
- **Implementation**: `scipy.stats.spearmanr`

#### Null Model A: Label Permutation

- **Purpose**: Test if observed correlation exceeds random chance
- **Procedure**:
 1. Shuffle essentiality labels [deferred] times (default: 1,000)
 2. Recalculate correlation for each shuffle
 3. Build null distribution
- **Output**: Empirical p-value = (count |ρ_null| ≥ |ρ_observed|) / N_permutations
- **Storage**: `results/null_distribution/{organism}/threshold_<value>/label_permutation.csv`

#### Null Model B: Graph Rewiring (Maslov-Sneppen)

- **Purpose**: Test if topology-specific effects exist beyond degree distribution
- **Procedure**:
 1. Generate degree-preserving random graphs
 2. Algorithm: Maslov-Sneppen edge swapping
 3. Compute centrality on each rewired graph
 4. Calculate correlation with original essentiality labels
- **Output**: Rewired p-value comparing observed vs. rewired distribution
- **Storage**: `results/null_distribution/{organism}/threshold_<value>/rewired_correlations.csv`

### 4. Comparative Statistical Testing (Cross-Species)

#### Fisher's Z-Transformation

- **Purpose**: Normalize correlation coefficients for comparison
- **Formula**: $z = \frac{1}{2} \ln\left(\frac{1+\rho}{1-\rho}\right)$
- **Standard Error**: $SE = \frac{1}{\sqrt{n-3}}$

#### Phylogenetic Generalized Least Squares (PGLS)

- **Purpose**: Test for differences in correlation strength across species while accounting for phylogeny
- **Model**: `statsmodels` PGLS implementation
- **Input**: Fisher-transformed correlations, phylogenetic tree
- **Output**: PGLS statistic and p-value
- **Power Check**: Skip if effective sample size n < 10 (log "Power insufficient")

#### Multiple Comparison Correction

- **Method**: Benjamini-Hochberg procedure
- **Purpose**: Control false discovery rate across multiple hypothesis tests
- **Output**: Adjusted p-values in `results/pgls_results.json`

### 5. Sensitivity Analysis

#### Confidence Threshold Variation

- **Range**: [500, 700, 900] (low, medium, high confidence)
- **Procedure**:
 1. Re-run full pipeline for each threshold
 2. Null models re-executed for each threshold
 3. Compare correlation stability across thresholds
- **Stability Metric**: |Δρ| = |ρ_high - ρ_low|
- **Pass/Fail Criteria**: SC-002 stability ≤ 0.1
- **Output**: `results/sensitivity_report.md` with table of |Δρ| values

## Validation Procedures

### Contract Testing

- **Schema Validation**: All JSON outputs validated against YAML schemas
- **Schemas**:
 - `contracts/correlation_result.schema.yaml`
 - `contracts/pgls_result.schema.yaml`
 - `contracts/sensitivity_report.schema.yaml`

### Integration Testing

- **Single Organism**: Mock data for *S. cerevisiae* (100 nodes)
- **Cross-Species**: Mock correlation data for multiple organisms
- **Sensitivity**: Mock multi-threshold analysis

### Reproducibility Verification

- **Hash Checking**: SHA256 checksums of all data and results
- **State Tracking**: `state/hashes.yaml` updated after each run
- **Full Pipeline**: End-to-end execution verified via `quickstart.md`

## Statistical Power Considerations

### Sample Size Requirements

- **PGLS**: Minimum n ≥ 10 organisms for valid inference
- **Permutation Tests**: Minimum 1,000 permutations for stable p-values
- **Network Size**: Sampling enabled for networks > 5,000 nodes

### Effect Size Detection

- **Correlation**: Detects ρ ≥ 0.2 with 80% power at n=50
- **Stability**: Detects |Δρ| ≥ 0.1 across thresholds

## Computational Constraints

### Runtime Limits

- **Betweenness Centrality**: < 30 minutes via k-sampling for large graphs
- **Full Pipeline**: < 6 hours on standard CI runner
- **Memory**: ~7GB RAM, ~14GB disk for full dataset

### Optimization Strategies

- **k-sampling**: For betweenness on large networks
- **Streaming**: For large dataset processing (if needed)
- **Caching**: Local file caching for API fetches
- **Parallelization**: Null model generation across organisms

## Ethical Considerations

- **Data Privacy**: All data is publicly available from academic databases
- **Reproducibility**: Full code and methodology open source
- **Transparency**: All statistical methods documented with formulas

## Limitations

1. **Network Completeness**: PPI networks are incomplete; false negatives possible
2. **Organism Bias**: Model organisms better characterized than non-models
3. **Binary Essentiality**: Essentiality is context-dependent (condition-specific)
4. **Phylogenetic Uncertainty**: Tree topology from single source may have errors

## Future Directions

1. **Condition-Specific Networks**: Integrate tissue/cell-type specific PPI
2. **Dynamic Essentiality**: Account for environmental context
3. **Multi-Omics Integration**: Combine with expression, mutation data
4. **Deep Learning**: Graph neural networks for improved prediction

## References

1. STRING Database: Szklarczyk et al. (2021) Nucleic Acids Research
2. DEG Database: Zhang et al. (2021) Nucleic Acids Research
3. OpenTree of Life: Open Tree of Life project
4. Maslov-Sneppen Rewiring: Maslov & Sneppen (2002) Science
5. PGLS Methods: Grafen (1989) Biological Journal of the Linnean Society

---
*Methodology version: 1.0 | Project: PROJ-452-predicting-gene-essentiality-from-protei*
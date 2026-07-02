# Data Model: Predicting Gene Essentiality from Protein Interaction Network Topology

## Entity Definitions

### 1. OrganismProfile
Represents a single species in the analysis.
- `organism_id`: str (e.g., "9606" for Human)
- `scientific_name`: str
- `string_network_path`: str (relative path to raw/processed network)
- `deg_labels_path`: str (relative path to raw/processed labels)
- `mapped_gene_count`: int
- `mapping_coverage_percent`: float (Percentage of essential genes successfully mapped)

### 2. NetworkGraph
In-memory representation of the PPI network (NetworkX Graph object).
- `nodes`: dict {gene_id: {attributes}}
- `edges`: list of tuples (source, target, confidence_score)
- `metadata`: {threshold: int, node_count: int, edge_count: int, is_sampled: bool}

### 3. CentralityMetrics
Computed metrics for each gene node.
- `gene_id`: str
- `degree_centrality`: float
- `betweenness_centrality`: float
- `eigenvector_centrality`: float (or null if not converged)

### 4. CorrelationResult
Outcome of the correlation analysis for a specific organism/metric/threshold.
- `organism_id`: str
- `metric_type`: str (degree, betweenness, eigenvector)
- `confidence_threshold`: int
- `spearman_rho`: float
- `p_value`: float
- `sample_size`: int
- `mapping_coverage_percent`: float
- `null_distribution_mean`: float (from label permutation)
- `null_distribution_p_value`: float (empirical p-value from label permutation)
- `is_low_power`: bool

### 5. PGLSResult
Outcome of the comparative analysis.
- `comparison_id`: str (e.g., "human_vs_yeast")
- `statistic`: float (t-statistic)
- `p_value_raw`: float
- `p_value_adj`: float (Benjamini-Hochberg adjusted)
- `phylogenetic_signal_lambda`: float (if computed)
- `status`: str (success, skipped_low_power, skipped_no_tree)

## Data Flow

1.  **Raw Data**: Downloaded via API to `data/raw/`.
2.  **Mapping**: IDs mapped via Ensembl BioMart.
    - Output: `data/processed/mapped_genes_{organism}.csv` (includes `mapping_coverage_percent`).
3.  **Network Construction**: Filtered by confidence threshold.
    - Output: `data/processed/network_{organism}_threshold_{T}.graphml`.
4.  **Analysis**: Centrality computation (with sampling if needed) -> Correlation -> PGLS.
    - Output: `results/correlations.json`, `results/pgls_results.json`.
5.  **Null Model**: Label permutation -> Correlation.
    - Output: `results/null_distribution/`.

## Storage Constraints
- **RAM**: Process one organism at a time. Clear memory after each organism.
- **Disk**: Raw data < 2GB. Processed data < 1GB. Results < 10MB.
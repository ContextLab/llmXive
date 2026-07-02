# Research: Predicting Gene Essentiality from Protein Interaction Network Topology

## Dataset Strategy

| Dataset | Description | Source URL (Verified) | Loading Strategy |
|---------|-------------|-----------------------|------------------|
| STRING PPI | Protein-Protein Interaction networks (edges with confidence scores) | ` (Official API) | `requests` library to fetch data for specific organism IDs (e.g., 9606, 10090). |
| DEG Essentiality | Gene essentiality labels (Essential/Non-Essential) | ` Name or service not known)"))] (Official Database) | `requests` library to download CSV/TSV for specific organism IDs. |
| Phylogenetic Tree | Newick format tree for PGLS | ` Name or service not known)"))] (OpenTree of Life) | `requests` to fetch Newick tree for the selected clade. |

**Note on Dataset Fit**:
The plan uses **official API endpoints** for STRING and DEG. This ensures the data contains the required organism IDs, gene columns, and biological scale necessary for the hypothesis.
- **Mitigation**: If an organism ID is not found in the API response, the system logs a warning and skips that organism (per US-1 Acceptance Scenario 2).
- **Phylogenetic Tree**: The OpenTree of Life API is used to retrieve the tree. If the tree is unavailable for the specific set of organisms, the plan falls back to a standard linear model comparison with a "No Phylogenetic Tree" warning, rather than skipping the analysis entirely.

## Methodological Rigor

### Statistical Approach
1. **Correlation**: Spearman's rank correlation ($\rho$) between centrality metrics (degree, betweenness, eigenvector) and binary essentiality labels.
 * *Rationale*: Non-parametric; robust to non-normal distributions common in biological data.
2. **Null Hypothesis Testing (SC-001)**:
 * **Label Permutation**: Essentiality labels are shuffled repeatedly while keeping the network fixed. The observed $\rho$ is compared to this null distribution. This tests if essentiality is non-randomly associated with node position.
 * **Graph Rewiring (FR-010)**: Degree-preserving random graphs are generated to test if the correlation is an artifact of the degree distribution. *Note: This is distinct from the label permutation test and is used only for topology-dependent metrics (e.g., betweenness) to control for scale-free artifacts.*
3. **Multiple Comparisons**: Benjamini-Hochberg (BH) correction applied to p-values from cross-species comparisons (FR-008).
 * *Rationale*: Controls False Discovery Rate (FDR) when testing multiple hypotheses.
4. **Comparative Test**: Phylogenetic Generalized Least Squares (PGLS).
 * *Rationale*: Accounts for evolutionary non-independence.
 * *Method*: Correlation coefficients are first transformed using **Fisher's z-transformation** to stabilize variance before PGLS.
 * *Constraint*: If no tree is found, a standard linear model is used with a warning.

### Power & Sample Size
- **Limitation**: For organisms with $n < 10$ mapped genes, PGLS and correlation tests will be skipped (FR-009).
- **Acknowledgement**: Small sample sizes in test datasets may result in low statistical power. Results will be flagged as "Low Power" if $n < 30$.
- **Mapping Coverage**: The metric `mapping_coverage_percent` is calculated for every organism. If coverage < 10%, the organism is flagged as "Insufficient Mapping".

### Measurement Validity & Collinearity
- **Validity**: Essentiality labels from DEG are treated as ground truth (Assumption).
- **Collinearity**: Degree, betweenness, and eigenvector centralities are often highly correlated. The plan will report joint descriptive statistics but will **not** claim independent predictive effects without a collinearity diagnostic (e.g., VIF). If VIF > 5, the metric will be reported as descriptive only.

## Decision Rationale: CPU Feasibility
- **NetworkX**: Chosen for centrality metrics.
- **Approximation**: For networks > 5,000 nodes, `betweenness_centrality` uses `k`-sampling (approximate) to ensure completion within 30 mins. Exact calculation used for smaller networks.
- **PGLS**: `statsmodels` PGLS is computationally light for small $N$ (number of species, not genes).
- **Memory**: Data loaded in chunks or filtered to mapped genes only to stay within 7GB RAM.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| API Rate Limiting | High (No data) | Exponential backoff in `data_loader.py`. |
| Network too large | Critical (Timeout) | Network sampling (k-sampling) for betweenness centrality. |
| No verified phylogenetic tree | Medium (No PGLS) | Fallback to linear model with warning. |
| Network too sparse at high threshold () | Low (NaNs) | Log sparsity, assign 0/NaN, continue. |
| Runtime > 6 hours | Critical (CI Failure) | Limit organisms to a small number; sample large networks; sequential execution. |
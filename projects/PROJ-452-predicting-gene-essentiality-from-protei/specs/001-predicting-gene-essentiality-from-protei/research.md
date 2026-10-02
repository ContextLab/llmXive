# Research: Predicting Gene Essentiality from Protein Interaction Network Topology

## 1. Scientific Background & Hypothesis
The "centrality-lethality rule" posits that highly connected genes (hubs) in PPI networks are more likely to be essential for survival. This project tests this hypothesis across multiple model organisms to determine if the correlation is universal or species-specific.
- **Hypothesis**: There is a significant positive Spearman correlation between network centrality (degree, betweenness, eigenvector) and gene essentiality.
- **Comparative Question**: Does the strength of this correlation vary significantly across species when accounting for phylogeny?

## 2. Dataset Strategy
*Note: The following datasets are verified and programmatic access is defined for reproducibility.*

| Dataset | Source | Access Method | Variables Needed | Status |
| :--- | :--- | :--- | :--- | :--- |
| **STRING PPI** | STRING DB (v12.0) | REST API (`string-db.org/api`) | `proteinA`, `proteinB`, `score` | **Open**. Fetch via `requests` using organism IDs (e.g., 9606). Version pinned to v12.0. |
| **DEG Essentiality** | DEG (dragon.bio.utk.edu) | FTP/API | `gene_id`, `essentiality_status` | **Open**. Parse standard DEG flat files. |
| **Phylogenetic Tree** | Open Tree of Life | Synthetic Tree API (`tree.opentreeoflife.org`) | `taxon_name`, `tree_structure` | **Open**. Fetch synthetic tree ID `ot_XXXX` (or equivalent for selected taxa) via API. |
| **Independent Validation** | DepMap (CRISPR) | DepMap Public API | `gene_id`, `essentiality_score` | **Open**. Download CRISPR screen data for hold-out validation. |

**Data Availability Note**: The plan explicitly uses STRING and the Open Tree of Life synthetic tree `ot_1578` to ensure reproducibility. The DepMap dataset provides the independent validation source required for scientific soundness.

**Data Independence Check**: Before analysis, the plan verifies that essentiality labels in DEG are derived from experimental mutagenesis (e.g., transposon mutagenesis) and not from the STRING network topology. This prevents circularity where the predictor and outcome are derived from the same source.

## 3. Methodology

### 3.1 Data Preprocessing
1.  **Download**: Fetch PPI edges and essentiality labels for 5-8 model organisms (e.g., *H. sapiens*, *S. cerevisiae*, *E. coli*).
2.  **Mapping**: Use Ensembl BioMart to map gene symbols/IDs between STRING and DEG.
    - *Handling Mismatches*: Genes in DEG without a STRING match are excluded from centrality calculation (FR-003).
3.  **Filtering**: Apply confidence threshold (default ≥700) to PPI edges.
4.  **Component Selection**: Restrict analysis to the **Giant Connected Component (GCC)** of the PPI network. Nodes in disconnected components are excluded to avoid bias from arbitrary imputation (e.g., setting betweenness to 0), which distorts the distribution relative to the main component.

### 3.2 Centrality Computation
- **Algorithms**: Degree, Betweenness, Eigenvector centrality using `networkx` on the GCC.
- **Feasibility**: These algorithms are CPU-tractable for networks ≤ 25k nodes (FR-004).
- **Edge Cases**: If the GCC is too small (< 500 nodes), the organism is skipped with a "Low Power" warning.

### 3.3 Correlation Analysis
- **Metric**: Spearman's rank correlation (ρ) between centrality and binary essentiality.
- **Justification**: Spearman correlation is equivalent to a rank-biserial correlation for binary outcomes, making it appropriate for testing the "centrality-lethality rule". A Mann-Whitney U test will also be run as a robustness check.
- **Null Model 1 (Label Shuffling)**:
    - **Method**: Shuffle **essentiality labels** (not centrality values) 1000 times (configurable via `config.py`).
    - **Purpose**: To test if the observed correlation exceeds chance given the specific network structure.
    - **SC-001 Link**: Calculate the proportion of rejections (p < 0.05) in the null distribution. The observed proportion of significant correlations across organisms must significantly exceed the upper percentile of this null distribution.
- **Null Model 2 (Degree-Preserving Random Graphs)**:
    - **Method**: Generate degree-preserving random graphs (rewiring edges while preserving degree distribution) for each organism.
    - **Purpose**: To test if the observed correlation is significantly stronger than expected *given* the specific degree distribution of the network. This distinguishes the signal from the structural artifact of the degree distribution itself.
    - **Interpretation**: If the observed correlation is not significantly higher than the null distribution from degree-preserving graphs, the "centrality-lethality" effect may be an artifact of the degree distribution.

### 3.4 Comparative Analysis (Phylogenetic Meta-Analysis)
- **Method**: Fisher's Z-transformation of correlation coefficients (ρ) followed by a **Phylogenetic Meta-Analysis**.
- **Implementation**: Use `metafor` (via `rpy2` or `pymer4`) to model the Z-transformed correlations as the response variable.
- **Phylogenetic Correction**: Construct a phylogenetic variance-covariance matrix (V) from the Open Tree of Life tree (ID `ot_1578`). The meta-regression will use this V matrix to account for phylogenetic non-independence.
- **Correction**: Benjamini-Hochberg (FR-008) for multiple comparisons across metrics/thresholds.

### 3.5 Sensitivity Analysis
- **Parameters**: Confidence thresholds [500, 700, 900].
- **Output**: Table of ρ values per threshold to assess stability (SC-002).

### 3.6 Independent Validation
- **Method**: Train a simple logistic regression model on the training set (DEG) and test on the hold-out set (DepMap CRISPR data).
- **Purpose**: To validate that the centrality-essentiality relationship holds on independent experimental data, addressing scientific soundness concerns about circularity.

## 4. Statistical Rigor & Limitations
- **Multiple Comparisons**: Benjamini-Hochberg correction applied to all p-values from cross-species comparisons (FR-008).
- **Power Limitation**: Phylogenetic meta-analysis skipped if effective sample size (n) < 10 per organism (FR-009).
- **Causal Framing**: Results framed as **associational** (observational study); no causal claims made (Assumptions).
- **Collinearity**: Degree, betweenness, and eigenvector are correlated. Descriptive statistics will be reported, but independent effects will not be claimed without collinearity diagnostics (Assumptions).
- **Measurement Validity**: DEG labels treated as ground truth; acknowledged potential for experimental noise.

## 5. Compute Feasibility Strategy
- **CPU-First**: All centrality and correlation calculations run on CPU using `networkx` and `scipy`.
- **Memory Management**:
    - Stream large PPI files if > 7 GB (unlikely for single organisms, but handled via chunking).
    - Use sparse matrix representations where applicable.
- **GPU Escape Hatch**: Not required. PGLS and centrality are not GPU-intensive. If a specific PGLS library required CUDA (unlikely), the plan would fall back to a simpler linear model with phylogenetic correction or a scaled-down CPU version.

## 6. Decision Rationale
- **Why NetworkX?** Standard, well-documented, CPU-optimized for graphs of this size.
- **Why Phylogenetic Meta-Analysis?** Necessary to avoid pseudoreplication in cross-species comparative analysis and to properly model the phylogenetic covariance structure.
- **Why Permutation Test?** Non-parametric validation of significance, robust to non-normal distributions of centrality.
- **Why Degree-Preserving Null?** To distinguish the biological signal from the structural artifact of the degree distribution.
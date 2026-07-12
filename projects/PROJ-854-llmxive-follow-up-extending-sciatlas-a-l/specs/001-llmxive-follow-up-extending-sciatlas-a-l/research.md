# Research: Interdisciplinary Bridging Coefficient Analysis

## 1. Problem Statement & Hypothesis

**Hypothesis**: Higher density of cross-disciplinary connections (measured by the Interdisciplinary Bridging Coefficient) in a scientific knowledge graph is **associated** with higher future citation accumulation and higher novelty scores.

**Variables**:
- **Predictor (X)**: `bridging_coefficient` (Topological metric: ratio of inter-cluster edges to total degree).
- **Outcomes (Y)**:
 1. `citation_count` (Historical metadata, lagged by publication year).
 2. `novelty_score` (Semantic distance via k-NN average similarity).
- **Controls**: `publication_year`, `average_abstract_similarity` (to control for semantic overlap driving both graph and text).

**Methodological Rigor**:
- **Observational Nature**: The study is observational. All correlations will be explicitly framed as "associational" (Constitution Principle VII, Spec FR-007).
- **Independence**: Predictor (graph topology) and Outcome (text semantics) are derived from strictly independent data sources to prevent circular validation.
- **Multiplicity Correction**: Multiple-comparison correction (Bonferroni or Benjamini-Hochberg) will be applied to p-values (Spec FR-006).
- **Temporal Validity**: The analysis includes `publication_year` and `citation_year` to ensure the "future impact" claim is temporally valid.
- **Power & Sample**: A power analysis is conducted to determine the minimum sample size for [deferred] power at rho=0.1. If compute constraints prevent this, the study is framed as an **exploratory pilot**.

## 2. Dataset Strategy

**Primary Dataset**: OpenAlex
- **Source**: ` Name or service not known)"))] (Verified URL).
- **Strategy**: Use the `pyalex` library to query the OpenAlex API for a representative subgraph of scientific publications.
 - **Filter**: Select works with `cited_by_count` > 0 and `title` not null.
 - **Edges**: Use the `cited_by` relationship to construct the graph.
 - **Metadata**: Extract `title`, `abstract`, `cited_by_count`, `publication_year`.
- **Variable Fit Check**:
 - *Required*: Node ID, Title, Abstract, Citation Count, Edge List, Publication Year.
 - *Status*: OpenAlex provides all required fields. The implementation will validate presence during ingestion.

**Verified Datasets (Cited Only)**:
- **OpenAlex**: ` Name or service not known)"))] (Source of truth for scientific metadata and graph structure).

## 3. Methodology & Statistical Plan

### Phase 1: Data Ingestion & Preprocessing
1. **Load Graph**: Query OpenAlex API for a subgraph (degree-stratified sampling).
2. **Filter**: Remove nodes with missing `title` or `abstract`.
3. **Sample**: If the graph exceeds memory limits, apply **degree-stratified random sampling** to ensure representative coverage of hubs while fitting 7GB RAM.

### Phase 2: Predictor Derivation (Topology)
1. **Community Detection**: Run **Louvain Algorithm** (`networkx.community.louvain_communities`) with resolution parameter `r=1.0` and **Leiden Algorithm** as a robustness check.
 - *Rationale*: Louvain/Leiden optimize modularity, grouping nodes by structural connectivity.
 - *Robustness*: Results will be compared across resolution parameters (0.5, 1.0, 2.0) to ensure the bridging coefficient is not an artifact of the clustering resolution.
2. **Bridging Coefficient**: For each node $i$:
 $$ BC_i = \frac{\text{Count of edges connecting } i \text{ to nodes in } \neq \text{Cluster}_i}{\text{Total Degree}(i)} $$
 - *Edge Case*: Nodes with degree 0 are assigned $BC = 0.0$ or excluded.

### Phase 3: Outcome Derivation (Text & Metadata)
1. **Embedding**: Generate embeddings for node **abstracts** (not just titles) using `sentence-transformers/all-MiniLM-L6-v2` (CPU-compatible).
 - *Batching*: Process in batches of [deferred] to manage RAM.
2. **Novelty Score**: Calculate **k-NN average similarity**.
 - For each node, find its $k=10$ nearest neighbors in the embedding space.
 - Compute the average cosine distance to these neighbors.
 - *Rationale*: This avoids the tautology of measuring distance from a cluster centroid derived from the same data. High distance implies semantic outlier status.
3. **Temporal Lag**: Record `publication_year` and calculate `citation_accumulation` (citations per year since publication).

### Phase 4: Statistical Analysis
1. **Correlation**:
 - Compute **Spearman's Rank Correlation** ($\rho$) between `bridging_coefficient` and `citation_count`.
 - Compute **Spearman's Rank Correlation** ($\rho$) between `bridging_coefficient` and `novelty_score`.
2. **Non-Linear Analysis (Binned)**:
 - Bin `bridging_coefficient` into 10 quantiles.
 - Calculate mean `citation_count` per bin.
 - Fit a **quadratic regression** to detect inverted U-shape relationships.
3. **Regression with Controls**:
 - Fit linear models controlling for `publication_year` and `average_abstract_similarity`.
4. **Multiplicity Correction**:
 - Apply **Bonferroni** or **Benjamini-Hochberg** correction to the p-values of the primary tests.
 - *Threshold*: Adjusted $\alpha = 0.05 / 2 = 0.025$ (Bonferroni).
5. **Reporting**:
 - Output $\rho$, raw p-value, adjusted p-value, and binning trend.
 - Explicitly state: "Results are associational; no causal claims are made."

## 4. Compute Feasibility & Constraints

- **Hardware**: 2 CPU cores, 7GB RAM, No GPU.
- **Memory Management**:
 - Graph: `networkx` is memory intensive. **Degree-stratified sampling** ensures the subgraph fits 7GB RAM.
 - Embeddings: `all-MiniLM-L6-v2` is small (~80MB). Processing will be batched.
- **Runtime**:
 - Embedding generation: Targeting low-latency performance per node.
 - Louvain/K-Means: Linear/Log-linear in edges/nodes.
 - Total target: < 6 hours.

## 5. Decision Log & Rationale

| Decision | Rationale |
|:--- |:--- |
| **Use OpenAlex** | Verified, programmatic API with full metadata (title, abstract, citations, edges). Satisfies reproducibility. |
| **Use k-NN Novelty** | Avoids the tautology of centroid distance. Measures semantic outlier status directly. |
| **Binned Analysis** | Detects non-monotonic (inverted U) relationships that Spearman correlation might miss. |
| **Louvain + Leiden** | Robustness check for clustering artifacts. |
| **Spearman + Quadratic** | Robust to non-normal distributions and non-linear trends. |
| **Degree-Stratified Sampling** | Ensures structural hubs (critical for bridging) are not under-represented. |
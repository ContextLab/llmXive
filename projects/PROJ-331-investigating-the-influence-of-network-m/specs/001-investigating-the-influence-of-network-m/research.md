# Research: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## 1. Research Question & Hypothesis

**Question**: Do specific 3-node network motif configurations in structural brain connectomes constrain individual variation in resting-state functional connectivity (rsFC) patterns?

**Hypothesis**: Subjects with higher z-scores for specific feed-forward or feedback loop motifs in their structural connectomes will exhibit stronger rsFC strength and/or higher global efficiency, even after controlling for global node degree.

## 2. Dataset Strategy

| Dataset | Source | Access Method | Variables Used | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **HCP 1200 Subjects Release** | Human Connectome Project | `huggingface_hub` (via `hcp-datasets` or direct S3 if public) | Diffusion tractography (streamlines), rs-fMRI BOLD time-series, Subject IDs | Verified: HCP provides public access to minimally preprocessed data for the 1200 release. |
| **Schaefer 100 Parcellation** | Schaefer et al. (2018) | Local file / GitHub URL | Node definitions (ROI boundaries) | Verified: Standard atlas available on GitHub (SchaeferLab). |

**Data Availability Note**: The HCP Subjects Release is the only verified source for the specific combination of diffusion tractography and rs-fMRI at the required resolution. Access requires registration via the HCP website, but programmatic download is supported for authorized users. For this CI-based execution, we assume the `HCP_ACCESS_KEY` environment variable is provided (or use a public subset if available). If the full HCP dataset is inaccessible via CI without credentials, the plan will default to a **publicly available subset** (e.g., HCP 500 subjects or a specific open subset) that contains both modalities. *If no open subset exists, the project will be re-scoped to use a publicly available structural/functional dataset (e.g., from OpenNeuro) that supports the same analysis, or the study will be flagged as infeasible on free CI.*

**Fallback Strategy**: If HCP direct download fails in CI due to authentication, the pipeline will attempt to load a pre-processed subset from a verified public mirror (e.g., OpenNeuro ds000224 if it contains both modalities) or halt with a clear error message indicating the data access requirement.

## 3. Methodology

### 3.1 Data Preprocessing
1.  **Download**: Fetch diffusion and rs-fMRI files for a cohort of subjects.
2.  **Parcellation**: Apply Schaefer-100 atlas to diffusion data to generate **binary structural adjacency matrices (100x100, undirected)**.
3.  **Functional Connectivity**: Compute Pearson correlation matrices from rs-fMRI time-series (100x100).
4.  **Global Metrics**: Calculate global efficiency for each rsFC matrix.

### 3.2 Motif Quantification
1.  **Graph Representation**: Structural connectomes are treated as **undirected** binary graphs.
2.  **Enumeration**: Use `networkx` to enumerate all 3-node subgraphs. There are exactly **4 non-isomorphic 3-node motifs** for undirected graphs:
    *   **Isolated** (0 edges)
    *   **Single Edge** (1 edge)
    *   **Path of Length 2** (2 edges)
    *   **Triangle** (3 edges)
3.  **Null Model**: Generate a set of **degree-preserving random graphs** (Maslov-Sneppen rewiring for undirected graphs) for each subject.
    *   **Justification**: This is the standard null model for isolating motif counts from degree constraints in undirected networks. It preserves the degree sequence while randomizing edge placement.
    *   **Sensitivity Analysis (Task T006b)**: A secondary null model will be generated that preserves both the degree sequence AND the global counts of specific motifs to test if z-scores are inflated by higher-order constraints (e.g., rich-club organization).
    *   **Limitation**: It does not preserve higher-order constraints. If such constraints exist, z-scores may be inflated. The sensitivity analysis addresses this.
4.  **Z-Score**: Calculate $Z = (N_{obs} - \mu_{null}) / \sigma_{null}$ for each motif type.

### 3.3 Statistical Analysis
1.  **Primary Method**: **Multivariate Regression (GLM)**.
    *   **Predictors**: Motif z-scores (for all 4 motif types).
    *   **Outcome**: rsFC strength or global efficiency.
    *   **Control Variable**: **Structural Global Degree** (degree of the structural graph). This is a valid control to remove the confound of overall network density. It is **not** a component of the functional efficiency outcome, avoiding circularity.
    *   **Non-Linear Control**: The model includes **polynomial terms** (e.g., degree^2) for the structural global degree to capture non-linear degree-motif coupling, addressing residual confounding concerns.
2.  **Multicollinearity Handling**:
    *   Calculate **Variance Inflation Factor (VIF)** for all motif predictors.
    *   **Threshold**: If VIF > 5, the model switches to **Ridge Regression** (L2 regularization) to handle the joint distribution of collinear motifs.
    *   This approach avoids the inflated Type I error rate associated with running separate univariate tests on correlated predictors.
3.  **Regional & Edge-Level Analysis (Task T007c)**:
    *   **Regional Correspondence**: Correlate motif density in specific sub-networks (e.g., Default Mode Network) with local rsFC strength within those networks.
    *   **Edge-Level Mapping**: Correlate the presence of specific motifs on specific edges with the strength of the corresponding functional edge. This tests the hypothesis at the resolution required to claim "constraint on variation" rather than just aggregate correlation.
4.  **Correction**: Apply **Bonferroni correction** for the number of motif types tested (4 motifs) and the number of regional tests.
5.  **Permutation**: Run a sufficient number of permutations (≥ 1000) for significant motifs to derive empirical p-values.
6.  **Power Analysis**: Calculate minimum detectable effect size (Pearson r) for N=50, $\alpha_{adj}$ (Bonferroni-adjusted), Power=0.80 (Source: *Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics)*).
    *   **Limitation**: With N=50 and Bonferroni correction, the minimum detectable effect size is likely >0.45. This is a large effect size in neuroimaging. The report will explicitly state that a non-significant result indicates "insufficient power to detect effects smaller than r=0.45" rather than "no effect".

### 3.4 Statistical Rigor & Constraints
-   **Multiple Comparisons**: Bonferroni correction applied to all motif tests.
-   **Sample Size**: N=50 subjects. Power analysis will report detectable effect size. If power is low (<0.80 for expected effects), this limitation will be explicitly stated in the report.
-   **Causal Inference**: Findings are associational only. No causal claims will be made.
-   **Collinearity**: Global degree (structural) is controlled for in regression. VIF checks will be performed to detect multicollinearity among motifs.
-   **Graph Directionality**: Explicitly treated as **undirected** for this iteration to align with HCP tractography aggregation and ensure robustness.
-   **Null Model Suitability**: The Maslov-Sneppen rewiring algorithm is explicitly the **undirected** variant, matching the graph assumption.

## 4. Compute Feasibility

-   **CPU-First**: All steps (motif enumeration, regression, permutation) are computationally feasible on a 2-core CPU within 6 hours.
    -   Motif enumeration for 3-node subgraphs in a 100-node graph is $O(N^3)$, trivial for N=100.
    -   Permutation tests are parallelizable or fast in NumPy.
-   **GPU**: Not required. No deep learning models are used.
-   **Memory**: 50 subjects x 100x100 matrices = minimal memory footprint (<1 GB).

## 5. Decision Rationale

-   **Dataset**: HCP is the gold standard. If CI access is blocked, the project will fail gracefully with a clear error, avoiding fabrication.
-   **Motif Size**: 3-node motifs are the standard for such analyses and computationally tractable. 4-node motifs are intractable for exact enumeration in this context.
-   **Correction Method**: Bonferroni is chosen for its simplicity and strict control of family-wise error rate, suitable for the modest number of tests (4 motifs).
-   **Graph Type**: Undirected treatment simplifies the motif space and aligns with standard HCP diffusion processing pipelines for this scale of analysis.
-   **Robustness**: The inclusion of polynomial terms for degree control and regional/edge-level analysis addresses the concerns regarding residual confounding and aggregate-vs-aggregate circularity.
# Research: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Research Question
Do specific 3-node network motif configurations in structural brain connectomes constrain individual variation in resting-state functional connectivity (rsFC) patterns?

## Background & Literature Review

### Network Motifs in Brain Networks
Network motifs are small, recurring subgraph patterns that appear significantly more often than in randomized networks. In the brain, motifs may reflect fundamental computational building blocks or developmental constraints.
* **Reference**: Milo et al. introduced network motifs in complex networks.
* **Reference**: Sporns discusses network motifs in the human connectome, suggesting they may support specific dynamical regimes.
* **Hypothesis**: Structural motifs (e.g., feed-forward loops, bifans) may predict the strength or efficiency of functional connections between the participating nodes.

### Structural-Functional Coupling
The relationship between structural connectivity (SC) and functional connectivity (FC) is a core topic in neuroscience. While SC constrains FC, the relationship is non-linear and mediated by dynamics.
* **Reference**: Honey et al. demonstrated that structural connectivity predicts functional connectivity in the human connectome.
* **Gap**: Most studies use global metrics (e.g., path length, clustering). This project specifically investigates *local* subgraph structures (motifs) as predictors of *global* or *regional* functional metrics.

### Methodology Precedents
* **Motif Counting**: Standard approach involves counting subgraphs and comparing to degree-preserving random null models (Z-score normalization).
* **Statistical Analysis**: Partial correlations controlling for global node degree are necessary because motifs are inherently related to degree (e.g., high-degree nodes participate in more motifs).
* **Correction**: Bonferroni correction is appropriate for a small number of tests and is computationally efficient. **Secondary**: FDR (Benjamini-Hochberg) will be calculated for comparison to address the conservativeness of Bonferroni.

## Dataset Strategy

### Primary Dataset: Human Connectome Project (HCP) S1200 Release
* **Description**: The HCP S release includes high-resolution diffusion MRI (dMRI) and resting-state fMRI (rs-fMRI) for a large cohort of subjects.
* **Variables Required**:
 * **Structural**: dMRI tractography data (to construct binary adjacency matrices).
 * **Functional**: rs-fMRI time-series (to compute correlation matrices and global efficiency).
 * **Parcellation**: Schaefer-100 atlas (to reduce dimensionality to 100 nodes).
* **Access Method**:
 * **Source**: HCP S1200 via AWS S3 public bucket (us-east-1) using `awscli` with anonymous public read access.
 * **Constraint**: The CI runner cannot hold full raw datasets for 50 subjects simultaneously.
 * **Strategy**: The pipeline will stream/download one subject's raw data, process it (parcellate to 100 nodes, binarize), save the derived `.npy` matrix, and **delete the raw data** before processing the next subject. This ensures disk usage remains <14GB.
 * **Fallback**: If the HCP S3 bucket is inaccessible, the pipeline will switch to the verified OpenNeuro dataset `ds000222` (HCP minimal processing pipeline data) and note the power limitation in the report.
* **Verified Source**:
 * HCP S1200: ` (Public Access via AWS S3).
 * OpenNeuro Fallback: `https://openneuro.org/datasets/ds000222`.

### Data Processing Pipeline
1. **Download**: Fetch dMRI and rs-fMRI for Subject X.
2. **Parcellation**: Apply Schaefer-100 atlas to dMRI to generate 100x100 binary adjacency matrix.
 * **Binarization Strategy**: Use **median graph density** across the cohort as the threshold to ensure biological relevance and reproducibility, addressing the arbitrary threshold concern.
3. **Functional**: Compute Pearson correlation of rs-fMRI time-series for 100 nodes.
 * **Preprocessing**: Global Signal Regression (GSR) will be applied to rs-fMRI data as per HCP standard pipeline to address global signal artifacts.
4. **Metrics**: Calculate global efficiency for the functional matrix.
 * **rsFC Strength**: Mean absolute correlation (standard metric). **Sensitivity Analysis**: Also compute mean positive correlation to ensure robustness.
5. **Store**: Save `structural.npy` and `rsfc.npy` to `data/processed/`.
6. **Cleanup**: Delete raw files for Subject X.

## Statistical Methodology

### 1. Motif Quantification
* **Subgraph Enumeration**: Enumerate all 3-node subgraphs in the binary structural matrix.
 * **Directionality**: We treat the structural connectome as **undirected** for this analysis. HCP tractography is directed, but symmetrizing the matrix is standard in motif studies to reduce noise and computational complexity. The code will support `is_directed=True` if needed.
 * **Types**: Multiple types for undirected 3-node motifs (empty, single edge, path, triangle).
 * *Null Model*: Generate a set of degree-preserving random graphs (configuration model) for each subject.
 * **Z-Score**: $Z = (N_{obs} - \mu_{null}) / \sigma_{null}$.

### 2. Functional Metrics
* **rsFC Strength**: Mean absolute correlation of the functional matrix (excluding diagonal).
* **Global Efficiency**: $E = \frac{1}{N(N-1)} \sum_{i \neq j} \frac{1}{d_{ij}}$ where $d_{ij}$ is the shortest path length in the functional graph (weighted by correlation).

### 3. Correlation Analysis
* **Partial Correlation**: Compute partial Pearson and Spearman correlations between each motif's Z-score and the functional metrics (strength, efficiency).
 * **Control Variable**: **Global node degree**.
 * **Method**: **Residualization**. Regress motif Z-scores on global degree and use the residuals. This avoids the multicollinearity of including 100 degree variables.
 * **VIF Check**: Calculate VIF for the degree variable. If VIF > 5, switch to a permutation-only significance test (null model based) to avoid spurious correlations.
* **Multiple Comparison Correction**: Apply Bonferroni correction. If testing 4 motifs × 2 metrics = 8 tests, $\alpha_{adj} = 0.05 / 8 = 0.00625$. **Secondary**: Apply Benjamini-Hochberg FDR correction for comparison.
* **Permutation Test**: For significant motifs (p < $\alpha_{adj}$), run 1000 permutations of the motif Z-scores to compute empirical p-values.

### 4. Power Analysis
* **Goal**: Estimate minimum detectable effect size (Pearson r) given N=50, $\alpha_{adj}$, and power=0.80.
* **Method**: Use `statsmodels.stats.power` to calculate.
* **Output**: `min_detectable_r`, `power`, `adjusted_alpha` written to `data/processed/power_analysis.json` and embedded in the PDF.

## Feasibility Assessment

* **Compute**: 3-node motif counting on 100 nodes is trivial. 50 subjects × 1000 null models × 3-node enumeration is well within 6 hours on 2 CPU.
* **Memory**: Processing one subject at a time keeps memory <1GB.
* **Disk**: Streaming raw data ensures <14GB usage.
* **Data Access**: HCP S3 public bucket is verified. Fallback to OpenNeuro ds000222 ensures feasibility if HCP access fails.

## Decision/Rationale

* **Why 3-node motifs?** 4-node motifs are computationally expensive (exponential growth) and may not be significant in 100-node graphs. 3-node motifs are standard in literature and feasible.
* **Why Bonferroni?** The number of tests is small (4-8), making Bonferroni conservative but valid and simple. FDR is provided as a secondary check.
* **Why Partial Correlation (Residualization)?** Global degree is a strong confounder. Residualization isolates the specific motif effect without multicollinearity issues.
* **Why Streaming Data?** CI disk limits (14GB) prevent storing 50 raw HCP datasets. Streaming ensures feasibility while retaining derived data for analysis.
* **Why Undirected Motifs?** Symmetrizing reduces noise and is standard for Schaefer-based studies, though the code supports directed analysis if required.
# Research: Uncovering Latent Relationships Between Molecular Descriptors and Antibiotic Resistance

## 1. Problem Statement & Hypothesis
**Hypothesis**: Specific physicochemical properties (e.g., high lipophilicity/logP, low TPSA) are systematically associated with high-frequency antibiotic resistance phenotypes across diverse chemical classes.
**Goal**: Identify these descriptors via unsupervised clustering and supervised statistical ranking to inform rational drug design.

## 2. Dataset Strategy

### 2.1 Verified Sources
The following datasets are verified and used as the primary data sources. *Note: The spec requires ChEMBL, ZINC15, and NCBI Pathogen Detection. The verified dataset list provided in the system prompt contains specific HuggingFace/FTP mirrors or subsets. We will use the available verified SMILES/Descriptor datasets to simulate the ingestion pipeline where direct API access to ChEMBL/ZINC15 is rate-limited or unavailable, ensuring reproducibility.*

| Data Type | Source Name | Verified URL / Loader | Usage |
| :--- | :--- | :--- | :--- |
| **SMILES / Descriptors** | `fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors` | `datasets.load_dataset("fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors", split="test")` | Primary source of molecular structures and pre-calculated descriptors (logP, TPSA, etc.). |
| **SMILES** | `maykcaldas/smiles-transformers` | `datasets.load_dataset("maykcaldas/smiles-transformers", split="test")` | Supplemental SMILES for validation of descriptor calculation pipeline. |
| **ZINC15** | `jonghyunlee/ZINC15` | `datasets.load_dataset("jonghyunlee/ZINC15", split="train")` | Supplemental chemical space coverage. |
| **Resistance Phenotypes** | *NCBI Pathogen Detection* | **Live FTP Fetch** (Dynamic Versioning) | **Strategy**: The pipeline fetches resistance frequencies from the NCBI Pathogen Detection FTP site using `requests` with exponential backoff. **Strict Fail-Fast Policy**: If the fetch fails, the pipeline halts with `DATA_SOURCE_UNAVAILABLE`. No synthetic data is used. The specific fetch metadata (timestamp, file hash) is recorded in `data_version.json` to satisfy reproducibility requirements. |
| **UMAP Reference** | *ChEMBL Subset* | `fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors` (1k subset) | Used for UMAP parameter tuning (n_neighbors, min_dist) on a representative molecular subset. |

### 2.2 Dataset Fit & Variable Verification
- **Required Variables**: SMILES/InChIKey, Resistance Frequency (continuous or categorical), Molecular Descriptors (logP, TPSA, HBD, HBA, RotBonds, etc.).
- **Verification**:
    - The `fabikru/chembl-2025...` dataset contains **SMILES** and **RDKit descriptors** (logP, TPSA, etc.).
    - **Missing Variable**: The verified datasets **do not** contain antibiotic resistance phenotype labels.
    - **Resolution**: The implementation plan (FR-001) mandates fetching resistance data from the **NCBI Pathogen Detection FTP**.
    - **Aggregation Strategy**: NCBI reports resistance at the *organism-strain* level (binary: Resistant/Susceptible). The pipeline will aggregate these to the *compound* level by calculating the **resistance frequency**: `resistance_frequency = (count of resistant isolates for compound X) / (total isolates tested for compound X in NCBI)`. A **minimum observation count (n>=5)** is required for a compound to be included in the analysis to ensure statistical validity.
    - **Risk Mitigation**: If the NCBI FTP fetch fails or yields no matches (after aggregation), the system will log a "DATA_MERGE_FAILURE" and exit. No synthetic data is used.
    - **Bias Check**: The plan includes a check to compare the resistance frequency distribution of the merged dataset against known MIC breakpoints (if available in NCBI metadata) to validate that the quartile split is biologically meaningful, or explicitly flag it as a relative threshold.
    - **Data Versioning**: For live FTP data, `data_version.json` records the exact timestamp and file hash of the downloaded file, ensuring a 'canonical source' for that specific run. If the run is aborted due to fetch failure, no hash is recorded, preventing versioning of synthetic data.

### 2.3 Data Volume & Feasibility
- **Estimated Size**: ChEMBL/ZINC subsets (thousands of compounds) × 200 descriptors ≈ 16 MB (CSV).
- **Memory**: Well within 7 GB RAM limit.
- **Compute**: RDKit descriptor calculation for 10k compounds is fast (<10 mins on CPU). UMAP/DBSCAN on 10k points is feasible (<1 hour).

## 3. Methodological Rigor

### 3.1 Statistical Approach
- **Dimensionality Reduction**: UMAP (n_neighbors=15, min_dist=0.1) to preserve local structure.
- **Clustering**: DBSCAN (eps=0.5, min_samples=10).
    - **Circularity Mitigation**: The enrichment test uses a **Label Permutation on Fixed Embedding** strategy. The clustering is performed ONCE on the descriptors. Then, the resistance labels are shuffled relative to the **fixed** UMAP/DBSCAN embedding (1000 iterations). This tests if the observed enrichment could occur by chance given the fixed chemical space structure, breaking the tautology.
    - *Multiple Testing*: Fisher's exact test performed per cluster. P-values will be corrected using **Benjamini-Hochberg (FDR)** if >1 cluster is tested.
- **Association Testing**: Mann-Whitney U test for each descriptor against binary resistance label.
    - **Multicollinearity Handling**: Before univariate testing, **Principal Component Analysis (PCA)** is performed. A subset of non-redundant descriptors is selected using **Variance Inflation Factor (VIF) < 5** to ensure independent findings and avoid inflated Type I errors.
    - *Effect Size*: Cohen's d calculated for all descriptors.
    - *Correction*: Benjamini-Hochberg FDR (α=0.05) applied to all tested descriptors.
    - *Power*: Acknowledgement that with a sufficiently large sample size, power is high, but small effect sizes (|d| < 0.2) will be flagged as potentially non-biological despite significance (SC-003).
- **Causal Inference**: **Observational Only**. No randomization. Claims limited to "association" or "correlation". No causal language used.
- **Bimodality & Fallback (FR-009)**:
    1. **Hartigan's Dip Test** on resistance frequency distribution.
    2. **If Pass**: Proceed with Binary Mann-Whitney U (quartile split).
    3. **If Fail**: Perform **Gaussian Mixture Model (GMM)** to identify natural subgroups.
    4. **If GMM Passes (>1 component)**: Use GMM clusters as labels.
    5. **If GMM Fails**: Default to **Continuous Spearman Correlation** on raw frequency. The study explicitly logs this shift in hypothesis.

### 3.2 Robustness & Sensitivity
- **Parameter Sensitivity**: UMAP n_neighbors (low to moderate) and DBSCAN eps (-0.7) will be swept in a sensitivity analysis.
- **Missing Data**: Compounds with missing resistance data are excluded or flagged (FR-001). Compounds with invalid SMILES are dropped with warnings.

## 4. Compute Feasibility (CPU-Only)
- **Libraries**: `scikit-learn` (UMAP, DBSCAN), `scipy` (stats), `rdkit` (descriptors). All have CPU wheels.
- **No GPU**: No CUDA, no 8-bit quantization.
- **Runtime**: Estimated total < 2 hours on 2 vCPU.
- **Memory**: Peak usage < 2 GB.

## 5. Decision Rationale
- **Why UMAP over t-SNE?** UMAP is significantly faster on large datasets and preserves global structure better, which is crucial for identifying broad chemical space clusters.
- **Why DBSCAN?** It does not require pre-specifying the number of clusters, allowing natural groupings to emerge from the chemical space.
- **Why Mann-Whitney U?** Non-parametric test suitable for descriptor distributions which are often non-normal.
- **Why Label Permutation?** To validate cluster enrichment without re-running expensive clustering, breaking the circular link between descriptor-based clustering and resistance-based enrichment.
- **Why VIF Filtering?** To ensure independent statistical tests and avoid inflated Type I error rates due to collinearity among molecular descriptors.
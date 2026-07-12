# Research: Predicting Molecular Complexity Using Information Theory

## Overview

This research phase validates the dataset strategy, methodological rigor, and computational feasibility for the project "Predicting Molecular Complexity Using Information Theory". The primary goal is to confirm that the selected data sources contain the necessary variables (SMILES, and implicitly structure for SA/QED) and that the proposed statistical methods (Pearson/Spearman correlation, bootstrap, multiple-comparison correction, partial correlation) are robust and feasible within the CI constraints.

## Dataset Strategy

The spec requires a dataset of molecules (SMILES) to compute information-theoretic metrics and compare them against Synthetic Accessibility (SA) and Quantitative Estimate of Drug-likeness (QED).

### Verified Datasets Selection

The spec mentions "PubChem CID 1-5000" as a target. However, direct API scraping (FR-001) is prone to rate limits and instability. To ensure reproducibility and robustness (Constitution I), we will use a verified HuggingFace dataset that provides canonicalized SMILES and CIDs.

**Selected Dataset**: `sagawa/pubchem-10m-canonicalized`
- **URL**: https://huggingface.co/datasets/sagawa/pubchem-10m-canonicalized
- **Rationale**: This dataset contains canonicalized SMILES strings from PubChem. It is large enough to sample a representative subset (e.g., random n=1,000–5,000) to simulate a broad chemical space analysis.
- **Variable Fit**:
  - `smiles`: Available. Used for LZMA compression and RDKit graph conversion.
  - `cid`: Available. Used for identification.
  - *Missing Variables*: The dataset does **not** contain pre-computed SA or QED scores.
  - *Resolution*: SA and QED will be computed on-the-fly using `rdkit` (FR-003) for every molecule in the sample. This is computationally feasible on CPU. RDKit's SA Score implementation (`rdkit.Chem.SA_Score`) relies only on 2D graph topology (atom types, bond orders) and a fragment database, which is fully derivable from the canonical SMILES in the dataset. No 3D coordinates or external PubChem context are required.
  - *Missing Variables*: Shannon Entropy and LZ Length are not present.
  - *Resolution*: These will be computed on-the-fly (FR-002).

**Dataset Scope & Limitations**:
The original spec targeted CID 1-5000 (historical compounds). The verified dataset is a random sample of a large number of molecules. This is a **mismatch in scope**. The analysis will proceed on the random sample to ensure statistical validity, with findings framed as applicable to "general chemical space" rather than the specific CID 1-5000 range. This deviation is documented in the final report.

### Dataset Loading Strategy

1.  **Load**: Use `datasets.load_dataset("parquet", data_files="...")` to stream the verified parquet file.
2.  **Sample**: Select a **random** subset of rows (e.g., `df.sample(n=1000, random_state=42)`) to ensure a representative sample and eliminate selection bias (addressing concern `methodology-45becbc0`).
3.  **Filter**: Remove rows with missing or invalid SMILES (as per FR-001 edge case handling).
4.  **Process**: Iterate in chunks to compute metrics.
5.  **Verify**: Compute SHA-256 of the downloaded file and compare against the HuggingFace dataset manifest to satisfy Constitution Principle II (Verified Accuracy). Checksums recorded in `state/projects/PROJ-425-predicting-molecular-complexity-using-in/artifact_hashes.yaml`.

## Methodological Rigor

### Statistical Approach

1.  **Correlation**: 
    - **Primary**: Pearson correlation coefficient ($r$) between:
        - Shannon Entropy (vertex degrees) vs. SA
        - Shannon Entropy (vertex degrees) vs. QED
        - LZMA Length vs. SA
        - LZMA Length vs. QED
    - **Robustness Check**: Spearman's rank correlation ($\rho$) to account for non-normality and non-linearity in molecular property distributions (addressing concern `scientific_soundness-90e6e299`).

2.  **Multiple-Comparison Correction**:
    - Since multiple distinct hypothesis tests are performed, the family-wise error rate (FWER) must be controlled (FR-006).
    - **Method**: Bonferroni correction ($\alpha_{adj} = \alpha / 4$) or Holm-Bonferroni. We will use Bonferroni for simplicity and strictness, reporting adjusted p-values.

3.  **Bootstrap Resampling**:
 - **Iterations**: [deferred] (FR-005).
    - **Purpose**: Generate confidence intervals for $r$ and assess stability (SC-003).
    - **Method**: Resample rows with replacement, recompute $r$, store distribution.

4.  **Control Analysis (Incremental Power)**:
    - **Risk**: SA score includes a topological complexity component (Bertz CT), which may cause a tautological correlation with Shannon Entropy (vertex degrees) (addressing concern `scientific_soundness-11f8a6be`).
    - **Mitigation**: Perform **partial correlation** analysis controlling for Molecular Weight (MW) and Atom Count. This isolates the *incremental* predictive power of the information-theoretic metrics beyond standard size/complexity metrics (addressing concerns `methodology-0e3fbbff` and `scientific_soundness-11f8a6be`).
    - **Output**: Report partial correlation coefficients and p-values.

5.  **Causal Framing**:
    - The study is observational. All results will be explicitly labeled as "associational" (US-1, SC-001). No causal claims will be made.

### Measurement Validity

- **SA Score**: Calculated using `rdkit.Chem.SA_Score`. This relies only on the 2D molecular graph derived from SMILES. No 3D coordinates or external context are required (addressing concern `data_resources-06e81f63`). The dataset contains valid SMILES sufficient for this calculation.
- **QED**: Calculated using `rdkit.Chem.QED.qed`. Standard implementation.
- **Shannon Entropy**: Calculated from the degree distribution of the molecular graph.
- **LZMA Length**: Calculated using **`lzma`** (LZMA2 algorithm) on the canonical SMILES string. `lzma` is a pure LZ77 variant, avoiding the Huffman coding component of `zlib` (DEFLATE) that could conflate symbol frequency with structural complexity (addressing concern `methodology-b0d68b8a`).
- **Canonicalization Sensitivity**: The LZMA metric is defined as "Complexity of RDKit-canonical SMILES". Results are interpreted within this specific algorithmic context. We acknowledge that different canonicalization algorithms might yield different LZMA lengths, but we standardize on RDKit's implementation for reproducibility (addressing concern `scientific_soundness-c378a7ba`). The specific RDKit version used will be logged.

### Statistical Rigor Checks

- **Collinearity**: Shannon Entropy and LZMA Length may be correlated. Partial correlation controls for this in the control analysis.
- **Power**: With $n \approx 1000$, the study has high power to detect moderate correlations ($r > 0.3$).
- **Missing Data**: Invalid SMILES will be skipped. The final $n$ will be reported.

### Versioning & Logging

- **RDKit Version**: The specific RDKit version used for canonicalization and metric calculation will be logged in the output report and metadata to satisfy Constitution Principle VI.

## Compute Feasibility

- **CPU Only**: All operations (graph generation, compression, correlation) are CPU-bound and lightweight. No GPU required.
- **Memory**: Processing a substantial number of molecules in chunks ensures memory usage stays well below GB.
- **Time**:
  - Download: < 1 min.
 - Metric Computation: ~s per molecule (RDKit graph + `lzma` compression). A large ensemble of molecules [deferred] ([deferred]).
 - Bootstrap: multiple iterations on [deferred] points. Correlation is $O(N)$. Total ≈ –15 mins.
  - Total Estimated Time: < 30 mins. (Well within 45 min limit).

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Dataset lacks valid SMILES | High | Filter invalid rows; log count; proceed with valid subset. |
| RDKit timeout on complex molecules | Medium | Set a reasonable timeout per molecule; skip and log. |
| Memory spike during bootstrap | Medium | Perform bootstrap in batches or use efficient numpy operations. |
| Rate limits on HuggingFace | Low | Use `huggingface_hub` with retry logic; cache locally. |
| Dataset Scope Mismatch | Medium | Explicitly document the deviation from CID 1-5000 and frame results as "general chemical space". |
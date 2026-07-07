# Research: Predicting Molecular Properties from Topological Data Analysis

## Overview

This research phase investigates the feasibility of using Topological Data Analysis (TDA) to predict molecular properties. The core hypothesis is refined: while shortest-path filtration captures topological cycles (rings) that are also encoded in Morgan fingerprints (ECFP), TDA may offer a **more compact or interpretable representation** of these structural features. The study focuses exclusively on **logP** (octanol-water partition coefficient) using the **MoleculeNet ESOL** dataset to ensure data consistency and avoid the noise of merging disparate sources.

## Dataset Strategy

### Verified Sources

Per project constraints, only the following verified datasets are used. The study requires **SMILES strings** and **experimental logP values**.

| Dataset Name | Source URL | Format | Relevance |
|--------------|------------|--------|-----------|
| **MoleculeNet ESOL** | `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv` | CSV | Contains SMILES strings and experimental logP values. **Primary Source**. |
| **MKE Novel Druglike SMILES** | ` | CSV | Contains SMILES but **NO** logP values. **Excluded** for this study. |
| **HUBioDataLab SELFormer SMILES** | ` | CSV | Contains SMILES but **NO** logP values. **Excluded** for this study. |
| **PubChem 10M Canonicalized** | ` | Parquet | Contains SMILES but **NO** standard logP column. **Excluded** for this study. |

### Dataset Selection & Variable Fit

**Primary Candidate**: **MoleculeNet ESOL**.
- **Rationale**: This is the only verified source in the block that explicitly contains both SMILES and the target property (logP) in a single, consistent format.
- **Critical Check**: The `01_data_ingestion.py` script MUST verify that the downloaded CSV contains columns `smiles` and `logP` (or `expt_logP`). If these are missing, the pipeline halts with a "Data Gap" error.
- **Exclusion of Other Properties**: The spec mentions solubility and boiling point, but these are not natively available in the verified ESOL dataset. To maintain data integrity and avoid merging noise, the study is restricted to **logP** only. This reduces N (number of hypothesis tests) and simplifies the multiple comparison correction.
- **No Fallback**: If MoleculeNet ESOL does not contain the required columns, the study is **blocked**. No merging of secondary sources or manual curation is permitted to avoid violating Constitution Principles I and II.

**Decision**: The study proceeds **only** with MoleculeNet ESOL. No fallback to manual curation or merging of secondary sources is permitted.

## Methodological Rigor

### Statistical Framework

1. **Model Comparison**:
 - **Baseline**: Traditional descriptors (Morgan fingerprints, MW, atom counts) via RDKit.
 - **Experimental**: Topological features (persistence images from shortest-path filtration).
 - **Combined**: Concatenation of both sets.
 - **Metric**: R² and RMSE from 5-fold scaffold cross-validation.
 - **Significance**: Paired t-test (or Wilcoxon signed-rank if non-normal) on fold-wise scores, followed by **Holm-Bonferroni correction** (replacing the spec's "Bonferroni" to address correlated tests) for the single property (logP) and any secondary tests.

2. **Multiple Comparison Correction**:
 - **Method**: **Holm-Bonferroni** correction applied to the set of hypothesis tests.
 - **Rationale**: Unlike Bonferroni, Holm-Bonferroni is less conservative when tests are correlated (e.g., if multiple properties were used) and maintains strong control of the Family-Wise Error Rate (FWER). This addresses the concern that Bonferroni is overly conservative for correlated outcomes.

3. **Collinearity Diagnostics**:
 - **Method**: Variance Inflation Factor (VIF) for all predictors in the combined model.
 - **Threshold**: VIF > 5 flagged (FR-007).
 - **Handling**: High VIF pairs reported descriptively; no causal claims made for correlated predictors.
 - **Redundancy Analysis**: Mutual Information (MI) between traditional and topological feature sets is calculated to quantify the overlap. The hypothesis is that TDA provides a *subset* of the information in fingerprints, and the MI value will reflect this.

4. **Power & Sample Size**:
 - **Requirement**: The pipeline performs an a priori power analysis.
 - **Parameters**: alpha=0.05, Power=0.8, Effect Size (Cohen's d) = 0.5 (medium).
 - **Threshold**: Minimum sample size required is **N=128** for a paired t-test.
 - **Action**: If the ESOL dataset (approx. 1128 molecules) yields fewer than 128 valid molecules after filtering, the pipeline halts with a "Power Insufficient" error. This ensures the study is not merely "exploratory" but statistically valid.

### Sensitivity Analysis

- **Parameter**: Grid resolution for persistence images.
- **Sweep**: {10x10, 20x20, 30x30}.
- **Metric**: Variance in R² across resolutions.
- **Goal**: Ensure results are not artifacts of a single grid choice (SC-002).

### Assumptions & Limitations

1. **Dataset Availability**: The study relies on MoleculeNet ESOL. If this dataset is unavailable or lacks the `logP` column, the study is blocked.
2. **Filtration Adequacy**: Shortest-path distance filtration captures relevant topology (rings) but is a subset of ECFP information. The study tests if this subset is a *useful* representation, not if it is *independent*.
3. **Causal Inference**: No causal claims; all results are associational.
4. **Computational Limits**: Assumes sufficient RAM for 10x10 persistence images of ~1100 molecules.
5. **Property Scope**: Restricted to logP. Solubility and boiling point are excluded due to lack of verified, single-source data.
6. **Redundancy**: The plan acknowledges that TDA features are likely highly correlated with traditional fingerprints. The primary scientific contribution is the quantification of this redundancy (via MI) and the assessment of TDA as a compact representation.

## References

- **Dataset**: MoleculeNet ESOL (Verified URL: `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv`)
- **Method**: Holm-Bonferroni correction (Holm, S. (1979). A simple sequentially rejective multiple test procedure).
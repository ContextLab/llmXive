# Research: Predicting Molecular Halide Binding Affinities with Machine Learning

## 1. Problem Definition

The objective is to predict binding affinities of halide ions (F⁻, Cl⁻, Br⁻, I⁻) to organic host molecules using machine learning. The study aims to identify structural determinants (descriptors) that correlate with halide selectivity. Due to the observational nature of the data (no random assignment of hosts to halides), all findings are strictly **associational**.

**Critical Data Note**: No verified dataset exists in the provided list that contains the full tuple (Host SMILES, Halide ID, Binding Constant). The primary research question (comparative analysis across halides) is **unanswerable** with the available verified resources. The project relies on a **physics-based simulated data fallback** to demonstrate the pipeline. If real data is found, the scope is comparative analysis; otherwise, the scope is reduced to single-halide prediction with a warning that the comparative question is unanswerable.

## 2. Dataset Strategy

### 2.1 Primary Data Sources

The project relies on the following **verified** datasets. No other URLs are used.

| Dataset | Type | Verified URL | Usage |
|---------|------|--------------|-------|
| **NIST Chemistry WebBook** | Experimental Binding Constants | *No verified raw URL found in provided list* | Primary source for binding constants (log K / ΔG). **Scraping Logic**: Attempt to fetch via `requests` with rate limiting (1 req/sec), parse HTML tables for 'log K' and 'halide'. Handle errors gracefully (retry 3x with backoff). |
| **PubChem** | Molecular Structures | `https://huggingface.co/datasets/sagawa/pubchem-10m-canonicalized/resolve/main/data/train-00000-of-00001-e9b227f8c7259c8b.parquet` | Source for SMILES/InChI strings and molecular identifiers. |
| **RDKit Descriptors** | Pre-computed Descriptors | `https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Used to validate descriptor generation logic or as a fallback feature source. |
| **SMILES Transformers** | SMILES Data | `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet` | Alternative source for host molecule structures if PubChem lacks specific hosts. |

**Critical Note on Data Availability**:
- The provided "Verified datasets" list **does not contain a direct URL** for NIST halide binding constants.
- The `WebBooks-1` dataset URL (`https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt`) appears to be a text dataset, not a structured chemistry binding table.
- **Contingency**: If the primary sources cannot be mapped to the required schema (Host SMILES, Halide ID, Binding Constant, Solvent) OR if the count of valid hosts is < 50, the system **MUST** trigger the fallback defined in **FR-011**: switch to a simulated dataset, reduce scope to single-halide prediction, and log the warning: "WARNING: Primary dataset insufficient (<50 hosts or missing columns). Scope reduced to single-halide prediction. Comparative analysis unanswerable with available data."

### 2.2 Simulated Data Generative Model

If the fallback is triggered, the system generates a simulated dataset that explicitly encodes halide binding physics:
1. **Host Properties**: Generate host molecules with random SMILES (using RDKit) and calculate descriptors (MolWt, LogP, HBD, HBA, TPSA).
2. **Cavity Size**: Estimate cavity size from molecular volume (calculated via `rdkit.Chem.rdMolDescriptors.CalcMolVolume`).
3. **Electrostatics**: Assign a random electrostatic potential to each host.
4. **Binding Constant Generation**:
   - `log_K = (Alpha * ElectrostaticPotential * HalideCharge) + (Beta * CavitySize) - (Gamma * StericHindrance) + Noise`
   - `HalideCharge`: F⁻ (-1), Cl⁻ (-1), etc. (all -1, but size varies).
   - `StericHindrance`: Function of HBD/HBA counts and MolWt.
   - `Noise`: Gaussian noise (std=0.5).
   - Parameters (Alpha, Beta, Gamma) are fixed to reflect known chemistry (e.g., Alpha > 0 for electrostatic attraction).
5. **Validation**: Ensure the generated data adheres to `dataset.schema.yaml` (valid SMILES pattern, correct enum values for halide identity, numeric binding constants).

This ensures the simulated data reflects the underlying chemical phenomenon, making the fallback scientifically meaningful.

## 3. Methodology

### 3.1 Data Preprocessing
1. **Ingestion**: Download from verified sources. If specific binding data is missing, generate simulated data with realistic distributions (log-normal binding constants, correlated with molecular size/polarity).
2. **Filtering**:
   - Exclude records with invalid SMILES (RDKit parsing failure).
   - Exclude records with ambiguous halide identity.
   - Filter to **non-aqueous solvents** (Acetonitrile, Chloroform) per Assumptions.
   - Retain only hosts with **≥3 different halide measurements**.
3. **Standardization**: Convert all binding constants to `log K`. If ΔG is provided, convert using ΔG = -RT ln(K).

### 3.2 Feature Engineering
- **Fingerprints**: ECFP4 (radius=2, nBits=2048) using RDKit.
- **Descriptors**: Calculate RDKit descriptors (MolWt, LogP, HBA, HBD, TPSA, MolVol for Cavity Size, etc.).
- **Collinearity Check**: Calculate Variance Inflation Factor (VIF) for descriptors. If VIF > 10, report collinearity but do not drop features (per spec assumptions).

### 3.3 Modeling Strategy
- **Algorithms**: Random RF (`RandomForestRegressor`) and Gradient Boosting (`GradientBoostingRegressor`) from `scikit-learn`.
- **Splitting**: **Stratified by Host ID**. K-fold Cross-Validation.
  - *Constraint*: Ensure no host ID appears in both train and test sets within a fold.
- **Hyperparameters**: Default `scikit-learn` parameters (per FR-005) to ensure CPU feasibility.
- **Compute Budget**: Target < 6 hours runtime, < 7 GB RAM. If the dataset is large, sample to a manageable subset size.

### 3.4 Statistical Analysis
- **Performance Metrics**: R² and RMSE calculated **per halide ion** (Constitution VI).
- **Comparisons**:
  - **Test**: **Bootstrap Resampling (1000 iterations)** to generate 95% Confidence Intervals for the **distribution of the difference in mean R² and RMSE** between halide pairs.
  - **Conditional Execution**: If `is_simulated` is true, pairwise comparisons are **skipped**, and the report states that comparative analysis is unanswerable.
  - **Correction**: Benjamini-Hochberg (FDR ≤ 0.05) applied to p-values if hypothesis testing is performed on the bootstrap distribution.
- **Power Analysis**: Removed. Replaced with reporting of 95% Confidence Intervals.

### 3.5 Interpretability
- **Feature Importance**: Permutation importance (scikit-learn).
- **Visualization**: Partial Dependence Plots (PDP) for top features vs. halide identity.
- **Domain Sanity Check**:
  1. **Curated List**: {HBD, HBA, TPSA, MolWt, Cavity Size (MolVol)}.
  2. **Validation**:
     - Check if at least 1 of the top 3 features is from the curated list.
     - Verify the slope direction of the top feature's relationship with binding affinity matches electrostatic theory (e.g., positive charge density correlates with higher affinity for anions).
  3. **Flag**: If checks fail, flag model as "chemically implausible".

## 4. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Simulated Data Fallback** | The verified dataset list lacks the specific "halide binding constant" column required for the primary research question. FR-011 mandates a fallback to ensure the pipeline is runnable and testable. The fallback data is now generated using a physics-based model to ensure scientific validity. |
| **Host-Based Splitting** | Essential to prevent data leakage. Random splitting would allow the model to "memorize" host structures rather than learning generalizable structure-activity relationships. |
| **Bootstrap Resampling** | Replaces the invalid Paired Wilcoxon test on N=5 folds. Bootstrap provides robust 95% Confidence Intervals for the difference in mean performance without assuming a specific dependency structure. |
| **Domain Sanity Check** | Replaces the circular 'overlap' check. Validates the model's reliance on known physics (slope direction) rather than just feature presence. |
| **CPU-Only, Default Precision** | Ensures compliance with GitHub Actions free-tier constraints (no GPU, 7GB RAM). |

## 5. Risk Assessment

- **Data Gap**: High risk. The verified sources do not contain the specific binding constants needed. **Mitigation**: Simulated data fallback implemented and documented with a physics-based generative model.
- **Sample Size**: Low risk of <50 hosts if simulated. If real data is found, risk of <50 is high given the specificity of halide binding data.
- **Collinearity**: High risk in molecular descriptors. **Mitigation**: VIF calculated and reported; results interpreted descriptively.
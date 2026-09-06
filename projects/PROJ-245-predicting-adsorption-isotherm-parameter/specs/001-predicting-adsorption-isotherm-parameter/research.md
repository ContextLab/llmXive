# Research: Predicting Adsorption Isotherm Parameters from Molecular Features

## 1. Problem Definition
The goal is to predict thermodynamic adsorption parameters (Henry's constant $K_H$, Langmuir capacity $Q_{max}$) for gas adsorbates in porous materials (MOFs, zeolites) using only molecular descriptors of the adsorbate and physical properties of the adsorbent. This enables high-throughput screening of materials without expensive simulations or experiments.

## 2. Dataset Strategy

### 2.1 Source Analysis & Verification
The specification relies on two primary sources:
1.  **NIST Adsorption Database**: Contains experimental isotherm data.
2.  **MOF-1000**: A curated repository of Metal-Organic Frameworks.

**Verified Datasets Status**:
The `Verified datasets` block provided for this project contains URLs that **do not** correspond to the NIST Adsorption Database or MOF-1000.
*   **Action**: The implementation will use the verified `matsci/qmof` dataset from HuggingFace. This dataset contains the required isotherm parameters (Henry's constant, Langmuir capacity) and molecular structures for a large number of MOF-adsorbate pairs.
*   **Fallback**: If `matsci/qmof` is unavailable or yields zero Type I entries, the pipeline will switch to `coreshare/coref_mof_2019` (CoRE MOF 2019), a verified open-access dataset containing MOF structures and experimental adsorption data.
*   **Hypothesis**: The `matsci/qmof` dataset provides a sufficient subset of Type I isotherms and the necessary molecular descriptors to train a robust model.

**Decision**: Proceed with `datasets.load_dataset("matsci/qmof")`.

### 2.2 Data Schema & "Type I" Isotherm Filtering
**Concern**: The spec requires filtering for "Type I" isotherms but does not specify the column name.
**Resolution**:
*   **Primary**: Filter where `isotherm_type` == "Type I" (or numeric 1).
*   **Secondary**: If the `isotherm_type` column is missing, the pipeline will filter based on physical validity: `target_henry` > 0 AND `target_langmuir` > 0. This ensures that only entries with valid Langmuir parameters (which imply Type I behavior) are retained.
*   **Tertiary**: If neither column exists, the pipeline will log a warning ("Mixed Isotherm Mode") and retain all rows to avoid a zero-data failure, while explicitly noting the limitation in the final report.

### 2.3 Data Availability & Streaming
*   **Streaming**: If the dataset > 2GB, use `datasets.load_dataset(..., streaming=True)` to process in chunks.
*   **Memory**: The limited RAM capacity of the CI runner requires careful handling. We will not load the full dataset into a single Pandas DataFrame if it exceeds a size threshold that would strain available memory resources. Instead, we will process in batches or use Polars (if available) or Dask for out-of-core operations.
*   **Sample Size**: If the full dataset is too large for the 6-hour runtime, we will take a stratified random sample of the first 2000 entries (or all if < 2000) to ensure feasibility.

## 3. Methodology

### 3.1 Feature Engineering (FR-001)
*   **Adsorbate Descriptors**: Calculated via RDKit from SMILES/SDF.
    *   `molecular_weight`, `polarizability`, `van_der_waals_volume`, `polar_surface_area`, `h_bond_donors`, `h_bond_acceptors`, `kinetic_diameter` (approximated).
*   **Adsorbent Properties**: Pore volume, surface area (converted to m²/g).
*   **Interaction Features**: Product of adsorbate polarizability and adsorbent surface area.

### 3.2 Data Splitting (FR-003)
*   **Strategy**: GroupKFold or custom split based on `adsorbent_id`.
*   **Goal**: Ensure no material appears in both train and test sets.
*   **Implementation**: `GroupShuffleSplit` from `scikit-learn`.

### 3.3 Modeling (FR-004)
*   **Models**:
    1.  **Linear Regression**: Baseline for linearity.
    2.  **Random Forest**: Captures non-linearities, robust to outliers.
    3.  **Gradient Boosting (XGBoost/LightGBM)**: High performance, handles complex interactions.
*   **Hyperparameter Tuning**: 5-fold Cross-Validation (GroupKFold) on training set. Grid search or Randomized Search.
*   **Null Model**: Predicts the mean of the training set.
*   **Uncertainty Weighting**: The target parameters ($K_H$, $Q_{max}$) are fitted parameters with inherent error. To prevent overfitting to noisy targets, the training loop will use `sample_weight` inversely proportional to the variance of the fitted parameters (if available in the source dataset) or estimated via bootstrap. If `target_se` columns are missing, a uniform weight (1/variance of target) is used.

### 3.4 Statistical Rigor (FR-006, FR-007)
*   **Multiple Comparison Correction**: Benjamini-Hochberg FDR applied to permutation p-values.
*   **Cluster-aware Permutation (FR-007)**:
    *   **Null Hypothesis**: Adsorbate descriptors have no predictive power for the target given the adsorbent identity.
    *   **Method**: For each adsorbent cluster (all entries sharing the same `adsorbent_id`), shuffle the *adsorbate index* (i.e., permute the adsorbate features among the adsorbates associated with that specific adsorbent). This breaks the specific adsorbate-adsorbent pairing while preserving the marginal distribution of targets and adsorbent properties.
    *   **Implementation**: `code/interpret/permutation.py` will implement this logic. The p-value is derived from the distribution of performance across these permutations.
    *   **Output**: `data/results/permutation_pvalues.json` containing adjusted p-values.
*   **Sample Size/Power**: If N < 100, explicitly state "Low power; results are exploratory."

### 3.5 Interpretation (FR-005, FR-008)
*   **SHAP**: `shap.TreeExplainer` for RF/GB.
*   **Consensus Check**: Compare top 3 features against `LiteratureConsensusList`.
    *   **Source**: `code/config/consensus_list.json` (derived from independent literature, e.g., Smit et al., 2019; Wilmer et al., 2012). This list is **external** to the training data and is curated from independent experimental studies to avoid circular validation.
    *   **Output**: Report highlighting convergence (e.g., "Polarizability was top 1, matching consensus") and divergence (e.g., "Kinetic diameter was not significant, contrary to consensus").
    *   **Avoid Circular Validation**: The `LiteratureConsensusList` is derived from *independent* experimental studies, not the training data.

### 3.6 Target Uncertainty
*   **Acknowledgement**: $K_H$ and $Q_{max}$ are fitted parameters derived from raw isotherm data using non-linear regression. They have inherent error.
*   **Mitigation**: The plan includes a step to capture `target_henry_se` and `target_langmuir_se` from the source dataset (if available) and use them as sample weights in the training loop (heteroscedastic loss). If missing, uncertainty is estimated via bootstrap or uniform weights are applied.

## 4. Compute Feasibility
*   **CPU-First**: All models (RF, GB) are CPU-tractable for N < 5000.
*   **GPU Escape Hatch**: Not required. SHAP and RF/GB are efficient on CPU.
*   **Runtime**: Estimated < 2 hours for N=2000.
*   **Memory**: Streaming + batch processing ensures < 6GB usage.

## 5. Risk Mitigation
*   **Missing Data**: Impute pore volume with group mean (by `adsorbent_id`) or exclude. Log exclusions.
*   **Poor Performance**: If R² < 0.2, generate diagnostic report (check for non-linearity, insufficient features).
*   **Dataset Unavailability**: If verified URLs are missing, halt and flag as "Data Feasibility Gap."
*   **Missing Uncertainty**: If `target_se` columns are missing, estimate via bootstrap or use uniform weights.

# Research: Predicting Adsorption Isotherm Parameters from Molecular Features

## Dataset Strategy

The primary dataset is the **NIST Adsorption Isotherms Database**, hosted on HuggingFace as `nist-adsorption-isotherms`. This dataset contains raw isotherm measurements (pressure, amount adsorbed, temperature) for various gas/adsorbent pairs. It also includes metadata linking `material_id` to a verified JSON file containing adsorbent structural properties (Surface Area, Pore Volume).

We explicitly **exclude** the "MOF-1000 Zenodo Repository" as a separate source to avoid data hygiene violations. Instead, the required adsorbent properties are extracted from the `material_metadata.json` file provided within the `nist-adsorption-isotherms` repository, ensuring a single, reproducible source of truth.

| Dataset | URL | Variables Needed | Usage |
|---|---|---|---|
| NIST Adsorption Isotherms | ` | Raw isotherm points (P, T, Amount), Material ID, Temperature | Training & Testing Models |
| MOF Metadata (Linked) | `https://huggingface.co/datasets/nist-adsorption-isotherms/blob/main/mof_metadata.json` | Surface Area (m²/g), Pore Volume (cm³/g) | Feature Engineering (Adsorbent Properties) |

**Data Access Method**:
- We will use `datasets.load_dataset("nist-adsorption-isotherms", split="train")` to fetch the isotherm data.
- We will download `mof_metadata.json` via `hf_hub_download` and merge it with the isotherm data on `material_id`.
- **Note**: The dataset does **not** contain pre-calculated `langmuir_capacity` or `henry_constant`. These will be **fitted** from the raw isotherm points using non-linear regression in the data processing pipeline, as required by scientific soundness.

## Decision/Rationale

**Compute Strategy**:
- **CPU-First**: All computations (data curation, descriptor calculation, model training, SHAP analysis) will be performed on the GitHub Actions CPU runner.
- **No GPU Offloading**: We explicitly **reject** the use of external GPU services (e.g., Kaggle) to maintain reproducibility and adhere to the CI runner constraints.
- **Scalability**: If the full dataset exceeds the memory limit (limited RAM), we will implement a **stratified sampling** strategy to select a representative subset (e.g., 1000-2000 entries) rather than offloading computation. This ensures the pipeline remains self-contained and reproducible.
- **Libraries**: `scikit-learn`, `RDKit`, `pandas`, `numpy`, `shap` (CPU mode), `matplotlib`.

## Feature Engineering Pipeline

1. **Data Filtering**: Filter raw isotherm data for Type I isotherms based on metadata flags.
2. **Parameter Fitting**: For each entry, fit the Langmuir model ($q = \frac{Q_{max} K_H P}{1 + K_H P}$) to the raw (P, q) points using non-linear least squares to derive `langmuir_capacity` ($Q_{max}$) and `henry_constant` ($K_H$). Entries with poor fit (R² < 0.9) are flagged and excluded.
3. **Molecular Descriptor Calculation**: Use RDKit to calculate descriptors for all adsorbates: Molecular Weight, Polar Surface Area, Polarizability, H-bond Donors/Acceptors, Van der Waals Volume.
4. **Adsorbent Property Extraction**: Join the isotherm data with `mof_metadata.json` on `material_id` to retrieve Surface Area and Pore Volume. Unit normalization (cm²/g to m²/g) is applied.
5. **Missing Data Handling**: Entries with missing `material_id` or missing metadata (Surface Area/Pore Volume) are excluded. No imputation is performed to avoid confounding.

## Statistical Methods

**Model Selection**:
- Linear Regression, Random Forest, Gradient Boosting.
- 5-fold Cross-Validation with **Material-Level Splitting** (stratified by `material_id` to prevent data leakage).

**Performance Metrics**:
- R², RMSE, MAE on the independent test set.
- Comparison against a Null Model (predicting the mean).

**Multiple Comparison Correction & Feature Significance**:
1. **Permutation Testing**: For each feature, we generate a null distribution by permuting the target variable (Langmuir capacity) **within material clusters** (grouped by `material_id`). This preserves intra-cluster correlations while breaking the feature-target relationship.
2. **P-Value Calculation**: Calculate the p-value for each feature as the proportion of permuted importances that exceed the observed importance.
3. **FDR Correction**: Apply the Benjamini-Hochberg procedure to the calculated p-values to generate adjusted p-values (q-values).
4. **Significance**: Features with q-value < 0.05 are considered statistically significant.

**Cluster-Aware Permutation Testing (FR-007 Compliance)**:
- To address multicollinearity and material-specific effects, feature values are shuffled **only within groups** defined by `material_id`. This ensures that the permutation respects the hierarchical structure of the data (multiple measurements per material) and prevents artificial inflation of significance due to material-level clustering.

**Reduced-Feature Model Validation (SC-003 Compliance)**:
- After identifying the top 3 features from the full model (via SHAP), we will train a **separate, reduced model** using **only** these 3 descriptors.
- The R² of this reduced model will be compared to the Null Model baseline to satisfy SC-003.

**Power Analysis**:
- We will perform a post-hoc power analysis to estimate the minimum detectable effect size given the sample size (N) and the number of predictors.
- If the power is insufficient (< 0.8) to detect small effect sizes, the report will explicitly state this limitation and focus on the direction and magnitude of effects rather than strict statistical significance.

## Power Limitation Acknowledgment

Given the potential collinearity between molecular descriptors (e.g., polarizability and van der Waals volume are often correlated) and the finite sample size (N ~ -1000), the statistical power to detect small, independent effects may be limited. We will prioritize the identification of **robust, high-magnitude drivers** and explicitly report any features that are significant only in the presence of strong collinearity. The plan includes a sensitivity analysis to assess the stability of feature rankings under different subsampling strategies.
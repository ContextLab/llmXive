# Research: Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

## Overview

This research investigates whether classical machine learning models (Random Forest, SVM) using molecular fingerprints can predict organic reaction yields with sufficient accuracy (R² ≥ 0.40) to be useful for reaction screening. The study leverages a verified USPTO yield dataset, focusing on rigorous data hygiene, **Stratified-by-Class + Intra-Class Scaffold Grouping** splitting to prevent leakage, and interpretable feature analysis via substructure aggregation.

## Dataset Strategy

### Primary Dataset: USPTO Yield Collection

The study utilizes the **USPTO Yield** dataset, which contains reaction SMILES, reagents, and **numeric yield values**. This dataset was selected for its explicit inclusion of yield values, which are critical for regression tasks.

| Dataset Name | Source URL | Format | Usage |
| :--- | :--- | :--- | :--- |
| USPTO Yield (Primary) | https://huggingface.co/datasets/chembl/uspto-yield/resolve/main/data/train.parquet | Parquet | Primary source for reaction SMILES, reagents, and numeric yield values. Verified to contain `yield` column. |
| USPTO-Yield (Fallback) | https://huggingface.co/datasets/chemistry/uspto-yields-50k/resolve/main/data/yields.parquet | Parquet | Fallback source if primary is unavailable. Verified to contain `yield` column. |

**Dataset Variable Fit Verification:**
- **Required Variables**: Reactant SMILES (multiple), Reagent SMILES, Yield (numeric), Reaction Class/Type.
- **Verification**: The selected USPTO Yield datasets contain columns for `reaction_smiles`, `reagents_smiles`, and `yield`. The `yield` column is verified to be numeric.
- **Potential Mismatch**: If the dataset lacks explicit `reaction_class` labels, they must be inferred from the reaction type (e.g., Suzuki, Amide) using regex on the SMILES or a separate mapping file. If the dataset only provides raw SMILES without class labels, the "Generalization" analysis (FR-007) will derive classes based on the reaction center (e.g., bond changes) to satisfy FR-007.
- **Action**: The preprocessing pipeline will attempt to parse `reaction_class` from metadata if available; otherwise, it will derive classes based on the reaction center to satisfy FR-007.

**Data Quality & Handling:**
- **Duplicates**: Reactions with identical SMILES but different yields will be handled by averaging the yield or selecting the mode, with logging.
- **Range Yields**: Entries with yield ranges (e.g., "50-60%") will be parsed to the midpoint. If parsing fails, the entry is excluded.
- **Missing Data**: Reactions with missing reagents or malformed SMILES will be excluded.

## Methodology

### 1. Data Preprocessing (FR-001, FR-002, FR-003)
- **Sanitization**: Use RDKit to remove salts, neutralize charges, and standardize tautomers.
- **Fingerprinting**: Generate ECFP4 (2048-bit) and MACCS (167-bit) fingerprints for the reaction components (reactants + reagents). Concatenate fingerprints for multi-component reactions.
- **Encoding**: Convert fingerprints to sparse or dense binary arrays suitable for scikit-learn.

### 2. Data Splitting (FR-004)
- **Strategy**: **Stratified-by-Class Split** (Primary) with **Intra-Class Scaffold Grouping** (Secondary).
  1. **Stratify**: Split the dataset into Train/Val/Test (70/15/15) such that the distribution of `reaction_class` is preserved in each split. This ensures every class is represented in train and test, satisfying Constitution Principle VI.
  2. **Group**: Within each class, group reactions by their Murcko scaffold. Ensure that no scaffold appears in both train and test sets *within the same class*. This prevents leakage of identical reactant cores while maintaining class diversity.
- **Ratios**: [deferred] Training, [deferred] Validation, [deferred] Test. Exact ratios logged.
- **Leakage Prevention**: Ensures no scaffold appears in both training and test sets, strictly testing generalization across classes and scaffolds.

### 3. Model Training (FR-005)
- **Fixed Representative Subset**: To ensure computational feasibility (RAM < 7GB, Runtime < 6h) and statistical validity, a **Fixed Representative Subset** of the training data (stratified by class and scaffold) is materialized as `data/processed/subset_train.parquet`. This subset is used for **both** hyperparameter tuning (grid search) and final model training. This eliminates the bias of tuning on a sample and training on a different distribution.
- **Subset Size**: Capped at a size that ensures grid search completes within 4 hours (e.g., 20k-50k reactions).
- **Algorithms**: Random Forest Regressor, Support Vector Machine (SVM) Regressor.
- **Hyperparameter Tuning**: Grid Search with 5-fold Cross-Validation on the **Fixed Representative Subset**.
  - *RF*: `n_estimators` (50, 100), `max_depth` (10, 20), `min_samples_split` (2, 5).
  - *SVM*: `C` (0.1, 1.0, 10.0), `kernel` (linear, rbf), `epsilon` (0.1).
- **Constraints**: CPU-only execution.

### 4. Evaluation & Analysis (FR-006, FR-007, FR-008)
- **Metrics**: R², RMSE, MAE on the held-out test set.
- **Generalization**: Per-reaction-class R² scores. Classes with <20 samples are merged or excluded.
- **Interpretability**: **Substructure Aggregation**.
  - Compute Permutation Importance for individual ECFP4 bits.
  - Map bits to substructures using RDKit's `GetBitInfo`.
  - **Aggregate**: Sum the permutation importance scores of all bits associated with a specific substructure. Report the top 20 substructures by aggregated score. This handles bit collisions and provides a stable, interpretable metric for SC-003.
- **Statistical Rigor**:
  - **Multiple Comparisons**: Apply **Bonferroni correction** to the p-values of the specific statistical tests defined below.
  - **Statistical Tests**:
    1.  **R² > 0**: One-sample t-test on cross-validation fold scores against the null hypothesis H₀: mean(R²) = 0.
    2.  **Model A > Model B**: Paired t-test on cross-validation fold scores between Model A and Model B (H₀: mean difference = 0).
    3.  **Class Performance Differences**: Paired t-test on per-class fold scores (H₀: mean difference = 0).
  - **Collinearity**: Acknowledge that ECFP bits are highly correlated. Feature importance is reported as "aggregated contribution to prediction" via the substructure aggregation method, not as independent causal effects.
  - **Power**: Acknowledge that with the fixed subset size, statistical power is determined by the subset size, which is chosen to be representative.

## Decision Rationale & Feasibility

### Computational Feasibility (Free-Tier CI)
- **RAM**: ECFP4 vectors for a fixed subset (e.g., 50k reactions) consume < 500 MB in dense boolean format.
- **Strategy**: Use the **Fixed Representative Subset** for the entire pipeline. This ensures the grid search is computationally feasible (smaller dataset) while remaining statistically valid for the final model, as the distribution is preserved.
- **No GPU**: All methods are CPU-native. `scikit-learn` and `rdkit` have efficient C++ backends.

### Risk Mitigation
- **Risk**: Dataset lacks yield values.
  - **Mitigation**: The primary and fallback datasets are verified to contain `yield` columns. If both fail, the pipeline halts with an explicit error.
- **Risk**: Runtime exceeds 6 hours.
  - **Mitigation**: The Fixed Representative Subset size is capped at a computationally manageable upper bound. Grid search grid size is limited.

## References
- USPTO Yield Dataset: https://huggingface.co/datasets/chembl/uspto-yield/resolve/main/data/train.parquet
- RDKit Documentation: (Internal library, no external URL needed)
- Scikit-learn Documentation: (Internal library, no external URL needed)

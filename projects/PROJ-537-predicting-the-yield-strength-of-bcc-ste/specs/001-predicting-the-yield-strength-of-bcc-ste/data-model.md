# Data Model: Predicting the Yield Strength of BCC Steels from Density Functional Theory

## 1. Entity Relationship Overview

The data model consists of three primary entities: `AlloyComposition`, `ExperimentalProperty`, and `DFTDescriptor`. These are merged into a single `UnifiedDataset` for modeling.

### Entities

1.  **AlloyComposition**
    -   **Description**: Represents the chemical makeup of a BCC iron alloy.
    -   **Key Attributes**: `formula` (string), `element_fractions` (map), `atomic_number_sum` (numeric).

2.  **ExperimentalProperty**
    -   **Description**: Macroscopic physical properties measured in a lab.
    -   **Key Attributes**: `yield_strength_MPa` (numeric), `source` (string), `temperature_K` (numeric).

3.  **DFTDescriptor**
    -   **Description**: Atomic-scale properties computed via Density Functional Theory.
    -   **Key Attributes**: `shear_modulus_GPa` (numeric), `bulk_modulus_GPa` (numeric), `space_group` (integer).

## 2. Schema Definitions

### 2.1 Raw Experimental Data (Input)
-   **Source**: MatNavi / NIST
-   **Format**: CSV
-   **Columns**:
    -   `formula`: Chemical formula (e.g., "Fe0.95Cr0.05").
    -   `yield_strength_MPa`: Yield strength value.
    -   `source_id`: Reference to the study.

### 2.2 Raw DFT Data (Input)
-   **Source**: Materials Project API
-   **Format**: JSON (parsed to DataFrame)
-   **Columns**:
    -   `material_id`: MP unique ID.
    -   `formula`: Chemical formula.
    -   `bulk_modulus`: GPa.
    -   `shear_modulus`: GPa.
    -   `space_group_number`: Integer (229 for BCC).

### 2.3 Unified Dataset (Intermediate/Processed)
-   **Format**: CSV / Parquet
-   **Columns**:
    -   `formula`: Primary key for merge.
    -   `yield_strength_MPa`: Target variable.
    -   `shear_modulus_GPa`: Predictor.
    -   `bulk_modulus_GPa`: Predictor.
    -   `element_fractions`: JSON string or separate columns (Fe, Cr, Ni, etc.).
    -   `uncertainty_flag`: Boolean (true if experimental value was a range).
    -   `vif_scores`: JSON string (Variance Inflation Factors for each feature).

### 2.4 Model Output (Results)
-   **Format**: JSON (`output.json`)
-   **Structure**:
    -   `metrics`: { `r2_rf`, `mae_rf`, `r2_baseline`, `mae_baseline`, `p_value`, `power` }
    -   `correlation`: { `shear_yield_r`, `shear_yield_p` } (SC-001)
    -   `feature_importance`: { `shap_values`: [], `permutation_importance`: [] }
    -   `stability`: { `std_shap`: [], `std_permutation`: [], `is_stable`: boolean }
    -   `multicollinearity`: { `vif_scores`: {} }

## 3. Data Flow

1.  **Ingestion**: Raw CSV (Exp) + API JSON (DFT) -> `raw/`.
2.  **Cleaning**: Filter for BCC (space_group=229), handle ranges (midpoint).
3.  **Merging**: Join on `formula`. Drop rows with missing DFT data.
4.  **Validation**: Check `len(df) >= 20`.
5.  **Feature Engineering**: Encode composition, normalize DFT, **Calculate VIF**.
6.  **Correlation Analysis**: Calculate Pearson correlation between Shear Modulus and Yield Strength.
7.  **Modeling**: Train RF (Nested CV), Calculate metrics.
8.  **Interpretability**: SHAP, Bootstrap (full dataset), Threshold Check.
9.  **Export**: `data/results/output.json`.
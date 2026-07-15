# Data Model: Predicting Insect Pollinator Networks from Floral Trait Data

## Data Flow

1.  **Raw Ingestion**: Download CSVs from Web of Life (interactions) and Dryad (traits).
2.  **Alignment**: Join interaction pairs with trait data on `species_id`.
3.  **Feature Construction**: Create a row for every *possible* pair in the ecosystem (observed + co-occurring unobserved).
4.  **Preprocessing**: Impute, normalize, encode.
5.  **Splitting**: Stratified train/test split (or K-fold).
6.  **Model Input**: Feature matrix `X` (traits only + sampling effort) and label `y` (link: 0/1).
7.  **Output**: Predicted probabilities, importance scores, network graphs.

## Entity Definitions

### Ecosystem
*   **Definition**: A unique geographic community (e.g., "Mallorca", "Alps").
*   **ID**: Unique string identifier (e.g., `MALL_01`).
*   **Attributes**: `location`, `season`, `dataset_source`.

### Species
*   **Definition**: A plant or pollinator taxon.
*   **ID**: `species_id` (e.g., `Apis_mellifera`, `Centaurea_cyanus`).
*   **Type**: `plant` or `pollinator`.

### Interaction (Link)
*   **Definition**: An observed event between a plant and a pollinator.
*   **Attributes**: `ecosystem_id`, `plant_id`, `pollinator_id`, `frequency` (optional, binarized to 1), `sampling_effort` (optional).

### Floral Trait
*   **Definition**: A measurable characteristic of a plant.
*   **Types**:
    *   `continuous`: Corolla depth (mm), flower size (mm).
    *   `categorical`: Color (Blue, White, Yellow), Scent (Present, Absent).
*   **Missingness**: Flagged if > 15% of species in the ecosystem lack the trait.

### Co-occurring Pair (Critical Definition)
*   **Definition**: A plant-pollinator pair where both species are known to exist in the same ecosystem at the same time.
*   **Derivation**: Co-occurrence is **derived strictly from the interaction matrix file**. If species A (plant) and species B (pollinator) both appear in the same interaction matrix CSV for a given ecosystem, they are defined as co-occurring.
*   **Temporal Proxy**: Temporal metadata is used only if explicitly provided in the source file; otherwise, spatial co-occurrence (presence in the same file) is the sole proxy. This aligns with the spec's assumption that spatial metadata is sufficient.
*   **Label Assignment**:
    *   If the pair is observed in the matrix: `label = 1`.
    *   If the pair is co-occurring but **unobserved**: `label = 0` (Probabilistic Negative).
    *   **Note**: Unobserved pairs are treated as "probabilistic negatives" (likely non-interactions), acknowledging the risk of false negatives (missed interactions).

## Data Schema (Processed)

The final feature matrix for training has the following structure. **Note**: The `ecosystem_id`, `plant_id`, and `pollinator_id` columns are **explicitly excluded** from the model input features. They are used only for internal grouping and tracking. The model input `X` contains ONLY trait features and the label.

| Column | Type | Description |
| :--- | :--- | :--- |
| `ecosystem_id` | string | ID of the ecosystem (used for grouping, **NOT** a feature). |
| `plant_id` | string | Plant species ID (used for grouping, **NOT** a feature). |
| `pollinator_id` | string | Pollinator species ID (used for grouping, **NOT** a feature). |
| `trait_corolla_depth` | float | Z-score normalized corolla depth. |
| `trait_flower_size` | float | Z-score normalized flower size. |
| `trait_color_blue` | int (0/1) | One-hot encoded (1 if blue, else 0). |
| `trait_color_white` | int (0/1) | One-hot encoded. |
| `trait_color_yellow` | int (0/1) | One-hot encoded. |
| `trait_scent_present` | int (0/1) | One-hot encoded. |
| `sampling_effort` | float | Normalized sampling effort (e.g., number of visits). If missing, imputed or flagged. |
| `label` | int (0/1) | 1 if observed link, 0 if co-occurring unobserved (probabilistic negative). |

## Transformation Logic

1.  **Imputation**:
    *   Missing continuous values → Median of the ecosystem.
    *   Missing categorical values → "Unknown" category (or drop if > 15% missing).
2.  **Normalization**:
    *   Winsorize outliers at 1st and 99th percentiles.
    *   Apply Z-score: `(x - mean) / std`.
3.  **Encoding**:
    *   One-hot encoding for categorical traits.
    *   No label encoding for target (binary 0/1).
4.  **Negative Sampling**:
    *   Generate all pairs `(p, q)` where `p` is plant, `q` is pollinator in the same ecosystem.
    *   **Co-occurrence**: Defined as presence of both species in the same interaction matrix file. If temporal metadata is available, it is used to filter; otherwise, spatial co-occurrence is the proxy.
    *   Mark observed pairs as `label=1`.
    *   Mark unobserved pairs as `label=0` (Probabilistic Negative).
    *   **Constraint**: Ensure `p` and `q` are co-occurring (verified by presence in the same ecosystem matrix).
    *   **Label Noise Note**: "Unobserved" pairs are treated as "probabilistic negatives" (likely non-interactions). The pipeline acknowledges that some of these may be false negatives (missed interactions).
5.  **Feature Selection**:
    *   **Trait-Only**: The model input `X` includes only trait columns and `sampling_effort`. `ecosystem_id`, `plant_id`, and `pollinator_id` are **dropped** before model training to ensure generalization to unseen species.
6.  **Label Noise Mitigation**:
    *   **Sampling Effort**: Included as a feature to help the model distinguish between true negatives and unobserved positives.
    *   **Sensitivity Analysis**: A subset of "high-confidence" negatives (high sampling effort, no interaction) is used for a secondary evaluation to assess bias.
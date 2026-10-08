# Data Model: Predicting Yield Strength of BCC Alloys

## Entity Definitions

### AlloyRecord
Represents a single alloy entry from the source dataset.
- `system_id`: `str` (Unique identifier from source)
- `elemental_composition`: `dict[str, float]` (Element symbol -> Atomic fraction)
- `yield_strength`: `float` (MPa)
- `crystal_structure`: `str` (e.g., "BCC", "FCC")
- `source_reference`: `str` (DOI or URL of source)
- `yield_definition`: `str` (e.g., "[deferred] offset", "[deferred] offset") - Added to track construct validity.

### CompositionalDescriptor
Derived features calculated from `AlloyRecord`.
- `delta_radius`: `float` (Atomic radius mismatch, %)
- `vec`: `float` (Valence Electron Concentration)
- `mixing_entropy`: `float` (J/mol/K)
- `mixing_enthalpy`: `float` (kJ/mol)
- `electronegativity_diff`: `float` (Pauling scale)
- `ilr_transformed_features`: `list[float]` (ILR coordinates)

### CombinedFeatureSet
The concatenated set of ILR and Scalar descriptors used for feature selection.
- `system_id`: `str`
- `scalar_features`: `dict[str, float]`
- `ilr_features`: `list[float]`
- `combined_vector`: `list[float]` (Concatenated scalar + ilr)

### ModelPerformance
Evaluation results for a trained model.
- `model_type`: `str` (e.g., "RandomForest", "Ridge")
- `r_squared`: `float` (Mean R² across folds)
- `mae`: `float` (Mean Absolute Error)
- `rmse`: `float` (Root Mean Squared Error)
- `confidence_interval`: `tuple[float, float]` (95% CI for R²)
- `feature_importance`: `dict[str, float]` (Ranked importance)

### FeatureStability
Metrics for feature importance stability (SC-003).
- `rank_std_dev`: `float` (Standard deviation of feature importance ranks across bootstrap resamples)
- `spearman_correlation`: `float` (Median Spearman correlation of ranks)

### PracticalUtility
Metrics for practical utility (SC-002).
- `mae_vs_threshold`: `bool` (True if MAE <= 50 MPa)
- `mae_value`: `float` (MAE in MPa)

### ThermodynamicParams
Binary interaction parameters for mixing enthalpy.
- `element_pair`: `tuple[str, str]` (e.g., ("Fe", "Cr"))
- `omega_ij`: `float` (kJ/mol)

## Data Flow

1. **Raw Data**: `data/raw/mpea.csv` (or parquet)
2. **Filtered Data**: `data/processed/bcc_filtered.csv` (BCC only, non-null yield, verified yield definition)
3. **Feature Data**: `data/processed/features_engineered.csv` (Descriptors + ILR)
4. **Model Artifacts**: `data/processed/models/` (pickle files)
5. **Results**: `reports/results.json`

## Calculations

### Atomic Radius Mismatch (δ)
$$ \delta = \sqrt{\sum_{i} c_i \left( 1 - \frac{r_i}{\bar{r}} \right)^2} \times 100 $$
Where $c_i$ is atomic fraction, $r_i$ is atomic radius, $\bar{r} = \sum c_i r_i$.

### Valence Electron Concentration (VEC)
$$ VEC = \sum_{i} c_i \cdot VEC_i $$

### Mixing Entropy (ΔS_mix)
$$ \Delta S_{mix} = -R \sum_{i} c_i \ln(c_i) $$

### Mixing Enthalpy (ΔH_mix)
$$ \Delta H_{mix} = \sum_{i \neq j} \Omega_{ij} c_i c_j $$
Where $\Omega_{ij}$ are binary interaction parameters from `data/raw/nist_janaf_params.json`.

### ILR Transformation
Isometric Log-Ratio transformation applied to the composition vector $x$ to handle closure.
$$ ilr(x) = V^T \ln(x) $$
Where $V$ is an orthonormal basis matrix for the simplex.

## Constraints

- **Composition Sum**: All composition rows MUST sum to 1.0 (within tolerance 1e-6).
- **BCC Filter**: Only rows with `crystal_structure == "BCC"` are included.
- **Yield Validity**: `yield_strength` MUST be a positive float AND `yield_definition` MUST be verified (e.g., "[deferred] offset").
- **Feature Selection**: L1/RFE MUST be performed on `CombinedFeatureSet` (ILR + Scalars).
- **Complementarity**: L1/RFE MUST NOT remove all ILR or all Scalar features (enforced by ComplementarityFailureContract).
- **Validation**: 5-fold CV MUST be repeated 10 times.
- **Bootstrap**: 100 resamples MUST be used for CI.
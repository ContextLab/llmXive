# Data Model: Predicting Yield Strength of BCC Alloys

## Entity Definitions

### AlloyRecord
| Attribute | Type | Description |
|-----------|------|-------------|
| `system_id` | `str` | Unique identifier from the source dataset |
| `elemental_composition` | `dict[str, float]` | Element symbol → atomic fraction (must sum to 1.0) |
| `yield_strength` | `float` | Yield strength in MPa (positive) |
| `crystal_structure` | `str` | Must be `"BCC"` for inclusion |
| `source_reference` | `str` | DOI or URL of original record |
| `yield_definition` | `str` | Textual description of the yield‑strength measurement method (e.g., `"[deferred] offset"`); required for construct validity |

### CompositionalDescriptor
| Attribute | Type | Description |
|-----------|------|-------------|
| `system_id` | `str` | FK to `AlloyRecord` |
| `delta_radius` | `float` | Atomic radius mismatch (%) |
| `vec` | `float` | Valence Electron Concentration |
| `mixing_entropy` | `float` | ΔS<sub>mix</sub> (J mol⁻¹ K⁻¹) |
| `mixing_enthalpy` | `float` | ΔH<sub>mix</sub> (kJ mol⁻¹) |
| `electronegativity_diff` | `float` | Difference in Pauling electronegativity |
| `ilr_transformed_features` | `list[float]` | ILR coordinates of the composition simplex |

### CombinedFeatureSet
| Attribute | Type | Description |
|-----------|------|-------------|
| `system_id` | `str` | FK |
| `scalar_features` | `dict[str, float]` | Keys: `delta_radius`, `vec`, `mixing_entropy`, `mixing_enthalpy`, `electronegativity_diff` |
| `ilr_features` | `list[float]` | ILR vector |
| `combined_vector` | `list[float]` | Concatenation of `scalar_features` values (ordered) + `ilr_features` |

### ModelPerformance
| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | `str` | `"RandomForest"`, `"GradientBoosting"` or `"Ridge"` |
| `r_squared` | `float` | Mean R² across CV repeats |
| `mae` | `float` | Mean Absolute Error (MPa) |
| `rmse` | `float` | Root Mean Squared Error (MPa) |
| `confidence_interval` | `tuple[float, float]` | 95 % CI for R² (percentile bootstrap) |
| `feature_importance` | `dict[str, float]` | Permutation importance scores for top‑5 features |
| `feature_stability` | `dict` | `rank_std_dev` and `spearman_correlation` (SC‑006) |
| `practical_utility` | `dict` | `mae_vs_threshold` (bool) and `mae_value` (SC‑002) |

## Calculations

All scalar descriptors use elemental properties from the `periodictable` library (static reference). Mixing enthalpy uses binary interaction parameters Ω<sub>ij</sub> stored in `data/raw/nist_janaf_params.json` (FR‑003).

- **Atomic Radius Mismatch (δ)**  
  $$\delta = \sqrt{\sum_i c_i\Bigl(1-\frac{r_i}{\bar r}\Bigr)^2}\times 100$$  
  where $c_i$ = atomic fraction, $r_i$ = atomic radius, $\bar r = \sum_i c_i r_i$.

- **Valence Electron Concentration (VEC)**  
  $$\text{VEC} = \sum_i c_i \, \text{VEC}_i$$  

- **Mixing Entropy (ΔS<sub>mix</sub>)**  
  $$\Delta S_{mix}= -R \sum_i c_i \ln c_i$$  
  $R = 8.314\ \text{J mol}^{-1}\text{K}^{-1}$.

- **Mixing Enthalpy (ΔH<sub>mix</sub>)**  
  $$\Delta H_{mix}= \sum_{i\neq j} \Omega_{ij}\,c_i\,c_j$$  
  Ω<sub>ij</sub> sourced from `nist_janaf_params.json`.

- **Electronegativity Difference**  
  $$\Delta \chi = \sqrt{\sum_i c_i (\chi_i - \bar\chi)^2}$$  
  where $\chi_i$ is Pauling electronegativity, $\bar\chi = \sum_i c_i \chi_i$.

- **ILR Transformation**  
  For composition vector $\mathbf{x}$ (length $k$), compute  
  $$\mathbf{z}=V^\top \ln(\mathbf{x})$$  
  where $V$ is an orthonormal basis for the $(k-1)$‑simplex (implemented via `skbio.stats.composition.ilr`).

All calculations are vectorised for speed; any domain error (e.g., `log(0)`) triggers the fallback defined in FR‑008 (value = 0.0, log alloy ID).

## Data Flow Summary
1. **Raw** → `data/raw/mpea.csv` (immutable)  
2. **Filtered** → `data/processed/bcc_filtered.csv` (FR‑001, FR‑002)  
3. **Aggregated** → `data/processed/bcc_aggregated.csv` (FR‑007)  
4. **Engineered** → `data/processed/features_engineered.csv` (FR‑003, FR‑003.1) – produces a `CombinedFeatureSet` per alloy.  
5. **Model Artifacts** → `data/processed/models/*.pkl` (FR‑005)  
6. **Results** → `reports/results.json` (FR‑006)

All intermediate files are version‑hashed and logged.

---


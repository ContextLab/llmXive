# Data Model: Predicting the Glass Forming Region of Metallic Glass Alloys Using Machine Learning

## Entity Definitions

### AlloyComposition
Represents a single metallic alloy with elemental fractions and phase label.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `composition_id` | string | Unique identifier (normalized formula) | Primary key |
| `formula` | string | Normalized chemical formula (e.g., "Zr50Cu35Al15") | Not null |
| `source` | string | Data source: "zenodo", "materials_project", or "synthetic" | Enum |
| `phase` | string | "amorphous" or "crystalline" | Not null; ≥98% completeness |
| `atomic_fractions` | object | Map of element → fraction (e.g., {"Zr": 0.5, "Cu": 0.35, "Al": 0.15}) | Sum = 1.0 |
| `elemental_properties` | object | Map of element → {radius, electronegativity, vec} | Fetched from MP API |
| `descriptors` | object | Computed features (δ, Δχ, ΔHmix, VEC, etc.) | Derived |
| `miedema_approximation_flag` | boolean | True if ΔHmix was computed using default parameters | Default: false |
| `is_dropped` | boolean | True if missing phase or insufficient descriptors | Default: false |
| `stratum_confounded` | boolean | True if phase labels are not balanced within the alloy system | Default: false |

### AtomicDescriptor
Represents a single computed feature value for a composition.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `composition_id` | string | Foreign key to AlloyComposition | Not null |
| `descriptor_name` | string | Name of descriptor (e.g., "atomic_size_mismatch") | Enum |
| `value` | float | Computed value | Range: δ ∈ [0,1], Δχ ∈ [,3] |

### ModelPerformance
Captures evaluation metrics for a trained model.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `model_name` | string | "rf", "xgb", or "lr" | Enum |
| `fold` | integer | Cross-validation fold (0–4) | 0–4 |
| `balanced_accuracy` | float | Primary metric | 0–1 |
| `precision` | float | Precision score | 0–1 |
| `recall` | float | Recall score | 0–1 |
| `f1_score` | float | F1 score | 0–1 |
| `train_timestamp` | datetime | When model was trained | ISO8601 |

## Data Flow

1. **Ingestion**: Raw compositions loaded from Zenodo (if available) or generated synthetically.
2. **Deduplication**: Compositions merged by normalized formula; Zenodo takes precedence.
3. **Feature Engineering**: Descriptors computed for each composition; missing properties trigger drop or flag.
4. **Stratification Integrity Check**: Verify phase balance within alloy systems; flag confounded strata.
5. **Splitting**: A standard split (Train/Validation/Test) stratified by alloy system.
6. **Training**: Models trained with k-fold CV on Train set; metrics stored in ModelPerformance.
7. **Evaluation**: Final evaluation on held-out Test set; SHAP and permutation importance generated.

## Data Validation Rules

- **Completeness**: ≥95% of compositions must have all descriptors computed (FR-001).
- **Label Completeness**: ≥98% of compositions must have definitive phase labels (FR-009).
- **Descriptor Ranges**: δ ∈ [0,1]; Δχ ∈ [0,3]; ΔHmix is expected to fall within a moderate range of enthalpy values, consistent with typical mixing behaviors, without specifying exact lower or upper bounds. (physically reasonable).
- **Deduplication**: No duplicate formulas in final dataset (FR-010).
- **Stratification**: No stratum with >90% of one class without flagging.
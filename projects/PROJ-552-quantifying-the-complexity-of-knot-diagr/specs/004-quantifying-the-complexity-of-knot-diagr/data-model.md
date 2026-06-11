# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              InvariantsDataset                           │
│  (Aggregated collection of KnotRecord entities with computed relationships) │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ contains
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                  KnotRecord                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Attributes:                                                      │   │
│  │   - knot_id: str (unique identifier)                            │   │
│  │   - crossing_number: int (primary invariant)                    │   │
│  │   - braid_index: int (primary invariant)                        │   │
│  │   - hyperbolic_volume: float | null (target variable)           │   │
│  │   - alternating_classification: bool                            │   │
│  │   - dt_code: str | null (diagram representation)                │   │
│  │   - braid_word: str | null (diagram representation)             │   │
│  │   - arc_index: int | null (computed invariant)                  │   │
│  │   - seifert_circle_count: int | null (computed invariant)       │   │
│  │   - bridge_number: int | null (computed invariant)              │   │
│  │   - missing_invariant_flags: list[str]                          │   │
│  │   - data_source: str (e.g., "Knot Atlas")                       │   │
│  │   - computation_timestamp: datetime                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ used to fit
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               RegressionModel                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Attributes:                                                      │   │
│  │   - model_id: str (unique identifier)                           │   │
│  │   - model_type: str (linear, polynomial, logarithmic)           │   │
│  │   - coefficients: dict (parameter names → values)               │   │
│  │   - r_squared: float (goodness-of-fit)                          │   │
│  │   - aic: float (model selection metric)                         │   │
│  │   - bic: float (model selection metric)                         │   │
│  │   - mae: float (mean absolute error)                            │   │
│  │   - vif_values: dict (predictor → VIF score)                    │   │
│  │   - sample_size: int (total dataset size for finite census)     │   │
│  │   - random_seed: int (reproducibility)                          │   │
│  │   - methodological_note: str (clarifies correlation vs. ML)     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ evaluated against
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CompositeComplexityScore                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Attributes:                                                      │   │
│  │   - score_id: str (unique identifier)                           │   │
│  │   - weight_crossing_number: float (default: 1.0)                │   │
│  │   - weight_braid_index: float (default: 1.0)                    │   │
│  │   - per_knot_scores: dict (knot_id → score)                     │   │
│  │   - pearson_correlation: float (vs. hyperbolic volume)          │   │
│  │   - spearman_correlation: float (vs. hyperbolic volume)         │   │
│  │   - p_value: float (correlation significance)                   │   │
│  │   - effect_size: float (r or r²)                                │   │
│  │   - sample_size: int (total dataset size for finite census)     │   │
│  │   - random_seed: int (reproducibility)                          │   │
│  │   - methodological_note: str (clarifies correlation vs. ML)     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Entity Definitions

### KnotRecord

**Purpose**: Represents a single prime knot with all computed and tabulated invariants.

**Attributes**:

| Attribute | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| knot_id | str | Yes | Unique identifier for the knot | Format: "c{crossing}_{index}" e.g., "c10_123" |
| crossing_number | int | Yes | Minimum number of crossings | Range: 1-13 (Phase 1: 1-10 validated) |
| braid_index | int | Yes | Minimum number of strands in braid representation | Range: 2 ≤ braid_index ≤ crossing_number |
| hyperbolic_volume | float | No (conditional) | Volume of knot complement in hyperbolic 3-space; required for volume analysis, null for torus/satellite knots | Zero/undefined for torus/satellite knots; required if hyperbolic volume analysis is performed |
| alternating_classification | bool | Yes | Whether knot is alternating | true = alternating, false = non-alternating |
| dt_code | str | No | Dowker-Thistlethwaite code representation | May be null if representation unavailable |
| braid_word | str | No | Braid word representation | May be null if representation unavailable |
| arc_index | int | No | Computed via Birman-Menasco algorithm | May be null if computation not possible |
| seifert_circle_count | int | No | Computed via Seifert's algorithm | May be null if computation not possible |
| bridge_number | int | No | Computed via Schubert's decomposition | May be null if computation not possible |
| missing_invariant_flags | list[str] | Yes | Flags for missing/uncomputable invariants | Empty list if all invariants computed |
| data_source | str | Yes | Source of the knot data | e.g., "Knot Atlas"; see field-level source attribution below |
| computation_timestamp | datetime | Yes | When the record was processed | ISO 8601 format |

**Field-Level Source Attribution** (per data_resources-abf97125 concern):

| Field | Primary Source | Validation Source |
|-------|---------------|-------------------|
| crossing_number | Knot Atlas | KnotInfo (for ≤10) |
| braid_index | Knot Atlas | KnotInfo (where available) |
| hyperbolic_volume | Knot Atlas | N/A (geometric invariant) |
| alternating_classification | Knot Atlas | KnotInfo |
| dt_code | Knot Atlas | N/A |
| braid_word | Knot Atlas | N/A |
| arc_index | Computed (Birman-Menasco) | N/A |
| seifert_circle_count | Computed (Seifert's algorithm) | N/A |
| bridge_number | Computed (Schubert's decomposition) | N/A |

**Invariant Dependency Note**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies are acknowledged in analysis and reporting.

### InvariantsDataset

**Purpose**: Aggregated collection of KnotRecord entities with metadata about data source and computation timestamps.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| dataset_id | str | Unique identifier for the dataset |
| total_knots | int | Total number of KnotRecord entities |
| crossing_number_range | tuple[int, int] | (min, max) crossing numbers in dataset |
| alternating_count | int | Number of alternating knots |
| non_alternating_count | int | Number of non-alternating knots |
| data_source | str | Source of the underlying data |
| download_timestamp | datetime | When the raw data was downloaded |
| computation_timestamp | datetime | When invariants were computed |
| checksum | str | SHA-256 checksum of the dataset file |
| validation_status | str | "validated" (≤10) or "exploratory" (11-13) |

### RegressionModel

**Purpose**: Represents a fitted regression model with all relevant metadata.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| model_id | str | Unique identifier for the model |
| model_type | str | Type: "linear", "polynomial", or "logarithmic" |
| predictors | list[str] | List of predictor variables used |
| coefficients | dict | Parameter names → coefficient values |
| r_squared | float | Coefficient of determination |
| adjusted_r_squared | float | Adjusted R² accounting for predictor count |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| rmse | float | Root Mean Squared Error |
| vif_values | dict | Predictor → Variance Inflation Factor |
| multicollinearity_flag | bool | True if any VIF > 5 (documented as mathematical constraint context, not a correction trigger) |
| sample_size | int | Total number of records in dataset (finite census correlation analysis; no train/validation split) |
| random_seed | int | Random seed used for any stochastic operations |
| fit_timestamp | datetime | When the model was fitted |
| methodological_note | str | Clarifies this is full-dataset correlation analysis, not ML predictive modeling |

### CompositeComplexityScore

**Purpose**: Represents the weighted complexity measure with validation metrics.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| score_id | str | Unique identifier for the score configuration |
| weight_crossing_number | float | Weight for crossing number (default: 1.0) |
| weight_braid_index | float | Weight for braid index (default: 1.0) |
| per_knot_scores | dict | knot_id → composite score mapping |
| pearson_correlation | float | Pearson r with hyperbolic volume |
| spearman_correlation | float | Spearman ρ with hyperbolic volume |
| p_value | float | Correlation significance (with exploratory disclaimer) |
| effect_size | float | r or r² for correlation strength |
| sample_size | int | Total number of knots in dataset (finite census) |
| split_method | str | "stratified_by_crossing_number" |
| random_seed | int | Random seed used for splitting |
| config_file | str | Path to complexity_weights.yaml |
| computation_timestamp | datetime | When the score was computed |
| methodological_note | str | Clarifies this is internal correlation assessment, not out-of-sample prediction |

## Data Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Knot Atlas      │────▶│  InvariantsDataset│────▶│  RegressionModel  │
│  (raw download)  │     │  (parsed + cleaned)│    │  (fitted models)  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
         │                        ▼                        ▼
         │               ┌──────────────────┐     ┌──────────────────┐
         │               │  KnotRecord      │     │  CompositeComplexityScore│
         │               │  (individual)    │     │  (validation)    │
         │               └──────────────────┘     └──────────────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│  docs/reproducibility/│ │  data/plots/     │
│  (validation logs) │     │  (visualization) │
└──────────────────┘     └──────────────────┘
```

## File Formats

### data/raw/knot_atlas_export.csv

**Format**: CSV with header row

**Columns**:
- knot_id (str)
- crossing_number (int)
- braid_index (int)
- hyperbolic_volume (float)
- alternating_classification (bool)
- dt_code (str | null)
- braid_word (str | null)

**Checksum**: SHA-256 recorded in data/checksums.txt

### data/derived/invariants_computed.csv

**Format**: CSV with header row

**Columns**: All KnotRecord attributes plus:
- arc_index (int | null)
- seifert_circle_count (int | null)
- bridge_number (int | null)
- missing_invariant_flags (list[str] encoded as semicolon-separated string)
- computation_timestamp (datetime)

### data/derived/regression_results.csv

**Format**: CSV with header row

**Columns**: All RegressionModel attributes flattened

**Checksum**: SHA-256 recorded in data/checksums.txt

### docs/reproducibility/validation_scope.md

**Purpose**: Documents Phase 1 scope boundaries and validation status.

**Content**:
- Phase 1 validation limited to crossing numbers ≤10
- Data availability extends to ≤13 but not validated
- Justification for scope limitation (computational impracticality)
- Reference to SC-001 and SC-013

### docs/reproducibility/selection_bias.md

**Purpose**: Documents selection bias limitations (per methodology-ba91ea97 concern).

**Content**:
- Analysis limited to hyperbolic knots only
- Torus/satellite knots excluded due to undefined hyperbolic volume
- Generalizability limited to hyperbolic knot class
- Impact on 'complexity' findings documented

## Data Integrity Constraints

1. **No In-Place Modification**: All transformations produce new files under data/derived/ (Constitution Principle III)
2. **Checksum Verification**: All data files under data/ must have corresponding SHA-256 checksums in data/checksums.txt
3. **Null Handling**: Missing invariant values encoded as null in CSV; missing_invariant_flags must list all missing fields
4. **Timestamp Consistency**: computation_timestamp must be monotonically increasing across derived files
5. **Random Seed Pinning**: All stochastic operations must use random_seed from config/seeds.yaml
6. **hyperbolic_volume Conditionality**: Required only when hyperbolic volume analysis is performed; nullable for torus/satellite knots
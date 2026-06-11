# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with computed and tabulated invariants.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| knot_id | string | Yes | Unique identifier | Primary key (e.g., "3_1", "4_1", "13_00001") |
| crossing_number | integer | Yes | ≥1, ≤13 | Tabulated crossing number from Knot Atlas |
| braid_index | integer | Yes | ≥1, ≤crossing_number | Braid index (algorithmic or tabulated) |
| arc_index | integer | No | ≥crossing_number | Computed via Birman-Menasco method (FR-003) |
| seifert_circle_count | integer | No | ≥1 | Computed via Seifert's algorithm on minimal crossing diagram (FR-003) |
| bridge_number | integer | No | ≥2, ≤crossing_number | Computed via Schubert's bridge decomposition (FR-003) |
| is_alternating | boolean | No | null if unclassifiable | Alternating classification (FR-012) |
| hyperbolic_volume | float | No | ≥0, null if undefined | Hyperbolic volume (excluded if 0 or undefined per FR-014) |
| diagram_representation | string | No | "braid_word", "dt_code", "both", "none" | Available diagram representation type |
| missing_invariant_flags | array[string] | No | Enum: ["arc_index", "seifert_circles", "bridge_number"] | Flags for invariants that could not be computed |
| data_source | string | Yes | "knot_atlas", "computed" | Source of primary data |
| computed_at | timestamp | Yes | ISO 8601 | Timestamp of invariant computation |
| checksum | string | Yes | SHA-256 | Content hash for reproducibility (Constitution Principle III) |

**Invariant Dependency Note**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies are acknowledged in analysis and validation is exploratory correlation, not independence testing.

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata.

| Field | Type | Description |
|-------|------|-------------|
| dataset_id | string | Unique dataset identifier |
| total_records | integer | Total number of knot records |
| crossing_number_range | object | {min: 1, max: 13} |
| alternating_count | integer | Count of alternating knots |
| non_alternating_count | integer | Count of non-alternating knots |
| unclassifiable_count | integer | Count of knots with ambiguous classification |
| hyperbolic_volume_available | integer | Count with valid hyperbolic volume |
| data_source | string | Primary data source |
| created_at | timestamp | Dataset creation timestamp |
| checksum | string | SHA-256 of entire dataset |
| derivation_notes | string | Path to derivation documentation |

### RegressionModel

Represents fitted model with attributes.

| Field | Type | Description |
|-------|------|-------------|
| model_id | string | Unique model identifier |
| model_type | string | "linear", "polynomial", "logarithmic" |
| predictors | array[string] | ["crossing_number", "braid_index"] |
| target | string | "hyperbolic_volume" |
| coefficients | object | Model coefficients |
| r_squared | float | R² goodness-of-fit metric |
| aic | float | AIC model selection criterion |
| bic | float | BIC model selection criterion |
| mae | float | Mean absolute error |
| vif_scores | object | Variance inflation factors per predictor |
| train_split | float | Training set proportion (e.g., 0.8) |
| validation_split | float | Validation set proportion (e.g., 0.2) |
| random_seed | integer | Seed for reproducibility (Constitution Principle I) |
| fitted_at | timestamp | Model fitting timestamp |

### CompositeComplexityScore

Represents the weighted complexity measure.

| Field | Type | Description |
|-------|------|-------------|
| score_id | string | Unique score identifier |
| weight_crossing | float | Weight for crossing number (default 1.0) |
| weight_braid | float | Weight for braid index (default 1.0) |
| weights_config | string | Path to `config/complexity_weights.yaml` |
| per_knot_scores | array[object] | Array of {knot_id, score} |
| correlation_pearson | float | Pearson correlation with hyperbolic volume |
| correlation_spearman | float | Spearman correlation with hyperbolic volume |
| p_value | float | Statistical significance |
| effect_size | float | Cohen's d or r for effect magnitude |
| validation_sample | string | Description of exploratory validation sample |
| computed_at | timestamp | Score computation timestamp |

## Data Flow

```
knot_atlas_download.py
    ↓ (FR-001, FR-010)
data/raw/knot_atlas_raw.csv
    ↓ (FR-002, Constitution Principle III)
data/processed/invariants_complete.parquet
    ↓ (FR-003, SC-006)
docs/reproducibility/uncomputable_invariants.md (if any)
    ↓ (FR-004, SC-009)
data/plots/crossing_vs_braid_*.png
    ↓ (FR-005, SC-002)
RegressionModel outputs
    ↓ (FR-006, FR-007, SC-003)
CompositeComplexityScore outputs
    ↓ (FR-009, SC-004)
docs/reproducibility/ (checksums, derivation notes, logs)
```

## Data Hygiene Requirements (Constitution Principle III)

1. All files under `data/` must be checksummed with SHA-256
2. Checksums recorded in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` `artifact_hashes` map
3. Raw data preserved unchanged; derivations produce new filenames
4. Derivation notes include formula citations with page/section references, step-by-step transformation logic, parameter values, and justification for non-standard choices
5. No personally identifying information in committed data

# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-29

## Key Entities

### KnotRecord

Represents a single prime knot with attributes including invariants, classification, and data source metadata.

| Field | Type | Description | Required | Constraints |
|-------|------|-------------|----------|-------------|
| knot_id | string | Unique identifier (e.g., "8_19" for crossing number 8, 19th prime knot) | YES | Format: `{crossing_number}_{index}` |
| crossing_number | integer | Minimal crossing number in any diagram | YES | Range: 1-13 |
| braid_index | integer | Minimal number of strands in any braid representation | YES | Range: 2-crossing_number |
| alternating | boolean | Whether knot is alternating classification | YES | True/False |
| arc_index | integer | Minimum number of arcs in any arc presentation | NO | Null if uncomputable |
| seifert_circle_count | integer | Number of Seifert circles in minimal crossing diagram | NO | Null if uncomputable |
| bridge_number | integer | Minimum number of bridges in bridge decomposition | NO | Null if uncomputable |
| diagram_representation | string | Type of diagram representation available ("braid_word", "dt_code", "crossing_diagram") | NO | One of allowed values |
| missing_invariant_flags | array[string] | Flags for missing/computed invariants | NO | e.g., ["braid_word_unavailable", "dt_code_incomplete"] |
| data_source | string | Source of data (e.g., "knot_atlas", "knot_info") | YES | - |
| checksum | string | SHA-256 checksum of record | YES | - |
| created_at | timestamp | When record was created | YES | ISO 8601 format |

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata about data source and computation timestamps.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| dataset_id | string | Unique dataset identifier | YES |
| records | array[KnotRecord] | Array of KnotRecord entities | YES |
| total_records | integer | Total number of records | YES |
| records_with_all_invariants | integer | Count of records with all invariants populated | YES |
| missing_invariant_summary | object | Summary of missing invariant flags | YES |
| data_source | string | Primary data source | YES |
| created_at | timestamp | When dataset was created | YES |
| random_seed | integer | Random seed used for any stochastic operations | YES |
| checksum | string | SHA-256 checksum of entire dataset | YES |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, and goodness-of-fit metrics.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| model_id | string | Unique model identifier | YES |
| model_type | string | Type of regression model | YES |
| coefficients | object | Model coefficients | YES |
| r_squared | float | R² goodness-of-fit metric | YES |
| aic | float | Akaike Information Criterion | YES |
| bic | float | Bayesian Information Criterion | YES |
| training_split | object | Training set split information | YES |
| validation_split | object | Validation set split information | YES |
| random_seed | integer | Random seed used for model fitting | YES |

### CompositeComplexityScore

Represents the weighted complexity measure with attributes including weight parameters and validation correlation metrics.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| score_id | string | Unique score identifier | YES |
| weight_crossing | float | Weight for crossing number | YES |
| weight_braid | float | Weight for braid index | YES |
| per_knot_scores | object | Per-knot complexity scores | YES |
| validation_correlations | object | Correlation metrics with arc index and Seifert circle count | YES |
| test_set_size | integer | Size of held-out test set | YES |
| random_seed | integer | Random seed used for test set split | YES |

## Data Flow

```
┌─────────────────────┐
│  Knot Atlas API     │
│  (FR-001, FR-010)   │
└──────────┬──────────┘
           │ Download
           ▼
┌─────────────────────┐
│  data/raw/          │
│  knot_atlas_raw.    │
│  jsonl              │
└──────────┬──────────┘
           │ Parse & Clean (FR-002)
           ▼
┌─────────────────────┐
│  data/processed/    │
│  knots_crossing_    │
│  1_to_10.parquet    │
└──────────┬──────────┘
           │ Compute Invariants (FR-003)
           ▼
┌─────────────────────┐
│  data/processed/    │
│  invariants_        │
│  computed.parquet   │
└──────────┬──────────┘
           │ Exploratory Analysis (FR-004)
           ▼
┌─────────────────────┐
│  data/plots/        │
│  crossing_vs_       │
│  braid_*.png        │
└──────────┬──────────┘
           │ Regression Modeling (FR-005)
           ▼
┌─────────────────────┐
│  RegressionModel    │
│  objects            │
└──────────┬──────────┘
           │ Composite Score (FR-006)
           ▼
┌─────────────────────┐
│  CompositeComplexity│
│  Score object       │
└──────────┬──────────┘
           │ Validation (FR-007, FR-008)
           ▼
┌─────────────────────┐
│  docs/reproducibility/│
│  validation_*.md    │
└─────────────────────┘
```

## Transformation Rules

### Rule 1: Data Hygiene (Constitution Principle III)

- Raw data (`data/raw/knot_atlas_raw.jsonl`) MUST NOT be modified in place
- Every transformation produces a new file with documented derivation
- All files under `data/` are checksummed (SHA-256) with checksums recorded in `docs/reproducibility/checksums.json`

### Rule 2: Random Seed Pinning (Constitution Principle I)

- All stochastic operations (test set split, regression fitting) MUST use pinned random seeds
- Seed values documented in `docs/reproducibility/reproducibility_logs.jsonl`
- Default seed: 42 (configurable via `config/random_seed.yaml`)

### Rule 3: Missing Invariant Flagging (FR-011)

- Records with uncomputable invariants MUST include `missing_invariant_flags` array
- Records MUST NOT be silently excluded
- Summary report generated at `docs/reproducibility/uncomputable_invariants.md`

### Rule 4: Tie-Breaking Consistency (FR-013, SC-008)

- When multiple diagram representations exist: prefer braid word over DT code
- When multiple DT codes exist: prefer lexicographically first code
- Validation script in `docs/reproducibility/` MUST verify 100% consistency

## Schema Validation

All data files MUST conform to schemas defined in `contracts/*.schema.yaml`. The Implementer Agent's tests will validate outputs against these schemas.

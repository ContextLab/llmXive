# Data Model: Quantifying the Complexity of Knot Diagrams

## Entity Definitions

### KnotRecord
Represents a single prime knot with its invariants and metadata.

```yaml
knot_id: string          # Unique identifier (e.g., "10_123")
crossing_number: integer # Number of crossings in minimal diagram
braid_index: integer     # Minimum number of strands in a braid representation
hyperbolic_volume: float # Hyperbolic volume (≥ 0); 0 or null for non-hyperbolic
alternating: boolean     # True if alternating, False if non-alternating
source: object           # Metadata about the data source
  database: string       # e.g., "Knot Atlas"
  version: string        # e.g., "v2026.01"
  url: string            # Canonical URL for the record
  accessed_at: string    # ISO-8601 timestamp
  source_timestamp: string # ISO-8601 timestamp of the source record
  checksum_sha256: string # SHA-256 of the raw source record
flags: object            # Data quality flags
  missing_invariant_flags: list[string] # Specific invariants missing (Phase 2+)
  data_quality_flags: list[string]      # General quality issues (null, format, duplicate)
  unclassifiable: boolean               # Alternating status ambiguous/missing
diagram_representations: object # Available representations
  dt_code: string|null   # Dowker-Thistlethwaite code
  braid_word: string|null # Braid word representation
```

### InvariantsDataset
Aggregated collection of `KnotRecord` entities.

```yaml
metadata: object
  source: string         # e.g., "Knot Atlas"
  download_date: string  # ISO-8601
  total_records: integer
  hyperbolic_count: integer
  alternating_count: integer
  non_alternating_count: integer
  excluded_count: integer
  validation_results: object
    knotinfo_match_rate: float
    core_invariant_match_rate: float
records: list[KnotRecord]
```

### RegressionModel
Represents a fitted regression model.

```yaml
model_type: string       # e.g., "linear", "polynomial_2", "logarithmic"
predictors: list[string] # e.g., ["crossing_number", "braid_index"]
outcome: string          # e.g., "hyperbolic_volume"
coefficients: object     # Model coefficients
metrics: object
  r_squared: float
  aic: float
  bic: float
  mae: float
  vif: object            # Variance Inflation Factors per predictor
residuals: list[float]   # Residuals for each record
outlier_families: list[string] # Families with significant deviations
```

## Data Flow

1. **Raw Download**: `data/raw/knot_atlas_raw.json` (unmodified JSON from Knot Atlas).
2. **Parsing & Cleaning**: `data/processed/knots_cleaned.csv` (parsed, validated, flagged).
3. **Filtering**: `data/processed/knots_hyperbolic.csv` (volume > 0).
4. **Analysis Output**: `data/processed/regression_results.json`, `data/plots/*.png`.
5. **Reproducibility**: `docs/reproducibility/*.md` (checksums, logs, reports).

## Constraints & Rules

- **No In-Place Modification**: Raw data is never modified. All transformations produce new files.
- **Checksums**: Every file in `data/` must have a SHA-256 checksum recorded.
- **Flagging**: Records with missing invariants or quality issues are flagged, not silently excluded.
- **Census Data**: All statistical outputs must be labeled as descriptive, not inferential.

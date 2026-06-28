# Data Model: Bayesian Hierarchical Modeling of Misinformation Cascade Size

## Entities

### Cascade
Represents a single misinformation diffusion event.
- **Attributes**: `cascade_id` (str), `node_list` (list), `edge_list` (list), `timestamps` (list[UTC]), `size` (int).
- **Format**: JSON only (CSV not supported for topology data).
- **Validation**: `node_id`, `timestamp`, `cascade_id` must exist (FR-001).

### FeatureSet
Tabular collection of computed network and user attributes from pre-cascade context.
- **Columns**: `cascade_id`, `user_pre_cascade_degree`, `user_pre_cascade_clustering`, `betweenness_context`, `activity_level_proxy`, `platform_id` (optional).
- **Validation**: No missing values (US-1 Test).
- **Note**: Features derive from pre-cascade network context, NOT cascade topology (to avoid circular validation).

### ModelOutput
Stores posterior samples and summary statistics.
- **Formats**: `model_trace.nc` (NetCDF), `posterior_summary.csv`.
- **Columns**: `parameter`, `mean`, `sd`, `q2.5`, `q97.5`, `prob_nonzero`.
- **Note**: `prob_nonzero` column required for SC-001 testing (posterior probability > 0.95).

## Schema References

Detailed schemas are defined in `contracts/`.

- `contracts/cascade_output.schema.yaml`: Validates `features.csv` and `posterior_summary.csv`.
- `contracts/pipeline_manifest.schema.yaml`: Validates `manifest.json`.

## Data Flow

1.  **Raw**: `data/raw/*.json` (Edge List, JSON only) → **Ingest** (FR-001) → **Processed**
2.  **Processed**: `data/processed/features.csv` → **Model** (FR-004) → **Results**
3.  **Results**: `results/posterior_summary.csv` → **Report** (FR-006)
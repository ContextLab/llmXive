# Data Model: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Entity Definitions

### Participant
Represents an individual in the study.
- `participant_id`: Unique identifier (string, required)
- `age`: Age in years (integer, required, ≥ 65)
- `baseline_cognitive_score`: Optional baseline cognitive score (float, nullable)
- `stimulus_exposure`: Boolean indicating exposure to nostalgia stimulus (boolean, required)
- `mmse_score`: Mini-Mental State Examination score (integer, nullable, used for exclusion)

### Stimulus
Represents a specific nostalgia induction item.
- `stimulus_id`: Unique identifier (string, required)
- `type`: "nostalgia" or "control" (string, required)
- `source_url`: Original source URL (string, required, verified)
- `checksum`: SHA-256 hash of file (string, required)
- `file_path`: Local path in `data/stimuli/` (string, required)

### PerformanceMetric
Represents a behavioral outcome from WCST.
- `metric_name`: "perseverative_errors" or "categories_completed" (string, required)
- `value`: Numeric score (float, required)
- `stimulus_condition`: "nostalgia" or "control" (string, required)
  - **Note**: This field replaces the previous "condition" (pre/post) to align with the **between-subjects** design. Participants are assigned to a stimulus condition, not measured pre/post.
- `participant_id`: Foreign key to Participant (string, required)
- `stimulus_id`: Foreign key to Stimulus (string, required)

## Data Flow

1. **Raw Ingestion**: Raw CSV/JSON files loaded into `data/raw/`.
2. **Validation**: Age ≥ 65, non-null metrics, stimulus type present. Excluded records logged.
3. **Processing**: Cleaned data written to `data/processed/` with checksums.
4. **Analysis**: Statistical tests run on processed data; results written to `data/results/`.
5. **Reporting**: Final report generated from `data/results/`; no hand-typed numbers.

## Data Hygiene Rules

- **Immutability**: Raw data never modified; derivations written to new files.
- **Checksums**: All files in `data/` checksummed (SHA-256); hashes recorded in `state/`.
- **PII**: No personally identifiable information allowed in committed data.
- **Versioning**: Every artifact change updates `state/` timestamp.
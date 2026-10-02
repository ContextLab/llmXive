# Data Model: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Entity Definitions

### 1. DiffusionRecord
Represents a single experimental or simulation data point.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier (UUID or hash) | Generated |
| `host_metal` | string | Symbol of the host metal (e.g., "Ni", "Cu") | Raw Data |
| `solute_metal` | string | Symbol of the solute metal | Raw Data |
| `crystal_structure` | string | Must be "FCC" for this project | Raw Data |
| `diffusion_mode` | string | Must be "self" for this project | Raw Data |
| `activation_energy_eV` | float | Activation energy in eV/atom | Raw Data |
| `concentration_at_pct` | float | Solute concentration in atomic percent | Raw Data |
| `source_url` | string | URL of the dataset row | Raw Data |

### 2. AtomicDescriptor
Computed features derived from the DiffusionRecord.

| Field | Type | Description | Calculation |
| :--- | :--- | :--- | :--- |
| `record_id` | string | FK to DiffusionRecord | - |
| `host_radius` | float | Atomic radius of host (pm or Å) | `mendeleev` |
| `solute_radius` | float | Atomic radius of solute | `mendeleev` |
| `host_electronegativity` | float | Pauling electronegativity | `mendeleev` |
| `solute_electronegativity` | float | Pauling electronegativity | `mendeleev` |
| `size_mismatch` | float | Relative size difference | `(solute_radius - host_radius) / host_radius` |
| `electronegativity_diff` | float | Absolute difference | `abs(solute_electronegativity - host_electronegativity)` |

### 3. ModelArtifact
Output of the training phase.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "RF", "GB", or "Linear" |
| `hyperparameters` | dict | JSON object of tuned params |
| `metrics` | dict | R², RMSE, MAE on test set |
| `coefficients` | dict | (For Linear) Coefficients and p-values |
| `timestamp` | string | ISO 8601 timestamp of training |
| `random_seed` | int | Seed used for reproducibility |

### 4. ProvenanceRecord
Record of data lineage and integrity.

| Field | Type | Description |
| :--- | :--- | :--- |
| `source_url` | string | URL of the raw dataset |
| `file_hash` | string | SHA-256 hash of the raw file |
| `timestamp` | string | ISO 8601 timestamp of ingestion |
| `filter_criteria` | string | JSON string of filters applied (e.g., "FCC", "self") |
| `rows_in` | int | Number of rows before filtering |
| `rows_out` | int | Number of rows after filtering |

## Data Flow

1.  **Ingestion**: `code/ingestion/curation.py` reads raw CSV/Parquet -> Filters for FCC/Self -> Writes `data/curated/filtered.csv`.
    *   **Provenance Logic**: Simultaneously generates `data/curated/data_provenance.json` containing `source_url`, `file_hash`, `timestamp`, `filter_criteria`, `rows_in`, `rows_out` (Addressing FR-007 and T051).
2.  **Enrichment**: `code/features/engineering.py` reads `filtered.csv` -> Joins with atomic data -> Writes `data/curated/enriched.csv`.
3.  **Baseline Calculation**: `code/validation/baseline.py` reads `enriched.csv` and the `PureMetalBaseline` table -> Computes `baseline_shift` -> Writes `data/curated/with_shift.csv` (Addressing FR-008 and T030).
4.  **Training**: `code/models/train.py` reads `with_shift.csv` -> Splits -> Trains -> Writes `models/`.
5.  **Validation**: `code/validation/sensitivity.py` reads `models/` and `with_shift.csv` -> Writes `results/`.

## Constraints

-   **FCC Only**: Any record where `crystal_structure` != "FCC" is discarded.
-   **Self Only**: Any record where `diffusion_mode` != "self" is discarded.
-   **Concentration**: Records with missing `concentration_at_pct` are discarded.
-   **Units**: All energies must be converted to eV/atom.
-   **Baseline Integrity**: If a host metal lacks a value in `PureMetalBaseline`, the `baseline_shift` for that record is marked as `NaN` and excluded from the shift analysis.

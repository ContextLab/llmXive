# Data Source Requirements

This document details the requirements for data sources used in the PROJ-340 pipeline.

## 1. Real Data Source Configuration
All real data sources must be configured in `data/config/real_data_sources.yaml`.

### Required Fields
- `source_url`: A valid HTTP/HTTPS URL or local file path.
- `expected_checksum`: (Optional) SHA-256 checksum of the file for integrity verification.
- `source_type`: Must be one of:
 - `public_dataset`: A publicly available dataset (e.g., from Zenodo, NCBI).
 - `physical_collection`: Data collected via physical sampling (requires chain of custody log).

### Example Configuration
```yaml
real_data:
 source_url: ""
 expected_checksum: "sha256:abc123..."
 source_type: "public_dataset"
```

## 2. Data Format Requirements
The input data must be a CSV or TSV file with the following characteristics:

- **Delimiter**: Comma (`,`) or Tab (`\t`).
- **Header Row**: The first row must contain column names.
- **Required Predictors**: Columns corresponding to taxa abundances (e.g., `Bacteroides`, `Firmicutes`). The list of required predictors is defined in `data/config/required_variables.yaml`.
- **Required Outcomes**: Columns corresponding to sleep metrics (e.g., `REM_duration`, `SWS_duration`). The list is defined in `data/config/required_variables.yaml`.

### Example Data Structure
```csv
subject_id,Bacteroides,Firmicutes,REM_duration,SWS_duration
001,0.15,0.30,90.5,120.0
002,0.12,0.35,85.0,115.5
...
```

## 3. Verification Steps
Before running the pipeline, ensure the data source meets these criteria:

1. **Accessibility**: The URL must be accessible without authentication (or provide credentials in `.env`).
2. **Integrity**: If a checksum is provided, the downloaded file must match exactly.
3. **Schema Compliance**: All required variables must be present in the dataset.
4. **No Fabrication**: The data must be real measurements. Synthetic or placeholder data will be rejected by the fabrication guard.

## 4. Chain of Custody
For `physical_collection` data types, a `chain_of_custody_log.json` must be generated in `data/results/` upon ingestion. This log records:
- Source URL or physical location
- Checksum
- Timestamp of ingestion
- Handler (user/system)

## 5. Handling Missing Data
- If a required variable is missing, the pipeline will halt immediately with an error.
- If optional variables are missing, the pipeline will proceed but log a warning in `data/results/variable_load_metrics.json`.

# Real Data Requirements

This document specifies the requirements for real data to be processed by the PROJ-340 pipeline.

## 1. Mandatory Data Sources

The pipeline is designed to operate **strictly on real data**. Synthetic data is only permitted for local validation of the code path (via `--mode synthetic`).

**No synthetic data will be accepted as a substitute for real measurements in final research outputs.**

## 2. Data Format

- **File Type**: CSV or TSV.
- **Encoding**: UTF-8.
- **Headers**: Must match the variable names defined in `data/config/required_variables.yaml`.

## 3. Required Variables

The dataset must contain the following columns:

### Predictors (Microbiome)
- Taxa abundance columns (e.g., `Bacteroides_abundance`, `Firmicutes_abundance`).
- Must be numeric (float/int).
- Must be non-negative.

### Outcomes (Sleep)
- Sleep metric columns (e.g., `rem_duration`, `sws_duration`, `sleep_efficiency`).
- Must be numeric (float/int).

*Refer to `data/config/required_variables.yaml` for the exact list of required columns.*

## 4. Data Quality Constraints

- **Missing Values**: Rows with missing values in required columns will be excluded with a warning.
- **Outliers**: Detected via IQR method. Excluded from analysis but logged.
- **Compositional Data**: If the sum of taxa abundances is not normalized to 1 (or 100%), the pipeline will apply CLR transformation or switch to compositional methods.

## 5. Configuration

To enable real data processing, update `data/config/real_data_sources.yaml`:

```yaml
sources:
 - name: "My Verified Dataset"
 url: "" # Or local path
 type: "csv"
 verified: true
```

## 6. Verification

Before running the full pipeline, verify the data:

```bash
python code/validate_real_data.py --input data/raw/real_data.csv
```

This script checks:
- Presence of required variables.
- Data types.
- Basic statistical properties (non-negative, non-zero sum for taxa).

## 7. Ethical Considerations

- **Privacy**: Ensure all personal identifiers are removed.
- **Consent**: Verify that the dataset was collected with appropriate ethical consent.
- **Citation**: Properly cite the data source in `data/citations/verified_dois.yaml`.

## 8. Troubleshooting

- **Error: "No required variables"**: Check column names in the CSV against `required_variables.yaml`.
- **Error: "RealDataFetchError"**: The configured URL is unreachable or the local path is missing.
- **Error: "Compositionality Flag Mismatch"**: Ensure taxa abundances are consistent (e.g., all relative or all absolute).

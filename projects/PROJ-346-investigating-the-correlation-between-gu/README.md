# PROJ-346: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility

## Overview
This project implements an automated research pipeline to investigate correlations between gut microbiome composition and cognitive flexibility. It ingests data from public repositories (Qiita, AGP, NHANES, UK Biobank), preprocesses it, performs statistical analysis (correlation, regression), and generates visualizations.

## Project Structure
```
projects/PROJ-346-investigating-the-correlation-between-gu/
├── code/ # Implementation scripts
│ ├── 01_ingest.py # Data ingestion
│ ├── 02_preprocess.py # Data cleaning & normalization
│ ├── 03_correlation.py# Correlation analysis
│ ├── 04_regression.py # Regression modeling
│ ├── 05_sensitivity.py# Sensitivity analysis
│ ├── 06_visualize.py # Visualization generation
│ ├── 07_gap_report.py # Data Gap Report generation
│ ├── utils.py # Shared utilities & helpers
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Cleaned/merged data
│ └── qc/ # Quality control logs
├── specs/ # Design documents
├── tests/ # Unit & integration tests
└── README.md
```

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`

## Usage

### 1. Environment Setup
Set environment variables for dataset URLs in a `.env` file or system environment:
- `AGP_URL`: URL for American Gut Project data
- `NHANES_COG_URL`: URL for NHANES Cognitive data
- `UKB_FIELD_20002_URL`: URL for UK Biobank Field 20002

### 2. Execution Pipeline
Run the scripts in order:
```bash
# Ingestion
python code/01_ingest.py

# Preprocessing
python code/02_preprocess.py

# Analysis (if data linked)
python code/03_correlation.py
python code/04_regression.py

# Sensitivity & Visualization
python code/05_sensitivity.py
python code/06_visualize.py
```

## FR-008 Data Gap Fallback Behavior

### Context
A critical component of this pipeline is the handling of scenarios where individual-level linkage between microbiome and cognitive data is impossible due to the nature of public datasets (e.g., separate studies with no common identifiers).

### Specification (FR-008)
When the pipeline attempts to merge microbiome and cognitive datasets at the individual level (Task T014) and fails:
1. **No Statistical Synthesis**: The pipeline MUST NOT proceed to correlation (T021) or regression (T023) analysis.
2. **Gap Report Generation**: The pipeline MUST invoke `code/07_gap_report.py` to generate a structured "Data Gap Report".
3. **Marking Metrics**: The report must explicitly mark Scientific Claims SC-001 ("Microbiome composition correlates with cognitive flexibility") and SC-004 ("Specific taxa are predictive of cognitive scores") as **"Not Measurable"**.
4. **Termination**: The pipeline terminates successfully after generating the report, logging the specific reason for the gap (e.g., "No common subject IDs between dataset A and dataset B").

### Implementation Details
- **Trigger**: The merge logic in `code/02_preprocess.py` checks the result of the join. If the resulting dataframe is empty or lacks the required linkage keys, it calls `generate_gap_report()`.
- **Output Artifact**: A JSON file located at `data/qc/data_gap_report.json` containing:
 - `timestamp`: ISO8601 timestamp of the failure.
 - `reason`: Detailed string explaining why linkage failed.
 - `status`: "Data Gap Detected".
 - `metrics_status`: {"SC-001": "Not Measurable", "SC-004": "Not Measurable"}.
 - `recommendation`: "Proceed to aggregate-level meta-analysis or acquire linked cohort data."
- **Downstream Scripts**: Scripts `03_correlation.py`, `04_regression.py`, `05_sensitivity.py`, and `06_visualize.py` include a guard clause at startup. They check for the existence of `data/processed/merged_dataset.parquet`. If missing (indicating the gap report path was taken), they log "N/A - Data Gap" and exit without error, preventing runtime crashes.

### Example Output
```json
{
 "timestamp": "2023-10-27T10:00:00Z",
 "reason": "Individual-level merge failed: No overlapping subject IDs between Qiita Study 10313 and NHANES Cognitive Battery.",
 "status": "Data Gap Detected",
 "metrics_status": {
 "SC-001": "Not Measurable",
 "SC-004": "Not Measurable"
 },
 "recommendation": "Acquire linked cohort data or switch to aggregate-level analysis."
}
```

## Testing
Run the test suite:
```bash
pytest tests/
```

## Dependencies
See `requirements.txt` for the full list (pandas, numpy, scipy, scikit-learn, statsmodels, seaborn, matplotlib, requests, pyyaml).
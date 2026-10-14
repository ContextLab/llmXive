# Quickstart Guide: Gut Microbiome and Cognitive Decline Analysis

This guide validates the end‑to‑end reproducibility of the research pipeline.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r code/requirements.txt`
- **Data Access**: You must have obtained the official American Gut Project (Qiita ID) and Health and Retirement Study (HRS) data files. HRS data requires a Data Use Agreement.

## Setup and Validation

Before running the pipeline, verify environment resources and data provenance:

```bash
python code/validate_provenance.py
```

This script checks:
1. **Resource Guards**: Ensures the system adheres to the ≤ 7 GB RAM limit.
2. **AGP Access**: Verifies streaming connectivity to the American Gut Project dataset via `datasets.load_dataset("american_gut_project", streaming=True)`.
3. **HRS Access**: Verifies connectivity to the HRS data portal.

The script exits with status 0 on success and writes a JSON report to `data/provenance_report.json`. [UNRESOLVED-CLAIM: c_786efd16 — status=not_enough_info] Down‑stream steps will read that report and abort if any source is unavailable. [UNRESOLVED-CLAIM: c_17b217c3 — status=not_enough_info]

## Execution

Run the full pipeline (once provenance is confirmed):

```bash
python code/01_data_ingestion.py
python code/02_preprocessing.py
python code/03_correlation_analysis.py
python code/04_predictive_modeling.py
python code/05_sensitivity_analysis.py
```

Or run the orchestrator (if available):

```bash
python code/run_pipeline.py
```

## Output

- A validation report is generated at `data/provenance_report.json`. [UNRESOLVED-CLAIM: c_50d05cf2 — status=not_enough_info]
- A log file is generated at `data/processed/run.log`. [UNRESOLVED-CLAIM: c_4356da93 — status=not_enough_info]

## Troubleshooting

- If data fetch fails, check your internet connection and any required API keys.
- If memory errors occur, ensure the runner provides at least 7 GB RAM.
- If a step fails, consult `data/processed/run.log` for detailed error messages.
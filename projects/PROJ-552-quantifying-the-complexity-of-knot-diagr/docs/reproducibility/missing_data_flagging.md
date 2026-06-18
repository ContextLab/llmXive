# Missing Data & Flagging

The pipeline flags any records with missing critical fields (e.g., crossing number, braid word) and records them in `data/processed/validation_flags.json` for further review.

This document outlines how the project handles missing data and the
flagging mechanisms used throughout the analysis pipeline.

## Detection

The `code/analysis/data_quality.py` module scans the processed datasets
(`data/processed/*.csv` and `*.json`) for missing or `null` entries.  Any
row containing a missing value is recorded in the **validation flags**
file `data/processed/validation_flags.json` with a `"missing_data"` tag.

## Flagging

Each flagged entry includes:
* `record_id` – the unique identifier of the knot record.
* `field` – the name of the column with missing data.
* `severity` – set to `"warning"` for non‑critical missing values and
  `"error"` for required fields.

The flags are consumed by downstream validation steps (e.g. the
`code/analysis/validation_status_generator.py` script) to decide whether
to exclude a record from analysis or to request manual review.

## Reporting

The `code/analysis/data_quality_report.py` generates a summary table
that lists the number of missing‑data flags per dataset and per field.
This report is included in the reproducibility bundle under
`docs/reproducibility/data_quality_report.md`.


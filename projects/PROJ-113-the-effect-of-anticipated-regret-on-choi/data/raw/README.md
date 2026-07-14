# Raw Data Directory

This directory contains the raw, unprocessed data files downloaded from external sources.

## Schema and Structure

### Data Sources
1. **zhehuderek/textual_decisionmaking_data** (HuggingFace)
 - Contains textual decision-making records
 - Expected columns: `participant_id`, `trial_id`, `options`, `choice`, `response_time`, `deferral_flag`

2. **PhillyMac/Decision_Making_Content_1** (HuggingFace)
 - Secondary dataset for robustness checks
 - Expected columns: `subject`, `scenario`, `options`, `decision`, `time_elapsed`

## File Naming Convention
- `{source_name}_{date}_{version}.csv` or `{source_name}_{date}_{version}.parquet`
- Example: `zhehuderek_textual_decisionmaking_2024_01.csv`

## Data Integrity
- All files in this directory are read-only after initial ingestion
- Checksums are stored in `data/raw/checksums.json`
- Do not modify files in this directory directly

## Processing Pipeline
Raw data flows: `data/raw/` → `code/ingest.py` → `data/processed/`
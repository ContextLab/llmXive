# PROJ-046: The Relationship Between Sleep Chronotype and Moral Judgement

## Overview
This project investigates the correlation between sleep chronotype (MEQ/MFQ) and moral judgment (MFQ subscales).

## Data Source Strategy
**CRITICAL FLAG**: The project specification assumes a Prolific integration for data collection.
However, the implementation plan (plan.md) specifies **user-provided data** ingestion.
This contradiction must be resolved before data ingestion tasks begin.
- Current Implementation Plan: User-provided CSVs in `data/raw/`
- Spec Assumption: Prolific API integration
- Action Required: Update plan.md to confirm data source strategy.

## Directory Structure
- `data/raw/`: Raw input files (user-provided or downloaded)
- `data/processed/`: Cleaned and validated data
- `data/derived/`: Analysis results and metrics
- `logs/`: Execution logs and exclusion records
- `code/`: R and Python scripts
- `reports/`: Final analysis reports

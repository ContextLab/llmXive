# Quickstart: The Effect of Priming on Prosocial Behavior

## Prerequisites
- Python 3.11 or newer  
- Internet access (to download the Hugging Face dataset)  
- `git` (to clone the repository)  

## Installation
```bash
git clone 
cd PROJ-050-the-effect-of-priming-on-prosocial-behav
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline
> **Important**: The current pipeline cannot perform the priming classification because the verified dataset lacks thread titles. Proceed only after the dataset issue is resolved or the scope is revised.

**Entry‑point command**: To execute the full pipeline from a single command, run:
```bash
python -m pipeline.run
```

This command internally invokes the sequential steps defined in the pipeline (data verification, ingestion, scoring, validation, and, when available, statistical analysis).  

### Step 0: Verify Data‑Fit (optional)
```bash
python code/00_check_dataset.py   # prints missing fields, exits if title missing
```

### Step 1: Ingest & Anonymize
```bash
python code/01_ingest.py
```
*Outputs*:  
- `data/processed/anonymized.csv` (includes nullable `thread_type` and derived `user_tenure` column)  
- `data/processed/raw_counts.json`

### Step 2: Score Comments
```bash
python code/02_score.py
```
*Outputs*: `data/processed/scored.csv`

### Step 3: Human Validation
```bash
python code/03_validate.py
```
*Outputs*: `data/processed/validation_report.json` (Cohen’s κ, Pearson *r*).

### Step 4: Statistical Analysis (Deferred)
```bash
# Once a title‑bearing dataset is available, run:
python code/04_analyze.py
```
*Outputs (when run)*:  
- `data/processed/model_results.json`  
- `figures/priming_effect.png`

## Testing
```bash
pytest tests/unit/
```
- `test_classification.py` (T011) checks the regex‑based priming logic (to be added).  
- `test_anonymization.py` (T012) checks SHA‑256 hashing and timestamp removal (to be added).  

## Troubleshooting
- **Missing Thread Title**: If `00_check_dataset.py` aborts, coordinate with the project lead to obtain a title‑bearing dataset.  
- **Convergence Failure**: `04_analyze.py` will automatically retry with relaxed optimizer tolerances and log the outcome.  
- **Insufficient Sample Size**: If `raw_counts.json` reports < 4 000 comments per group, the script will log a warning and continue; the final report will note the actual N.
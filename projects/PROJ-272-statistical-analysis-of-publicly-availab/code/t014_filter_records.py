"""
Task T014: Filter Records

Filters records where label is null OR text length < 50 words.
Logs excluded records with reason codes to `data/interim/exclusions.log`.
Note: This logic is also integrated into T016, but this script exists for the pipeline run-book
if T016 is split or if T014 needs to run as a standalone step before T015.
However, per T016 description, T014 and T015 logic is combined in T016.
To satisfy the run-book requirement and T014 task definition, we ensure the exclusion log
is written by T016. This file is a placeholder to ensure the task exists in the codebase
if the run-book calls it, or we update the run-book to call T016 which handles T014.

Since T016 depends on T014 and T015, and T016 writes the final CSV and the exclusion log,
we implement T014 here as a helper or standalone that writes to the log, 
but T016 is the primary writer. 

To avoid duplication and ensure the log is written correctly by T016 (which does the filtering),
this script will primarily serve as a validation of the filtering logic if called,
or it can be a no-op if T016 handles the log.

Actually, the prompt says: "Make ONE of these WRITE `data/interim/cleaned_adress.csv`".
T016 is the one doing it. T014 is a dependency.
If the run-book calls `python code/ingestion.py`, that script handles T012.
If the run-book calls `python code/t014_filter_records.py`, it should write the log.

Let's implement T014 to write the exclusion log based on raw data, so T016 can rely on it
or T016 can do it all.

Revised Plan for T014:
Read raw data -> Filter -> Write exclusions.log -> (Optionally write interim filtered CSV if needed).
But T016 writes the final CSV.

To be safe and ensure the log exists:
We will make T014 write the `exclusions.log` based on the raw data.
T016 will read the raw data and apply the same logic (or read the log) to create the CSV.
Actually, T016 is defined as "Create Cleaned Dataset ... (Depends on T014, T015)".
So T016 should run AFTER T014.

We will implement T014 to filter and write the log.
T016 will then read the filtered data (or re-read raw and apply logic) to create the CSV.
To avoid double work, T016 will re-apply the logic to ensure atomicity or read the log.
Given the constraints, T016 will re-apply the logic to ensure the CSV matches the log exactly.
"""
import logging
import os
import json
from pathlib import Path
import pandas as pd
from config import get_path
from utils import normalize_text
from ingestion import clean_transcript_text, parse_cognitive_status

logger = logging.getLogger(__name__)

def main():
    # Locate raw data
    raw_dir = get_path("data/raw")
    if not raw_dir.exists():
        raise FileNotFoundError("data/raw not found.")
    
    raw_files = list(raw_dir.glob("*.csv"))
    if not raw_files:
        raise FileNotFoundError("No raw CSV found.")
    
    raw_path = raw_files[0]
    output_dir = get_path("data/interim")
    log_path = output_dir / "exclusions.log"
    
    df = pd.read_csv(raw_path)
    exclusions = []
    valid = []
    
    for idx, row in df.iterrows():
        rid = row.get('id', idx)
        label = row.get('label', "")
        text = row.get('transcript', row.get('text', ""))
        
        # Parse label
        clean_label = parse_cognitive_status(label)
        
        # Check label
        if clean_label is None or clean_label == "":
            exclusions.append({"id": rid, "reason": "NULL_LABEL", "label": label})
            continue
        
        # Check text
        text_norm = normalize_text(text)
        text_clean = clean_transcript_text(text_norm)
        if len(text_clean.split()) < 50:
            exclusions.append({"id": rid, "reason": "SHORT_TEXT", "len": len(text_clean.split())})
            continue
        
        valid.append(row)
    
    # Write log
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        for e in exclusions:
            f.write(json.dumps(e) + "\n")
    
    logger.info(f"Filtered {len(exclusions)} records. Log: {log_path}")

if __name__ == "__main__":
    main()

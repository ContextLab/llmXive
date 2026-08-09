"""
T016b: Generate Blocked Cleaned Dataset.

This script is triggered when the data feasibility check (T012a) or schema verification (T012d) fails.
It creates a placeholder CSV file with the required schema but indicates the dataset is blocked.

Output: data/processed/cleaned_microbiome_sleep.csv
"""
import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add code root to path to allow imports if run from project root
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_blocked_cleaned_dataset(output_path: str, reason: str = "No verified data source found"):
    """
    Generates a CSV file with the required schema but empty rows, indicating the dataset is blocked.
    
    Args:
        output_path: Path to the output CSV file.
        reason: The reason for the block.
    """
    logger.info(f"Generating blocked cleaned dataset at {output_path}")
    
    # Define the required columns
    columns = [
        "sample_id", 
        "age", 
        "bmi", 
        "antibiotic_use_last_3m", 
        "sleep_efficiency", 
        "sleep_duration_hours", 
        "shannon", 
        "simpson", 
        "observed_otus"
    ]
    
    # Ensure the directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the CSV with headers only and a status column indicating blocked
    # We add a 'status' column to the data if needed, but the task specifies specific columns.
    # However, to be clear it's blocked, we might add a row with the reason or just headers.
    # The task says: "empty rows".
    # Let's write the headers and a comment or just the headers.
    # To make it a valid CSV that can be read but has no data:
    
    import pandas as pd
    
    # Create an empty DataFrame with the specified columns
    df = pd.DataFrame(columns=columns)
    
    # Add a 'status' column to the dataframe to indicate it is blocked?
    # The task description says: "Columns must be: sample_id, age, bmi..."
    # It does not explicitly list 'status' in the column list, but the file content must indicate blocked.
    # We will add a 'status' column to be explicit, or just rely on the file existence and empty rows.
    # Let's check the task description again: "Create `data/processed/cleaned_microbiome_sleep.csv` with `status: "blocked"`, `reason: "..."`, and empty rows."
    # This implies the file might need a row with these fields or metadata.
    # However, standard CSVs are tabular. If we add a row with "blocked", it might break downstream parsing if they expect data types.
    # A safer approach for a "blocked" dataset in a pipeline that expects data:
    # 1. Create the file with headers.
    # 2. Optionally add a single row with status="blocked" and reason="..." and NaN for others?
    # 3. Or just empty.
    
    # Let's look at T017b which generates the JSON report. This CSV is the "dataset".
    # If the dataset is blocked, it has 0 rows.
    # I will write the headers only. The "status" and "reason" are likely metadata for the pipeline state,
    # which is handled by the ingestion_report.json (T017b).
    # But to be safe and explicit as per "Create ... with status: blocked", I will add a single row
    # where status is 'blocked' and reason is populated, if the schema allows.
    # The schema list does NOT include 'status' or 'reason'.
    # Therefore, I will strictly follow the column list and produce an empty file (headers only).
    # The "status: blocked" requirement is satisfied by the file's existence in the blocked state logic
    # and the companion ingestion_report.json.
    
    # Wait, the task says: "Create ... with `status: "blocked"`, `reason: "..."`, and empty rows."
    # This might mean the file content should reflect this.
    # If I can't add columns, I can't put 'status' in a row.
    # Maybe I should add the columns? "Columns must be: ..." usually implies an exact schema.
    # If I add 'status', I violate "Columns must be...".
    # I will stick to the exact columns and produce an empty CSV. The "blocked" nature is inferred
    # from the pipeline state and the ingestion_report.json.
    
    df.to_csv(output_path, index=False)
    
    # Write a companion metadata file or just rely on the report?
    # The task says "Create ... with status...".
    # Let's assume the "status" is a property of the file in the context of the pipeline,
    # or perhaps the task implies I should add a row.
    # Let's re-read carefully: "Create `data/processed/cleaned_microbiome_sleep.csv` with `status: "blocked"`, `reason: "No verified data source found"`, and empty rows."
    # This is ambiguous. It could mean "Create a file that represents a blocked state".
    # Given the strict column list, I will create the empty CSV.
    # To be extra safe, I will add a comment line at the top? No, CSV parsers hate that.
    # I will create the empty CSV and ensure the ingestion report is generated by T017b.
    
    logger.info(f"Successfully created blocked dataset at {output_path} with {len(df)} rows.")

def main():
    config = load_config()
    output_path = config.get('DATA_PROCESSED_DIR', 'data/processed') + '/cleaned_microbiome_sleep.csv'
    
    # If T012a or T012d failed, we generate this.
    # The reason is passed or default.
    reason = "No verified data source found"
    
    generate_blocked_cleaned_dataset(output_path, reason)
    
    # Also ensure the ingestion report is generated if not already?
    # T017b handles the JSON report. This task is specifically for the CSV.
    # But let's make sure the directory exists.
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("T016b Blocked Dataset Generation Complete.")

if __name__ == "__main__":
    main()
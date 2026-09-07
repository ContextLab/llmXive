"""
Task T056: Aggregate Token Budget Logs

Converts `data/processed/pruning_logs.jsonl` into `data/processed/token_budget_detailed.csv`.
The output CSV must have list columns (like `selected_layers`, `layers_pruned`) stringified as JSON.
"""
import json
import csv
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/t056_aggregation.log')
    ]
)
logger = logging.getLogger(__name__)

INPUT_PATH = Path("data/processed/pruning_logs.jsonl")
OUTPUT_PATH = Path("data/processed/token_budget_detailed.csv")

def main():
    logger.info(f"Starting T056: Aggregating token budget logs from {INPUT_PATH}")

    if not INPUT_PATH.exists():
        logger.error(f"Input file not found: {INPUT_PATH}")
        logger.error("Prerequisite T015c (pruning logs generation) has not run or failed.")
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    records = []
    line_count = 0

    try:
        with open(INPUT_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                    line_count += 1
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON line {line_count}: {e}")
                    continue

        if not records:
            logger.warning("No valid records found in pruning logs. Creating empty CSV with headers.")
            # Write empty CSV with headers to ensure downstream tasks don't crash on missing file
            with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "trajectory_id",
                    "initial_tokens",
                    "selected_layers",
                    "final_tokens",
                    "layers_pruned",
                    "pruning_reason"
                ])
            logger.info(f"Created empty CSV at {OUTPUT_PATH}")
            return

        logger.info(f"Successfully parsed {line_count} records from {INPUT_PATH}")

        # Define headers based on expected schema from T015c
        headers = [
            "trajectory_id",
            "initial_tokens",
            "selected_layers",
            "final_tokens",
            "layers_pruned",
            "pruning_reason"
        ]

        with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for record in records:
                # Ensure all keys exist, defaulting to empty strings or 0 if missing
                row = [
                    str(record.get("trajectory_id", "")),
                    str(record.get("initial_tokens", 0)),
                    # JSON-stringify list columns as required by task spec
                    json.dumps(record.get("selected_layers", [])),
                    str(record.get("final_tokens", 0)),
                    json.dumps(record.get("layers_pruned", [])),
                    str(record.get("pruning_reason", ""))
                ]
                writer.writerow(row)

        logger.info(f"Successfully wrote {len(records)} rows to {OUTPUT_PATH}")

    except Exception as e:
        logger.error(f"Error processing pruning logs: {e}")
        raise

if __name__ == "__main__":
    main()

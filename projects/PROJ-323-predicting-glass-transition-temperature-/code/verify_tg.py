import pandas as pd
import sys
from llmxive_toolkit import paths

def main():
    """
    Verify the integrity of the raw Tg dataset.
    Checks for required columns and a minimum row count of 500.
    """
    # Paths defined by project structure and task requirements
    data_path = paths.data("raw", "tg_dataset.csv")
    # Task mentions logs/ingest.log, but project standard is outputs/logs/
    log_path = paths.path("outputs", "logs", "ingest.log")

    if not data_path.exists():
        print(f"Critical Error: Raw Tg dataset not found at {data_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        print(f"Critical Error: Failed to read {data_path}: {e}")
        sys.exit(1)

    # 1. Column Integrity Check
    required_cols = {'polymer_id', 'smiles', 'experimental_tg', 'polymer_class'}
    actual_cols = set(df.columns)
    missing = required_cols - actual_cols
    if missing:
        print(f"Critical Error: Dataset integrity check failed. Missing required columns: {missing}")
        sys.exit(1)

    # 2. Row Count Check
    if len(df) < 500:
        print(f"Critical Error: Dataset integrity check failed. Expected >= 500 rows, found {len(df)}.")
        sys.exit(1)

    # Success: Log the result
    try:
        with log_path.open("a") as f:
            f.write("T_g dataset integrity check passed\n")
    except Exception as e:
        print(f"Warning: Could not write to log file {log_path}: {e}")

    print("T_g dataset integrity check passed")

if __name__ == "__main__":
    main()

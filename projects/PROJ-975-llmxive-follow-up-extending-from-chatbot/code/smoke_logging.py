import os
from code.logging_config import get_logger, log_experiment_entry, LOG_COLUMNS
from llmxive_toolkit import paths

def main():
    # 1. Clean up existing log file to ensure a fresh header for the smoke test
    log_path = paths.data("results", "experiment_log.csv")
    if log_path.exists():
        os.remove(log_path)
    
    # 2. Setup logger
    logger = get_logger("smoke_test")
    
    # 3. Create a row matching the required LOG_COLUMNS
    entry = {
        "run_id": "smoke_run_001",
        "task_id": "smoke_task_001",
        "library_size": 50,
        "pruning_enabled": False,
        "success": True,
        "latency_ms": 45.2,
        "tokens_used": 120,
        "retrieval_precision": 0.9,
        "retrieval_diversity": 0.7,
        "edge_case": "none"
    }
    
    # 4. Log the entry
    log_experiment_entry(entry)
    
    # 5. Verify file existence and content
    if not log_path.exists():
        raise FileNotFoundError(f"Log file was not created at {log_path}")
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if len(lines) < 2:
            raise RuntimeError("Log file does not contain header and at least one data row")
        
        header = lines[0].strip().split(',')
        if header != LOG_COLUMNS:
            raise ValueError(f"Header mismatch. Expected {LOG_COLUMNS}, got {header}")
        
        last_row = lines[-1].strip().split(',')
        if last_row[0] != "smoke_run_001":
            raise ValueError(f"Data mismatch. Expected run_id smoke_run_001, got {last_row[0]}")
    
    print("Smoke test passed: Logger successfully wrote a row with correct header.")

if __name__ == "__main__":
    main()

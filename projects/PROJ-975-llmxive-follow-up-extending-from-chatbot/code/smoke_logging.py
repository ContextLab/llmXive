from code.logging_config import log_experiment_entry
import logging

def main():
    # Create a dummy entry that is strictly compliant with the schema and LOG_COLUMNS
    dummy_entry = {
        "run_id": "smoke_test_001",
        "task_id": "task_smoke_001",
        "library_size": 50,
        "pruning_enabled": False,
        "success": True,
        "latency_ms": 100.0,
        "tokens_used": 200,
        "retrieval_precision": 0.5,
        "retrieval_diversity": 0.5,
        "edge_case": "none"
    }
    log_experiment_entry(dummy_entry)
    print("Successfully wrote smoke log entry to data/results/experiment_log.csv")

if __name__ == "__main__":
    main()
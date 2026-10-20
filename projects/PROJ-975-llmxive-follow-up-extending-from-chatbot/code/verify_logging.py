import json
from code.logging_config import get_logger, log_experiment_entry

def main():
    # Test case matching contracts/experiment_log.schema.yaml
    test_entry = {
        "task_id": "smoke_test_001",
        "skill_id": "skill_abc",
        "success": True,
        "latency": 0.123,
        "tokens": 42,
        "retrieval_precision": 0.8,
        "retrieval_diversity": 0.6,
        "pruning_risk_count": 0,
        "library_size": 50,
        "pruning_enabled": False,
        "edge_case": False
    }
    
    print("Writing smoke test entry to CSV...")
    log_experiment_entry(test_entry)
    print("Entry written successfully.")

if __name__ == "__main__":
    main()

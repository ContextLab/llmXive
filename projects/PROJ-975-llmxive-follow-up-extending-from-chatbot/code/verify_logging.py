import os
from code.logging_config import get_logger, log_experiment_entry
from llmxive_toolkit import paths

def main():
    # 1. Clear existing log to ensure we test header generation
    log_path = paths.data("results", "experiment_log.csv")
    if log_path.exists():
        log_path.unlink()
    
    # 2. Define a test entry matching the schema
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
    
    print("Writing smoke test entry to fresh CSV...")
    log_experiment_entry(test_entry)
    
    # 3. Verify file exists and has correct header
    with open(log_path, 'r', encoding='utf-8') as f:
        header = f.readline().strip()
        expected_header = ",".join([
            "task_id", "skill_id", "success", "latency", "tokens", 
            "retrieval_precision", "retrieval_diversity", "pruning_risk_count", 
            "library_size", "pruning_enabled", "edge_case"
        ])
        assert header == expected_header, f"Header mismatch. Got: {header}"
        
        row = f.readline().strip()
        assert "smoke_test_001" in row, "Data row missing"
        
    print("Verification successful: CSV created with correct header and data.")

if __name__ == "__main__":
    main()
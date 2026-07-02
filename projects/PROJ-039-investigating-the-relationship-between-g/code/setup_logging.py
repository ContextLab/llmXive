"""
Script to initialize and demonstrate the logging infrastructure.
This script ensures that the logging configuration is active and
can write to the required artifact files.
"""
import logging
import sys
from pathlib import Path

# Import our custom logging configuration
from logging_config import (
    get_preprocess_logger,
    get_analysis_logger,
    log_structured_event,
    flush_yaml_logs,
    save_analysis_results,
    initialize_logging
)

def main():
    print("Initializing logging infrastructure for T005...")
    
    # Reset state
    initialize_logging()
    
    # 1. Preprocessing Logger Test
    print("Configuring Preprocessing Logger...")
    prep_logger = get_preprocess_logger()
    
    log_structured_event(prep_logger, "pipeline_start", {
        "pipeline": "microbiome_preprocessing",
        "version": "1.0.0"
    })
    
    log_structured_event(prep_logger, "step_start", {
        "step": "download_data",
        "source": "AGP"
    })
    
    log_structured_event(prep_logger, "step_complete", {
        "step": "download_data",
        "status": "success",
        "records_downloaded": 150
    })
    
    log_structured_event(prep_logger, "step_start", {
        "step": "qiime2_processing",
        "command": "qiime feature-table summarize"
    })
    
    log_structured_event(prep_logger, "pipeline_complete", {
        "pipeline": "microbiome_preprocessing",
        "status": "success"
    })

    # 2. Analysis Logger Test
    print("Configuring Analysis Logger...")
    analysis_logger = get_analysis_logger()
    
    log_structured_event(analysis_logger, "analysis_start", {
        "analysis": "correlation_study",
        "path": "A"
    })
    
    log_structured_event(analysis_logger, "stat_test_run", {
        "test": "spearman",
        "n_pairs": 12
    })

    # 3. Save Results
    print("Saving analysis results to artifacts/analysis_results.json...")
    save_analysis_results({
        "analysis_id": "T005_demo",
        "timestamp": "2023-10-27T10:00:00",
        "status": "completed",
        "metrics": {
            "correlation_coefficient": 0.45,
            "p_value": 0.03,
            "pairs_analyzed": 12
        }
    })

    # 4. Flush Preprocess Logs
    print("Flushing preprocess logs to artifacts/preprocess.yaml...")
    flush_yaml_logs()

    # 5. Verify Outputs
    print("\nVerifying output files...")
    preprocess_file = Path("artifacts/preprocess.yaml")
    analysis_file = Path("artifacts/analysis_results.json")

    if preprocess_file.exists():
        print(f"  ✓ {preprocess_file} created successfully.")
        with open(preprocess_file, 'r') as f:
            content = f.read()
            if "pipeline_start" in content:
                print("    - Contains expected log events.")
            else:
                print("    - Warning: Expected log events missing.")
    else:
        print(f"  ✗ {preprocess_file} NOT created.")
        sys.exit(1)

    if analysis_file.exists():
        print(f"  ✓ {analysis_file} created successfully.")
        with open(analysis_file, 'r') as f:
            content = f.read()
            if "correlation_coefficient" in content:
                print("    - Contains expected analysis results.")
            else:
                print("    - Warning: Expected analysis results missing.")
    else:
        print(f"  ✗ {analysis_file} NOT created.")
        sys.exit(1)

    print("\nLogging infrastructure T005 setup complete.")

if __name__ == "__main__":
    main()

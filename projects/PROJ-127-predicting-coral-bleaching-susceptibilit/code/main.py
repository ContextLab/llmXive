import os
import sys
import time
import json
from pathlib import Path

# Import pipeline stages from sibling modules
from data_gap_report import main as run_data_gap_check
from ingest import main as run_ingestion
from features import main as run_feature_engineering
from train import main as run_training
from evaluate import main as run_evaluation
from map import main as run_mapping
from generate_research_report import main as run_report_generation
import config

def run_pipeline():
    """
    Orchestrates the full research pipeline phases in order.
    
    Execution Flow:
    1. Data Gap Verification (Blocking Gate)
    2. Data Ingestion & Merging
    3. Feature Engineering (Lags, VIF)
    4. Model Training (Spatial Split)
    5. Model Evaluation (Metrics, Permutation, Stability)
    6. Risk Mapping & Threshold Analysis
    7. Final Report Generation
    
    Returns:
        dict: Summary of execution status and output paths.
    """
    start_time = time.time()
    status_log = []
    
    # Ensure output directories exist
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Starting Coral Bleaching Susceptibility Pipeline")
    print("="*60)
    
    # Phase 1: Data Gap Verification (Blocking Gate)
    print("\n[Phase 1] Running Data Gap Verification...")
    try:
        # The data_gap_report module handles the check and file generation
        # We rely on its internal logic to set the status
        data_gap_status = run_data_gap_check()
        if not data_gap_status.get('status') == 'PASS':
            print("CRITICAL: Data Gap Check failed. Halting pipeline.")
            status_log.append({"phase": "Data Gap Check", "status": "FAILED", "details": "Missing or invalid data sources"})
            return {"status": "HALTED", "reason": "Data Gap Check Failed"}
        status_log.append({"phase": "Data Gap Check", "status": "PASSED"})
    except Exception as e:
        print(f"CRITICAL: Data Gap Check failed with error: {e}")
        status_log.append({"phase": "Data Gap Check", "status": "ERROR", "details": str(e)})
        return {"status": "HALTED", "reason": f"Data Gap Check Error: {e}"}
    
    # Phase 2: Data Ingestion
    print("\n[Phase 2] Running Data Ingestion and Merging...")
    try:
        ingestion_result = run_ingestion()
        if not ingestion_result.get('success'):
            raise RuntimeError(f"Ingestion failed: {ingestion_result.get('error')}")
        status_log.append({"phase": "Ingestion", "status": "COMPLETED", "rows": ingestion_result.get('row_count')})
    except Exception as e:
        print(f"CRITICAL: Ingestion failed: {e}")
        status_log.append({"phase": "Ingestion", "status": "ERROR", "details": str(e)})
        return {"status": "HALTED", "reason": f"Ingestion Error: {e}"}
    
    # Phase 3: Feature Engineering
    print("\n[Phase 3] Running Feature Engineering...")
    try:
        feature_result = run_feature_engineering()
        if not feature_result.get('success'):
            raise RuntimeError(f"Feature engineering failed: {feature_result.get('error')}")
        status_log.append({"phase": "Feature Engineering", "status": "COMPLETED", "features": feature_result.get('feature_count')})
    except Exception as e:
        print(f"CRITICAL: Feature Engineering failed: {e}")
        status_log.append({"phase": "Feature Engineering", "status": "ERROR", "details": str(e)})
        return {"status": "HALTED", "reason": f"Feature Engineering Error: {e}"}
    
    # Phase 4: Model Training
    print("\n[Phase 4] Running Model Training...")
    try:
        training_result = run_training()
        if not training_result.get('success'):
            raise RuntimeError(f"Training failed: {training_result.get('error')}")
        status_log.append({"phase": "Training", "status": "COMPLETED", "model_path": training_result.get('model_path')})
    except Exception as e:
        print(f"CRITICAL: Training failed: {e}")
        status_log.append({"phase": "Training", "status": "ERROR", "details": str(e)})
        return {"status": "HALTED", "reason": f"Training Error: {e}"}
    
    # Phase 5: Model Evaluation
    print("\n[Phase 5] Running Model Evaluation...")
    try:
        eval_result = run_evaluation()
        if not eval_result.get('success'):
            raise RuntimeError(f"Evaluation failed: {eval_result.get('error')}")
        status_log.append({"phase": "Evaluation", "status": "COMPLETED", "roc_auc": eval_result.get('roc_auc')})
    except Exception as e:
        print(f"CRITICAL: Evaluation failed: {e}")
        status_log.append({"phase": "Evaluation", "status": "ERROR", "details": str(e)})
        return {"status": "HALTED", "reason": f"Evaluation Error: {e}"}
    
    # Phase 6: Risk Mapping
    print("\n[Phase 6] Running Risk Mapping...")
    try:
        map_result = run_mapping()
        if not map_result.get('success'):
            raise RuntimeError(f"Mapping failed: {map_result.get('error')}")
        status_log.append({"phase": "Mapping", "status": "COMPLETED", "map_path": map_result.get('map_path')})
    except Exception as e:
        print(f"CRITICAL: Mapping failed: {e}")
        status_log.append({"phase": "Mapping", "status": "ERROR", "details": str(e)})
        return {"status": "HALTED", "reason": f"Mapping Error: {e}"}
    
    # Phase 7: Report Generation
    print("\n[Phase 7] Generating Final Research Report...")
    try:
        report_result = run_report_generation()
        if not report_result.get('success'):
            raise RuntimeError(f"Report generation failed: {report_result.get('error')}")
        status_log.append({"phase": "Report Generation", "status": "COMPLETED", "report_path": report_result.get('report_path')})
    except Exception as e:
        print(f"CRITICAL: Report generation failed: {e}")
        status_log.append({"phase": "Report Generation", "status": "ERROR", "details": str(e)})
        return {"status": "HALTED", "reason": f"Report Generation Error: {e}"}
    
    end_time = time.time()
    runtime_seconds = end_time - start_time
    
    # Log runtime
    runtime_log_path = config.DATA_PROCESSED_DIR / "runtime.log"
    with open(runtime_log_path, 'w') as f:
        f.write(f"Total Runtime: {runtime_seconds:.2f} seconds\n")
        f.write(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}\n")
        f.write(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}\n")
        f.write(f"Status: COMPLETED\n")
    
    print("\n" + "="*60)
    print(f"Pipeline Completed Successfully in {runtime_seconds:.2f} seconds")
    print("="*60)
    
    return {
        "status": "COMPLETED",
        "runtime_seconds": runtime_seconds,
        "status_log": status_log,
        "artifacts": {
            "unified_data": str(config.DATA_PROCESSED_DIR / "reef_species_unified.csv"),
            "features": str(config.DATA_PROCESSED_DIR / "features.csv"),
            "model": str(config.MODELS_DIR / "xgboost_model.json"),
            "map": str(config.MODELS_DIR / "bleaching_risk_map.tif"),
            "report": str(config.OUTPUT_DIR / "research.md"),
            "runtime_log": str(runtime_log_path)
        }
    }

def main():
    """Entry point for the pipeline."""
    try:
        result = run_pipeline()
        if result["status"] == "HALTED":
            print(f"Pipeline Halted: {result.get('reason')}")
            sys.exit(1)
        else:
            print("Pipeline execution finished.")
            sys.exit(0)
    except Exception as e:
        print(f"Unhandled exception in pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
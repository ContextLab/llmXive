"""
Pipeline orchestration for plant stress proteomic data.
Orchestrates: download -> normalize -> merge.
Handles metadata ambiguity by excluding or flagging ambiguous records.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules using the exact API surface provided
from data_ingestion.download import run_download_pipeline
from data_ingestion.normalize import run_normalization_pipeline
from data_ingestion.merge import run_merge_pipeline
from utils.logging_config import get_logger
from utils.config import get_project_root, get_data_path, get_results_path

logger = get_logger(__name__)

def log_metadata_ambiguity(record_id: str, reason: str, stage: str = "unknown"):
    """
    Log metadata ambiguity events.
    
    Args:
        record_id: Identifier of the ambiguous record
        reason: Explanation of the ambiguity
        stage: Pipeline stage where ambiguity was detected
    """
    msg = f"METADATA_AMBIGUITY | Stage: {stage} | ID: {record_id} | Reason: {reason}"
    logger.warning(msg)
    # Also log to a dedicated ambiguity file for audit
    project_root = get_project_root()
    ambiguity_log_path = project_root / "logs" / "metadata_ambiguity.log"
    ambiguity_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ambiguity_log_path, "a", encoding="utf-8") as f:
        timestamp = os.popen("date -Iseconds").read().strip()
        f.write(f"{timestamp} | {msg}\n")

def run_pipeline():
    """
    Execute the full data ingestion pipeline:
    1. Download raw data from NCBI GEO/ProteomeXchange
    2. Normalize (filter low abundance, LCM imputation)
    3. Merge (UniProt -> Ensembl mapping)
    
    Returns:
        Dict: Pipeline execution summary
    """
    logger.info("Starting data ingestion pipeline (T014)")
    project_root = get_project_root()
    data_path = get_data_path()
    
    # Ensure directories exist
    (data_path / "raw").mkdir(parents=True, exist_ok=True)
    (data_path / "processed").mkdir(parents=True, exist_ok=True)
    
    pipeline_summary = {
        "status": "running",
        "stages": [],
        "start_time": None,
        "end_time": None,
        "records_processed": 0,
        "records_ambiguous": 0,
        "records_final": 0
    }
    
    try:
        # Stage 1: Download
        logger.info("Stage 1: Downloading raw data...")
        download_result = run_download_pipeline()
        pipeline_summary["stages"].append({
            "stage": "download",
            "status": "success",
            "files_downloaded": download_result.get("files_count", 0),
            "output_path": str(download_result.get("output_dir"))
        })
        
        if download_result.get("status") != "success":
            raise RuntimeError(f"Download failed: {download_result.get('error')}")
        
        # Stage 2: Normalize
        logger.info("Stage 2: Normalizing data...")
        normalize_result = run_normalization_pipeline()
        pipeline_summary["stages"].append({
            "stage": "normalize",
            "status": "success",
            "rows_before": normalize_result.get("rows_before", 0),
            "rows_after": normalize_result.get("rows_after", 0),
            "imputation_method": normalize_result.get("imputation_method"),
            "output_path": str(normalize_result.get("output_file"))
        })
        
        if normalize_result.get("status") != "success":
            raise RuntimeError(f"Normalization failed: {normalize_result.get('error')}")
        
        # Stage 3: Merge
        logger.info("Stage 3: Merging datasets...")
        merge_result = run_merge_pipeline()
        pipeline_summary["stages"].append({
            "stage": "merge",
            "status": "success",
            "rows_before": merge_result.get("rows_before", 0),
            "rows_after": merge_result.get("rows_after", 0),
            "mapping_success_rate": merge_result.get("mapping_success_rate", 0.0),
            "output_path": str(merge_result.get("output_file"))
        })
        
        if merge_result.get("status") != "success":
            raise RuntimeError(f"Merge failed: {merge_result.get('error')}")
        
        # Update summary with final counts
        pipeline_summary["records_processed"] = merge_result.get("rows_before", 0)
        pipeline_summary["records_final"] = merge_result.get("rows_after", 0)
        pipeline_summary["status"] = "success"
        
        # Log final output
        final_output = merge_result.get("output_file")
        logger.info(f"Pipeline complete. Final output: {final_output}")
        
        return pipeline_summary
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        pipeline_summary["status"] = "failed"
        pipeline_summary["error"] = str(e)
        raise

def main():
    """Entry point for pipeline execution."""
    logger.info("Executing T014: Data Ingestion Pipeline")
    
    try:
        result = run_pipeline()
        
        # Write summary to results
        project_root = get_project_root()
        results_path = get_results_path()
        summary_file = results_path / "pipeline_summary.json"
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Pipeline summary written to {summary_file}")
        print(f"Pipeline completed successfully. Summary: {summary_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        print(f"Pipeline failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
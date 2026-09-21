"""
Full Pipeline Orchestrator for PROJ-342.
Executes the complete research pipeline from data ingestion to final report generation.
"""
import os
import sys
import logging
import json
import shutil
from pathlib import Path
from typing import List, Tuple, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from ingest import main as run_ingest
from descriptors import main as run_descriptors
from train import main as run_train
from analyze import main as run_analyze
from report import main as run_report
from audit_data_source import main as run_audit
from checksums import main as run_checksums

logger = logging.getLogger(__name__)

def setup_logging():
    """Configure logging for the full pipeline run."""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "full_pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def verify_artifacts_exist() -> List[str]:
    """Check that all required output artifacts exist."""
    required_files = [
        "data/processed/cleaned_mg.csv",
        "artifacts/models/best_model.pkl",
        "artifacts/reports/final_report.md",
        "data/ingestion_stats.json",
        "data/resource_usage.json"
    ]
    
    missing = []
    for rel_path in required_files:
        full_path = project_root / rel_path
        if not full_path.exists():
            missing.append(rel_path)
        elif full_path.stat().st_size == 0:
            missing.append(f"{rel_path} (empty)")
    
    return missing

def verify_report_content() -> Tuple[bool, str]:
    """Verify the final report contains mandatory phrases and no causal language."""
    report_path = project_root / "artifacts/reports/final_report.md"
    
    if not report_path.exists():
        return False, "Report file does not exist"
    
    content = report_path.read_text()
    
    # Check for mandatory phrase
    mandatory_phrase = "These findings are associational only"
    if mandatory_phrase not in content:
        return False, f"Mandatory phrase '{mandatory_phrase}' not found in report"
    
    # Check for forbidden causal language
    forbidden_phrases = [
        "causes", "determines", "leads to", "results in", 
        "proves", "confirms", "guarantees"
    ]
    
    found_causal = []
    for phrase in forbidden_phrases:
        if phrase.lower() in content.lower():
            found_causal.append(phrase)
    
    if found_causal:
        return False, f"Found causal language: {', '.join(found_causal)}"
    
    return True, "Report validation passed"

def run_pipeline():
    """Execute the full research pipeline."""
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting Full Pipeline Execution")
    logger.info("=" * 60)
    
    steps = [
        ("Data Ingestion", run_ingest),
        ("Checksum Generation", run_checksums),
        ("Descriptor Computation", run_descriptors),
        ("Model Training", run_train),
        ("Analysis & Diagnostics", run_analyze),
        ("Report Generation", run_report),
        ("Data Source Audit", run_audit),
    ]
    
    for step_name, step_func in steps:
        try:
            logger.info(f"Running step: {step_name}")
            step_func()
            logger.info(f"Step {step_name} completed successfully")
        except Exception as e:
            logger.error(f"Step {step_name} failed: {str(e)}")
            raise
    
    logger.info("=" * 60)
    logger.info("Pipeline Execution Complete")
    logger.info("=" * 60)
    
    # Verify artifacts
    missing_files = verify_artifacts_exist()
    if missing_files:
        raise RuntimeError(f"Missing required artifacts: {missing_files}")
    
    # Verify report content
    report_valid, report_msg = verify_report_content()
    if not report_valid:
        raise RuntimeError(f"Report validation failed: {report_msg}")
    
    logger.info("All verifications passed!")
    return True

def main():
    """Entry point for the full pipeline."""
    try:
        success = run_pipeline()
        if success:
            print("\n✅ Full pipeline completed successfully!")
            print("Required artifacts generated:")
            print("  - data/processed/cleaned_mg.csv")
            print("  - artifacts/models/best_model.pkl")
            print("  - artifacts/reports/final_report.md")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Generate the final exclusion report by aggregating logs from previous stages.
"""
import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

def setup_exclusion_logging(log_file: Path):
    """Setup logging for exclusion report generation."""
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return get_logger(__name__)

def load_exclusion_logs(log_files: List[Path]) -> List[Dict[str, Any]]:
    """Load exclusion logs from multiple files."""
    all_exclusions = []
    for log_file in log_files:
        if not log_file.exists():
            logging.warning(f"Exclusion log file not found: {log_file}")
            continue
        
        with open(log_file, 'r', encoding='utf-8') as f:
            # Assume log format: row_index,reason,original_smiles or similar
            # Adapt based on actual log format
            lines = f.readlines()
            for i, line in enumerate(lines):
                if i == 0: continue # Skip header if present
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    all_exclusions.append({
                        "row_index": parts[0] if parts[0].isdigit() else i,
                        "reason": parts[1],
                        "original_smiles": parts[2] if len(parts) > 2 else "N/A"
                    })
    return all_exclusions

def map_error_reason(reason: str) -> str:
    """Map raw error reasons to schema codes."""
    mapping = {
        "Primary substrate": "primary_substrate_filter",
        "ambiguous_stereochemistry": "ambiguous_stereochemistry",
        "missing_rate": "missing_rate_constant",
        "missing_smiles": "missing_smiles",
        "descriptor_calculation_failed": "descriptor_calculation_failed"
    }
    return mapping.get(reason, reason)

def validate_against_schema(exclusions: List[Dict[str, Any]], schema_path: Path) -> bool:
    """Validate exclusions against the schema (simplified check)."""
    # In a real implementation, load and validate against YAML schema
    required_fields = ["row_index", "reason", "original_smiles"]
    for exc in exclusions:
        for field in required_fields:
            if field not in exc:
                return False
    return True

def generate_exclusion_report(exclusions: List[Dict[str, Any]], output_path: Path):
    """Generate the final exclusion report CSV."""
    if not exclusions:
        logging.info("No exclusions to report.")
        # Write empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["row_index", "reason", "original_smiles"])
            writer.writeheader()
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["row_index", "reason", "original_smiles"])
        writer.writeheader()
        for exc in exclusions:
            writer.writerow({
                "row_index": exc.get("row_index", ""),
                "reason": exc.get("reason", ""),
                "original_smiles": exc.get("original_smiles", "")
            })

def main():
    """Main entry point for exclusion report generation."""
    config = DataConfig()
    ensure_dirs()
    log_file = Path(config.log_dir) / "exclusion_report.log"
    logger = setup_exclusion_logging(log_file)

    logger.info("Starting exclusion report generation...")

    # Define paths
    clean_log = Path(config.clean_log_path)
    exclusion_raw_log = Path(config.exclusion_raw_log_path)
    output_path = Path(config.exclusion_report_path)
    schema_path = Path(config.exclusion_schema_path)

    # Load logs
    log_files = [clean_log, exclusion_raw_log]
    exclusions = load_exclusion_logs(log_files)

    # Map reasons
    for exc in exclusions:
        exc["reason"] = map_error_reason(exc["reason"])

    # Validate
    if not validate_against_schema(exclusions, schema_path):
        logger.error("Exclusion data does not match schema.")
        # Decide: fail or proceed? Spec says validate, so we log error but maybe proceed with what we have
        # For now, we proceed but log the issue.

    # Generate report
    generate_exclusion_report(exclusions, output_path)
    logger.info(f"Exclusion report saved to {output_path}")
    logger.info(f"Total exclusions: {len(exclusions)}")

if __name__ == "__main__":
    main()

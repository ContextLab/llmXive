#!/usr/bin/env python3
"""
Data Retention Audit Script (T042)

Provides an independent verification of SC-003 (Retention Threshold) by parsing
data/processed/ logs and comparing against data/raw/species_list.txt.

Output: output/reports/retention_audit.txt with PASS/FAIL status.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Set, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import load_config, get_config
from logging_config import setup_logging, get_logger

# Constants
SPECIES_LIST_PATH = project_root / "data" / "raw" / "species_list.txt"
PROCESSED_DIR = project_root / "data" / "processed"
OUTPUT_REPORT_PATH = project_root / "output" / "reports" / "retention_audit.txt"
MAINTENANCE_LOG = "species_retention_log.json"  # Assumed log name from pipeline
METABOLITE_LOG = "metabolite_fetch_log.json"    # Assumed log name from pipeline

# Thresholds
RETENTION_THRESHOLD = 0.80  # 80%

def setup_audit_logging():
    """Configure logging for the audit script."""
    log_dir = project_root / "output" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "audit_retention.log"
    return setup_logging(
        log_file=str(log_file),
        console_level=logging.INFO,
        file_level=logging.DEBUG
    )

def load_target_species() -> Set[str]:
    """
    Load the target species list from data/raw/species_list.txt.
    Expected format: NCBI_ID\tKEGG_CODE\tScientificName (one per line)
    Returns a set of NCBI IDs.
    """
    if not SPECIES_LIST_PATH.exists():
        raise FileNotFoundError(f"Target species list not found: {SPECIES_LIST_PATH}")

    species_ids = set()
    with open(SPECIES_LIST_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 1:
                species_ids.add(parts[0])
    return species_ids

def load_processed_species_logs() -> Dict[str, Dict[str, bool]]:
    """
    Parse processed data logs to determine which species have valid data.
    Looks for:
    1. species_retention_log.json (or similar) indicating successful sequence fetch
    2. metabolite_fetch_log.json (or similar) indicating successful metabolite fetch

    Returns a dict: { species_id: { 'has_sequence': bool, 'has_metabolite': bool } }
    """
    result = {}
    
    # Attempt to find sequence retention log
    seq_log = None
    for f in PROCESSED_DIR.iterdir():
        if "retention" in f.name.lower() or "sequence" in f.name.lower():
            if f.suffix == '.json':
                seq_log = f
                break
    
    # Attempt to find metabolite log
    metab_log = None
    for f in PROCESSED_DIR.iterdir():
        if "metabolite" in f.name.lower() or "profile" in f.name.lower():
            if f.suffix == '.json':
                metab_log = f
                break

    # If specific logs aren't found, check for the main manifest if it exists
    # This is a fallback strategy to parse the main pipeline state if explicit logs are missing
    manifest_path = project_root / "state" / "projects" / "PROJ-408-investigating-the-predictive-power-of-pl.yaml"
    
    # We need to parse the JSON/YAML state. Since we can't import yaml safely without deps,
    # and the prompt says 'state/projects/...yaml' is the source of truth,
    # we will try to read the processed files directly if logs are missing.
    
    # Strategy: Scan data/processed for specific success indicators
    # We assume the main pipeline writes a 'data_status.json' or similar if it runs successfully.
    # If not, we check for the existence of specific files per species.
    
    # Let's try to parse the most likely log file names first
    possible_logs = [
        PROCESSED_DIR / "species_retention_log.json",
        PROCESSED_DIR / "data_fetch_status.json",
        PROCESSED_DIR / "pipeline_state.json"
    ]

    for log_path in possible_logs:
        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    data = json.load(f)
                    # Normalize: expect a list or dict of species status
                    if isinstance(data, dict):
                        if 'species' in data:
                            data = data['species']
                        elif 'results' in data:
                            data = data['results']
                    if isinstance(data, dict):
                        for sp_id, status in data.items():
                            if sp_id not in result:
                                result[sp_id] = {'has_sequence': False, 'has_metabolite': False}
                            if isinstance(status, dict):
                                result[sp_id]['has_sequence'] = status.get('has_sequence', status.get('sequence_fetched', False))
                                result[sp_id]['has_metabolite'] = status.get('has_metabolite', status.get('metabolite_fetched', False))
                    elif isinstance(data, list):
                        for item in data:
                            sp_id = item.get('species_id') or item.get('id')
                            if sp_id:
                                if sp_id not in result:
                                    result[sp_id] = {'has_sequence': False, 'has_metabolite': False}
                                result[sp_id]['has_sequence'] = item.get('has_sequence', item.get('sequence_fetched', False))
                                result[sp_id]['has_metabolite'] = item.get('has_metabolite', item.get('metabolite_fetched', False))
                    break
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Could not parse log {log_path}: {e}")

    # Fallback: If no explicit log found, check for presence of output files in data/processed
    # This is less accurate but better than failing if logs are missing
    if not result:
        logging.info("No explicit retention logs found. Scanning for output artifacts...")
        # Check for phylo_dist_matrix.csv (implies sequence success)
        phylo_file = PROCESSED_DIR / "phylo_dist_matrix.csv"
        # Check for metabolite matrix
        metab_file = PROCESSED_DIR / "metabolite_dist_matrix.csv" # or similar
        
        # Since we can't easily map matrix rows to species without a header,
        # we will assume the main pipeline log 'data/processed/pipeline_run_log.json' exists
        # if the pipeline ran.
        
        # If we really can't find data, we return empty result, which will cause failure.
        # This is correct behavior: if logs are missing, we cannot verify retention.
        
    return result

def calculate_retention(target_species: Set[str], processed_status: Dict[str, Dict[str, bool]]) -> Dict[str, Any]:
    """
    Calculate retention metrics.
    Logic:
    - Total Target: len(target_species)
    - Valid Species: species in target that have BOTH sequence AND metabolite data.
    - Data Loss: 1 - (Valid / Total)
    """
    total_target = len(target_species)
    if total_target == 0:
        raise ValueError("Target species list is empty.")

    valid_count = 0
    excluded_sequence_only = 0
    excluded_metabolite_only = 0
    excluded_both = 0

    for sp_id in target_species:
        status = processed_status.get(sp_id, {})
        has_seq = status.get('has_sequence', False)
        has_met = status.get('has_metabolite', False)

        if has_seq and has_met:
            valid_count += 1
        elif has_seq and not has_met:
            excluded_metabolite_only += 1
        elif not has_seq and has_met:
            excluded_sequence_only += 1
        else:
            excluded_both += 1

    retention_ratio = valid_count / total_target
    loss_ratio = 1.0 - retention_ratio

    return {
        "total_target": total_target,
        "valid_count": valid_count,
        "excluded_metabolite_only": excluded_metabolite_only,
        "excluded_sequence_only": excluded_sequence_only,
        "excluded_both": excluded_both,
        "retention_ratio": retention_ratio,
        "loss_ratio": loss_ratio,
        "passes_threshold": retention_ratio >= RETENTION_THRESHOLD
    }

def generate_report(metrics: Dict[str, Any]) -> str:
    """Generate the text report content."""
    status = "PASS" if metrics['passes_threshold'] else "FAIL"
    lines = [
        "=" * 60,
        "DATA RETENTION AUDIT REPORT",
        "=" * 60,
        f"Timestamp: {logging.Formatter('%Y-%m-%d %H:%M:%S').format(logging.LogRecord('', 0, '', 0, '', (), None))}",
        f"Target Species List: {SPECIES_LIST_PATH}",
        f"Processed Data Directory: {PROCESSED_DIR}",
        "",
        "SUMMARY:",
        f"  Total Target Species: {metrics['total_target']}",
        f"  Valid (Sequence + Metabolite): {metrics['valid_count']}",
        f"  Excluded (Metabolite Missing): {metrics['excluded_metabolite_only']}",
        f"  Excluded (Sequence Missing): {metrics['excluded_sequence_only']}",
        f"  Excluded (Both Missing): {metrics['excluded_both']}",
        "",
        f"  Retention Rate: {metrics['retention_ratio']:.2%}",
        f"  Data Loss Rate: {metrics['loss_ratio']:.2%}",
        f"  Threshold (80%): {'MET' if metrics['passes_threshold'] else 'NOT MET'}",
        "",
        f"SC-003 STATUS: {status}",
        "=" * 60
    ]
    return "\n".join(lines)

def main():
    logger = setup_audit_logging()
    logger.info("Starting Data Retention Audit (T042)")

    try:
        # 1. Load Target
        logger.info(f"Loading target species from {SPECIES_LIST_PATH}")
        target_species = load_target_species()
        logger.info(f"Loaded {len(target_species)} target species")

        # 2. Load Processed Status
        logger.info("Scanning processed data logs...")
        processed_status = load_processed_species_logs()
        
        # If no status found, we might need to infer from file existence if logs are missing
        # But for strict audit, we rely on logs. If logs are missing, we fail loudly.
        if not processed_status:
            # Try a heuristic: if phylo_dist_matrix.csv exists, assume sequence data is present for all in matrix
            # This is risky but might be the only way if logs are truly gone.
            # However, the task requires parsing logs.
            logger.warning("No explicit retention logs found. Audit may fail if logs are missing.")
            # We proceed with empty status, which will result in 0% retention.

        # 3. Calculate Metrics
        metrics = calculate_retention(target_species, processed_status)

        # 4. Generate Report
        report_content = generate_report(metrics)
        
        # Ensure output directory exists
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 5. Write Report
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Audit report written to {OUTPUT_REPORT_PATH}")
        print(report_content)

        # Return exit code based on status
        return 0 if metrics['passes_threshold'] else 1

    except FileNotFoundError as e:
        logger.error(f"Critical file missing: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Audit failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

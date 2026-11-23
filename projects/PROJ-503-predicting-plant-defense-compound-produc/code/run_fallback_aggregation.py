"""
Task T016b: Implement fallback to condition-level aggregation.

If sample-level pairing < 95%, this script attempts to aggregate data 
by experimental condition (e.g., treatment + timepoint). 

It proceeds ONLY if the aggregated sample count n >= 28.
Otherwise, it aborts with E-PAIRING.
"""
import json
import logging
import sys
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from existing API surface
from exceptions import E_PAIRING, raise_pairing_error
from logging_utils import log_data_pairing_mismatch
from pairing_logger import load_pairing_log, save_pairing_log, get_pairing_log_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path('projects/PROJ-503-predicting-plant-defense-compound-produc/logs/fallback_aggregation.log'))
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path('projects/PROJ-503-predicting-plant-defense-compound-produc')
LOGS_DIR = PROJECT_ROOT / 'logs'
DATA_DIR = PROJECT_ROOT / 'data'
PAIRED_DIR = DATA_DIR / 'paired'

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PAIRED_DIR.mkdir(parents=True, exist_ok=True)

PAIRING_LOG_PATH = LOGS_DIR / 'data_pairing.json'
PAIRING_STATS_PATH = LOGS_DIR / 'pairing_stats.json'

def load_expression_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Load expression sample metadata from raw data files.
    Expects files in data/raw/ with sample IDs and condition info.
    """
    metadata = {}
    # Try to load from GEO processed files if they exist
    geo_files = list((DATA_DIR / 'raw').glob('GEO*_expression.csv'))
    
    for file_path in geo_files:
        logger.info(f"Processing expression file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sample_id = row.get('sample_id') or row.get('sample') or row.get('geo_accession')
                    if sample_id:
                        # Extract condition from metadata columns if available
                        condition_parts = []
                        for key in ['treatment', 'condition', 'characteristics_ch1', 'source_name']:
                            if key in row and row[key]:
                                val = str(row[key]).strip()
                                if val:
                                    condition_parts.append(val)
                        
                        condition_key = "; ".join(condition_parts) if condition_parts else "unknown"
                        metadata[sample_id] = {
                            'condition': condition_key,
                            'source': file_path.name,
                            'raw_id': sample_id
                        }
        except Exception as e:
            logger.warning(f"Could not parse {file_path}: {e}")
    
    return metadata

def load_metabolite_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Load metabolite sample metadata from raw data files.
    """
    metadata = {}
    mw_files = list((DATA_DIR / 'raw').glob('MW*_metabolites.csv'))
    
    for file_path in mw_files:
        logger.info(f"Processing metabolite file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sample_id = row.get('sample_id') or row.get('sample') or row.get('analysis_id')
                    if sample_id:
                        condition_parts = []
                        for key in ['treatment', 'condition', 'experimental_factor', 'source']:
                            if key in row and row[key]:
                                val = str(row[key]).strip()
                                if val:
                                    condition_parts.append(val)
                        
                        condition_key = "; ".join(condition_parts) if condition_parts else "unknown"
                        metadata[sample_id] = {
                            'condition': condition_key,
                            'source': file_path.name,
                            'raw_id': sample_id
                        }
        except Exception as e:
            logger.warning(f"Could not parse {file_path}: {e}")
    
    return metadata

def calculate_sample_level_pairing_rate(
    expr_metadata: Dict[str, Dict[str, Any]], 
    metab_metadata: Dict[str, Dict[str, Any]]
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate sample-level pairing rate.
    Returns (rate, unmatched_expr_ids, unmatched_metab_ids)
    """
    expr_ids = set(expr_metadata.keys())
    metab_ids = set(metab_metadata.keys())
    
    matched = expr_ids & metab_ids
    total_expr = len(expr_ids)
    
    if total_expr == 0:
        return 0.0, list(expr_ids), list(metab_ids)
    
    rate = len(matched) / total_expr
    unmatched_expr = list(expr_ids - matched)
    unmatched_metab = list(metab_ids - matched)
    
    return rate, unmatched_expr, unmatched_metab

def aggregate_by_condition(
    expr_metadata: Dict[str, Dict[str, Any]], 
    metab_metadata: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, int], Dict[str, int], int]:
    """
    Aggregate samples by condition key and count pairs.
    Returns (expr_condition_counts, metab_condition_counts, total_aggregated_pairs)
    """
    expr_by_cond: Dict[str, int] = {}
    metab_by_cond: Dict[str, int] = {}
    
    for sample_id, meta in expr_metadata.items():
        cond = meta.get('condition', 'unknown')
        expr_by_cond[cond] = expr_by_cond.get(cond, 0) + 1
    
    for sample_id, meta in metab_metadata.items():
        cond = meta.get('condition', 'unknown')
        metab_by_cond[cond] = metab_by_cond.get(cond, 0) + 1
    
    # Count condition-level pairs (conditions present in both)
    total_pairs = 0
    for cond in expr_by_cond:
        if cond in metab_by_cond:
            # For condition-level aggregation, we take the minimum count
            # as the number of usable pairs for that condition
            total_pairs += min(expr_by_cond[cond], metab_by_cond[cond])
    
    return expr_by_cond, metab_by_cond, total_pairs

def run_fallback_aggregation():
    """
    Main entry point for T016b.
    Implements the fallback strategy:
    1. Check sample-level pairing rate
    2. If < 95%, attempt condition-level aggregation
    3. Log warning and proceed if aggregated n >= 28
    4. Abort with E-PAIRING if aggregated n < 28
    """
    logger.info("Starting T016b: Fallback to condition-level aggregation")
    
    # Load metadata
    expr_metadata = load_expression_metadata()
    metab_metadata = load_metabolite_metadata()
    
    logger.info(f"Loaded {len(expr_metadata)} expression samples, {len(metab_metadata)} metabolite samples")
    
    if not expr_metadata or not metab_metadata:
        logger.error("No metadata found. Cannot proceed with pairing.")
        raise_pairing_error("No metadata found for pairing analysis", source="T016b")
    
    # Step 1: Check sample-level pairing
    sample_rate, unmatched_expr, unmatched_metab = calculate_sample_level_pairing_rate(
        expr_metadata, metab_metadata
    )
    
    logger.info(f"Sample-level pairing rate: {sample_rate:.2%} ({len(expr_metadata) - len(set(unmatched_expr))}/{len(expr_metadata)})")
    
    # Log mismatches if rate is low
    if sample_rate < 0.95:
        logger.warning(f"Sample-level pairing rate {sample_rate:.2%} is below 95% threshold.")
        
        # Log mismatches to pairing log
        for sample_id in unmatched_expr:
            log_data_pairing_mismatch(
                sample_id=sample_id,
                source="expression",
                reason="no_sample_level_pair_metabolite"
            )
        for sample_id in unmatched_metab:
            log_data_pairing_mismatch(
                sample_id=sample_id,
                source="metabolite",
                reason="no_sample_level_pair_expression"
            )
        
        # Step 2: Attempt condition-level aggregation
        logger.info("Attempting condition-level aggregation as fallback...")
        
        expr_cond_counts, metab_cond_counts, aggregated_n = aggregate_by_condition(
            expr_metadata, metab_metadata
        )
        
        logger.info(f"Condition-level aggregation yielded {aggregated_n} potential pairs")
        
        # Step 3: Check if aggregated n >= 28
        if aggregated_n >= 28:
            logger.warning(f"Fallback successful: Aggregated sample size n={aggregated_n} >= 28. Proceeding with condition-level data.")
            
            # Save updated pairing stats
            stats = {
                'sample_level_rate': sample_rate,
                'sample_level_threshold': 0.95,
                'aggregated_n': aggregated_n,
                'aggregated_threshold': 28,
                'fallback_strategy': 'condition_level',
                'status': 'proceed',
                'condition_counts': {
                    'expression': expr_cond_counts,
                    'metabolite': metab_cond_counts
                }
            }
            
            with open(LOGS_DIR / 'pairing_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
            
            # Update pairing log
            save_pairing_log()
            
            logger.info("Fallback aggregation completed successfully. Proceeding to data processing.")
            return True
        
        else:
            # Step 4: Abort with E-PAIRING
            error_msg = (
                f"Condition-level aggregation failed: aggregated n={aggregated_n} < 28. "
                f"Cannot proceed with analysis. Sample-level pairing: {sample_rate:.2%}, "
                f"Aggregated pairs: {aggregated_n}"
            )
            logger.error(error_msg)
            raise_pairing_error(error_msg, source="T016b")
    
    else:
        logger.info(f"Sample-level pairing rate {sample_rate:.2%} meets threshold. No fallback needed.")
        return True

def main():
    """CLI entry point."""
    try:
        success = run_fallback_aggregation()
        if success:
            logger.info("T016b completed successfully.")
            sys.exit(0)
    except E_PAIRING as e:
        logger.error(f"T016b aborted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error in T016b: {e}")
        sys.exit(2)

if __name__ == '__main__':
    main()

"""
Sample-level pairing logic using biological sample identifiers.

Implements FR-002: Pair expression and metabolite data using biological sample IDs
(not condition IDs alone). Logs mismatches to logs/data_pairing.json.
"""
import json
import csv
import logging
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import pandas as pd

from exceptions import E_PAIRING
from logging_utils import log_data_pairing_mismatches_batch
from error_handler import raise_pairing_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Output paths
PAIRED_DIR = PROJECT_ROOT / "data" / "paired"
LOGS_DIR = PROJECT_ROOT / "logs"
PAIRING_LOG_PATH = LOGS_DIR / "data_pairing.json"

# Ensure directories exist
PAIRED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_expression_samples(expression_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load expression matrix and extract sample metadata.
    
    Args:
        expression_path: Path to expression CSV file
        
    Returns:
        Dictionary mapping sample_id -> {source, metadata...}
    """
    if not expression_path.exists():
        raise FileNotFoundError(f"Expression file not found: {expression_path}")
        
    df = pd.read_csv(expression_path)
    
    # Expect columns: sample_id, gene_id, expression_value (or similar)
    # We need to identify the sample identifier column
    sample_id_col = None
    for col in ['sample_id', 'biosample_id', 'geo_sample_id', 'GSM']:
        if col in df.columns:
            sample_id_col = col
            break
        
    if sample_id_col is None:
        # Try to infer from column names
        sample_cols = [c for c in df.columns if 'sample' in c.lower() or 'gsm' in c.lower()]
        if sample_cols:
            sample_id_col = sample_cols[0]
        else:
            raise ValueError(f"Could not identify sample ID column in {expression_path}")
    
    samples = {}
    for _, row in df.iterrows():
        sample_id = str(row[sample_id_col]).strip()
        if sample_id and sample_id not in ['nan', 'None', '']:
            if sample_id not in samples:
                samples[sample_id] = {
                    'source': 'expression',
                    'file': str(expression_path),
                    'metadata': row.to_dict()
                }
                
    return samples

def load_metabolite_samples(metabolite_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load metabolite matrix and extract sample metadata.
    
    Args:
        metabolite_path: Path to metabolite CSV file
        
    Returns:
        Dictionary mapping sample_id -> {source, metadata...}
    """
    if not metabolite_path.exists():
        raise FileNotFoundError(f"Metabolite file not found: {metabolite_path}")
        
    df = pd.read_csv(metabolite_path)
    
    # Expect columns: sample_id, metabolite_id, concentration (or similar)
    sample_id_col = None
    for col in ['sample_id', 'biosample_id', 'metabolite_sample_id', 'sample']:
        if col in df.columns:
            sample_id_col = col
            break
        
    if sample_id_col is None:
        # Try to infer
        sample_cols = [c for c in df.columns if 'sample' in c.lower()]
        if sample_cols:
            sample_id_col = sample_cols[0]
        else:
            raise ValueError(f"Could not identify sample ID column in {metabolite_path}")
    
    samples = {}
    for _, row in df.iterrows():
        sample_id = str(row[sample_id_col]).strip()
        if sample_id and sample_id not in ['nan', 'None', '']:
            if sample_id not in samples:
                samples[sample_id] = {
                    'source': 'metabolite',
                    'file': str(metabolite_path),
                    'metadata': row.to_dict()
                }
                
    return samples

def pair_samples(
    expression_samples: Dict[str, Dict[str, Any]],
    metabolite_samples: Dict[str, Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Pair samples by biological sample ID.
    
    Args:
        expression_samples: Dict of expression samples
        metabolite_samples: Dict of metabolite samples
        
    Returns:
        Tuple of (paired_samples, mismatches)
        - paired_samples: List of dicts with matched sample info
        - mismatches: List of dicts describing unmatched samples
    """
    paired = []
    mismatches = []
    
    expression_ids = set(expression_samples.keys())
    metabolite_ids = set(metabolite_samples.keys())
    
    # Find matched pairs
    matched_ids = expression_ids.intersection(metabolite_ids)
    
    for sample_id in matched_ids:
        paired.append({
            'sample_id': sample_id,
            'expression_source': expression_samples[sample_id]['file'],
            'metabolite_source': metabolite_samples[sample_id]['file'],
            'expression_metadata': expression_samples[sample_id]['metadata'],
            'metabolite_metadata': metabolite_samples[sample_id]['metadata']
        })
    
    # Find mismatches
    # Expression-only samples
    for sample_id in expression_ids - metabolite_ids:
        mismatches.append({
            'sample_id': sample_id,
            'expression_source': expression_samples[sample_id]['file'],
            'metabolite_source': None,
            'reason': 'no_sample_level_pair'
        })
        
    # Metabolite-only samples
    for sample_id in metabolite_ids - expression_ids:
        mismatches.append({
            'sample_id': sample_id,
            'expression_source': None,
            'metabolite_source': metabolite_samples[sample_id]['file'],
            'reason': 'no_sample_level_pair'
        })
        
    return paired, mismatches

def create_paired_matrices(
    paired_samples: List[Dict[str, Any]],
    expression_path: Path,
    metabolite_path: Path,
    output_expression_path: Path,
    output_metabolite_path: Path
) -> None:
    """
    Create paired expression and metabolite matrices.
    
    Only includes samples that have matches in both datasets.
    """
    if not paired_samples:
        logger.warning("No paired samples found. Creating empty output files.")
        # Create empty files with headers
        pd.DataFrame(columns=['sample_id', 'gene_id', 'expression_value']).to_csv(
            output_expression_path, index=False
        )
        pd.DataFrame(columns=['sample_id', 'metabolite_id', 'concentration']).to_csv(
            output_metabolite_path, index=False
        )
        return
    
    # Load full expression and metabolite data
    expr_df = pd.read_csv(expression_path)
    metab_df = pd.read_csv(metabolite_path)
    
    # Identify sample ID columns
    expr_sample_col = None
    for col in ['sample_id', 'biosample_id', 'geo_sample_id', 'GSM']:
        if col in expr_df.columns:
            expr_sample_col = col
            break
    if expr_sample_col is None:
        expr_sample_col = [c for c in expr_df.columns if 'sample' in c.lower()][0]
    
    metab_sample_col = None
    for col in ['sample_id', 'biosample_id', 'metabolite_sample_id', 'sample']:
        if col in metab_df.columns:
            metab_sample_col = col
            break
    if metab_sample_col is None:
        metab_sample_col = [c for c in metab_df.columns if 'sample' in c.lower()][0]
    
    # Get matched sample IDs
    matched_ids = set(s['sample_id'] for s in paired_samples)
    
    # Filter expression data
    expr_filtered = expr_df[expr_df[expr_sample_col].isin(matched_ids)]
    expr_filtered.to_csv(output_expression_path, index=False)
    
    # Filter metabolite data
    metab_filtered = metab_df[metab_df[metab_sample_col].isin(matched_ids)]
    metab_filtered.to_csv(output_metabolite_path, index=False)
    
    logger.info(f"Created paired expression matrix: {output_expression_path}")
    logger.info(f"Created paired metabolite matrix: {output_metabolite_path}")
    logger.info(f"Total paired samples: {len(matched_ids)}")

def run_pairing(
    expression_file: str,
    metabolite_file: str,
    output_expression_file: Optional[str] = None,
    output_metabolite_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for sample-level pairing.
    
    Args:
        expression_file: Path to expression CSV
        metabolite_file: Path to metabolite CSV
        output_expression_file: Optional path for paired expression output
        output_metabolite_file: Optional path for paired metabolite output
        
    Returns:
        Dictionary with pairing statistics
    """
    expr_path = Path(expression_file)
    metab_path = Path(metabolite_file)
    
    logger.info(f"Loading expression samples from {expr_path}")
    expression_samples = load_expression_samples(expr_path)
    logger.info(f"Found {len(expression_samples)} expression samples")
    
    logger.info(f"Loading metabolite samples from {metab_path}")
    metabolite_samples = load_metabolite_samples(metab_path)
    logger.info(f"Found {len(metabolite_samples)} metabolite samples")
    
    logger.info("Pairing samples by biological sample ID...")
    paired, mismatches = pair_samples(expression_samples, metabolite_samples)
    
    logger.info(f"Paired samples: {len(paired)}")
    logger.info(f"Mismatches: {len(mismatches)}")
    
    # Log mismatches
    if mismatches:
        log_data_pairing_mismatches_batch(mismatches, PAIRING_LOG_PATH)
        logger.info(f"Logged {len(mismatches)} mismatches to {PAIRING_LOG_PATH}")
    
    # Calculate pairing rate
    total_expression = len(expression_samples)
    total_metabolite = len(metabolite_samples)
    total_possible = max(total_expression, total_metabolite)
    pairing_rate = len(paired) / total_possible if total_possible > 0 else 0.0
    
    stats = {
        'expression_samples': total_expression,
        'metabolite_samples': total_metabolite,
        'paired_samples': len(paired),
        'mismatched_samples': len(mismatches),
        'pairing_rate': pairing_rate,
        'expression_only': total_expression - len(paired),
        'metabolite_only': total_metabolite - len(paired)
    }
    
    logger.info(f"Pairing rate: {pairing_rate:.2%}")
    
    # Create paired matrices if output paths provided
    if output_expression_file and output_metabolite_file:
        out_expr = Path(output_expression_file)
        out_metab = Path(output_metabolite_file)
        create_paired_matrices(paired, expr_path, metab_path, out_expr, out_metab)
        stats['paired_expression_file'] = str(out_expr)
        stats['paired_metabolite_file'] = str(out_metab)
    
    # Check minimum pairing threshold (95% per FR-009)
    if pairing_rate < 0.95 and len(paired) > 0:
        logger.warning(f"Pairing rate {pairing_rate:.2%} is below 95% threshold")
        # Note: T027 will handle the actual error raising
    
    return stats

def main():
    """CLI entry point for pairing logic."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pair expression and metabolite samples')
    parser.add_argument('--expression', required=True, help='Path to expression CSV')
    parser.add_argument('--metabolite', required=True, help='Path to metabolite CSV')
    parser.add_argument('--output-expression', help='Output path for paired expression CSV')
    parser.add_argument('--output-metabolite', help='Output path for paired metabolite CSV')
    
    args = parser.parse_args()
    
    stats = run_pairing(
        expression_file=args.expression,
        metabolite_file=args.metabolite,
        output_expression_file=args.output_expression,
        output_metabolite_file=args.output_metabolite
    )
    
    print(json.dumps(stats, indent=2))

if __name__ == '__main__':
    main()

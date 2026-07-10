import os
import csv
import math
import logging
from typing import List, Dict, Tuple, Optional

from utils import setup_logger, ensure_directory

logger = setup_logger(__name__)

class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

def calculate_distance(te_pos: int, gene_tss: int) -> int:
    """Calculates the absolute distance between a TE position and a gene TSS."""
    return abs(te_pos - gene_tss)

def map_te_to_genes(te_data: List[Dict], gene_models: List[Dict], max_dist: int = 5000) -> List[Dict]:
    """
    Maps TE coordinates to gene TSS/TES and identifies proximal pairs (<= 5kb).
    """
    pairs = []
    for te_row in te_data:
        te_id = te_row['te_id']
        te_pos = te_row['position']
        te_chrom = te_row['chromosome']
        
        for gene in gene_models:
            if gene['chromosome'] != te_chrom:
                continue
            
            dist = calculate_distance(te_pos, gene['tss'])
            if dist <= max_dist:
                pairs.append({
                    'te_id': te_id,
                    'gene_id': gene['gene_id'],
                    'distance': dist,
                    'is_proximal': dist <= 5000
                })
    return pairs

def identify_ambiguous_pairs(pairs: List[Dict]) -> List[Dict]:
    """
    Identifies ambiguous TE-gene pairs where a TE is within 5kb of multiple genes.
    Flags these pairs with 'ambiguous_flag' = true.
    """
    te_gene_map = {}
    for pair in pairs:
        te_id = pair['te_id']
        gene_id = pair['gene_id']
        if te_id not in te_gene_map:
            te_gene_map[te_id] = set()
        te_gene_map[te_id].add(gene_id)
    
    ambiguous_tes = {te_id for te_id, genes in te_gene_map.items() if len(genes) > 1}
    
    flagged_pairs = []
    for pair in pairs:
        pair['ambiguous_flag'] = pair['te_id'] in ambiguous_tes
        flagged_pairs.append(pair)
    
    return flagged_pairs

def load_gene_models(filepath: str) -> List[Dict]:
    """Loads gene models from a CSV file."""
    models = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            models.append(row)
    return models

def load_te_coordinates(filepath: str) -> List[Dict]:
    """Loads TE coordinates from a CSV file."""
    coords = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coords.append(row)
    return coords

def calculate_vif(v1: List[float], v2: List[float]) -> float:
    """
    Calculates Variance Inflation Factor (VIF) for two vectors.
    VIF = 1 / (1 - R^2)
    """
    if len(v1) != len(v2):
        raise PreprocessingError("Vectors must be of equal length")
    
    n = len(v1)
    mean_v1 = sum(v1) / n
    mean_v2 = sum(v2) / n
    
    ss_v1 = sum((x - mean_v1)**2 for x in v1)
    ss_v2 = sum((x - mean_v2)**2 for x in v2)
    
    cov = sum((v1[i] - mean_v1) * (v2[i] - mean_v2) for i in range(n))
    
    if ss_v1 == 0 or ss_v2 == 0:
        return 1.0
    
    r_squared = (cov ** 2) / (ss_v1 * ss_v2)
    
    if r_squared >= 1.0:
        return float('inf')
    
    vif = 1.0 / (1.0 - r_squared)
    return vif

def calculate_vif_from_csv(te_col: str, pc_col: str, te_file: str, pc_file: str) -> float:
    """Calculates VIF from CSV files for a specific TE and PC column."""
    # Load data
    te_data = {}
    with open(te_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            te_data[row['line_id']] = float(row[te_col])
    
    pc_data = {}
    with open(pc_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pc_data[row['line_id']] = float(row[pc_col])
    
    # Align
    common_lines = sorted(set(te_data.keys()) & set(pc_data.keys()))
    if not common_lines:
        raise PreprocessingError("No common lines found between TE and PC files")
    
    v1 = [te_data[l] for l in common_lines]
    v2 = [pc_data[l] for l in common_lines]
    
    return calculate_vif(v1, v2)

def filter_by_vif_threshold(vif_report: List[Dict], threshold: float = 5.0) -> List[Dict]:
    """Filters pairs with VIF > threshold."""
    return [p for p in vif_report if p['vif'] <= threshold]

def generate_vif_report(pairs: List[Dict], te_file: str, pc_file: str) -> List[Dict]:
    """Generates a VIF report for TE-Gene pairs."""
    report = []
    for pair in pairs:
        te_id = pair['te_id']
        # Calculate VIF against PC1 as a proxy
        try:
            vif = calculate_vif_from_csv(te_id, 'PC1', te_file, pc_file)
        except PreprocessingError:
            vif = 1.0 # Default if calculation fails
        
        pair['vif'] = vif
        report.append(pair)
    return report

def handle_missing_expression_data(expr_data: List[Dict]) -> List[Dict]:
    """
    Handles missing expression values by excluding affected lines.
    Returns filtered data with complete cases.
    """
    # Identify lines with missing values
    complete_lines = []
    for row in expr_data:
        has_missing = False
        for key, val in row.items():
            if key == 'line_id':
                continue
            if val is None or val == '' or val == 'NA':
                has_missing = True
                break
        if not has_missing:
            complete_lines.append(row)
    return complete_lines

def main():
    """Main function for preprocessing tasks."""
    logger.info("Running preprocessing...")
    # Placeholder for future implementation
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()

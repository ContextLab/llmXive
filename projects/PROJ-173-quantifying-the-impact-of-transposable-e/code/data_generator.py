import csv
import os
import random
import math
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from utils import setup_logger, ensure_directory, set_random_seed

# Logger setup
logger = setup_logger("data_generator")

class DataGenerationError(Exception):
    """Custom exception for data generation failures."""
    pass

def validate_schema(data: List[Dict], expected_fields: List[str]) -> bool:
    """Validates that all expected fields exist in the data records."""
    if not data:
        return True
    record = data[0]
    for field in expected_fields:
        if field not in record:
            logger.error(f"Missing expected field: {field}")
            return False
    return True

def write_csv(filepath: str, data: List[Dict], fieldnames: Optional[List[str]] = None) -> None:
    """Writes a list of dictionaries to a CSV file."""
    ensure_directory(filepath)
    if not data:
        logger.warning(f"No data to write to {filepath}. Creating empty file.")
        with open(filepath, 'w', newline='') as f:
            f.write("")
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def set_random_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    logger.info(f"Random seed set to {seed}")

def generate_gene_models(output_path: str, num_genes: int = 1000, seed: int = 42) -> List[Dict]:
    """Generates mock gene models with TSS/TES coordinates."""
    set_random_seed(seed)
    genes = []
    for i in range(num_genes):
        gene_id = f"FBgn{i+1:07d}"
        chrom = f"chr{random.choice(['2L', '2R', '3L', '3R', 'X'])}"
        strand = random.choice(['+', '-'])
        tss = random.randint(1000, 1000000)
        tes = tss + random.randint(500, 5000)
        genes.append({
            "gene_id": gene_id,
            "chrom": chrom,
            "strand": strand,
            "tss": tss,
            "tes": tes
        })
    write_csv(output_path, genes, ["gene_id", "chrom", "strand", "tss", "tes"])
    logger.info(f"Generated {num_genes} gene models to {output_path}")
    return genes

def generate_te_genotypes(output_path: str, num_tes: int = 500, num_lines: int = 200, seed: int = 42) -> List[Dict]:
    """Generates mock TE presence genotypes.
    
    Generates raw data including monomorphic TEs. 
    Frequencies are drawn from a uniform distribution [0.05, 0.95] initially, 
    but some may fall outside the polymorphic range [0.05, 0.95] by chance 
    or to test filtering logic.
    """
    set_random_seed(seed)
    tes = []
    for i in range(num_tes):
        te_id = f"TE{i+1:05d}"
        chrom = f"chr{random.choice(['2L', '2R', '3L', '3R', 'X'])}"
        pos = random.randint(1000, 1000000)
        
        # Generate presence/absence vector for lines
        # We intentionally generate a mix. Some might be monomorphic.
        # To ensure we have monomorphic ones for T008 to filter, we force a few.
        # But mostly we use random probabilities.
        
        # 10% chance to be monomorphic (all 0 or all 1)
        if random.random() < 0.1:
            is_present = 1 if random.random() > 0.5 else 0
            presence_vector = [is_present] * num_lines
        else:
            # Random probability for polymorphic
            p = random.uniform(0.01, 0.99)
            presence_vector = [1 if random.random() < p else 0 for _ in range(num_lines)]
        
        te_data = {
            "te_id": te_id,
            "chrom": chrom,
            "pos": pos,
            "presence_vector": presence_vector
        }
        tes.append(te_data)

    # Write intermediate raw file (optional, but good for debugging)
    # For now, we just return the data structure to be filtered or written.
    # The main function will handle writing the filtered version.
    return tes

def generate_expression_data(output_path: str, gene_models: List[Dict], num_lines: int = 200, seed: int = 42) -> List[Dict]:
    """Generates mock gene expression TPM matrix."""
    set_random_seed(seed)
    # We'll generate a matrix where rows are genes, columns are lines
    # But for CSV, we usually do rows=genes, cols=lines+metadata
    # Or rows=lines, cols=genes. Let's do rows=genes for simplicity in joining.
    
    expression_data = []
    for gene in gene_models:
        row = {"gene_id": gene["gene_id"]}
        # Generate TPM values. Add small constant to avoid log(0) later.
        for i in range(num_lines):
            # Base expression + noise
            base = random.uniform(0.1, 100.0)
            noise = random.gauss(0, 1.0)
            val = max(0.0, base + noise)
            # Add small constant as per FR-001
            val += 1e-6
            row[f"line_{i}"] = val
        expression_data.append(row)
    
    write_csv(output_path, expression_data)
    logger.info(f"Generated expression data for {len(gene_models)} genes to {output_path}")
    return expression_data

def generate_population_pcs(output_path: str, num_lines: int = 200, seed: int = 42) -> List[Dict]:
    """Generates mock population structure PCs."""
    set_random_seed(seed)
    pcs = []
    for i in range(num_lines):
        pcs.append({
            "line_id": f"line_{i}",
            "PC1": random.gauss(0, 1),
            "PC2": random.gauss(0, 1),
            "PC3": random.gauss(0, 1)
        })
    write_csv(output_path, pcs, ["line_id", "PC1", "PC2", "PC3"])
    logger.info(f"Generated population PCs for {num_lines} lines to {output_path}")
    return pcs

def filter_monomorphic_tes(te_genotypes: List[Dict], min_freq: float = 0.05, max_freq: float = 0.95) -> Tuple[List[Dict], List[str]]:
    """Filters TE genotypes to keep only polymorphic TEs.
    
    Args:
        te_genotypes: List of TE genotype dicts with 'presence_vector'.
        min_freq: Minimum allele frequency (inclusive) to keep.
        max_freq: Maximum allele frequency (inclusive) to keep.
        
    Returns:
        Tuple of (filtered_tes, excluded_te_ids)
    """
    filtered = []
    excluded_ids = []
    
    for te in te_genotypes:
        presence_vector = te.get("presence_vector", [])
        if not presence_vector:
            excluded_ids.append(te["te_id"])
            logger.warning(f"TE {te['te_id']} has empty presence vector, excluding.")
            continue
        
        total_lines = len(presence_vector)
        count_present = sum(presence_vector)
        freq = count_present / total_lines
        
        if min_freq <= freq <= max_freq:
            filtered.append(te)
        else:
            excluded_ids.append(te["te_id"])
            logger.info(f"Excluding monomorphic TE {te['te_id']} (freq={freq:.4f}, outside [{min_freq}, {max_freq}])")
    
    logger.info(f"Filtered {len(excluded_ids)} monomorphic TEs. Retained {len(filtered)} polymorphic TEs.")
    return filtered, excluded_ids

def main():
    """Main entry point to generate and filter mock data."""
    seed = 42
    num_tes = 500
    num_lines = 200
    num_genes = 1000
    
    base_dir = "data"
    ensure_directory(os.path.join(base_dir, "raw"))
    ensure_directory(os.path.join(base_dir, "processed"))
    
    # 1. Generate Gene Models
    gene_models_path = os.path.join(base_dir, "raw", "gene_models.csv")
    gene_models = generate_gene_models(gene_models_path, num_genes=num_genes, seed=seed)
    
    # 2. Generate TE Genotypes (Raw)
    te_raw_path = os.path.join(base_dir, "raw", "te_genotypes_raw.csv")
    te_genotypes = generate_te_genotypes(te_raw_path, num_tes=num_tes, num_lines=num_lines, seed=seed)
    
    # 3. Filter Monomorphic TEs (T008 Implementation)
    # We need to convert the list of dicts to a format suitable for filtering
    # The generate_te_genotypes returns a list of dicts with 'presence_vector'
    
    filtered_tes, excluded_ids = filter_monomorphic_tes(te_genotypes, min_freq=0.05, max_freq=0.95)
    
    # Prepare data for CSV output
    # We need to flatten the presence_vector for CSV
    csv_data = []
    for te in filtered_tes:
        row = {
            "te_id": te["te_id"],
            "chrom": te["chrom"],
            "pos": te["pos"]
        }
        # Add presence for each line
        for i, val in enumerate(te["presence_vector"]):
            row[f"line_{i}"] = val
        csv_data.append(row)
    
    filtered_path = os.path.join(base_dir, "processed", "te_genotypes_polymorphic.csv")
    write_csv(filtered_path, csv_data)
    
    # Log exclusions to a text file
    exclusion_log_path = os.path.join(base_dir, "processed", "excluded_monomorphic_tes.txt")
    ensure_directory(exclusion_log_path)
    with open(exclusion_log_path, 'w') as f:
        f.write("Excluded Monomorphic TEs (FR-008)\n")
        f.write(f"Total Excluded: {len(excluded_ids)}\n")
        f.write("TE IDs:\n")
        for tid in excluded_ids:
            f.write(f"{tid}\n")
    
    logger.info(f"Polymorphic TE data written to {filtered_path}")
    logger.info(f"Exclusion log written to {exclusion_log_path}")
    
    # 4. Generate Expression Data
    expr_path = os.path.join(base_dir, "raw", "expression_data.csv")
    generate_expression_data(expr_path, gene_models, num_lines=num_lines, seed=seed+1)
    
    # 5. Generate Population PCs
    pcs_path = os.path.join(base_dir, "raw", "population_pcs.csv")
    generate_population_pcs(pcs_path, num_lines=num_lines, seed=seed+2)

if __name__ == "__main__":
    main()
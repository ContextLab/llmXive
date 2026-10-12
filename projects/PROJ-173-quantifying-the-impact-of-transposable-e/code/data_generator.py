import csv
import os
import random
import math
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import yaml

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
        # 10% chance to be monomorphic (all 0 or all 1)
        if random.random() < 0.1:
            is_present = 1 if random.random() > 0.5 else 0
            presence_vector = [is_present] * num_lines
        else:
            p = random.uniform(0.01, 0.99)
            presence_vector = [1 if random.random() < p else 0 for _ in range(num_lines)]

        te_data = {
            "te_id": te_id,
            "chrom": chrom,
            "pos": pos,
            "presence_vector": presence_vector
        }
        tes.append(te_data)

    # Return the raw list; writing is handled later after filtering
    return tes

def generate_expression_data(output_path: str, gene_models: List[Dict], num_lines: int = 200, seed: int = 42) -> List[Dict]:
    """Generates mock gene expression TPM matrix.

    Each gene receives a TPM value per line. Values are drawn from a
    log‑normal‑like distribution to emulate realistic expression variance.
    A small constant (1e‑6) is added to avoid zeros for downstream log2
    transformations (FR‑001).
    """
    set_random_seed(seed)
    expression_data = []
    for gene in gene_models:
        row = {"gene_id": gene["gene_id"]}

        for i in range(num_lines):
            # Simulate expression on a log‑scale: log_TPM ~ N(mu, sigma^2)
            # Choose mu uniformly between 0 and 5 (TPM ~ 1 to ~150)
            mu = random.uniform(0, 5)
            sigma = random.uniform(0.3, 1.0)  # realistic dispersion
            log_tpm = random.gauss(mu, sigma)
            tpm = max(0.0, math.exp(log_tpm))  # ensure non‑negative
            # Add tiny constant to avoid exact zero
            tpm += 1e-6
            row[f"line_{i}"] = tpm

        expression_data.append(row)

    write_csv(output_path, expression_data)
    logger.info(f"Generated expression data for {len(gene_models)} genes to {output_path}")
    return expression_data

def simulate_missing_expression_data(csv_path: str, missing_fraction: float = 0.05, seed: int = 42) -> None:
    """
    Introduces missing expression values for a random subset of lines.

    FR‑009 requires the pipeline to handle missing expression data by
    excluding affected lines from individual tests. This helper randomly
    selects a fraction of the line columns and replaces their values with
    empty strings in the CSV, representing missing data.
    """
    set_random_seed(seed)
    logger.info(f"Simulating missing expression data in {csv_path} (missing_fraction={missing_fraction})")
    # Load existing CSV
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        raise DataGenerationError(f"No columns found in expression CSV at {csv_path}")

    # Identify line columns (those that start with 'line_')
    line_cols = [col for col in fieldnames if col.startswith('line_')]
    if not line_cols:
        raise DataGenerationError("No line columns detected in expression data for missingness simulation.")

    # Determine how many line columns to corrupt
    num_missing = max(1, int(len(line_cols) * missing_fraction))
    missing_cols = random.sample(line_cols, num_missing)
    logger.info(f"Selected {num_missing} line columns to set as missing: {missing_cols}")

    # Insert missing values
    for row in rows:
        for col in missing_cols:
            row[col] = ""  # empty string denotes missing

    # Write back the CSV with missing entries
    write_csv(csv_path, rows, fieldnames)
    logger.info(f"Missing expression data simulation completed for {csv_path}")

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

def write_dataset_metadata(metadata_path: str) -> None:
    """Writes a minimal dataset metadata file marking TE‑aware quantification."""
    metadata = {
        "quantification_method": "TEaware",
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }
    ensure_directory(metadata_path)
    with open(metadata_path, 'w') as f:
        yaml.safe_dump(metadata, f)
    logger.info(f"Wrote dataset metadata with TE‑aware flag to {metadata_path}")

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

def generate_te_gene_pairs(
    output_path: str,
    gene_models: List[Dict],
    te_genotypes: List[Dict],
    max_dist: int = 5000
) -> List[Dict]:
    """
    Simulates TE‑Gene pairing logic.

    For each TE, computes the distance to each gene's TSS and TES.
    A pair is marked `proximity_flag = True` if the minimum distance
    is less than or equal to `max_dist` (≤5 kb).  If a TE is proximal
    to more than one gene, all those pairs receive `ambiguous_flag = True`.

    The resulting list of dictionaries is written to CSV and also
    returned for downstream use.
    """
    logger.info("Generating TE‑Gene pairing metadata")
    # Build a lookup of gene info by chromosome for faster access
    genes_by_chrom: Dict[str, List[Dict]] = {}
    for gene in gene_models:
        genes_by_chrom.setdefault(gene["chrom"], []).append(gene)

    # First pass: compute distances and provisional flags
    pair_records: List[Dict] = []
    te_to_gene_matches: Dict[str, List[Dict]] = {}

    for te in te_genotypes:
        te_id = te["te_id"]
        te_chrom = te["chrom"]
        te_pos = te["pos"]
        matches = []

        for gene in genes_by_chrom.get(te_chrom, []):
            # Distance to TSS and TES; take the smaller absolute distance
            dist_tss = abs(te_pos - gene["tss"])
            dist_tes = abs(te_pos - gene["tes"])
            distance = min(dist_tss, dist_tes)

            proximity_flag = distance <= max_dist
            record = {
                "te_id": te_id,
                "gene_id": gene["gene_id"],
                "te_chrom": te_chrom,
                "gene_chrom": gene["chrom"],
                "te_pos": te_pos,
                "gene_tss": gene["tss"],
                "gene_tes": gene["tes"],
                "distance": distance,
                "proximity_flag": proximity_flag,
                # temporary, will be overwritten if ambiguous
                "ambiguous_flag": False
            }
            pair_records.append(record)
            if proximity_flag:
                matches.append(record)

        te_to_gene_matches[te_id] = matches

    # Second pass: set ambiguous_flag where needed
    for te_id, matches in te_to_gene_matches.items():
        if len(matches) > 1:
            # Mark all proximal matches for this TE as ambiguous
            for match in matches:
                # Find the corresponding entry in pair_records and update
                for rec in pair_records:
                    if (rec["te_id"] == te_id and rec["gene_id"] == match["gene_id"]
                        and rec["proximity_flag"]):
                        rec["ambiguous_flag"] = True

    # Write to CSV
    fieldnames = [
        "te_id", "gene_id", "te_chrom", "gene_chrom", "te_pos",
        "gene_tss", "gene_tes", "distance", "proximity_flag", "ambiguous_flag"
    ]
    write_csv(output_path, pair_records, fieldnames)
    logger.info(f"Wrote TE‑Gene pairing file with {len(pair_records)} rows to {output_path}")
    return pair_records

def main():
    """Main entry point to generate and filter mock data."""
    seed = 42
    num_tes = 500
    num_lines = 200
    num_genes = 1000

    # Base directories
    base_dir = "data"
    raw_dir = os.path.join(base_dir, "raw")
    processed_dir = os.path.join(base_dir, "processed")
    mock_dir = os.path.join(base_dir, "mock")

    # Ensure directories exist
    ensure_directory(raw_dir)
    ensure_directory(processed_dir)
    ensure_directory(mock_dir)

    # 1. Generate Gene Models (raw)
    gene_models_path = os.path.join(raw_dir, "gene_models.csv")
    gene_models = generate_gene_models(gene_models_path, num_genes=num_genes, seed=seed)

    # 2. Generate TE Genotypes (raw)
    te_raw_path = os.path.join(raw_dir, "te_genotypes_raw.csv")
    # The raw TE file is not written directly; we keep the list for filtering.
    te_genotypes = generate_te_genotypes(te_raw_path, num_tes=num_tes, num_lines=num_lines, seed=seed)

    # 3. Filter Monomorphic TEs (T008)
    filtered_tes, excluded_ids = filter_monomorphic_tes(te_genotypes, min_freq=0.05, max_freq=0.95)

    # Write filtered TE genotypes to the mock folder (polymorphic only)
    te_polymorphic_path = os.path.join(mock_dir, "te_genotypes.csv")
    te_csv_data = []
    for te in filtered_tes:
        row = {
            "te_id": te["te_id"],
            "chrom": te["chrom"],
            "pos": te["pos"]
        }
        for i, val in enumerate(te["presence_vector"]):
            row[f"line_{i}"] = val
        te_csv_data.append(row)
    write_csv(te_polymorphic_path, te_csv_data)
    logger.info(f"Polymorphic TE data written to {te_polymorphic_path}")

    # Log exclusions (optional)
    exclusion_log_path = os.path.join(processed_dir, "excluded_monomorphic_tes.txt")
    with open(exclusion_log_path, 'w') as f:
        f.write("Excluded Monomorphic TEs (FR-008)\n")
        f.write(f"Total Excluded: {len(excluded_ids)}\n")
        f.write("TE IDs:\n")
        for tid in excluded_ids:
            f.write(f"{tid}\n")
    logger.info(f"Exclusion log written to {exclusion_log_path}")

    # 4. Generate TE‑Gene pairing metadata (T006A)
    te_gene_pairs_path = os.path.join(mock_dir, "te_gene_pairs.csv")
    generate_te_gene_pairs(te_gene_pairs_path, gene_models, filtered_tes, max_dist=5000)

    # 5. Generate Expression Data (mock)
    expr_path = os.path.join(mock_dir, "gene_expression.csv")
    generate_expression_data(expr_path, gene_models, num_lines=num_lines, seed=seed + 1)

    # 6. Simulate missing expression data for specific lines (FR-009)
    simulate_missing_expression_data(expr_path, missing_fraction=0.05, seed=seed + 3)

    # 7. Generate Population PCs (mock)
    pcs_path = os.path.join(mock_dir, "population_pcs.csv")
    generate_population_pcs(pcs_path, num_lines=num_lines, seed=seed + 2)

    # 8. Write dataset metadata with TE‑aware flag (Constitution Principle VII)
    metadata_path = os.path.join(mock_dir, "dataset_metadata.yaml")
    write_dataset_metadata(metadata_path)

    logger.info("Mock data generation completed successfully.")

if __name__ == "__main__":
    main()
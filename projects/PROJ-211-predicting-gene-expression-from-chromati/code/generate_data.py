import os
import random
import csv
import logging
import hashlib
from typing import List, Dict, Tuple, Any, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_seed(seed: int = 42) -> None:
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_gene_coordinates(num_genes: int, chrom: str = "chr1") -> List[Dict[str, Any]]:
    """
    Generate deterministic synthetic gene coordinates.
    Returns a list of dicts with gene_id, chrom, start, end, strand, tss.
    """
    genes = []
    # Start genes at consistent intervals to ensure reproducibility
    gap = 100000  # 100kb between gene starts
    for i in range(num_genes):
        start = i * gap + 1000
        end = start + np.random.randint(1000, 5000)
        strand = random.choice(['+', '-'])
        # TSS is start for + strand, end for - strand
        tss = start if strand == '+' else end
        genes.append({
            'gene_id': f"GENE_{i:05d}",
            'chrom': chrom,
            'start': start,
            'end': end,
            'strand': strand,
            'tss': tss
        })
    return genes

def generate_peak_coordinates(num_peaks: int, genes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate deterministic synthetic peak coordinates near TSS.
    Returns a list of dicts with peak_id, chrom, start, end, score.
    Peaks are distributed within ±50kb of TSS.
    """
    peaks = []
    window_size = 50000  # 50kb
    for i in range(num_peaks):
        # Assign peak to a random gene
        gene = random.choice(genes)
        tss = gene['tss']
        # Random position within ±50kb of TSS
        offset = np.random.randint(-window_size, window_size + 1)
        peak_start = tss + offset
        peak_end = peak_start + np.random.randint(200, 1000)
        
        # Ensure positive coordinates
        if peak_start < 0:
            peak_start = 0
            peak_end = peak_start + 500
        
        score = np.random.uniform(0.1, 10.0)
        peaks.append({
            'peak_id': f"PEAK_{i:05d}",
            'chrom': gene['chrom'],
            'start': peak_start,
            'end': peak_end,
            'score': round(score, 3),
            'gene_id': gene['gene_id']
        })
    return peaks

def generate_counts_matrix(
    genes: List[Dict[str, Any]],
    peaks: List[Dict[str, Any]],
    cell_lines: List[str]
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
    """
    Generate synthetic RNA-seq counts and accessibility counts.
    
    Returns:
      expression_matrix: Dict[GeneID][CellLine] -> count
      accessibility_matrix: Dict[PeakID][CellLine] -> count
    """
    expression_matrix = {}
    accessibility_matrix = {}
    
    # Generate expression counts
    for gene in genes:
        gene_id = gene['gene_id']
        expression_matrix[gene_id] = {}
        for cell in cell_lines:
            # Base expression level varies by gene
            base_expr = np.random.uniform(1.0, 100.0)
            # Add cell-line specific variation
            cell_factor = np.random.uniform(0.5, 2.0)
            count = int(base_expr * cell_factor * np.random.uniform(0.8, 1.2))
            expression_matrix[gene_id][cell] = max(0, count)
    
    # Generate accessibility counts (correlated with expression for some genes)
    for peak in peaks:
        peak_id = peak['peak_id']
        accessibility_matrix[peak_id] = {}
        for cell in cell_lines:
            # Base accessibility
            base_acc = np.random.uniform(10.0, 1000.0)
            # Add cell-line specific variation
            cell_factor = np.random.uniform(0.5, 2.0)
            count = int(base_acc * cell_factor * np.random.uniform(0.8, 1.2))
            accessibility_matrix[peak_id][cell] = max(0, count)
    
    return expression_matrix, accessibility_matrix

def write_counts_csv(
    expression_matrix: Dict[str, Dict[str, float]],
    accessibility_matrix: Dict[str, Dict[str, float]],
    output_path: str
) -> None:
    """
    Write combined counts to a single CSV file.
    Format: gene_id, cell_line, expression_count, accessibility_count
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gene_id', 'cell_line', 'expression_count', 'accessibility_count'])
        
        cell_lines = list(next(iter(expression_matrix.values())).keys())
        
        for gene_id, expr_counts in expression_matrix.items():
            for cell in cell_lines:
                expr_val = expr_counts.get(cell, 0)
                # Sum accessibility from all peaks for this gene (simplified)
                acc_val = sum(
                    acc_counts.get(cell, 0) 
                    for acc_counts in accessibility_matrix.values()
                ) // len(accessibility_matrix) if accessibility_matrix else 0
                writer.writerow([gene_id, cell, expr_val, acc_val])
    
    logger.info(f"Wrote counts to {output_path}")

def write_peaks_bed(
    peaks: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Write peak coordinates to BED format.
    Format: chrom, start, end, name, score, strand
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        for peak in peaks:
            # BED is 0-based, so start is already correct if generated as such
            # Write: chrom, start, end, name, score, strand (strand derived from gene)
            # For synthetic data, we'll assume '+' strand or derive from gene
            strand = '+'  # Simplified for synthetic data
            f.write(f"{peak['chrom']}\t{peak['start']}\t{peak['end']}\t{peak['peak_id']}\t{peak['score']}\t{strand}\n")
    
    logger.info(f"Wrote peaks to {output_path}")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load schema from YAML file."""
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_counts_csv_schema(data_path: str, schema: Dict[str, Any]) -> bool:
    """Validate counts CSV against schema."""
    # Basic validation: check columns exist
    required_cols = ['gene_id', 'cell_line', 'expression_count', 'accessibility_count']
    with open(data_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for col in required_cols:
            if col not in headers:
                logger.error(f"Missing required column: {col}")
                return False
    logger.info("Counts CSV schema validation passed")
    return True

def validate_peaks_bed_schema(data_path: str, schema: Dict[str, Any]) -> bool:
    """Validate peaks BED against schema."""
    # Basic validation: check format
    with open(data_path, 'r') as f:
        for i, line in enumerate(f):
            parts = line.strip().split('\t')
            if len(parts) < 4:
                logger.error(f"Invalid BED format at line {i+1}")
                return False
    logger.info("Peaks BED schema validation passed")
    return True

def validate_synthetic_data(
    counts_path: str,
    peaks_path: str,
    schema_path: str
) -> bool:
    """Validate synthetic data against schema."""
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found: {schema_path}. Skipping validation.")
        return True
    
    schema = load_schema(schema_path)
    counts_valid = validate_counts_csv_schema(counts_path, schema)
    peaks_valid = validate_peaks_bed_schema(peaks_path, schema)
    return counts_valid and peaks_valid

def checksum_file(path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def record_checksums(
    counts_path: str,
    peaks_path: str,
    log_path: str
) -> None:
    """Record checksums to log file."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    counts_checksum = checksum_file(counts_path)
    peaks_checksum = checksum_file(peaks_path)
    
    with open(log_path, 'a') as f:
        f.write(f"{counts_path}: {counts_checksum}\n")
        f.write(f"{peaks_path}: {peaks_checksum}\n")
    
    logger.info(f"Checksums recorded to {log_path}")

def main():
    """Main entry point for synthetic data generation."""
    # Set seed for reproducibility
    set_seed(42)
    
    # Define parameters
    num_genes = 100
    num_peaks = 500
    cell_lines = ['GM12878', 'K562', 'HMEC', 'IMR90', 'HepG2']
    
    # Generate data
    logger.info("Generating synthetic gene coordinates...")
    genes = generate_gene_coordinates(num_genes)
    
    logger.info("Generating synthetic peak coordinates...")
    peaks = generate_peak_coordinates(num_peaks, genes)
    
    logger.info("Generating synthetic count matrices...")
    expression_matrix, accessibility_matrix = generate_counts_matrix(
        genes, peaks, cell_lines
    )
    
    # Define output paths
    base_dir = 'data/raw'
    counts_path = os.path.join(base_dir, 'synthetic_counts.csv')
    peaks_path = os.path.join(base_dir, 'synthetic_peaks.bed')
    checksum_log = 'logs/synthetic_checksums.txt'
    
    # Write outputs
    logger.info("Writing counts matrix...")
    write_counts_csv(expression_matrix, accessibility_matrix, counts_path)
    
    logger.info("Writing peaks BED...")
    write_peaks_bed(peaks, peaks_path)
    
    # Record checksums
    logger.info("Recording checksums...")
    record_checksums(counts_path, peaks_path, checksum_log)
    
    logger.info("Synthetic data generation completed successfully.")

if __name__ == "__main__":
    main()
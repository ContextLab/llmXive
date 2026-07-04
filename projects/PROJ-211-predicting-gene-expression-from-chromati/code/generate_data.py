import os
import random
import csv
import logging
from typing import List, Dict, Tuple, Any
import numpy as np

def set_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def generate_gene_coordinates(n_genes: int = 10000) -> List[Dict[str, Any]]:
    """Generate synthetic gene coordinates."""
    genes = []
    chromosomes = [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY"]
    
    for i in range(n_genes):
        chrom = random.choice(chromosomes)
        start = random.randint(1, 50_000_000)
        end = start + random.randint(1000, 50000)
        strand = random.choice(["+", "-"])
        gene_id = f"GENE{i:05d}"
        genes.append({
            "gene_id": gene_id,
            "chrom": chrom,
            "start": start,
            "end": end,
            "strand": strand,
            "tss": start if strand == "+" else end
        })
    
    return genes

def generate_peak_coordinates(n_peaks: int = 10000) -> List[Dict[str, Any]]:
    """Generate synthetic peak coordinates."""
    peaks = []
    chromosomes = [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY"]
    
    for i in range(n_peaks):
        chrom = random.choice(chromosomes)
        start = random.randint(1, 50_000_000)
        end = start + random.randint(200, 2000)
        peaks.append({
            "peak_id": f"PEAK{i:05d}",
            "chrom": chrom,
            "start": start,
            "end": end,
            "score": random.randint(1, 1000)
        })
    
    return peaks

def generate_counts_matrix(
    n_genes: int,
    n_cells: int,
    n_peaks: int,
    cell_lines: List[str]
) -> Dict[str, Any]:
    """Generate synthetic count matrices for RNA-seq and accessibility."""
    # Generate expression counts (RNA-seq)
    expression_counts = {}
    for cell_line in cell_lines:
        expression_counts[cell_line] = np.random.negative_binomial(
            n=5, p=0.3, size=(n_genes, n_peaks)
        ).astype(int)
    
    # Generate accessibility counts (DNase-seq/ATAC-seq)
    accessibility_counts = {}
    for cell_line in cell_lines:
        accessibility_counts[cell_line] = np.random.negative_binomial(
            n=3, p=0.4, size=(n_genes, n_peaks)
        ).astype(int)
    
    return {
        "expression": expression_counts,
        "accessibility": accessibility_counts
    }

def write_counts_csv(
    counts: Dict[str, Any],
    genes: List[Dict[str, Any]],
    output_path: str
) -> None:
    """Write expression counts to CSV file."""
    cell_lines = list(counts["expression"].keys())
    n_genes = len(genes)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        header = ["gene_id", "chrom", "start", "end", "strand"]
        for cell_line in cell_lines:
            header.extend([f"{cell_line}_expr", f"{cell_line}_access"])
        writer.writerow(header)
        
        # Data rows
        for i, gene in enumerate(genes):
            row = [
                gene["gene_id"],
                gene["chrom"],
                gene["start"],
                gene["end"],
                gene["strand"]
            ]
            for cell_line in cell_lines:
                # Aggregate counts across peaks for each gene to create a summary row
                # This matches the expected schema where rows are genes and columns are cell-line-specific metrics
                row.append(int(counts["expression"][cell_line][i, :].mean()))
                row.append(int(counts["accessibility"][cell_line][i, :].mean()))
            writer.writerow(row)

def write_peaks_bed(
    peaks: List[Dict[str, Any]],
    output_path: str
) -> None:
    """Write peak coordinates to BED file."""
    with open(output_path, 'w') as f:
        for peak in peaks:
            f.write(f"{peak['chrom']}\t{peak['start']}\t{peak['end']}\t{peak['peak_id']}\t{peak['score']}\n")

def main():
    """Main entry point for synthetic data generation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Parameters
    seed = 42
    n_genes = 10000
    n_peaks = 10000
    cell_lines = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
    
    # Set seed for reproducibility
    set_seed(seed)
    logger.info(f"Set random seed to {seed}")
    
    # Generate coordinates
    logger.info("Generating gene coordinates...")
    genes = generate_gene_coordinates(n_genes)
    
    logger.info("Generating peak coordinates...")
    peaks = generate_peak_coordinates(n_peaks)
    
    # Generate counts
    logger.info("Generating count matrices...")
    counts = generate_counts_matrix(n_genes, len(cell_lines), n_peaks, cell_lines)
    
    # Determine output paths relative to project root
    # Assuming script is in code/, project root is parent of code/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_raw_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(data_raw_dir, exist_ok=True)
    
    counts_path = os.path.join(data_raw_dir, "synthetic_counts.csv")
    peaks_path = os.path.join(data_raw_dir, "synthetic_peaks.bed")
    
    # Write outputs
    logger.info(f"Writing counts to {counts_path}...")
    write_counts_csv(counts, genes, counts_path)
    
    logger.info(f"Writing peaks to {peaks_path}...")
    write_peaks_bed(peaks, peaks_path)
    
    logger.info("Data generation complete!")
    logger.info(f"Generated {len(genes)} genes and {len(peaks)} peaks for {len(cell_lines)} cell lines.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
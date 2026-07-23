"""
Phylogenetic analysis module for plant pathogen virulence prediction.

This module handles:
1. Extraction of core housekeeping genes (rpoB, gyrB, 16S) from genome assemblies.
2. Construction of phylogenetic trees using Maximum Likelihood.
3. Generation of phylogenetic covariance matrices for PGLS.
"""

import os
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import Align
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio.Phylo import BaseTree

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Housekeeping gene identifiers (common naming conventions)
HOUSEKEEPING_GENES = ['rpoB', 'gyrB', '16S', 'rpoC', 'dnaK', 'gyrA']

@dataclass
class PhylogenyResult:
    """Container for phylogenetic analysis results."""
    tree_path: str
    covariance_matrix_path: str
    extracted_genes_count: int
    isolates_processed: List[str]
    success: bool
    error_message: Optional[str] = None

def find_housekeeping_genes(genome_path: Path) -> List[SeqRecord]:
    """
    Extract core housekeeping genes from a genome assembly.

    Searches for genes by name in the FASTA file. If the file contains
    annotated features (e.g., GenBank), it looks for CDS with gene names.
    For raw FASTA, it searches headers for gene identifiers.

    Args:
        genome_path: Path to the genome assembly file (.fna, .fa, .fasta).

    Returns:
        List of SeqRecord objects for found housekeeping genes.
    """
    found_genes = []
    try:
        # Try to parse as GenBank first if available, otherwise FASTA
        if genome_path.suffix.lower() in ['.gb', '.gbk', '.gbff']:
            for record in SeqIO.parse(str(genome_path), 'genbank'):
                for feature in record.features:
                    if feature.type == 'CDS':
                        gene_name = feature.qualifiers.get('gene', [None])[0]
                        if gene_name and gene_name.lower() in HOUSEKEEPING_GENES:
                            found_genes.append(feature.extract(record.seq))
                            logger.info(f"Found {gene_name} in {genome_path.name}")
        else:
            # Standard FASTA search
            for record in SeqIO.parse(str(genome_path), 'fasta'):
                header_lower = record.description.lower()
                for gene in HOUSEKEEPING_GENES:
                    if gene.lower() in header_lower:
                        found_genes.append(record)
                        logger.info(f"Found {gene} in {genome_path.name} (header match)")
                        break
    except Exception as e:
        logger.error(f"Error parsing {genome_path}: {e}")
        raise

    return found_genes

def concatenate_genes(gene_records: List[SeqRecord]) -> SeqRecord:
    """
    Concatenate multiple gene sequences into a single supermatrix record.

    Args:
        gene_records: List of SeqRecord objects for individual genes.

    Returns:
        Single SeqRecord with concatenated sequence.
    """
    if not gene_records:
        raise ValueError("No gene records provided for concatenation")

    # Sort by gene name to ensure consistent ordering
    sorted_genes = sorted(gene_records, key=lambda x: x.id)

    concatenated_seq = Seq('')
    for record in sorted_genes:
        concatenated_seq += record.seq

    # Create new record with combined ID
    combined_id = "_".join([r.id.split()[0] for r in sorted_genes])
    combined_desc = f"Concatenated genes: {', '.join([r.id for r in sorted_genes])}"

    return SeqRecord(
        seq=concatenated_seq,
        id=combined_id,
        description=combined_desc
    )

def align_sequences(seq_records: List[SeqRecord], output_path: Path) -> Path:
    """
    Align multiple sequences using MUSCLE (or ClustalW if MUSCLE unavailable).

    Args:
        seq_records: List of SeqRecord objects to align.
        output_path: Path to save the alignment.

    Returns:
        Path to the alignment file.
    """
    if len(seq_records) < 2:
        raise ValueError("Need at least 2 sequences to perform alignment")

    # Write temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as tmp_in:
        SeqIO.write(seq_records, tmp_in, 'fasta')
        tmp_in_path = tmp_in.name

    try:
        # Try MUSCLE first
        try:
            subprocess.run(
                ['muscle', '-in', tmp_in_path, '-out', str(output_path)],
                check=True,
                capture_output=True
            )
            logger.info("Alignment completed with MUSCLE")
        except FileNotFoundError:
            # Fallback to ClustalW
            logger.warning("MUSCLE not found, trying ClustalW...")
            subprocess.run(
                ['clustalw', '-INFILE=' + tmp_in_path, '-OUTPUT=FASTA'],
                check=True,
                capture_output=True
            )
            # ClustalW outputs to .aln by default
            aln_path = Path(tmp_in_path).with_suffix('.aln')
            if aln_path.exists():
                # Convert to FASTA if needed or rename
                shutil.move(str(aln_path), str(output_path))
            else:
                raise RuntimeError("ClustalW did not produce expected output")

        return output_path
    finally:
        os.unlink(tmp_in_path)

def build_tree(alignment_path: Path, tree_output_path: Path) -> Path:
    """
    Build a phylogenetic tree using Distance Matrix method (Neighbor-Joining)
    as a robust fallback when IQ-TREE/RAxML are not available.

    Args:
        alignment_path: Path to the multiple sequence alignment file.
        tree_output_path: Path to save the resulting tree.

    Returns:
        Path to the tree file.
    """
    # Read alignment
    alignment = Align.MultipleSeqAlignment(list(SeqIO.parse(str(alignment_path), 'fasta')))

    if len(alignment) < 3:
        raise ValueError("Need at least 3 sequences to build a meaningful tree")

    # Calculate distance matrix
    calculator = DistanceCalculator('identity')
    dm = calculator.get_distance(alignment)

    # Build tree using Neighbor-Joining
    constructor = DistanceTreeConstructor()
    tree = constructor.nj(dm)

    # Root the tree (midpoint rooting if unrooted, or arbitrary if small)
    if tree.root is None:
        try:
            tree.root_with_outgroup(alignment[0].seq)
        except Exception:
            # Fallback: just set root if midpoint fails
            pass

    # Write tree
    SeqIO.write([tree], str(tree_output_path), 'newick')
    logger.info(f"Tree built and saved to {tree_output_path}")

    return tree_output_path

def compute_covariance_matrix(tree_path: Path, output_path: Path) -> Path:
    """
    Compute the phylogenetic covariance matrix from a tree.

    Uses patristic distances (sum of branch lengths) between all pairs of taxa.

    Args:
        tree_path: Path to the Newick tree file.
        output_path: Path to save the numpy array.

    Returns:
        Path to the saved .npy file.
    """
    import numpy as np

    tree = BaseTree.Tree.read(str(tree_path), 'newick')

    # Get tip names
    tips = [leaf.name for leaf in tree.get_terminals()]
    n = len(tips)

    # Initialize covariance matrix
    # For Brownian motion model, covariance is proportional to shared branch length
    # We compute the patristic distance matrix and convert to covariance
    dist_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(i, n):
            if i == j:
                dist_matrix[i, j] = 0.0
            else:
                # Calculate patristic distance
                try:
                    d = tree.distance(tips[i], tips[j])
                    dist_matrix[i, j] = d
                    dist_matrix[j, i] = d
                except KeyError:
                    logger.warning(f"Could not find distance between {tips[i]} and {tips[j]}")
                    dist_matrix[i, j] = 1e6 # Large distance for missing
                    dist_matrix[j, i] = 1e6

    # Convert distance to covariance (simplified Brownian motion)
    # Cov = (TotalTreeLength - Distance) / 2  (conceptually)
    # Or simply use the distance matrix directly for PGLS if the library expects it
    # Here we save the distance matrix which can be converted by the PGLS solver
    # or we compute the shared path length.
    # Let's compute the shared path length (height of MRCA) as covariance.
    
    # For simplicity in this implementation, we save the distance matrix
    # and note that PGLS implementations often accept the distance matrix
    # or require a specific covariance structure derived from it.
    # We will save the distance matrix as the 'phylogenetic covariance' proxy.
    # A more rigorous implementation would calculate the variance-covariance
    # matrix based on branch lengths from root to MRCA.

    # Rigorous calculation of V (Covariance) under Brownian Motion:
    # V_ij = height of MRCA(i, j)
    # We need to traverse the tree to find MRCA height.
    
    # Since Bio.Phylo doesn't have a direct MRCA height calculator for all pairs easily,
    # we will use the distance matrix approach which is standard input for many PGLS tools
    # or compute V_ij = (D_ii + D_jj - D_ij) / 2 if D_ii = D_jj = root-to-tip.
    # Assuming ultrametric or approximating:
    
    # Calculate root-to-tip distances
    root_to_tip = [tree.distance(tree.root, tip) for tip in tips]
    avg_root_to_tip = np.mean(root_to_tip)
    
    # Estimate Covariance: V_ij = (root_to_tip[i] + root_to_tip[j] - D_ij) / 2
    cov_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                cov_matrix[i, j] = avg_root_to_tip # Variance
            else:
                cov_matrix[i, j] = (root_to_tip[i] + root_to_tip[j] - dist_matrix[i, j]) / 2.0
                # Ensure non-negative
                if cov_matrix[i, j] < 0:
                    cov_matrix[i, j] = 0.0

    np.save(str(output_path), cov_matrix)
    logger.info(f"Covariance matrix saved to {output_path}")

    return output_path

def run_phylogeny_pipeline(
    raw_data_dir: Path,
    output_dir: Path,
    min_isolates: int = 2
) -> PhylogenyResult:
    """
    Execute the full phylogenetic pipeline:
    1. Extract housekeeping genes from raw genomes.
    2. Concatenate genes per isolate.
    3. Align sequences.
    4. Build tree.
    5. Compute covariance matrix.

    Args:
        raw_data_dir: Directory containing raw genome assemblies (.fna).
        output_dir: Directory to save intermediate and final results.
        min_isolates: Minimum number of isolates required to proceed.

    Returns:
        PhylogenyResult object containing paths and status.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Starting phylogeny pipeline in {raw_data_dir}")

    # 1. Extract genes
    all_concatenated = []
    processed_isolates = []

    genome_files = list(raw_data_dir.glob('*.fna')) + list(raw_data_dir.glob('*.fa')) + list(raw_data_dir.glob('*.fasta'))
    
    if not genome_files:
        raise FileNotFoundError(f"No genome files found in {raw_data_dir}")

    for genome_file in genome_files:
        try:
            genes = find_housekeeping_genes(genome_file)
            if genes:
                concat_rec = concatenate_genes(genes)
                all_concatenated.append(concat_rec)
                processed_isolates.append(concat_rec.id)
                logger.info(f"Processed {genome_file.name}: {len(genes)} genes found")
            else:
                logger.warning(f"No housekeeping genes found in {genome_file.name}")
        except Exception as e:
            logger.error(f"Failed to process {genome_file.name}: {e}")
            continue

    if len(processed_isolates) < min_isolates:
        raise ValueError(f"Insufficient isolates with housekeeping genes: {len(processed_isolates)} < {min_isolates}")

    # 2. Write concatenated sequences
    concat_file = output_dir / 'concatenated_genes.fasta'
    SeqIO.write(all_concatenated, str(concat_file), 'fasta')

    # 3. Align
    alignment_file = output_dir / 'alignment.fasta'
    align_sequences(all_concatenated, alignment_file)

    # 4. Build Tree
    tree_file = output_dir / 'tree.newick'
    build_tree(alignment_file, tree_file)

    # 5. Compute Covariance
    cov_file = output_dir / 'phylo_covariance_matrix.npy'
    compute_covariance_matrix(tree_file, cov_file)

    return PhylogenyResult(
        tree_path=str(tree_file),
        covariance_matrix_path=str(cov_file),
        extracted_genes_count=len(all_concatenated),
        isolates_processed=processed_isolates,
        success=True
    )

def main():
    """Main entry point for the phylogeny module."""
    # Define paths based on project structure
    raw_data_dir = Path('data/raw')
    output_dir = Path('data/processed')

    if not raw_data_dir.exists():
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        return

    try:
        result = run_phylogeny_pipeline(raw_data_dir, output_dir)
        if result.success:
            logger.info(f"Pipeline completed successfully. Processed {result.extracted_genes_count} isolates.")
            logger.info(f"Tree saved to: {result.tree_path}")
            logger.info(f"Covariance matrix saved to: {result.covariance_matrix_path}")
        else:
            logger.error(f"Pipeline failed: {result.error_message}")
    except Exception as e:
        logger.critical(f"Fatal error in phylogeny pipeline: {e}")
        raise

if __name__ == '__main__':
    main()

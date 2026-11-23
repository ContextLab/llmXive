"""
Phylogenetic analysis module for plant pathogen virulence prediction.

This module handles:
1. Extraction of core housekeeping genes (rpoB, gyrB, 16S for bacteria; RPB1, RPB2 for fungi)
2. Concatenation of gene sequences
3. Multiple sequence alignment
4. Phylogenetic tree construction using Maximum Likelihood
5. Computation of phylogenetic covariance matrix
"""

import os
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, NamedTuple

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import AlignIO
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio.Phylo.Applications import FasttreeCommandline
import numpy as np

from src.utils.errors import AnalysisError, handle_analysis_error

logger = logging.getLogger(__name__)

# Housekeeping gene identifiers for bacteria
BACTERIAL_HOUSEKEEPING_GENES = ['rpoB', 'gyrB', '16S']
# Alternative housekeeping genes for fungi (e.g., Fusarium)
FUNGAL_HOUSEKEEPING_GENES = ['RPB1', 'RPB2', 'TEF1']

class PhylogenyResult(NamedTuple):
    """Result of phylogenetic analysis pipeline."""
    housekeeping_fasta: Path
    alignment_fasta: Path
    tree_newick: Path
    covariance_matrix: np.ndarray
    species_list: List[str]

@handle_analysis_error
def find_housekeeping_genes(genome_path: Path, output_dir: Path, is_fungal: bool = False) -> Dict[str, Path]:
    """
    Extract core housekeeping genes from a genome assembly.
    
    Args:
        genome_path: Path to the genome assembly file (.fna)
        output_dir: Directory to write extracted gene sequences
        is_fungal: Whether the organism is fungal (uses RPB1/RPB2 instead of rpoB/gyrB)
    
    Returns:
        Dictionary mapping gene name to extracted FASTA file path
    
    Raises:
        AnalysisError: If no housekeeping genes are found
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define gene identifiers based on organism type
    if is_fungal:
        target_genes = FUNGAL_HOUSEKEEPING_GENES
    else:
        target_genes = BACTERIAL_HOUSEKEEPING_GENES
    
    logger.info(f"Searching for housekeeping genes {target_genes} in {genome_path}")
    
    # Read genome sequences
    sequences = list(SeqIO.parse(str(genome_path), "fasta"))
    
    if not sequences:
        raise AnalysisError(f"No sequences found in {genome_path}")
    
    extracted_genes = {}
    
    # Use prodigal for bacterial genomes to predict ORFs and search for housekeeping genes
    # For simplicity in this implementation, we'll search by sequence similarity or HMM
    # In a production system, we'd use HMMER with PFAM profiles for these genes
    
    for seq_record in sequences:
        seq_str = str(seq_record.seq).upper()
        
        # Search for housekeeping genes by sequence patterns or exact matches
        # In practice, this would use HMMER or BLAST against reference sequences
        for gene in target_genes:
            # Check if gene name appears in description (common in NCBI downloads)
            if gene in seq_record.description.upper():
                gene_output = output_dir / f"{seq_record.id}_{gene}.fasta"
                SeqIO.write(seq_record, str(gene_output), "fasta")
                extracted_genes[gene] = gene_output
                logger.info(f"Found {gene} in {seq_record.id}")
    
    # If no genes found by description, attempt to use HMMER (if available)
    if not extracted_genes:
        logger.warning("No housekeeping genes found by description. Attempting HMMER search...")
        extracted_genes = _hmm_search_genes(sequences, target_genes, output_dir)
    
    if not extracted_genes:
        raise AnalysisError(
            f"Could not extract any housekeeping genes from {genome_path}. "
            f"Tried: {target_genes}. This may indicate a fungal genome where "
            f"bacterial markers (rpoB, gyrB, 16S) are absent. Consider using fungal markers (RPB1, RPB2)."
        )
    
    return extracted_genes

def _hmm_search_genes(sequences: List[SeqRecord], target_genes: List[str], output_dir: Path) -> Dict[str, Path]:
    """
    Use HMMER to search for housekeeping genes (placeholder for production implementation).
    
    In a full implementation, this would:
    1. Download PFAM HMM profiles for housekeeping genes
    2. Run hmmscan against the genome
    3. Extract sequences matching the HMM profiles
    
    For now, this returns empty dict to indicate failure.
    """
    # Check if hmmsearch is available
    try:
        result = subprocess.run(['which', 'hmmsearch'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("hmmsearch not found in PATH. Skipping HMM search.")
            return {}
    except FileNotFoundError:
        logger.warning("hmmsearch not found in PATH. Skipping HMM search.")
        return {}
    
    # Production implementation would go here
    # For now, return empty to indicate we couldn't find genes
    return {}

@handle_analysis_error
def concatenate_genes(gene_files: Dict[str, Path], output_path: Path) -> Path:
    """
    Concatenate multiple gene FASTA files into a single multi-FASTA file.
    
    Args:
        gene_files: Dictionary mapping gene name to FASTA file path
        output_path: Path to write concatenated sequences
    
    Returns:
        Path to the concatenated FASTA file
    """
    all_sequences = []
    
    for gene_name, gene_file in sorted(gene_files.items()):
        for record in SeqIO.parse(str(gene_file), "fasta"):
            # Rename record to include gene name for clarity
            record.id = f"{record.id}_{gene_name}"
            record.description = ""
            all_sequences.append(record)
    
    SeqIO.write(all_sequences, str(output_path), "fasta")
    logger.info(f"Wrote {len(all_sequences)} sequences to {output_path}")
    
    return output_path

@handle_analysis_error
def align_sequences(input_fasta: Path, output_path: Path) -> Path:
    """
    Perform multiple sequence alignment using MUSCLE or MAFFT.
    
    Args:
        input_fasta: Path to input FASTA file
        output_path: Path to write aligned sequences
    
    Returns:
        Path to the aligned FASTA file
    """
    # Check for available aligners
    aligner = None
    for cmd in ['mafft', 'muscle']:
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            if result.returncode == 0:
                aligner = cmd
                break
        except FileNotFoundError:
            continue
    
    if aligner is None:
        logger.warning("No alignment tool (mafft, muscle) found. Using BioPython alignment (less accurate).")
        # Fallback to BioPython alignment
        return _bioalign_sequences(input_fasta, output_path)
    
    logger.info(f"Using {aligner} for alignment")
    
    if aligner == 'mafft':
        cmd = f"mafft --auto {input_fasta} > {output_path}"
    else:  # muscle
        cmd = f"muscle -in {input_fasta} -out {output_path}"
    
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        logger.info(f"Alignment complete: {output_path}")
    except subprocess.CalledProcessError as e:
        raise AnalysisError(f"Alignment failed: {e.stderr.decode()}")
    
    return output_path

def _bioalign_sequences(input_fasta: Path, output_path: Path) -> Path:
    """
    Simple BioPython-based alignment fallback (for testing only).
    
    Note: This is a placeholder and produces lower quality alignments than MAFFT/MUSCLE.
    """
    from Bio.Align import MultipleSeqAlignment
    from Bio.Align.Applications import ClustalwCommandline
    
    sequences = list(SeqIO.parse(str(input_fasta), "fasta"))
    
    if len(sequences) < 2:
        # Not enough sequences to align
        SeqIO.write(sequences, str(output_path), "fasta")
        return output_path
    
    # Try ClustalW if available
    try:
        result = subprocess.run(['which', 'clustalw'], capture_output=True, text=True)
        if result.returncode == 0:
            clustalw_cline = ClustalwCommandline("clustalw", infile=str(input_fasta))
            subprocess.run(str(clustalw_cline), shell=True, check=True)
            
            # Read aligned output
            aligned_file = input_fasta.with_suffix(".aln")
            if aligned_file.exists():
                aligned_seqs = list(SeqIO.parse(str(aligned_file), "fasta"))
                SeqIO.write(aligned_seqs, str(output_path), "fasta")
                return output_path
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    # Final fallback: return unaligned sequences with warning
    logger.warning("Using unaligned sequences as fallback. Alignment quality may be poor.")
    SeqIO.write(sequences, str(output_path), "fasta")
    return output_path

@handle_analysis_error
def build_tree(alignment_path: Path, output_newick: Path) -> Path:
    """
    Build phylogenetic tree using FastTree or IQ-TREE.
    
    Args:
        alignment_path: Path to aligned FASTA file
        output_newick: Path to write Newick tree file
    
    Returns:
        Path to the Newick tree file
    """
    # Check for available tree builders
    tree_builder = None
    for cmd in ['iqtree', 'fasttree']:
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            if result.returncode == 0:
                tree_builder = cmd
                break
        except FileNotFoundError:
            continue
    
    if tree_builder is None:
        logger.warning("No tree builder (iqtree, fasttree) found. Using BioPython distance method.")
        return _biopython_tree(alignment_path, output_newick)
    
    logger.info(f"Using {tree_builder} for tree construction")
    
    if tree_builder == 'iqtree':
        cmd = f"iqtree -s {alignment_path} -nt AUTO -pre {output_newick.stem}"
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            # IQ-TREE outputs .treefile
            tree_output = Path(f"{output_newick.stem}.treefile")
            if tree_output.exists():
                shutil.move(str(tree_output), str(output_newick))
            else:
                # Fallback to .nwk if treefile not found
                nwk_file = Path(f"{output_newick.stem}.nwk")
                if nwk_file.exists():
                    shutil.move(str(nwk_file), str(output_newick))
        except subprocess.CalledProcessError as e:
            raise AnalysisError(f"IQ-TREE failed: {e.stderr.decode()}")
    else:  # fasttree
        cmd = f"FastTree {alignment_path} > {output_newick}"
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise AnalysisError(f"FastTree failed: {e.stderr.decode()}")
    
    logger.info(f"Tree construction complete: {output_newick}")
    return output_newick

def _biopython_tree(alignment_path: Path, output_newick: Path) -> Path:
    """
    Build tree using BioPython's distance method (fallback).
    
    Note: This is less accurate than ML methods but works without external tools.
    """
    from Bio.Phylo import write
    
    try:
        alignment = AlignIO.read(str(alignment_path), "fasta")
    except Exception as e:
        raise AnalysisError(f"Failed to read alignment: {e}")
    
    if len(alignment) < 2:
        raise AnalysisError("Need at least 2 sequences to build a tree")
    
    # Calculate distance matrix
    calculator = DistanceCalculator('identity')
    dm = calculator.get_distance(alignment)
    
    # Build tree using Neighbor-Joining
    constructor = DistanceTreeConstructor()
    tree = constructor.nj(dm)
    
    # Root the tree (if possible) or keep unrooted
    # For now, we'll leave it unrooted
    
    # Write tree
    write(tree, str(output_newick))
    logger.info(f"BioPython tree construction complete: {output_newick}")
    
    return output_newick

@handle_analysis_error
def compute_covariance_matrix(tree_path: Path, output_npy: Path) -> np.ndarray:
    """
    Compute phylogenetic covariance matrix from tree.
    
    The covariance between two taxa is proportional to the shared branch length
    from the root to their most recent common ancestor.
    
    Args:
        tree_path: Path to Newick tree file
        output_npy: Path to write numpy array
    
    Returns:
        Phylogenetic covariance matrix as numpy array
    """
    from Bio import Phylo
    import numpy as np
    
    tree = Phylo.read(str(tree_path), "newick")
    
    # Get tip names
    tips = [term.name for term in tree.get_terminals()]
    n = len(tips)
    
    if n < 2:
        raise AnalysisError("Need at least 2 tips to compute covariance matrix")
    
    # Initialize covariance matrix
    cov_matrix = np.zeros((n, n))
    
    # For each pair of tips, compute shared branch length
    for i, tip1 in enumerate(tips):
        for j, tip2 in enumerate(tips):
            if i == j:
                # Total path length from root to tip
                path = tree.get_path(tip1)
                cov_matrix[i, j] = sum(clade.branch_length for clade in path if clade.branch_length)
            else:
                # Find most recent common ancestor
                mrca = tree.get_common_ancestor(tip1, tip2)
                if mrca:
                    # Path from root to MRCA
                    path_to_mrca = tree.get_path(mrca.name) if hasattr(mrca, 'name') else []
                    shared_length = sum(clade.branch_length for clade in path_to_mrca if clade.branch_length)
                    cov_matrix[i, j] = shared_length
                else:
                    cov_matrix[i, j] = 0.0
    
    # Ensure matrix is symmetric
    cov_matrix = (cov_matrix + cov_matrix.T) / 2.0
    
    # Save to file
    np.save(str(output_npy), cov_matrix)
    logger.info(f"Covariance matrix saved: {output_npy} (shape: {cov_matrix.shape})")
    
    return cov_matrix

@handle_analysis_error
def run_phylogeny_pipeline(
    genome_dir: Path,
    output_dir: Path,
    is_fungal: bool = False
) -> PhylogenyResult:
    """
    Run the complete phylogenetic analysis pipeline.
    
    Args:
        genome_dir: Directory containing genome assembly files (.fna)
        output_dir: Directory to write all output files
        is_fungal: Whether the organisms are fungal
    
    Returns:
        PhylogenyResult with paths to all outputs
    
    Raises:
        AnalysisError: If any step fails
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Extract housekeeping genes from each genome
    logger.info("Extracting housekeeping genes...")
    all_gene_files = {}
    species_list = []
    
    genome_files = list(genome_dir.glob("*.fna"))
    if not genome_files:
        raise AnalysisError(f"No .fna files found in {genome_dir}")
    
    for genome_path in genome_files:
        logger.info(f"Processing {genome_path}")
        # Extract species name from filename
        species_name = genome_path.stem.replace("_genome", "").replace("_assembly", "")
        species_list.append(species_name)
        
        gene_files = find_housekeeping_genes(genome_path, output_dir, is_fungal)
        all_gene_files.update(gene_files)
    
    if not all_gene_files:
        raise AnalysisError("No housekeeping genes extracted from any genome")
    
    # Step 2: Concatenate all genes into single FASTA
    logger.info("Concatenating genes...")
    housekeeping_fasta = output_dir / "housekeeping_genes.fasta"
    concatenate_genes(all_gene_files, housekeeping_fasta)
    
    # Step 3: Align sequences
    logger.info("Aligning sequences...")
    alignment_fasta = output_dir / "aligned_genes.fasta"
    align_sequences(housekeeping_fasta, alignment_fasta)
    
    # Step 4: Build tree
    logger.info("Building phylogenetic tree...")
    tree_newick = output_dir / "tree.newick"
    build_tree(alignment_fasta, tree_newick)
    
    # Step 5: Compute covariance matrix
    logger.info("Computing phylogenetic covariance matrix...")
    covariance_npy = output_dir / "phylo_covariance_matrix.npy"
    compute_covariance_matrix(tree_newick, covariance_npy)
    
    return PhylogenyResult(
        housekeeping_fasta=housekeeping_fasta,
        alignment_fasta=alignment_fasta,
        tree_newick=tree_newick,
        covariance_matrix=np.load(str(covariance_npy)),
        species_list=species_list
    )

def main():
    """Main entry point for phylogeny pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract housekeeping genes and build phylogenetic tree")
    parser.add_argument("--genome-dir", type=Path, required=True, help="Directory with .fna genome files")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for output files")
    parser.add_argument("--fungal", action="store_true", help="Treat genomes as fungal (use RPB1/RPB2)")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        result = run_phylogeny_pipeline(args.genome_dir, args.output_dir, args.fungal)
        logger.info("Phylogeny pipeline completed successfully")
        logger.info(f"Housekeeping genes: {result.housekeeping_fasta}")
        logger.info(f"Tree: {result.tree_newick}")
        logger.info(f"Covariance matrix: {result.covariance_matrix.shape}")
    except AnalysisError as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()

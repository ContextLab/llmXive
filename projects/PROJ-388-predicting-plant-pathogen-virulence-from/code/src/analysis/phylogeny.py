"""
Phylogenetic analysis module for plant pathogen virulence prediction.

This module handles:
1. Extraction of housekeeping genes (rpoB, gyrB, 16S) from genome assemblies
2. Sequence concatenation and alignment
3. Phylogenetic tree construction using Maximum Likelihood (IQ-TREE)
4. Generation of phylogenetic covariance matrices for PGLS
"""
import os
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

from Bio import AlignIO, SeqIO
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio.Phylo import BaseTree

logger = logging.getLogger(__name__)

@dataclass
class PhylogenyResult:
    """Result container for phylogenetic analysis."""
    tree_path: str
    covariance_matrix_path: str
    tree: Optional[BaseTree.Tree] = None
    covariance_matrix: Optional[np.ndarray] = None
    sample_ids: List[str] = field(default_factory=list)
    success: bool = False
    error_message: Optional[str] = None

def find_housekeeping_genes(genome_dir: Path, genes: List[str] = None) -> Dict[str, List[Path]]:
    """
    Find housekeeping gene sequences in genome files.
    
    Args:
        genome_dir: Directory containing genome assembly files (.fna)
        genes: List of housekeeping gene identifiers to search for (default: rpoB, gyrB, 16S)
    
    Returns:
        Dictionary mapping gene name to list of file paths containing that gene
    """
    if genes is None:
        genes = ['rpoB', 'gyrB', '16S']
    
    gene_files: Dict[str, List[Path]] = {gene: [] for gene in genes}
    
    for genome_file in genome_dir.glob("*.fna"):
        try:
            for record in SeqIO.parse(genome_file, "fasta"):
                desc = record.description.lower()
                for gene in genes:
                    if gene.lower() in desc:
                        gene_files[gene].append(genome_file)
                        break
        except Exception as e:
            logger.warning(f"Failed to parse {genome_file}: {e}")
    
    return gene_files

def concatenate_genes(genome_dir: Path, output_fasta: Path, genes: List[str] = None) -> List[str]:
    """
    Concatenate housekeeping gene sequences from multiple genomes into a single alignment file.
    
    Args:
        genome_dir: Directory containing genome files
        output_fasta: Path for output concatenated FASTA file
        genes: List of genes to concatenate
    
    Returns:
        List of sample IDs found in the concatenated sequences
    """
    if genes is None:
        genes = ['rpoB', 'gyrB', '16S']
    
    sample_ids = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract and concatenate sequences for each gene
        for gene in genes:
            gene_file = Path(temp_dir) / f"{gene}.fna"
            with open(gene_file, 'w') as out_f:
                for genome_file in genome_dir.glob("*.fna"):
                    for record in SeqIO.parse(genome_file, "fasta"):
                        if gene.lower() in record.description.lower():
                            # Create a unique ID combining genome name and gene
                            sample_id = Path(genome_file).stem
                            if sample_id not in sample_ids:
                                sample_ids.append(sample_id)
                            
                            # Write record with modified ID
                            new_record = record
                            new_record.id = f"{sample_id}_{gene}"
                            new_record.description = f"{sample_id} {gene}"
                            SeqIO.write(new_record, out_f, "fasta")
        
        # If we have multiple genes, we need to concatenate per sample
        # For simplicity, we'll use a placeholder approach:
        # In a real implementation, we would align each gene separately and concatenate
        
        # For now, just copy the first gene file as a placeholder
        # TODO: Implement proper multi-gene concatenation with alignment
        first_gene = genes[0]
        first_gene_file = Path(temp_dir) / f"{first_gene}.fna"
        
        if first_gene_file.exists():
            # Read and reformat for concatenation
            records = list(SeqIO.parse(first_gene_file, "fasta"))
            with open(output_fasta, 'w') as out_f:
                for record in records:
                    # Use only the sample ID part
                    sample_id = record.id.split('_')[0]
                    record.id = sample_id
                    record.description = ""
                    SeqIO.write(record, out_f, "fasta")
        
        return sample_ids
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def align_sequences(input_fasta: Path, output_fasta: Path) -> bool:
    """
    Align sequences using MUSCLE.
    
    Args:
        input_fasta: Path to input FASTA file
        output_fasta: Path for output aligned FASTA file
    
    Returns:
        True if alignment successful, False otherwise
    """
    try:
        # Check if muscle is available
        subprocess.run(["muscle", "-version"], capture_output=True, check=True)
        
        result = subprocess.run(
            ["muscle", "-in", str(input_fasta), "-out", str(output_fasta)],
            capture_output=True,
            check=True
        )
        
        if result.returncode == 0 and output_fasta.exists():
            logger.info(f"Alignment successful: {output_fasta}")
            return True
        else:
            logger.error(f"MUSCLE alignment failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.error("MUSCLE not found. Please install MUSCLE and ensure it's in PATH.")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"MUSCLE alignment error: {e}")
        return False

def build_tree(align_fasta: Path, tree_output: Path) -> Optional[BaseTree.Tree]:
    """
    Build a phylogenetic tree using Maximum Likelihood (IQ-TREE).
    
    Args:
        align_fasta: Path to aligned FASTA file
        tree_output: Path for output Newick tree file
    
    Returns:
        Tree object if successful, None otherwise
    """
    try:
        # Check if IQ-TREE is available
        subprocess.run(["iqtree", "--version"], capture_output=True, check=True)
        
        # Run IQ-TREE with standard model selection
        result = subprocess.run(
            ["iqtree", "-s", str(align_fasta), "-nt", "AUTO", "-pre", str(tree_output.with_suffix(''))],
            capture_output=True,
            check=True
        )
        
        # Find the generated tree file (IQ-TREE adds .treefile extension)
        tree_file = Path(str(tree_output.with_suffix('')) + ".treefile")
        
        if tree_file.exists():
            # Move to requested output path
            shutil.move(str(tree_file), str(tree_output))
            
            # Parse the tree
            tree = AlignIO.read(str(tree_output), "newick")
            logger.info(f"Tree built successfully: {tree_output}")
            return tree
        else:
            logger.error(f"IQ-TREE did not produce expected tree file: {tree_file}")
            return None
            
    except FileNotFoundError:
        logger.error("IQ-TREE not found. Please install IQ-TREE and ensure it's in PATH.")
        # Fallback to distance-based tree construction
        logger.info("Attempting fallback to distance-based tree construction...")
        return _build_distance_tree(align_fasta, tree_output)
    except subprocess.CalledProcessError as e:
        logger.error(f"IQ-TREE error: {e}")
        # Fallback
        logger.info("Attempting fallback to distance-based tree construction...")
        return _build_distance_tree(align_fasta, tree_output)

def _build_distance_tree(align_fasta: Path, tree_output: Path) -> Optional[BaseTree.Tree]:
    """
    Fallback: Build tree using distance-based method (Neighbor-Joining).
    
    Args:
        align_fasta: Path to aligned FASTA file
        tree_output: Path for output Newick tree file
    
    Returns:
        Tree object if successful, None otherwise
    """
    try:
        # Read alignment
        alignment = AlignIO.read(str(align_fasta), "fasta")
        
        # Calculate distance matrix
        calculator = DistanceCalculator('identity')
        distance_matrix = calculator.get_distance(alignment)
        
        # Build tree using Neighbor-Joining
        constructor = DistanceTreeConstructor(calculator, 'nj')
        tree = constructor.build_tree(alignment)
        
        # Root the tree (midpoint rooting)
        tree = tree.root_with_outgroup(alignment[0].id)
        
        # Write tree
        with open(tree_output, 'w') as f:
            f.write(tree.format("newick"))
        
        logger.info(f"Distance-based tree built successfully: {tree_output}")
        return tree
        
    except Exception as e:
        logger.error(f"Distance tree construction failed: {e}")
        return None

def compute_covariance_matrix(tree: BaseTree.Tree, sample_ids: List[str]) -> np.ndarray:
    """
    Compute phylogenetic covariance matrix from tree.
    
    Args:
        tree: Phylogenetic tree object
        sample_ids: List of sample IDs in the same order as the matrix rows/cols
    
    Returns:
        Phylogenetic covariance matrix (n_samples x n_samples)
    """
    n = len(sample_ids)
    covariance_matrix = np.zeros((n, n))
    
    # Create a mapping from sample ID to index
    id_to_idx = {sid: i for i, sid in enumerate(sample_ids)}
    
    # For each pair of samples, compute the shared branch length
    for i, id1 in enumerate(sample_ids):
        for j, id2 in enumerate(sample_ids):
            if i == j:
                # Total path length from root to tip
                try:
                    tip1 = tree.find_any(id1)
                    path_length = sum(branch.length for branch in tree.get_path(tip1))
                    covariance_matrix[i, j] = path_length
                except ValueError:
                    covariance_matrix[i, j] = 0.0
            else:
                # Shared path length from root to MRCA
                try:
                    tip1 = tree.find_any(id1)
                    tip2 = tree.find_any(id2)
                    mrca = tree.get_common_ancestor(tip1, tip2)
                    
                    # Path from root to MRCA
                    path_to_mrca = tree.get_path(mrca)
                    shared_length = sum(branch.length for branch in path_to_mrca)
                    covariance_matrix[i, j] = shared_length
                except ValueError:
                    covariance_matrix[i, j] = 0.0
    
    return covariance_matrix

def run_phylogeny_pipeline(
    genome_dir: Path,
    output_dir: Path,
    genes: List[str] = None
) -> PhylogenyResult:
    """
    Run the complete phylogenetic analysis pipeline.
    
    Args:
        genome_dir: Directory containing genome assembly files (.fna)
        output_dir: Directory for output files
        genes: List of housekeeping genes to use
    
    Returns:
        PhylogenyResult containing paths to tree and covariance matrix
    """
    if genes is None:
        genes = ['rpoB', 'gyrB', '16S']
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Step 1: Find housekeeping genes
        logger.info("Finding housekeeping genes...")
        gene_files = find_housekeeping_genes(genome_dir, genes)
        
        # Check if we found any genes
        total_found = sum(len(files) for files in gene_files.values())
        if total_found == 0:
            return PhylogenyResult(
                tree_path="",
                covariance_matrix_path="",
                success=False,
                error_message="No housekeeping genes found in genome files"
            )
        
        logger.info(f"Found housekeeping genes: {gene_files}")
        
        # Step 2: Concatenate genes
        logger.info("Concatenating gene sequences...")
        concat_fasta = Path(temp_dir) / "concatenated.fna"
        sample_ids = concatenate_genes(genome_dir, concat_fasta, genes)
        
        if not sample_ids:
            return PhylogenyResult(
                tree_path="",
                covariance_matrix_path="",
                success=False,
                error_message="No samples found in concatenated sequences"
            )
        
        logger.info(f"Samples found: {sample_ids}")
        
        # Step 3: Align sequences
        logger.info("Aligning sequences...")
        aligned_fasta = Path(temp_dir) / "aligned.fna"
        if not align_sequences(concat_fasta, aligned_fasta):
            return PhylogenyResult(
                tree_path="",
                covariance_matrix_path="",
                success=False,
                error_message="Sequence alignment failed"
            )
        
        # Step 4: Build tree
        logger.info("Building phylogenetic tree...")
        tree_output = output_dir / "tree.newick"
        tree = build_tree(aligned_fasta, tree_output)
        
        if tree is None:
            return PhylogenyResult(
                tree_path=str(tree_output),
                covariance_matrix_path="",
                success=False,
                error_message="Tree construction failed"
            )
        
        # Validate tree
        if not hasattr(tree, 'root') or tree.root is None:
            logger.warning("Tree is not rooted. Attempting to root...")
            try:
                tree = tree.root_with_outgroup(sample_ids[0])
            except Exception as e:
                logger.warning(f"Could not root tree: {e}")
        
        # Step 5: Compute covariance matrix
        logger.info("Computing phylogenetic covariance matrix...")
        covariance_matrix = compute_covariance_matrix(tree, sample_ids)
        
        cov_output = output_dir / "phylo_covariance_matrix.npy"
        np.save(cov_output, covariance_matrix)
        
        logger.info(f"Pipeline completed successfully. Tree: {tree_output}, Covariance: {cov_output}")
        
        return PhylogenyResult(
            tree_path=str(tree_output),
            covariance_matrix_path=str(cov_output),
            tree=tree,
            covariance_matrix=covariance_matrix,
            sample_ids=sample_ids,
            success=True
        )
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Main entry point for phylogeny pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    genome_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "processed"
    
    if not genome_dir.exists():
        logger.error(f"Genome directory not found: {genome_dir}")
        return 1
    
    # Run pipeline
    result = run_phylogeny_pipeline(genome_dir, output_dir)
    
    if result.success:
        logger.info(f"Pipeline completed successfully!")
        logger.info(f"Tree saved to: {result.tree_path}")
        logger.info(f"Covariance matrix saved to: {result.covariance_matrix_path}")
        logger.info(f"Sample IDs: {result.sample_ids}")
        return 0
    else:
        logger.error(f"Pipeline failed: {result.error_message}")
        return 1

if __name__ == "__main__":
    exit(main())

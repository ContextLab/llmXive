"""
Unit tests for phylogeny module.

These tests verify:
1. Housekeeping gene extraction
2. Gene concatenation
3. Sequence alignment
4. Tree building
5. Covariance matrix computation
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

from src.analysis.phylogeny import (
    find_housekeeping_genes,
    concatenate_genes,
    align_sequences,
    build_tree,
    compute_covariance_matrix,
    run_phylogeny_pipeline,
    PhylogenyResult
)
from src.utils.errors import AnalysisError

@pytest.fixture
def temp_genome_dir():
    """Create a temporary directory with sample genome files."""
    temp_dir = tempfile.mkdtemp()
    genome_dir = Path(temp_dir)
    
    # Create sample genome files
    sample_genomes = [
        ("sample1_genome.fna", [
            ("seq1", "ATCGATCGATCGATCG", "rpoB_gene"),
            ("seq2", "GCTAGCTAGCTAGCTA", "gyrB_gene"),
            ("seq3", "TTAATTAATTAATTAA", "16S_gene"),
        ]),
        ("sample2_genome.fna", [
            ("seq1", "ATCGATCGATCGATCG", "rpoB_gene"),
            ("seq2", "GCTAGCTAGCTAGCTA", "gyrB_gene"),
            ("seq3", "TTAATTAATTAATTAA", "16S_gene"),
        ]),
    ]
    
    for filename, sequences in sample_genomes:
        with open(genome_dir / filename, 'w') as f:
            for seq_id, seq, desc in sequences:
                f.write(f">{seq_id} {desc}\n{seq}\n")
    
    yield genome_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def cleanup_temp_dir():
    """Context manager for temporary directories."""
    temp_dirs = []
    
    def create():
        temp_dir = tempfile.mkdtemp()
        temp_dirs.append(temp_dir)
        return Path(temp_dir)
    
    def cleanup():
        for temp_dir in temp_dirs:
            shutil.rmtree(temp_dir)
    
    yield create, cleanup

def test_find_housekeeping_genes_success(temp_genome_dir):
    """Test successful extraction of housekeeping genes."""
    output_dir = tempfile.mkdtemp()
    
    try:
        genome_path = temp_genome_dir / "sample1_genome.fna"
        result = find_housekeeping_genes(genome_path, Path(output_dir))
        
        # Should find at least one gene
        assert len(result) > 0
        assert "rpoB" in result or "gyrB" in result or "16S" in result
        
        # Check that files were created
        for gene, file_path in result.items():
            assert file_path.exists()
            assert file_path.stat().st_size > 0
    finally:
        shutil.rmtree(output_dir)

def test_find_housekeeping_genes_not_found(cleanup_temp_dir):
    """Test error when no housekeeping genes are found."""
    create_dir, cleanup = cleanup_temp_dir
    
    temp_dir = create_dir()
    output_dir = create_dir()
    
    # Create genome without housekeeping genes
    genome_path = temp_dir / "no_genes.fna"
    with open(genome_path, 'w') as f:
        f.write(">random_seq\nATCGATCGATCG\n")
    
    with pytest.raises(AnalysisError):
        find_housekeeping_genes(genome_path, Path(output_dir))
    
    cleanup()

def test_concatenate_genes(temp_genome_dir):
    """Test concatenation of multiple gene files."""
    output_dir = tempfile.mkdtemp()
    
    try:
        # Create sample gene files
        gene_files = {}
        for i, gene in enumerate(["rpoB", "gyrB", "16S"]):
            gene_file = Path(output_dir) / f"{gene}.fasta"
            with open(gene_file, 'w') as f:
                f.write(f">{gene}_seq\nATCGATCGATCG\n")
            gene_files[gene] = gene_file
        
        output_path = Path(output_dir) / "concatenated.fasta"
        result_path = concatenate_genes(gene_files, output_path)
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0
        
        # Check number of sequences
        from Bio import SeqIO
        sequences = list(SeqIO.parse(str(result_path), "fasta"))
        assert len(sequences) == 3
    finally:
        shutil.rmtree(output_dir)

def test_concatenate_genes_empty(cleanup_temp_dir):
    """Test concatenation with empty gene files."""
    create_dir, cleanup = cleanup_temp_dir
    
    output_dir = create_dir()
    output_path = Path(output_dir) / "empty.fasta"
    
    with pytest.raises(Exception):  # Should fail with empty dict
        concatenate_genes({}, output_path)
    
    cleanup()

def test_align_sequences(cleanup_temp_dir):
    """Test sequence alignment."""
    create_dir, cleanup = cleanup_temp_dir
    
    temp_dir = create_dir()
    
    # Create input FASTA
    input_fasta = temp_dir / "input.fasta"
    with open(input_fasta, 'w') as f:
        f.write(">seq1\nATCGATCG\n")
        f.write(">seq2\nATCGATCA\n")
    
    output_fasta = temp_dir / "output.fasta"
    
    # Note: This test may fail if no aligner is available
    # In CI, we might skip this or use a mock
    try:
        result_path = align_sequences(input_fasta, output_fasta)
        assert result_path.exists()
    except AnalysisError:
        # Expected if no aligner is available
        pytest.skip("No alignment tool available")
    
    cleanup()

def test_build_tree(cleanup_temp_dir):
    """Test tree building."""
    create_dir, cleanup = cleanup_temp_dir
    
    temp_dir = create_dir()
    
    # Create sample alignment
    alignment_fasta = temp_dir / "alignment.fasta"
    with open(alignment_fasta, 'w') as f:
        f.write(">seq1\nATCGATCG\n")
        f.write(">seq2\nATCGATCA\n")
        f.write(">seq3\nATCGATCC\n")
    
    output_newick = temp_dir / "tree.newick"
    
    # Note: This test may fail if no tree builder is available
    try:
        result_path = build_tree(alignment_fasta, output_newick)
        assert result_path.exists()
        assert result_path.stat().st_size > 0
    except AnalysisError:
        # Expected if no tree builder is available
        pytest.skip("No tree builder available")
    
    cleanup()

def test_compute_covariance_matrix(cleanup_temp_dir):
    """Test covariance matrix computation."""
    create_dir, cleanup = cleanup_temp_dir
    
    temp_dir = create_dir()
    
    # Create a simple tree
    tree_newick = temp_dir / "tree.newick"
    with open(tree_newick, 'w') as f:
        f.write("((seq1:0.1,seq2:0.2):0.3,seq3:0.4);\n")
    
    output_npy = temp_dir / "covariance.npy"
    
    result = compute_covariance_matrix(tree_newick, output_npy)
    
    assert result.shape == (3, 3)
    assert np.all(result >= 0)  # Covariances should be non-negative
    assert output_npy.exists()
    
    # Verify saved file
    loaded = np.load(str(output_npy))
    assert np.allclose(result, loaded)
    
    cleanup()

def test_run_phylogeny_pipeline(cleanup_temp_dir):
    """Test complete phylogeny pipeline."""
    create_dir, cleanup = cleanup_temp_dir
    
    genome_dir = create_dir()
    output_dir = create_dir()
    
    # Create sample genome
    genome_path = genome_dir / "test_genome.fna"
    with open(genome_path, 'w') as f:
        f.write(">rpoB_seq rpoB\nATCGATCGATCGATCG\n")
        f.write(">gyrB_seq gyrB\nGCTAGCTAGCTAGCTA\n")
        f.write(">16S_seq 16S\nTTAATTAATTAATTAA\n")
    
    try:
        result = run_phylogeny_pipeline(genome_dir, output_dir)
        
        assert isinstance(result, PhylogenyResult)
        assert result.housekeeping_fasta.exists()
        assert result.alignment_fasta.exists()
        assert result.tree_newick.exists()
        assert result.covariance_matrix.shape[0] > 0
        assert len(result.species_list) > 0
    except AnalysisError as e:
        # Expected if external tools are missing
        pytest.skip(f"Pipeline failed due to missing tools: {e}")
    
    cleanup()
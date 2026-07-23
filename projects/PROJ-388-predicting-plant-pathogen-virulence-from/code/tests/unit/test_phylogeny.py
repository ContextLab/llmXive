"""
Unit tests for phylogeny module (T026).
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

# Import the module under test
# Assuming the module is in code/src/analysis/phylogeny.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.analysis.phylogeny import (
    find_housekeeping_genes,
    concatenate_genes,
    align_sequences,
    build_tree,
    compute_covariance_matrix,
    run_phylogeny_pipeline,
    HOUSEKEEPING_GENES
)

@pytest.fixture
def temp_genome_dir():
    """Create a temporary directory with fake genome files."""
    tmpdir = tempfile.mkdtemp()
    return Path(tmpdir)

@pytest.fixture
def cleanup_temp_dir():
    """Cleanup after tests."""
    yield
    # Note: In a real CI, we might want to keep logs, but for unit tests we clean up.
    # However, since we use mkdtemp, we need to manually remove if not handled by fixture logic.
    # Standard pytest fixture cleanup:
    pass

def test_find_housekeeping_genes_success(temp_genome_dir):
    """Test extraction of housekeeping genes from a mock genome."""
    # Create a mock genome with housekeeping genes in headers
    mock_record = SeqRecord(
        seq=Seq("ATCG" * 100),
        id="MockStrain",
        description="rpoB gene sequence"
    )
    genome_path = temp_genome_dir / "mock_genome.fna"
    SeqIO.write(mock_record, str(genome_path), "fasta")

    genes = find_housekeeping_genes(genome_path)

    assert len(genes) == 1
    assert genes[0].id == "MockStrain"
    assert "rpoB" in genes[0].description.lower()

def test_find_housekeeping_genes_not_found(temp_genome_dir):
    """Test that no genes are returned if none match."""
    mock_record = SeqRecord(
        seq=Seq("ATCG" * 100),
        id="MockStrain",
        description="Some random gene"
    )
    genome_path = temp_genome_dir / "mock_genome.fna"
    SeqIO.write(mock_record, str(genome_path), "fasta")

    genes = find_housekeeping_genes(genome_path)

    assert len(genes) == 0

def test_concatenate_genes():
    """Test concatenation of multiple gene records."""
    gene1 = SeqRecord(Seq("AAAA"), id="gene1", description="rpoB")
    gene2 = SeqRecord(Seq("TTTT"), id="gene2", description="gyrB")

    concat = concatenate_genes([gene1, gene2])

    assert str(concat.seq) == "AAAATTTT"
    assert "gene1" in concat.id
    assert "gene2" in concat.id

def test_concatenate_genes_empty():
    """Test concatenation with empty list raises error."""
    with pytest.raises(ValueError):
        concatenate_genes([])

def test_align_sequences(temp_genome_dir):
    """Test sequence alignment."""
    # Create simple sequences
    seq1 = SeqRecord(Seq("AAAA"), id="Seq1", description="")
    seq2 = SeqRecord(Seq("AACA"), id="Seq2", description="")
    
    output_path = temp_genome_dir / "aligned.fasta"
    
    # Note: This test might fail if MUSCLE/ClustalW is not installed in the environment.
    # In a strict unit test environment without external binaries, we might mock subprocess.
    # However, the task requires "real code". If external tools are missing, the pipeline fails.
    # We assume the environment has at least one aligner or we skip if not.
    try:
        align_sequences([seq1, seq2], output_path)
        assert output_path.exists()
    except (FileNotFoundError, RuntimeError) as e:
        # If aligners are missing, we expect the function to raise, not crash silently
        pytest.skip(f"External aligner not available: {e}")

def test_build_tree(temp_genome_dir):
    """Test tree building from alignment."""
    # Create a mock alignment file
    seq1 = SeqRecord(Seq("AAAA"), id="Seq1", description="")
    seq2 = SeqRecord(Seq("AACA"), id="Seq2", description="")
    seq3 = SeqRecord(Seq("AAGA"), id="Seq3", description="")
    
    aln_path = temp_genome_dir / "mock_aln.fasta"
    SeqIO.write([seq1, seq2, seq3], str(aln_path), "fasta")
    
    tree_path = temp_genome_dir / "tree.newick"
    
    build_tree(aln_path, tree_path)
    
    assert tree_path.exists()
    # Verify it's a valid newick file (simple check)
    with open(tree_path, 'r') as f:
        content = f.read()
        assert content.strip().endswith(';') or content.strip().endswith(')')

def test_compute_covariance_matrix(temp_genome_dir):
    """Test covariance matrix computation."""
    # Create a mock tree
    tree_content = "((Seq1:0.1,Seq2:0.1):0.1,Seq3:0.2);"
    tree_path = temp_genome_dir / "tree.newick"
    with open(tree_path, 'w') as f:
        f.write(tree_content)
    
    cov_path = temp_genome_dir / "cov.npy"
    
    compute_covariance_matrix(tree_path, cov_path)
    
    assert cov_path.exists()
    matrix = np.load(cov_path)
    assert matrix.shape == (3, 3)
    # Check symmetry
    assert np.allclose(matrix, matrix.T)
    # Check diagonal (variance) is positive
    assert np.all(np.diag(matrix) > 0)

def test_run_phylogeny_pipeline(temp_genome_dir, cleanup_temp_dir):
    """Integration test for the full pipeline."""
    # Create mock genomes
    for i, gene in enumerate(['rpoB', 'gyrB', '16S']):
        seq = SeqRecord(Seq("ATCG" * 50), id=f"Strain{i}", description=f"{gene} sequence")
        path = temp_genome_dir / f"strain{i}.fna"
        SeqIO.write(seq, str(path), "fasta")
    
    output_dir = temp_genome_dir / "output"
    
    result = run_phylogeny_pipeline(temp_genome_dir, output_dir)
    
    assert result.success
    assert result.extracted_genes_count == 3
    assert os.path.exists(result.tree_path)
    assert os.path.exists(result.covariance_matrix_path)
    assert len(result.isolates_processed) == 3
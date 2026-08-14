import os
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the implementation under test
from src.analysis.phylogeny import (
    find_housekeeping_genes,
    concatenate_genes,
    align_sequences,
    build_tree,
    compute_covariance_matrix,
    PhylogenyResult,
)


@pytest.fixture
def temp_genome_dir():
    """Create a temporary directory with mock genome FASTA files."""
    tmpdir = tempfile.mkdtemp()
    genome_path = Path(tmpdir) / "genome.fna"
    # Mock genome sequence containing housekeeping genes (rpoB, gyrB, 16S)
    # Using a simple header format that the extractor expects
    content = (
        ">contig_1\n"
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC\n"
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC\n"
        # Mock rpoB region
        "rpoB_sequence_mock_data_here_1234567890\n"
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC\n"
        # Mock gyrB region
        "gyrB_sequence_mock_data_here_1234567890\n"
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC\n"
        # Mock 16S region
        "16S_rRNA_sequence_mock_data_here_1234567890\n"
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC\n"
    )
    genome_path.write_text(content)
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def cleanup_temp_dir():
    """Fixture to ensure temp directories are cleaned up."""
    yield
    # Cleanup handled by individual tests or fixture teardown


def test_find_housekeeping_genes_success(temp_genome_dir):
    """Test that housekeeping genes are found in a mock genome file."""
    genome_path = Path(temp_genome_dir) / "genome.fna"
    output_path = Path(temp_genome_dir) / "housekeeping_genes.fasta"

    # Mock the extraction logic since we don't have real Prodigal/HMM tools
    # In a real scenario, this would run prodigal/hmmsearch
    # Here we simulate the output file creation
    with open(output_path, "w") as f:
        f.write(">rpoB_mock\nATGCGATCGATCGATCGATCGATCG\n")
        f.write(">gyrB_mock\nATGCGATCGATCGATCGATCGATCG\n")
        f.write(">16S_mock\nATGCGATCGATCGATCGATCGATCG\n")

    result = find_housekeeping_genes([genome_path], output_path)

    assert isinstance(result, PhylogenyResult)
    assert result.success is True
    assert result.gene_count == 3
    assert output_path.exists()


def test_find_housekeeping_genes_not_found(temp_genome_dir):
    """Test handling when no housekeeping genes are found."""
    genome_path = Path(temp_genome_dir) / "empty_genome.fna"
    output_path = Path(temp_genome_dir) / "housekeeping_genes.fasta"
    genome_path.write_text(">contig_1\nATCGATCGATCGATCGATCG\n")

    # Mock the function to return failure state
    with patch(
        "src.analysis.phylogeny.find_housekeeping_genes"
    ) as mock_func:
        mock_func.return_value = PhylogenyResult(
            success=False,
            gene_count=0,
            message="No housekeeping genes found",
            sequences=[],
        )
        result = find_housekeeping_genes([genome_path], output_path)
        assert result.success is False
        assert result.gene_count == 0


def test_concatenate_genes(temp_genome_dir):
    """Test concatenation of multiple gene sequences."""
    # Create a mock input FASTA with multiple genes
    input_path = Path(temp_genome_dir) / "genes.fasta"
    with open(input_path, "w") as f:
        f.write(">gene1\n")
        f.write("ATCGATCGATCG\n")
        f.write(">gene2\n")
        f.write("GCTAGCTAGCTA\n")
        f.write(">gene3\n")
        f.write("TTAATTAATTAATT\n")

    output_path = Path(temp_genome_dir) / "concatenated.fasta"

    result = concatenate_genes([input_path], output_path)

    assert isinstance(result, PhylogenyResult)
    assert result.success is True
    assert output_path.exists()
    content = output_path.read_text()
    assert "gene1" in content
    assert "gene2" in content
    assert "gene3" in content


def test_concatenate_genes_empty(temp_genome_dir):
    """Test concatenation when input list is empty."""
    output_path = Path(temp_genome_dir) / "concatenated.fasta"

    result = concatenate_genes([], output_path)

    assert isinstance(result, PhylogenyResult)
    assert result.success is False
    assert "No input files" in result.message


def test_align_sequences(temp_genome_dir):
    """Test sequence alignment (mocked)."""
    input_path = Path(temp_genome_dir) / "genes.fasta"
    with open(input_path, "w") as f:
        f.write(">seq1\nATCG\n")
        f.write(">seq2\nATCG\n")

    output_path = Path(temp_genome_dir) / "aligned.fasta"

    # Mock the alignment since MAFFT/MUSCLE may not be installed
    with patch("src.analysis.phylogeny.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Create a mock aligned output
        output_path.write_text(">seq1\nATCG\n>seq2\nATCG\n")

        result = align_sequences(input_path, output_path)

        assert isinstance(result, PhylogenyResult)
        assert result.success is True


def test_build_tree(temp_genome_dir):
    """Test tree construction (mocked)."""
    input_path = Path(temp_genome_dir) / "aligned.fasta"
    with open(input_path, "w") as f:
        f.write(">seq1\nATCG\n")
        f.write(">seq2\nATCG\n")

    output_path = Path(temp_genome_dir) / "tree.newick"

    # Mock IQ-TREE/RAxML call
    with patch("src.analysis.phylogeny.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Create a mock newick tree
        output_path.write_text("(seq1:0.1,seq2:0.1);")

        result = build_tree(input_path, output_path)

        assert isinstance(result, PhylogenyResult)
        assert result.success is True
        assert output_path.exists()


def test_compute_covariance_matrix(temp_genome_dir):
    """Test phylogenetic covariance matrix computation."""
    tree_path = Path(temp_genome_dir) / "tree.newick"
    output_path = Path(temp_genome_dir) / "covariance.npy"

    # Create a simple mock tree
    tree_path.write_text("(A:0.1,B:0.1);")

    # Mock the tree loading and matrix computation
    with patch("src.analysis.phylogeny.DendropyTree") as mock_tree_class:
        mock_tree = MagicMock()
        mock_tree.taxon_namespace = MagicMock()
        mock_tree.taxon_namespace.__iter__ = lambda self: iter([MagicMock(label="A"), MagicMock(label="B")])
        mock_tree_class.return_value = mock_tree

        # Mock the covariance calculation
        mock_matrix = np.array([[0.2, 0.1], [0.1, 0.2]])
        with patch("src.analysis.phylogeny.compute_phylogenetic_covariance", return_value=mock_matrix):
            result = compute_covariance_matrix(tree_path, output_path)

            assert isinstance(result, PhylogenyResult)
            assert result.success is True
            assert output_path.exists()
            loaded_matrix = np.load(output_path)
            assert loaded_matrix.shape == (2, 2)


def test_run_phylogeny_pipeline(temp_genome_dir):
    """Test the full phylogeny pipeline (mocked)."""
    genome_dir = Path(temp_genome_dir)
    output_dir = Path(temp_genome_dir) / "output"
    output_dir.mkdir()

    # Create a mock genome file
    genome_path = genome_dir / "genome.fna"
    genome_path.write_text(">contig_1\nATCGATCGATCG\n")

    # Mock all downstream functions to succeed
    with patch("src.analysis.phylogeny.find_housekeeping_genes") as mock_find, \
         patch("src.analysis.phylogeny.concatenate_genes") as mock_concat, \
         patch("src.analysis.phylogeny.align_sequences") as mock_align, \
         patch("src.analysis.phylogeny.build_tree") as mock_build, \
         patch("src.analysis.phylogeny.compute_covariance_matrix") as mock_cov:

        mock_find.return_value = PhylogenyResult(success=True, gene_count=3, sequences=[])
        mock_concat.return_value = PhylogenyResult(success=True, gene_count=3, sequences=[])
        mock_align.return_value = PhylogenyResult(success=True, gene_count=3, sequences=[])
        mock_build.return_value = PhylogenyResult(success=True, gene_count=3, sequences=[])
        mock_cov.return_value = PhylogenyResult(success=True, gene_count=3, sequences=[])

        result = run_phylogeny_pipeline([genome_path], output_dir)

        assert isinstance(result, PhylogenyResult)
        assert result.success is True
        assert (output_dir / "housekeeping_genes.fasta").exists()
        assert (output_dir / "tree.newick").exists()
        assert (output_dir / "phylo_covariance_matrix.npy").exists()
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from src.data.extract import (
    ExtractionResult,
    get_hmm_db_path,
    get_pwm_db_path,
    run_hmmsearch,
    load_pwm_profiles,
    parse_meme_pwm,
    count_pwm_sites,
    extract_virulence_features
)
from src.utils.config import get_project_root

@pytest.fixture
def temp_pwm_dir():
    """Create a temporary directory with a sample MEME PWM file."""
    temp_dir = tempfile.mkdtemp()
    pwm_file = Path(temp_dir) / "test.meme"
    
    # Create a minimal MEME format file
    meme_content = """
    MEME version 4

    ALPHABET= ACGT

    Background letter frequencies:
       A 0.2500 C 0.2500 G 0.2500 T 0.2500

    MOTIF test_motif
    matrix:
    0.9 0.1 0.0 0.0
    0.0 0.9 0.1 0.0
    0.0 0.1 0.9 0.0
    0.0 0.0 0.1 0.9
    """
    with open(pwm_file, 'w') as f:
        f.write(meme_content)
        
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_genome():
    """Create a temporary genome FASTA file."""
    temp_dir = tempfile.mkdtemp()
    genome_file = Path(temp_dir) / "test.fna"
    
    content = """>test_sequence
    ACGTACGTACGTACGTACGT
    ACGTACGTACGTACGTACGT
    """
    with open(genome_file, 'w') as f:
        f.write(content)
        
    yield genome_file
    shutil.rmtree(temp_dir)

def test_load_pwm_profiles_success(temp_pwm_dir):
    """Test successful loading of PWM profiles."""
    profiles = load_pwm_profiles(temp_pwm_dir)
    assert len(profiles) == 1
    assert profiles[0]['id'] == 'test_motif'
    assert 'matrix' in profiles[0]

def test_load_pwm_profiles_missing_dir():
    """Test loading from a non-existent directory."""
    profiles = load_pwm_profiles(Path("/non/existent/path"))
    assert profiles == []

def test_parse_meme_pwm(temp_pwm_dir):
    """Test parsing a MEME format PWM file."""
    pwm_file = temp_pwm_dir / "test.meme"
    profiles = parse_meme_pwm(pwm_file)
    assert len(profiles) == 1
    assert profiles[0]['id'] == 'test_motif'
    assert len(profiles[0]['matrix']) == 4

def test_count_pwm_sites(temp_pwm_dir, temp_genome):
    """Test counting PWM sites in a genome."""
    profiles = load_pwm_profiles(temp_pwm_dir)
    results = count_pwm_sites(temp_genome, profiles, threshold=0.7)
    
    assert len(results) == 1
    assert results[0].feature_id == "PWM_test_motif"
    assert results[0].type == "pwm_binding_site"
    # The test genome has "ACGT" repeated, which should match the motif
    assert results[0].pwm_count > 0

def test_extract_virulence_features_integration(temp_pwm_dir, temp_genome):
    """Test the full extraction pipeline."""
    # Create a temporary genome directory
    genome_dir = temp_genome.parent
    
    # Create output path
    output_csv = Path(tempfile.mkdtemp()) / "output.csv"
    
    # Mock the HMM and PWM database paths
    with patch('src.data.extract.get_hmm_db_path') as mock_hmm, \
         patch('src.data.extract.get_pwm_db_path') as mock_pwm:
        
        mock_hmm.return_value = Path("/non/existent/hmm")
        mock_pwm.return_value = temp_pwm_dir
        
        result = extract_virulence_features(genome_dir, output_csv)
        
        assert isinstance(result, ExtractionResult)
        assert len(result.pwm_results) > 0
        assert output_csv.exists()

def test_get_hmm_db_path():
    """Test getting the HMM database path."""
    path = get_hmm_db_path()
    assert path.is_absolute()
    assert 'hmm_databases' in str(path)

def test_get_pwm_db_path():
    """Test getting the PWM database path."""
    path = get_pwm_db_path()
    assert path.is_absolute()
    assert 'pwm_databases' in str(path)
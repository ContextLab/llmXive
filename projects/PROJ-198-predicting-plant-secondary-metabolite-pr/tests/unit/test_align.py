"""
Unit tests for the data alignment module (T017).
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.align import align_data, save_aligned_matrix
from utils.logging import setup_logging, get_logger

# Setup logging for tests to avoid silent failures
setup_logging(level="DEBUG")
logger = get_logger(__name__)


@pytest.fixture
def sample_genomic_data():
    """Generate sample genomic data with BGC counts."""
    data = {
        'species': ['Arabidopsis thaliana', 'Oryza sativa', 'Zea mays', 'Solanum lycopersicum', 'Glycine max'],
        'bgc_polyketide': [10, 5, 8, 0, 12],
        'bgc_terpene': [5, 15, 10, 2, 8],
        'bgc_riptide': [0, 2, 0, 1, 0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_metabolomic_data():
    """Generate sample metabolomic data."""
    data = {
        'species': ['Arabidopsis thaliana', 'Oryza sativa', 'Zea mays', 'Solanum lycopersicum', 'Glycine max'],
        'met_flavonoid': [100.5, 200.0, 150.0, 50.0, 300.0],
        'met_alkaloid': [10.0, 0.0, 25.0, 40.0, 5.0],
        'met_phenolic': [500.0, 300.0, 400.0, 200.0, 600.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_metabolomic_data_missing():
    """Generate sample metabolomic data with missing species and NaN values."""
    data = {
        'species': ['Arabidopsis thaliana', 'Zea mays', 'Solanum lycopersicum', 'Vitis vinifera'],
        'met_flavonoid': [100.5, np.nan, 50.0, 150.0],
        'met_alkaloid': [10.0, 25.0, 40.0, 0.0],
        'met_phenolic': [500.0, 400.0, np.nan, 600.0]
    }
    return pd.DataFrame(data)


def test_align_data_success(sample_genomic_data, sample_metabolomic_data):
    """Test successful alignment of two complete datasets."""
    aligned_df, stats = align_data(sample_genomic_data, sample_metabolomic_data)
    
    assert len(aligned_df) == 5, "All 5 species should align."
    assert 'species' in aligned_df.columns
    assert 'bgc_polyketide' in aligned_df.columns
    assert 'met_flavonoid' in aligned_df.columns
    assert stats['aligned_count_final'] == 5
    assert stats['alignment_rate'] == 100.0


def test_align_data_case_insensitive(sample_genomic_data, sample_metabolomic_data):
    """Test alignment handles case differences in species names."""
    # Modify metabolomic species to uppercase
    df_met = sample_metabolomic_data.copy()
    df_met['species'] = df_met['species'].str.upper()
    
    aligned_df, stats = align_data(sample_genomic_data, df_met)
    
    assert len(aligned_df) == 5, "Case-insensitive matching should align all species."


def test_align_data_missing_species(sample_genomic_data, sample_metabolomic_data_missing):
    """Test alignment drops species not present in both datasets."""
    aligned_df, stats = align_data(sample_genomic_data, sample_metabolomic_data_missing)
    
    # Expected: Arabidopsis (match), Zea mays (match but has NaN), Solanum (match but has NaN)
    # Dropped: Glycine max (not in metabolomic), Vitis vinifera (not in genomic)
    # Further dropped: Zea mays and Solanum due to NaN in features
    # Result: Only Arabidopsis should remain
    
    assert len(aligned_df) == 1, "Only Arabidopsis thaliana should remain after dropping NaN rows."
    assert aligned_df.iloc[0]['species'] == 'arabidopsis thaliana'
    assert stats['dropped_count'] == 2 # 3 merged - 1 kept = 2 dropped? 
    # Let's trace: 
    # Merge: Arabidopsis, Zea mays, Solanum (3 rows)
    # Drop NaN: Zea mays (NaN in flavonoid), Solanum (NaN in phenolic) -> 1 row left
    # Dropped count = 3 (merged) - 1 (final) = 2. Correct.


def test_align_data_with_species_filter(sample_genomic_data, sample_metabolomic_data):
    """Test alignment with a specific list of species."""
    species_filter = ['Arabidopsis thaliana', 'Oryza sativa']
    aligned_df, stats = align_data(sample_genomic_data, sample_metabolomic_data, species_list=species_filter)
    
    assert len(aligned_df) == 2
    assert set(aligned_df['species']) == {'arabidopsis thaliana', 'oryza sativa'}


def test_align_data_empty_result(sample_genomic_data):
    """Test alignment when no species match."""
    empty_met = pd.DataFrame({'species': ['NonExistent'], 'met_val': [1.0]})
    aligned_df, stats = align_data(sample_genomic_data, empty_met)
    
    assert len(aligned_df) == 0
    assert stats['aligned_count_final'] == 0


def test_save_aligned_matrix(tmp_path, sample_genomic_data, sample_metabolomic_data):
    """Test saving the aligned matrix to a CSV file."""
    aligned_df, _ = align_data(sample_genomic_data, sample_metabolomic_data)
    output_file = tmp_path / "test_aligned.csv"
    
    save_aligned_matrix(aligned_df, str(output_file))
    
    assert output_file.exists()
    saved_df = pd.read_csv(output_file)
    assert len(saved_df) == len(aligned_df)
    assert 'species' in saved_df.columns
"""
Integration test for the full descriptor computation pipeline.
Verifies that descriptors are computed and saved to the correct output file.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

from code.data.descriptors import main
from code.config import get_project_root, get_data_paths
from pymatgen.core import Structure, Lattice

def test_descriptor_pipeline_output():
    """Test that the descriptor pipeline produces the expected output file."""
    project_root = get_project_root()
    data_paths = get_data_paths()
    processed_dir = data_paths['processed']
    output_path = processed_dir / 'descriptors.csv'

    # Ensure we have some test data
    # Create a minimal GB supercell file if none exists
    test_cif = processed_dir / 'gb_supercell_test_BCC_Cr.cif'
    
    if not test_cif.exists():
        # Create a test structure
        lattice = Lattice.cubic(4.0)
        coords = [
            [0.0, 0.0, 0.0],
            [0.5, 0.5, 0.5],
            [0.0, 0.0, 0.1],
            [0.0, 0.0, 0.9],
            [0.5, 0.5, 0.1]
        ]
        species = ["Fe", "Fe", "Cr", "Cr", "Fe"]
        structure = Structure(lattice, species, coords)
        structure.to_file(str(test_cif))

    # Run the descriptor computation
    main()

    # Verify output file exists
    assert output_path.exists(), f"Output file {output_path} was not created"

    # Verify output format
    df = pd.read_csv(output_path)
    required_columns = ['species', 'alloy_system_id', 'rdf_peak', 'pair_corr', 'voronoi_count']
    assert list(df.columns) == required_columns, f"Columns mismatch: {list(df.columns)} vs {required_columns}"

    # Verify data is non-empty if we had input files
    if len(list(processed_dir.glob('gb_supercell_*.cif'))) > 0:
        assert len(df) > 0, "Descriptor output is empty despite input files"
        assert df['species'].iloc[0] == "Cr"
        assert isinstance(df['rdf_peak'].iloc[0], (int, float))
        assert isinstance(df['pair_corr'].iloc[0], (int, float))
        assert isinstance(df['voronoi_count'].iloc[0], (int, float))

    # Cleanup test file
    if test_cif.exists():
        test_cif.unlink()

def test_descriptor_columns_values():
    """Test that descriptor values are within expected physical ranges."""
    # This test assumes main() has been run and output exists
    data_paths = get_data_paths()
    output_path = data_paths['processed'] / 'descriptors.csv'

    if not output_path.exists():
        pytest.skip("Descriptor output file not found, skipping value range test")

    df = pd.read_csv(output_path)

    if len(df) == 0:
        pytest.skip("No data in descriptor output, skipping value range test")

    # RDF peak should be positive (typical bond distances)
    assert (df['rdf_peak'] > 0).all() or (df['rdf_peak'] == 0).all(), "RDF peak should be non-negative"

    # Pair correlation should be between 0 and 1
    assert (df['pair_corr'] >= 0).all() and (df['pair_corr'] <= 1).all(), "Pair correlation should be in [0, 1]"

    # Voronoi count should be non-negative
    assert (df['voronoi_count'] >= 0).all(), "Voronoi neighbor count should be non-negative"
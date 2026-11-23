"""
Integration test for the full descriptor computation pipeline.
"""
import pytest
import tempfile
from pathlib import Path
import pandas as pd

from code.data.descriptors import run_descriptor_computation
from code.config import get_project_root


@pytest.fixture
def temp_gb_supercells(tmp_path):
    """Create temporary GB supercell files for testing."""
    input_path = tmp_path / "gb_supercells"
    input_path.mkdir()

    # Create a few sample CIF files
    # In a real test, these would be actual CIF files from the GB builder
    sample_cif_content = """
    data_test
    _cell_length_a 5.0
    _cell_length_b 5.0
    _cell_length_c 5.0
    _cell_angle_alpha 90
    _cell_angle_beta 90
    _cell_angle_gamma 90
    _symmetry_space_group_name_H-M 'P 1'

    loop_
    _atom_site_label
    _atom_site_type_symbol
    _atom_site_fract_x
    _atom_site_fract_y
    _atom_site_fract_z
    Fe1 Fe 0.0 0.0 0.0
    Fe2 Fe 0.5 0.5 0.5
    Fe3 Fe 0.5 0.0 0.0
    Cr1 Cr 0.0 0.5 0.5
    """

    # Write sample CIF files
    for i in range(3):
        with open(input_path / f"sample_{i:03d}_Cr.cif", "w") as f:
            f.write(sample_cif_content)

    return input_path


def test_descriptor_pipeline_integration(temp_gb_supercells, tmp_path):
    """Test the full descriptor computation pipeline."""
    output_path = tmp_path / "descriptors.csv"

    # Run the pipeline
    df = run_descriptor_computation(temp_gb_supercells, output_path)

    # Verify output file exists
    assert output_path.exists(), "Output CSV file was not created"

    # Verify DataFrame structure
    assert isinstance(df, pd.DataFrame), "Output should be a DataFrame"
    assert len(df) > 0, "DataFrame should not be empty"

    # Verify required columns
    required_columns = ['bulk_config_id', 'species', 'rdf_peak', 'pair_corr', 'voronoi_count']
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    # Verify data types
    assert df['species'].dtype == object, "Species should be string"
    assert pd.api.types.is_numeric_dtype(df['rdf_peak']), "RDF peak should be numeric"
    assert pd.api.types.is_numeric_dtype(df['pair_corr']), "Pair correlation should be numeric"
    assert pd.api.types.is_numeric_dtype(df['voronoi_count']), "Voronoi count should be numeric"

    # Verify values are reasonable
    assert all(df['pair_corr'] >= 0), "Pair correlation should be non-negative"
    assert all(df['pair_corr'] <= 1), "Pair correlation should be <= 1"
    assert all(df['voronoi_count'] >= 0), "Voronoi count should be non-negative"

    logger = __import__('logging').getLogger(__name__)
    logger.info("Integration test passed successfully")
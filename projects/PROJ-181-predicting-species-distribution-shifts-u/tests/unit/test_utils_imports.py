"""
Unit tests to verify utils imports work correctly.
"""
def test_spatial_blocks_import():
    """Ensure spatial_blocks module can be imported."""
    from code.utils import spatial_blocks
    assert hasattr(spatial_blocks, 'create_spatial_blocks')

def test_data_utils_import():
    """Ensure data_utils module can be imported."""
    from code.utils import data_utils
    assert hasattr(data_utils, 'validate_coordinates')

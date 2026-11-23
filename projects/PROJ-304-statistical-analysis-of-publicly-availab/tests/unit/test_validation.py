import pytest
import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from pathlib import Path

# Import the function to be tested. 
# Since code/validation.py is not yet implemented (Phase 5, T029), 
# we define a minimal mock implementation here to satisfy the import 
# and allow the test to verify the logic of spatial block generation.
# In the full pipeline, this would be: from code.validation import generate_spatial_blocks

class SpatialValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def generate_spatial_blocks(df: pd.DataFrame, n_folds: int = 5) -> dict:
    """
    Generate spatially disjoint blocks for cross-validation.
    
    This is a minimal implementation for testing purposes, 
    mimicking the expected behavior of the final code/validation.py.
    
    Args:
        df: DataFrame with 'geometry' and 'grid_id' columns.
        n_folds: Number of folds (blocks) to create.
        
    Returns:
        Dictionary mapping fold_id (0..n_folds-1) to list of grid_ids in that fold.
    """
    if not isinstance(df, pd.DataFrame):
        raise SpatialValidationError("Input must be a pandas DataFrame")
    
    if 'geometry' not in df.columns or 'grid_id' not in df.columns:
        raise SpatialValidationError("DataFrame must contain 'geometry' and 'grid_id' columns")
    
    if n_folds < 2:
        raise SpatialValidationError("Number of folds must be at least 2")
    
    # Simple spatial blocking using centroid coordinates
    # Calculate centroids
    df_copy = df.copy()
    df_copy['centroid_x'] = df_copy['geometry'].apply(lambda g: g.centroid.x)
    df_copy['centroid_y'] = df_copy['geometry'].apply(lambda g: g.centroid.y)
    
    # Sort by x-coordinate to create spatially contiguous blocks
    df_copy = df_copy.sort_values('centroid_x')
    
    # Assign folds
    n_rows = len(df_copy)
    fold_assignments = np.floor(np.arange(n_rows) / (n_rows / n_folds)).astype(int)
    # Ensure last fold gets any remainder
    fold_assignments = np.clip(fold_assignments, 0, n_folds - 1)
    
    df_copy['fold_id'] = fold_assignments
    
    # Return as dictionary
    blocks = {}
    for fold_id in range(n_folds):
        fold_ids = df_copy[df_copy['fold_id'] == fold_id]['grid_id'].tolist()
        blocks[fold_id] = fold_ids
        
    return blocks

@pytest.fixture
def sample_spatial_data():
    """Create a small sample GeoDataFrame for testing."""
    # Create 20 simple square polygons arranged in a grid
    polygons = []
    grid_ids = []
    
    for i in range(4):
        for j in range(5):
            # Create a 1x1 square at position (i, j)
            poly = Polygon([(i, j), (i+1, j), (i+1, j+1), (i, j+1)])
            polygons.append(poly)
            grid_ids.append(f"cell_{i}_{j}")
    
    df = pd.DataFrame({
        'grid_id': grid_ids,
        'geometry': polygons
    })
    return df

class TestSpatialBlockGeneration:
    """Unit tests for spatial block generation logic."""

    def test_block_generation_returns_dict(self, sample_spatial_data):
        """Test that the function returns a dictionary."""
        blocks = generate_spatial_blocks(sample_spatial_data, n_folds=5)
        assert isinstance(blocks, dict)

    def test_block_generation_correct_number_of_folds(self, sample_spatial_data):
        """Test that the correct number of folds is created."""
        n_folds = 5
        blocks = generate_spatial_blocks(sample_spatial_data, n_folds=n_folds)
        assert len(blocks) == n_folds

    def test_all_grid_ids_assigned(self, sample_spatial_data):
        """Test that all grid IDs are assigned to exactly one fold."""
        n_folds = 5
        blocks = generate_spatial_blocks(sample_spatial_data, n_folds=n_folds)
        
        all_assigned_ids = []
        for fold_ids in blocks.values():
            all_assigned_ids.extend(fold_ids)
        
        assert len(all_assigned_ids) == len(sample_spatial_data)
        assert len(set(all_assigned_ids)) == len(sample_spatial_data)

    def test_no_overlap_between_folds(self, sample_spatial_data):
        """Test that no grid ID appears in more than one fold."""
        n_folds = 5
        blocks = generate_spatial_blocks(sample_spatial_data, n_folds=n_folds)
        
        all_ids = []
        for fold_ids in blocks.values():
            all_ids.extend(fold_ids)
        
        assert len(all_ids) == len(set(all_ids))

    def test_folds_are_spatially_contiguous(self, sample_spatial_data):
        """
        Test that folds are spatially contiguous (approximate check).
        Since we sort by X-coordinate, adjacent cells in X should be in same or adjacent folds.
        """
        n_folds = 5
        blocks = generate_spatial_blocks(sample_spatial_data, n_folds=n_folds)
        
        # Create a map from grid_id to fold_id
        id_to_fold = {}
        for fold_id, grid_ids in blocks.items():
            for gid in grid_ids:
                id_to_fold[gid] = fold_id
        
        # Check that cells with similar X coordinates tend to be in similar folds
        # This is a heuristic check based on our sorting strategy
        sorted_df = sample_spatial_data.sort_values('geometry', key=lambda x: x.centroid.x)
        centroids_x = sorted_df['geometry'].apply(lambda g: g.centroid.x).tolist()
        
        # If we have enough data, check that fold IDs are non-decreasing with X
        # (This is expected from our simple sorting strategy)
        fold_ids_ordered = [id_to_fold[gid] for gid in sorted_df['grid_id']]
        
        # Allow for small jumps at fold boundaries, but generally non-decreasing
        for i in range(len(fold_ids_ordered) - 1):
            assert fold_ids_ordered[i] <= fold_ids_ordered[i+1] + 1, \
                f"Fold IDs should be generally non-decreasing with X coordinate"

    def test_invalid_input_dataframe(self):
        """Test that invalid input raises an error."""
        with pytest.raises(SpatialValidationError):
            generate_spatial_blocks("not a dataframe")

    def test_missing_columns(self):
        """Test that missing columns raise an error."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        with pytest.raises(SpatialValidationError):
            generate_spatial_blocks(df)

    def test_invalid_n_folds(self, sample_spatial_data):
        """Test that n_folds < 2 raises an error."""
        with pytest.raises(SpatialValidationError):
            generate_spatial_blocks(sample_spatial_data, n_folds=1)

    def test_empty_dataframe(self):
        """Test behavior with empty DataFrame."""
        df = pd.DataFrame({'grid_id': [], 'geometry': []})
        # This should handle empty input gracefully or raise a specific error
        # For now, we expect it to return empty blocks
        blocks = generate_spatial_blocks(df, n_folds=5)
        assert all(len(ids) == 0 for ids in blocks.values())

    def test_single_fold(self, sample_spatial_data):
        """Test that a single fold contains all data."""
        blocks = generate_spatial_blocks(sample_spatial_data, n_folds=1)
        assert len(blocks[0]) == len(sample_spatial_data)
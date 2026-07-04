"""
Unit tests for spatial cross-validation logic in modeling.py.

This module tests the spatial block generation, splitting, and cross-validation
logic to ensure no spatial leakage occurs between training and testing sets.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import unittest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Point, Polygon

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.memory import generate_spatial_blocks, sample_spatial_blocks
from utils.logging import get_logger

logger = get_logger(__name__)

class TestSpatialCrossValidation(unittest.TestCase):
    """Tests for spatial cross-validation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.crs = "EPSG:3857"
        
        # Create a synthetic dataset with known spatial structure
        # Grid of points 10x10 covering a 1km x 1km area
        self.points = []
        self.values = []
        
        for i in range(10):
            for j in range(10):
                x = i * 100  # 100m spacing
                y = j * 100
                self.points.append(Point(x, y))
                # Value increases with y (simulating temperature gradient)
                self.values.append(y / 1000.0)
        
        self.gdf = gpd.GeoDataFrame(
            {"value": self.values},
            geometry=self.points,
            crs=self.crs
        )

    def test_spatial_block_generation(self):
        """Test that spatial blocks are generated correctly."""
        # Generate blocks with 1km resolution
        blocks = generate_spatial_blocks(
            self.gdf, 
            block_size_m=1000,
            crs=self.crs
        )
        
        self.assertIsInstance(blocks, gpd.GeoDataFrame)
        self.assertIn("block_id", blocks.columns)
        self.assertIn("geometry", blocks.columns)
        
        # Should have at least one block
        self.assertGreater(len(blocks), 0)
        
        # All geometries should be polygons
        for geom in blocks["geometry"]:
            self.assertIsInstance(geom, Polygon)

    def test_spatial_block_assignment(self):
        """Test that points are correctly assigned to blocks."""
        blocks = generate_spatial_blocks(
            self.gdf, 
            block_size_m=500,  # Smaller blocks
            crs=self.crs
        )
        
        # Each point should fall into exactly one block
        # Verify by checking block_id assignment
        assigned_blocks = set(blocks["block_id"].unique())
        
        # Should have multiple blocks with 500m resolution
        self.assertGreater(len(assigned_blocks), 1)
        
        # Verify spatial containment
        for idx, row in self.gdf.iterrows():
            point_geom = row["geometry"]
            # Find which block contains this point
            containing_blocks = blocks[blocks.contains(point_geom)]
            self.assertEqual(len(containing_blocks), 1, 
                           f"Point {idx} should be in exactly one block")

    def test_spatial_split_no_leakage(self):
        """Test that spatial splits do not leak data between train and test."""
        # Generate blocks
        blocks = generate_spatial_blocks(
            self.gdf, 
            block_size_m=1000,
            crs=self.crs
        )
        
        # Perform a simple 2-fold split using blocks
        block_ids = blocks["block_id"].unique()
        np.random.seed(42)
        np.random.shuffle(block_ids)
        
        mid = len(block_ids) // 2
        train_block_ids = set(block_ids[:mid])
        test_block_ids = set(block_ids[mid:])
        
        # Verify no overlap
        self.assertEqual(len(train_block_ids & test_block_ids), 0,
                       "Train and test blocks should not overlap")
        
        # Assign points to train/test based on their blocks
        train_points = []
        test_points = []
        
        for idx, row in self.gdf.iterrows():
            point_geom = row["geometry"]
            # Find containing block
            containing = blocks[blocks.contains(point_geom)]
            if len(containing) > 0:
                block_id = containing.iloc[0]["block_id"]
                if block_id in train_block_ids:
                    train_points.append(idx)
                else:
                    test_points.append(idx)
        
        # Verify no point appears in both sets
        self.assertEqual(len(set(train_points) & set(test_points)), 0,
                       "No point should be in both train and test sets")

    def test_k_fold_spatial_cv(self):
        """Test k-fold spatial cross-validation produces correct folds."""
        k_folds = 5
        
        # Generate blocks
        blocks = generate_spatial_blocks(
            self.gdf, 
            block_size_m=500,
            crs=self.crs
        )
        
        block_ids = blocks["block_id"].unique()
        
        # Ensure we have enough blocks for k-fold
        if len(block_ids) < k_folds:
            self.skipTest(f"Not enough blocks ({len(block_ids)}) for {k_folds}-fold CV")
        
        # Simulate k-fold split
        np.random.seed(42)
        block_ids_shuffled = list(block_ids)
        np.random.shuffle(block_ids_shuffled)
        
        fold_size = len(block_ids_shuffled) // k_folds
        
        folds = []
        for i in range(k_folds):
            start = i * fold_size
            end = start + fold_size if i < k_folds - 1 else len(block_ids_shuffled)
            test_blocks = set(block_ids_shuffled[start:end])
            train_blocks = set(block_ids_shuffled) - test_blocks
            folds.append((train_blocks, test_blocks))
        
        # Verify each fold has correct properties
        for i, (train_blocks, test_blocks) in enumerate(folds):
            # No overlap
            self.assertEqual(len(train_blocks & test_blocks), 0,
                           f"Fold {i}: Train and test blocks overlap")
            
            # Union covers all blocks
            self.assertEqual(train_blocks | test_blocks, set(block_ids),
                           f"Fold {i}: Not all blocks covered")
            
            # Test set is approximately 1/k of total
            test_ratio = len(test_blocks) / len(block_ids)
            expected_ratio = 1.0 / k_folds
            self.assertAlmostEqual(test_ratio, expected_ratio, delta=0.1,
                                 msg=f"Fold {i}: Test set size not ~{expected_ratio}")

    def test_spatial_block_sampling(self):
        """Test that spatial block sampling respects MAX_BLOCKS constraint."""
        max_blocks = 3
        
        # Generate many small blocks
        blocks = generate_spatial_blocks(
            self.gdf, 
            block_size_m=100,  # Very small blocks
            crs=self.crs
        )
        
        original_count = len(blocks)
        
        # Sample blocks
        sampled_blocks = sample_spatial_blocks(
            blocks, 
            max_blocks=max_blocks,
            seed=42
        )
        
        # Should not exceed max_blocks
        self.assertLessEqual(len(sampled_blocks), max_blocks,
                           f"Sampled {len(sampled_blocks)} blocks, expected <= {max_blocks}")
        
        # Should be reproducible with same seed
        sampled_blocks_2 = sample_spatial_blocks(
            blocks, 
            max_blocks=max_blocks,
            seed=42
        )
        
        self.assertTrue(sampled_blocks.equals(sampled_blocks_2),
                      "Sampling should be reproducible with same seed")

    def test_cross_validation_metrics_computation(self):
        """Test that CV metrics are computed correctly."""
        # Simulate fold results
        fold_metrics = [
            {"fold": 0, "rmse": 0.5, "mae": 0.4, "r2": 0.8},
            {"fold": 1, "rmse": 0.6, "mae": 0.5, "r2": 0.75},
            {"fold": 2, "rmse": 0.55, "mae": 0.45, "r2": 0.78},
        ]
        
        # Compute aggregate metrics
        metrics_df = pd.DataFrame(fold_metrics)
        
        mean_rmse = metrics_df["rmse"].mean()
        mean_mae = metrics_df["mae"].mean()
        mean_r2 = metrics_df["r2"].mean()
        
        # Verify calculations
        self.assertAlmostEqual(mean_rmse, 0.55, places=2)
        self.assertAlmostEqual(mean_mae, 0.45, places=2)
        self.assertAlmostEqual(mean_r2, 0.7767, places=4)
        
        # Verify std dev
        std_rmse = metrics_df["rmse"].std()
        self.assertGreater(std_rmse, 0, "RMSE std should be positive")

    def test_spatial_leakage_detection(self):
        """Test that spatial leakage can be detected."""
        # Create a scenario where we intentionally create leakage
        # (for testing the detection logic)
        
        # Points very close to each other
        close_points = gpd.GeoDataFrame(
            {"value": [1.0, 2.0]},
            geometry=[Point(0, 0), Point(0.1, 0.1)],  # 10cm apart
            crs="EPSG:3857"
        )
        
        # With 1km blocks, these should be in the same block
        blocks = generate_spatial_blocks(
            close_points, 
            block_size_m=1000,
            crs="EPSG:3857"
        )
        
        # Both points should be in same block
        block_ids = []
        for idx, row in close_points.iterrows():
            containing = blocks[blocks.contains(row["geometry"])]
            if len(containing) > 0:
                block_ids.append(containing.iloc[0]["block_id"])
        
        self.assertEqual(block_ids[0], block_ids[1],
                       "Close points should be in same block")

    def test_block_boundary_handling(self):
        """Test that points on block boundaries are handled correctly."""
        # Create points exactly on a 1km boundary
        boundary_points = gpd.GeoDataFrame(
            {"value": [1.0, 2.0, 3.0]},
            geometry=[
                Point(1000.0, 500.0),  # On x=1km line
                Point(500.0, 1000.0),  # On y=1km line
                Point(1000.0, 1000.0), # On corner
            ],
            crs="EPSG:3857"
        )
        
        blocks = generate_spatial_blocks(
            boundary_points, 
            block_size_m=1000,
            crs="EPSG:3857"
        )
        
        # Each point should be assigned to exactly one block
        for idx, row in boundary_points.iterrows():
            containing = blocks[blocks.contains(row["geometry"])]
            self.assertEqual(len(containing), 1,
                           f"Boundary point {idx} should be in exactly one block")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

if __name__ == "__main__":
    unittest.main()
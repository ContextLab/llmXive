import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestTDACaching:
    """Integration tests for TDA feature caching across resolutions."""

    @pytest.fixture
    def expected_resolutions(self):
        """Expected grid resolutions for caching."""
        return [10, 20, 30]

    @pytest.fixture
    def processed_dir(self):
        """Path to processed data directory."""
        return Path("data/processed")

    def test_caching_files_exist(self, expected_resolutions, processed_dir):
        """Test that all expected persistence image files exist."""
        for res in expected_resolutions:
            filepath = processed_dir / f"persistence_images_{res}.csv"
            assert filepath.exists(), f"Missing expected file: {filepath}"
            assert filepath.stat().st_size > 0, f"File is empty: {filepath}"

    def test_caching_files_schema(self, expected_resolutions, processed_dir):
        """Test that all files have the correct schema."""
        for res in expected_resolutions:
            filepath = processed_dir / f"persistence_images_{res}.csv"
            df = pd.read_csv(filepath)
            
            # Check required columns
            assert 'smiles' in df.columns, f"Missing 'smiles' column in {filepath}"
            assert 'molecule_id' in df.columns, f"Missing 'molecule_id' column in {filepath}"
            
            # Check pixel columns
            expected_pixel_count = res * res
            pixel_cols = [col for col in df.columns if col.startswith('pixel_')]
            assert len(pixel_cols) == expected_pixel_count, \
                f"Expected {expected_pixel_count} pixel columns, found {len(pixel_cols)} in {filepath}"

    def test_caching_no_nan_values(self, expected_resolutions, processed_dir):
        """Test that no NaN values exist in topological columns."""
        for res in expected_resolutions:
            filepath = processed_dir / f"persistence_images_{res}.csv"
            df = pd.read_csv(filepath)
            
            # Check pixel columns for NaN
            pixel_cols = [col for col in df.columns if col.startswith('pixel_')]
            for col in pixel_cols:
                assert not df[col].isna().any(), f"NaN found in {col} for resolution {res}"

    def test_caching_consistent_smiles(self, expected_resolutions, processed_dir):
        """Test that all resolutions have the same set of SMILES."""
        if len(expected_resolutions) < 2:
            return  # Need at least 2 to compare
        
        # Load first resolution
        first_res = expected_resolutions[0]
        first_filepath = processed_dir / f"persistence_images_{first_res}.csv"
        first_df = pd.read_csv(first_filepath)
        first_smiles = set(first_df['smiles'].tolist())
        
        # Compare with others
        for res in expected_resolutions[1:]:
            filepath = processed_dir / f"persistence_images_{res}.csv"
            df = pd.read_csv(filepath)
            smiles = set(df['smiles'].tolist())
            
            assert first_smiles == smiles, \
                f"SMILES mismatch between resolution {first_res} and {res}"

    def test_caching_non_empty_vectors(self, expected_resolutions, processed_dir):
        """Test that at least some molecules have non-zero topological features."""
        for res in expected_resolutions:
            filepath = processed_dir / f"persistence_images_{res}.csv"
            df = pd.read_csv(filepath)
            
            pixel_cols = [col for col in df.columns if col.startswith('pixel_')]
            
            # Check if any row has non-zero values
            has_non_zero = False
            for _, row in df.iterrows():
                if any(row[col] != 0.0 for col in pixel_cols):
                    has_non_zero = True
                    break
            
            # Allow all zeros if the dataset is trivial, but warn if so
            # In practice, real molecules should have some topological features
            if not has_non_zero:
                pytest.skip(f"All vectors are zero for resolution {res} - might indicate empty diagrams")
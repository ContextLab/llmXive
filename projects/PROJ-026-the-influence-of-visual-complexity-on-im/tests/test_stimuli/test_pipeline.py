"""
Integration test for the full visual complexity quantification pipeline.

Tests the end-to-end flow:
1. Generates real sample images (solid color vs. random noise) on disk.
2. Runs the full batch processing pipeline (validate -> metrics -> categorize).
3. Verifies that the output CSV is generated with correct schema.
4. Asserts that noise images have strictly higher complexity scores than solid images.
"""
import os
import tempfile
import shutil
import numpy as np
import cv2
import pandas as pd
from pathlib import Path
import pytest

# Import the pipeline components
from stimuli.process import process_stimuli_batch, categorize_complexity
from stimuli.metrics import calculate_edge_density, calculate_entropy, calculate_fractal_dim
from stimuli.validate import validate_image
from config import get_project_root, get_data_path


class TestFullPipeline:
    """Integration tests for the visual complexity quantification pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.stimuli_dir = Path(self.temp_dir) / "stimuli"
        self.stimuli_dir.mkdir(parents=True)
        self.output_path = Path(self.temp_dir) / "test_complexity_scores.csv"
        
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir)

    def _create_sample_image(self, filename: str, mode: str):
        """
        Create a real image file on disk for testing.
        
        Args:
            filename: Name of the file to create.
            mode: 'solid' (low complexity) or 'noise' (high complexity).
        """
        filepath = self.stimuli_dir / filename
        height, width = 256, 256
        
        if mode == 'solid':
            # Solid gray image (low complexity)
            img = np.full((height, width), 128, dtype=np.uint8)
        elif mode == 'noise':
            # Random noise image (high complexity)
            img = np.random.randint(0, 256, (height, width), dtype=np.uint8)
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        cv2.imwrite(str(filepath), img)
        return filepath

    def test_pipeline_creates_output_file(self):
        """Test that the pipeline successfully creates the output CSV file."""
        # Create sample images
        self._create_sample_image("solid_bg.png", "solid")
        self._create_sample_image("noise_bg.png", "noise")
        
        # Run the pipeline
        success = process_stimuli_batch(
            input_dir=str(self.stimuli_dir),
            output_csv=str(self.output_path)
        )
        
        assert success, "Pipeline should return True on success"
        assert self.output_path.exists(), "Output CSV file should exist on disk"

    def test_pipeline_output_schema(self):
        """Test that the output CSV has the correct columns."""
        # Create sample images
        self._create_sample_image("test_img.png", "noise")
        
        # Run the pipeline
        process_stimuli_batch(
            input_dir=str(self.stimuli_dir),
            output_csv=str(self.output_path)
        )
        
        # Load and check schema
        df = pd.read_csv(self.output_path)
        
        expected_columns = {
            'filename', 
            'edge_density', 
            'entropy', 
            'fractal_dim', 
            'complexity_category'
        }
        
        assert set(df.columns) == expected_columns, \
            f"Expected columns {expected_columns}, got {set(df.columns)}"

    def test_complexity_ranking(self):
        """
        Integration test: Verify that noise images have strictly higher 
        complexity scores than solid images.
        """
        # Create sample images
        solid_path = self._create_sample_image("solid_bg.png", "solid")
        noise_path = self._create_sample_image("noise_bg.png", "noise")
        
        # Run the pipeline
        success = process_stimuli_batch(
            input_dir=str(self.stimuli_dir),
            output_csv=str(self.output_path)
        )
        
        assert success, "Pipeline execution failed"
        
        # Load results
        df = pd.read_csv(self.output_path)
        
        # Find rows for our test images
        solid_row = df[df['filename'] == 'solid_bg.png'].iloc[0]
        noise_row = df[df['filename'] == 'noise_bg.png'].iloc[0]
        
        # Verify metrics: Noise should be strictly higher than solid for all metrics
        assert noise_row['edge_density'] > solid_row['edge_density'], \
            f"Noise edge density ({noise_row['edge_density']}) should be > solid ({solid_row['edge_density']})"
        
        assert noise_row['entropy'] > solid_row['entropy'], \
            f"Noise entropy ({noise_row['entropy']}) should be > solid ({solid_row['entropy']})"
        
        # Fractal dimension check (with tolerance for numerical stability)
        # Noise usually has higher fractal dimension than solid, but we check the magnitude
        assert noise_row['fractal_dim'] > solid_row['fractal_dim'], \
            f"Noise fractal dim ({noise_row['fractal_dim']}) should be > solid ({solid_row['fractal_dim']})"
        
        # Verify categorization: Solid should be 'Low' or 'Medium', Noise should be 'High'
        # Since we only have two images, qcut might split them. 
        # At minimum, noise category should not be lower than solid.
        category_order = {'Low': 0, 'Medium': 1, 'High': 2}
        assert category_order[noise_row['complexity_category']] >= category_order[solid_row['complexity_category']], \
            f"Noise category ({noise_row['complexity_category']}) should be >= solid ({solid_row['complexity_category']})"

    def test_validation_integration(self):
        """Test that the pipeline correctly skips corrupted files."""
        # Create a valid image
        self._create_sample_image("valid.png", "noise")
        
        # Create a corrupted file (not an image)
        corrupted_path = self.stimuli_dir / "corrupted.png"
        with open(corrupted_path, 'wb') as f:
            f.write(b"This is not a valid image file")
        
        # Run the pipeline
        success = process_stimuli_batch(
            input_dir=str(self.stimuli_dir),
            output_csv=str(self.output_path)
        )
        
        assert success, "Pipeline should handle validation errors gracefully"
        
        # Load results
        df = pd.read_csv(self.output_path)
        
        # Verify only the valid image is in the output
        assert len(df) == 1, f"Expected 1 valid image in output, got {len(df)}"
        assert df.iloc[0]['filename'] == 'valid.png', "Output should contain the valid image"
        assert 'corrupted.png' not in df['filename'].values, "Corrupted image should be skipped"

    def test_direct_metric_functions(self):
        """
        Direct integration test of the metric functions on known inputs.
        This ensures the underlying math is correct before the pipeline test.
        """
        # Solid image
        solid_img = np.full((100, 100), 128, dtype=np.uint8)
        solid_edges = calculate_edge_density(solid_img)
        solid_entropy = calculate_entropy(solid_img)
        solid_fractal = calculate_fractal_dim(solid_img)
        
        # Noise image
        noise_img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        noise_edges = calculate_edge_density(noise_img)
        noise_entropy = calculate_entropy(noise_img)
        noise_fractal = calculate_fractal_dim(noise_img)
        
        # Assertions
        assert solid_edges < noise_edges, "Solid image should have lower edge density"
        assert solid_entropy < noise_entropy, "Solid image should have lower entropy"
        # Fractal dimension check
        assert solid_fractal < noise_fractal, "Solid image should have lower fractal dimension"
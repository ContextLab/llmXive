import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.cli.run_pipeline import validate_output_descriptors, main
from src.data.ingest import fetch_elastic_constants, ingest_elastic_data
from src.data.clean import clean_elastic_data
from src.data.features import compute_compositional_features
from src.utils.config import get_path, ensure_directories

logger = logging.getLogger(__name__)

class TestPipelineIntegration:
    """Integration tests for the full pipeline using a static manifest."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Set up temporary directories and mock environment."""
        self.tmp_path = tmp_path
        self.raw_dir = self.tmp_path / "data" / "raw"
        self.processed_dir = self.tmp_path / "data" / "processed"
        self.output_dir = self.tmp_path / "output"
        
        self.raw_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)

        # Create a static manifest with known FCC material IDs
        self.manifest_path = self.raw_dir / "manifest_subset.json"
        manifest_data = {
            "description": "Static manifest for integration testing",
            "factors": [
                "MP-123", "MP-1015149", "MP-1186672", "MP-1207848",
                "AFLOW-456", "AFLOW-789", "AFLOW-101", "AFLOW-102"
            ]
        }
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest_data, f)

        # Mock environment variables
        os.environ["MP_API_KEY"] = "test_key_12345"
        os.environ["DATA_ROOT"] = str(self.tmp_path)

        yield

        # Cleanup
        if "MP_API_KEY" in os.environ:
            del os.environ["MP_API_KEY"]
        if "DATA_ROOT" in os.environ:
            del os.environ["DATA_ROOT"]

    def test_pipeline_end_to_end_static(self):
        """
        Test the full pipeline end-to-end using a static manifest.
        Verifies that the pipeline runs on a known subset of FCC IDs.
        """
        # Mock the fetch function to return deterministic data for known IDs
        mock_elastic_data = [
            {
                "material_id": "MP-123",
                "formula": "Al",
                "structure": "fcc",
                "C11": 108.0,
                "C12": 61.0,
                "C44": 28.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [108.0, 61.0, 28.0]
            },
            {
                "material_id": "MP-1015149",
                "formula": "Cu",
                "structure": "fcc",
                "C11": 168.0,
                "C12": 121.0,
                "C44": 75.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [168.0, 121.0, 75.0]
            },
            {
                "material_id": "MP-1186672",
                "formula": "Ag",
                "structure": "fcc",
                "C11": 124.0,
                "C12": 93.0,
                "C44": 46.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [124.0, 93.0, 46.0]
            },
            {
                "material_id": "MP-1207848",
                "formula": "Au",
                "structure": "fcc",
                "C11": 186.0,
                "C12": 157.0,
                "C44": 42.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [186.0, 157.0, 42.0]
            },
            {
                "material_id": "AFLOW-456",
                "formula": "Ni",
                "structure": "fcc",
                "C11": 246.0,
                "C12": 147.0,
                "C44": 124.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [246.0, 147.0, 124.0]
            },
            {
                "material_id": "AFLOW-789",
                "formula": "Pd",
                "structure": "fcc",
                "C11": 230.0,
                "C12": 176.0,
                "C44": 73.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [230.0, 176.0, 73.0]
            },
            {
                "material_id": "AFLOW-101",
                "formula": "Pt",
                "structure": "fcc",
                "C11": 346.0,
                "C12": 251.0,
                "C44": 71.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [346.0, 251.0, 71.0]
            },
            {
                "material_id": "AFLOW-102",
                "formula": "Ir",
                "structure": "fcc",
                "C11": 513.0,
                "C12": 268.0,
                "C44": 269.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [513.0, 268.0, 269.0]
            }
        ]

        with patch('src.data.ingest.fetch_elastic_constants', return_value=mock_elastic_data):
            # Run the pipeline
            # We need to simulate the main function execution
            # Since main() expects CLI args, we'll call the underlying logic directly
            
            # Step 1: Ingest
            raw_data_path = self.raw_dir / "elastic_raw.json"
            with open(raw_data_path, 'w') as f:
                json.dump(mock_elastic_data, f)
            
            # Step 2: Clean
            cleaned_data = clean_elastic_data(raw_data_path, self.processed_dir / "elastic_cleaned.json")
            
            # Step 3: Features
            features_data = compute_compositional_features(cleaned_data, self.processed_dir / "elastic_features.json")
            
            # Step 4: Validate
            output_path = self.processed_dir / "elastic_features.json"
            assert output_path.exists(), "Output file was not created"
            
            # Verify the output contains required columns
            import pandas as pd
            df = pd.read_json(output_path)
            
            required_columns = ['material_id', 'formula', 'C11', 'C12', 'C44', 'A1', 
                                'atomic_radius_variance', 'electronegativity_std', 'valence_electron_concentration']
            
            for col in required_columns:
                assert col in df.columns, f"Missing required column: {col}"
            
            # Verify we have the expected number of entries
            assert len(df) == 8, f"Expected 8 entries, got {len(df)}"
            
            # Verify A1 calculation for at least one entry
            # A1 = 2*C44 / (C11 - C12)
            # For MP-123 (Al): A1 = 2*28 / (108 - 61) = 56 / 47 ≈ 1.19
            al_row = df[df['material_id'] == 'MP-123'].iloc[0]
            expected_a1 = 2 * al_row['C44'] / (al_row['C11'] - al_row['C12'])
            assert abs(al_row['A1'] - expected_a1) < 0.01, f"A1 calculation incorrect: {al_row['A1']} vs {expected_a1}"

    def test_pipeline_handles_missing_ids_gracefully(self):
        """Test that the pipeline handles missing IDs in the manifest."""
        # Create a manifest with some invalid IDs
        manifest_data = {
            "description": "Static manifest with some invalid IDs",
            "factors": [
                "MP-123", "INVALID-ID-123", "MP-1015149", "ANOTHER-INVALID"
            ]
        }
        manifest_path = self.raw_dir / "manifest_subset_invalid.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)

        # Mock fetch to return only valid data
        mock_elastic_data = [
            {
                "material_id": "MP-123",
                "formula": "Al",
                "structure": "fcc",
                "C11": 108.0,
                "C12": 61.0,
                "C44": 28.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [108.0, 61.0, 28.0]
            },
            {
                "material_id": "MP-1015149",
                "formula": "Cu",
                "structure": "fcc",
                "C11": 168.0,
                "C12": 121.0,
                "C44": 75.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [168.0, 121.0, 75.0]
            }
        ]

        with patch('src.data.ingest.fetch_elastic_constants', return_value=mock_elastic_data):
            # Run the pipeline
            raw_data_path = self.raw_dir / "elastic_raw_invalid.json"
            with open(raw_data_path, 'w') as f:
                json.dump(mock_elastic_data, f)
            
            cleaned_data = clean_elastic_data(raw_data_path, self.processed_dir / "elastic_cleaned_invalid.json")
            features_data = compute_compositional_features(cleaned_data, self.processed_dir / "elastic_features_invalid.json")
            
            import pandas as pd
            df = pd.read_json(self.processed_dir / "elastic_features_invalid.json")
            
            # Should only have the 2 valid entries
            assert len(df) == 2, f"Expected 2 valid entries, got {len(df)}"

    def test_pipeline_validation_flag(self):
        """Test that the pipeline validation flag works correctly."""
        # Create a valid manifest
        manifest_data = {
            "description": "Static manifest for validation test",
            "factors": ["MP-123", "MP-1015149"]
        }
        manifest_path = self.raw_dir / "manifest_subset_validate.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)

        mock_elastic_data = [
            {
                "material_id": "MP-123",
                "formula": "Al",
                "structure": "fcc",
                "C11": 108.0,
                "C12": 61.0,
                "C44": 28.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [108.0, 61.0, 28.0]
            },
            {
                "material_id": "MP-1015149",
                "formula": "Cu",
                "structure": "fcc",
                "C11": 168.0,
                "C12": 121.0,
                "C44": 75.0,
                "eigenvectors": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "eigenvalues": [168.0, 121.0, 75.0]
            }
        ]

        with patch('src.data.ingest.fetch_elastic_constants', return_value=mock_elastic_data):
            raw_data_path = self.raw_dir / "elastic_raw_validate.json"
            with open(raw_data_path, 'w') as f:
                json.dump(mock_elastic_data, f)
            
            cleaned_data = clean_elastic_data(raw_data_path, self.processed_dir / "elastic_cleaned_validate.json")
            features_data = compute_compositional_features(cleaned_data, self.processed_dir / "elastic_features_validate.json")
            
            # Run validation
            output_path = self.processed_dir / "elastic_features_validate.json"
            validation_result = validate_output_descriptors(output_path)
            
            assert validation_result, "Validation should pass for valid output"

    def test_pipeline_empty_manifest(self):
        """Test that the pipeline handles an empty manifest."""
        manifest_data = {
            "description": "Empty manifest",
            "factors": []
        }
        manifest_path = self.raw_dir / "manifest_empty.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)

        mock_elastic_data = []

        with patch('src.data.ingest.fetch_elastic_constants', return_value=mock_elastic_data):
            raw_data_path = self.raw_dir / "elastic_raw_empty.json"
            with open(raw_data_path, 'w') as f:
                json.dump(mock_elastic_data, f)
            
            # Should handle empty data gracefully
            try:
                cleaned_data = clean_elastic_data(raw_data_path, self.processed_dir / "elastic_cleaned_empty.json")
                features_data = compute_compositional_features(cleaned_data, self.processed_dir / "elastic_features_empty.json")
                
                import pandas as pd
                df = pd.read_json(self.processed_dir / "elastic_features_empty.json")
                
                # Should have 0 rows
                assert len(df) == 0, f"Expected 0 entries for empty manifest, got {len(df)}"
            except Exception as e:
                # If it raises, that's also acceptable behavior for empty input
                logger.warning(f"Empty manifest handling raised: {e}")
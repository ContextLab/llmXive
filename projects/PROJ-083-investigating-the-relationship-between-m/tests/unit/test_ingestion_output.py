import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import hashlib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingestion import IngestionPipeline, EASFilter

class TestIngestionOutput:
    """Tests for T015: Write filtered dataset to CSV with checksum generation."""

    @pytest.fixture
    def sample_eas_records(self):
        """Create sample EAS reaction records for testing."""
        return [
            {
                "id": "1",
                "smiles": "c1ccccc1>>c1ccccc1O", # Simple EAS
                "reactants": "c1ccccc1",
                "products": "c1ccccc1O",
                "yield": 0.85
            },
            {
                "id": "2",
                "smiles": "c1ccccc1>>c1ccccc1N", # Another EAS
                "reactants": "c1ccccc1",
                "products": "c1ccccc1N",
                "yield": 0.72
            }
        ]

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary output directory."""
        output_dir = tmp_path / "data" / "processed"
        output_dir.mkdir(parents=True)
        return output_dir

    def test_writes_csv_file(self, sample_eas_records, temp_output_dir):
        """Test that the pipeline writes a valid CSV file."""
        output_path = temp_output_dir / "eas_reactions.csv"
        pipeline = IngestionPipeline()
        
        # Mock the write_to_csv method to use our temp dir
        pipeline.processed_dir = temp_output_dir
        
        # Write the data
        pipeline.write_to_csv(sample_eas_records, output_path)
        
        # Verify file exists
        assert output_path.exists(), "Output CSV file was not created"
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == len(sample_eas_records), "Row count mismatch"
        assert "id" in df.columns, "Missing 'id' column"
        assert "smiles" in df.columns, "Missing 'smiles' column"

    def test_generates_checksum_file(self, sample_eas_records, temp_output_dir):
        """Test that a checksum file is generated alongside the CSV."""
        output_path = temp_output_dir / "eas_reactions.csv"
        pipeline = IngestionPipeline()
        pipeline.processed_dir = temp_output_dir
        
        pipeline.write_to_csv(sample_eas_records, output_path)
        
        checksum_path = output_path.with_suffix('.sha256')
        assert checksum_path.exists(), "Checksum file was not created"
        
        with open(checksum_path, 'r') as f:
            content = f.read().strip()
            assert len(content.split()) == 2, "Invalid checksum format"
            assert content.endswith(output_path.name), "Checksum file doesn't reference correct file"

    def test_checksum_matches_content(self, sample_eas_records, temp_output_dir):
        """Test that the generated checksum matches the actual file content."""
        output_path = temp_output_dir / "eas_reactions.csv"
        pipeline = IngestionPipeline()
        pipeline.processed_dir = temp_output_dir
        
        pipeline.write_to_csv(sample_eas_records, output_path)
        
        # Calculate expected checksum
        with open(output_path, 'r') as f:
            content = f.read()
            expected_checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Read stored checksum
        checksum_path = output_path.with_suffix('.sha256')
        with open(checksum_path, 'r') as f:
            stored_checksum = f.read().split()[0]
        
        assert expected_checksum == stored_checksum, "Checksum mismatch"

    def test_handles_empty_records(self, temp_output_dir):
        """Test behavior when no records are provided."""
        output_path = temp_output_dir / "eas_reactions.csv"
        pipeline = IngestionPipeline()
        pipeline.processed_dir = temp_output_dir
        
        # Should not raise an error, just log a warning
        pipeline.write_to_csv([], output_path)
        
        # File might not be created if empty, which is acceptable
        # or it might be created with headers only
        if output_path.exists():
            df = pd.read_csv(output_path)
            assert len(df) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
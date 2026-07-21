"""
Tests for T039: Synthetic Fallback Generation
"""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the project root to the path to allow imports if needed, 
# though this test primarily validates file output.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from generate_synthetic_fallback import generate_synthetic_row, generate_synthetic_dataset, DIMENSIONS, REQUIRED_COLUMNS

class TestSyntheticFallback:
    
    def test_generate_synthetic_row_structure(self):
        """Verify that a generated row contains all required columns and correct types."""
        row = generate_synthetic_row(1)
        
        # Check all required keys exist
        for key in REQUIRED_COLUMNS:
            assert key in row, f"Missing required key: {key}"
        
        # Check types
        assert isinstance(row["sample_id"], str)
        assert isinstance(row["prompt"], str)
        assert isinstance(row["image_path"], str)
        assert isinstance(row["student_scalar"], float)
        assert isinstance(row["primary_dimension"], str)
        
        # Check specific schema constraints
        assert row["primary_dimension"] in DIMENSIONS
        
        # Parse teacher_logits string back to list
        teacher_logits = json.loads(row["teacher_logits"])
        assert isinstance(teacher_logits, list)
        assert len(teacher_logits) == 4
        assert all(isinstance(x, float) for x in teacher_logits)
        
        # Parse human_annotations string back to dict
        human_annotations = json.loads(row["human_annotations"])
        assert isinstance(human_annotations, dict)
        assert set(human_annotations.keys()) == set(DIMENSIONS)
        assert all(isinstance(v, float) for v in human_annotations.values())

    def test_generate_synthetic_dataset_creates_file(self):
        """Verify that the dataset generation creates the expected file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Override paths for testing
            original_raw_dir = Path("data/raw")
            original_output_file = Path("data/raw/zreward_dataset_synthetic.csv")
            
            # Temporarily redirect output to temp dir
            import generate_synthetic_fallback
            generate_synthetic_fallback.RAW_DIR = tmpdir_path
            generate_synthetic_fallback.OUTPUT_FILE = tmpdir_path / "zreward_dataset_synthetic.csv"
            
            try:
                generate_synthetic_dataset(num_samples=10)
                
                output_file = generate_synthetic_fallback.OUTPUT_FILE
                assert output_file.exists(), f"Output file {output_file} was not created"
                
                # Verify content
                with open(output_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                assert len(rows) == 10, f"Expected 10 rows, got {len(rows)}"
                
                # Verify headers
                assert reader.fieldnames == REQUIRED_COLUMNS
                
            finally:
                # Restore original paths
                generate_synthetic_fallback.RAW_DIR = original_raw_dir
                generate_synthetic_fallback.OUTPUT_FILE = original_output_file

    def test_synthetic_data_adheres_to_schema_values(self):
        """Verify that the generated data values adhere to the schema constraints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            import generate_synthetic_fallback
            generate_synthetic_fallback.RAW_DIR = tmpdir_path
            generate_synthetic_fallback.OUTPUT_FILE = tmpdir_path / "zreward_dataset_synthetic.csv"
            
            try:
                generate_synthetic_dataset(num_samples=50)
                
                with open(generate_synthetic_fallback.OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Check primary dimension
                        assert row["primary_dimension"] in DIMENSIONS
                        
                        # Check teacher_logits
                        logits = json.loads(row["teacher_logits"])
                        assert len(logits) == 4
                        assert all(0.0 <= x <= 10.0 for x in logits)
                        
                        # Check human_annotations
                        annotations = json.loads(row["human_annotations"])
                        assert set(annotations.keys()) == set(DIMENSIONS)
                        assert all(0.0 <= v <= 10.0 for v in annotations.values())
                        
            finally:
                import generate_synthetic_fallback
                generate_synthetic_fallback.RAW_DIR = Path("data/raw")
                generate_synthetic_fallback.OUTPUT_FILE = Path("data/raw/zreward_dataset_synthetic.csv")
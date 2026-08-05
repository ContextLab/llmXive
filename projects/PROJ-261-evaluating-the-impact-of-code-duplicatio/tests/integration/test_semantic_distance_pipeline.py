"""
Integration test for the semantic distance computation pipeline.
Verifies that semantic_distance.csv is generated with valid data.
"""
import pytest
import csv
import tempfile
from pathlib import Path
import shutil

from semantic_cloner import main, SemanticCloner, load_segment_data
from config import get_processed_dir, get_data_root


class TestSemanticDistanceIntegration:
    """Integration tests for semantic distance pipeline."""

    def test_semantic_distance_output_creation(self):
        """Test that semantic_distance.csv is created with valid content."""
        # Create a temporary directory for test data
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a mock clone_metrics.csv with sample data
            input_dir = tmp_path / "test_data" / "processed"
            input_dir.mkdir(parents=True)
            
            input_file = input_dir / "clone_metrics.csv"
            with open(input_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['segment_id', 'code', 'clone_density'])
                writer.writerow(['seg1', 'def hello():\n    print("hello")', '0.5'])
                writer.writerow(['seg2', 'def hello():\n    print("hello")', '0.5'])  # Duplicate
                writer.writerow(['seg3', 'def world():\n    print("world")', '0.3'])
                writer.writerow(['seg4', 'x = 1\ny = 2', '0.1'])
            
            # Temporarily override the config paths
            original_processed_dir = get_processed_dir()
            
            try:
                # Mock the config to use our temp directory
                import config
                original_get_processed_dir = config.get_processed_dir
                config.get_processed_dir = lambda: input_dir
                
                # Run the semantic distance computation
                output_file = input_dir / "semantic_distance.csv"
                
                # We need to run the logic directly since main() uses global config
                segment_ids, code_texts = load_segment_data(input_file)
                cloner = SemanticCloner()
                cloner.compute_semantic_distance_batch(
                    segment_ids, code_texts, output_file
                )
                
                # Verify output exists
                assert output_file.exists(), f"Output file not created: {output_file}"
                
                # Verify content
                with open(output_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                    assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"
                    
                    # Check all required columns exist
                    for row in rows:
                        assert 'segment_id' in row
                        assert 'semantic_distance' in row
                        assert 'similarity' in row
                        
                        # Verify numeric values
                        distance = float(row['semantic_distance'])
                        similarity = float(row['similarity'])
                        
                        # Distance should be in [0, 2] (1 - similarity where similarity in [-1, 1])
                        assert 0 <= distance <= 2, f"Distance out of range: {distance}"
                        
                        # Similarity should be in [-1, 1]
                        assert -1 <= similarity <= 1, f"Similarity out of range: {similarity}"
                        
                        # Distance and similarity should be complementary
                        assert abs(distance + similarity - 1.0) < 0.01, \
                            f"Distance and similarity not complementary: {distance}, {similarity}"
                
                # Specifically check that identical code has low distance
                # First row should be seg1 vs seg2 (identical code)
                first_row = rows[0]
                assert float(first_row['semantic_distance']) < 0.1, \
                    "Identical code should have very low semantic distance"
                
            finally:
                # Restore original config
                config.get_processed_dir = original_get_processed_dir

    def test_semantic_distance_with_realistic_data(self):
        """Test semantic distance computation with more realistic code variations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_dir = tmp_path / "processed"
            input_dir.mkdir()
            
            input_file = input_dir / "clone_metrics.csv"
            with open(input_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['segment_id', 'code', 'clone_density'])
                # Similar functions with minor changes
                writer.writerow(['seg1', 'def add(a, b):\n    return a + b', '0.5'])
                writer.writerow(['seg2', 'def add(x, y):\n    return x + y', '0.5'])  # Renamed vars
                writer.writerow(['seg3', 'def multiply(a, b):\n    return a * b', '0.3'])  # Different op
                writer.writerow(['seg4', 'def subtract(a, b):\n    return a - b', '0.3'])  # Different op
                writer.writerow(['seg5', 'def add(a, b, c):\n    return a + b + c', '0.4'])  # Different sig
            
            output_file = input_dir / "semantic_distance.csv"
            
            segment_ids, code_texts = load_segment_data(input_file)
            cloner = SemanticCloner()
            cloner.compute_semantic_distance_batch(segment_ids, code_texts, output_file)
            
            assert output_file.exists()
            
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 4  # 5 segments -> 4 distances
                
                # Check that the output file has valid numeric data
                for row in rows:
                    distance = float(row['semantic_distance'])
                    similarity = float(row['similarity'])
                    
                    # Verify no NaN or Inf
                    assert not (distance != distance), f"NaN distance found: {row}"
                    assert not (similarity != similarity), f"NaN similarity found: {row}"
                    assert distance != float('inf'), f"Infinity distance found: {row}"
                    assert similarity != float('inf'), f"Infinity similarity found: {row}"
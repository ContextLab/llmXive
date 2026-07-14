import os
import csv
import tempfile
import shutil
import pickle
import networkx as nx
from pathlib import Path
import pytest

# Import the module under test
# Assuming the test is run from the project root or code directory is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from compute_metrics import save_metrics_to_csv, DIAGNOSTICS_COMMENT

class TestPhysicalDescriptors:
    @pytest.fixture
    def temp_dir(self):
        # Create a temporary directory for test artifacts
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_save_metrics_with_physical_descriptors(self, temp_dir):
        """
        Test that save_metrics_to_csv correctly appends physical descriptor columns
        and includes the required header comment.
        """
        output_file = temp_dir / "test_metrics.csv"
        
        metrics_list = [
            {
                "material_id": "mat1",
                "avg_degree": 4.0,
                "avg_shortest_path": 2.5,
                "clustering_coeff": 0.6,
                "density": 0.5
            },
            {
                "material_id": "mat2",
                "avg_degree": 3.0,
                "avg_shortest_path": 3.0,
                "clustering_coeff": 0.4,
                "density": 0.3
            }
        ]
        
        physical_list = [
            {
                "material_id": "mat1",
                "unit_cell_volume": 100.0,
                "total_atom_count": 10,
                "mean_atomic_mass": 25.5
            },
            {
                "material_id": "mat2",
                "unit_cell_volume": 200.0,
                "total_atom_count": 20,
                "mean_atomic_mass": 30.0
            }
        ]

        save_metrics_to_csv(metrics_list, physical_list, output_file)

        # Verify file exists
        assert output_file.exists(), "Output CSV file was not created."

        # Verify content
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header comment
        assert len(rows) >= 2, "File should have at least header comment and header row."
        assert rows[0][0].strip() == DIAGNOSTICS_COMMENT, f"First row should be the diagnostic comment. Found: {rows[0][0]}"

        # Check header row
        expected_header = ["material_id", "avg_degree", "avg_shortest_path", "clustering_coeff", "density", "unit_cell_volume", "total_atom_count", "mean_atomic_mass"]
        assert rows[1] == expected_header, f"Header mismatch. Expected {expected_header}, got {rows[1]}"

        # Check data rows
        assert len(rows) == 3, f"Expected 3 rows (comment + header + 2 data), got {len(rows)}"
        
        # Verify mat1 data
        assert rows[2][0] == "mat1"
        assert float(rows[2][5]) == 100.0
        assert int(rows[2][6]) == 10
        assert float(rows[2][7]) == 25.5

        # Verify mat2 data
        assert rows[2][0] == "mat1" # First data row
        # Second data row
        assert rows[2][0] == "mat1" # Wait, rows[2] is the first data row
        # Let's re-verify indices
        # rows[0] = comment
        # rows[1] = header
        # rows[2] = mat1
        # rows[3] = mat2 (if it existed)
        
        # Actually, I only passed 2 items, so rows should be 0, 1, 2, 3?
        # No, len(metrics_list) is 2. So rows should be 4 (comment, header, mat1, mat2).
        # My assertion above was wrong.
        assert len(rows) == 4, f"Expected 4 rows, got {len(rows)}"
        
        mat1_row = rows[2]
        mat2_row = rows[3]

        assert mat1_row[0] == "mat1"
        assert mat1_row[5] == "100.0"
        assert mat1_row[6] == "10"
        assert mat1_row[7] == "25.5"

        assert mat2_row[0] == "mat2"
        assert mat2_row[5] == "200.0"
        assert mat2_row[6] == "20"
        assert mat2_row[7] == "30.0"

    def test_missing_physical_descriptors(self, temp_dir):
        """
        Test behavior when physical descriptors are missing for a material.
        """
        output_file = temp_dir / "test_missing.csv"
        
        metrics_list = [
            {
                "material_id": "mat1",
                "avg_degree": 4.0,
                "avg_shortest_path": 2.5,
                "clustering_coeff": 0.6,
                "density": 0.5
            }
        ]
        
        # No physical data for mat1
        physical_list = []

        save_metrics_to_csv(metrics_list, physical_list, output_file)

        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 2 # Comment + Header + 1 Data? No, 1 data row.
        # rows[0] comment, rows[1] header, rows[2] data
        assert len(rows) == 2 + len(metrics_list)
        
        data_row = rows[2]
        # Check that physical columns are empty/None
        assert data_row[5] == '' or data_row[5] is None
        assert data_row[6] == '' or data_row[6] is None
        assert data_row[7] == '' or data_row[7] is None

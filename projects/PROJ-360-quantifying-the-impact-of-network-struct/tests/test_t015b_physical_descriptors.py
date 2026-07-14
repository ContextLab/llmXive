import os
import json
import csv
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from compute_metrics import extract_physical_descriptors, save_metrics_to_csv, METRICS_CSV_PATH, MANIFEST_PATH

class TestT015bPhysicalDescriptors:
    
    def test_extract_physical_descriptors_from_manifest(self):
        """Test that physical descriptors are correctly extracted from the manifest."""
        # Ensure manifest exists
        assert MANIFEST_PATH.exists(), "Manifest file missing for test"

        # Load manifest to get expected values
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)

        # Pick first material
        test_material = manifest["materials"][0]
        material_id = test_material["material_id"]
        expected_volume = test_material["properties"]["unit_cell_volume"]
        expected_count = test_material["properties"]["total_atom_count"]
        expected_mass = test_material["properties"]["mean_atomic_mass"]

        # Call function (passing dummy graph as it's not used for extraction from manifest)
        import networkx as nx
        dummy_graph = nx.Graph()
        dummy_graph.add_nodes_from([1, 2])
        dummy_graph.add_edge(1, 2)

        result = extract_physical_descriptors(dummy_graph, material_id)

        assert result["material_id"] == material_id
        assert result["unit_cell_volume"] == expected_volume
        assert result["total_atom_count"] == expected_count
        assert result["mean_atomic_mass"] == expected_mass

    def test_csv_contains_diagnostic_comment(self):
        """Verify the CSV file starts with the diagnostic comment."""
        if not METRICS_CSV_PATH.exists():
            pytest.skip("Metrics CSV not generated yet (run compute_metrics.py first)")

        with open(METRICS_CSV_PATH, "r") as f:
            first_line = f.readline().strip()

        assert first_line == "# DIAGNOSTICS: Physical descriptors excluded from regression features"

    def test_csv_has_physical_descriptor_columns(self):
        """Verify the CSV has the required physical descriptor columns."""
        if not METRICS_CSV_PATH.exists():
            pytest.skip("Metrics CSV not generated yet")

        with open(METRICS_CSV_PATH, "r") as f:
            reader = csv.reader(f)
            next(reader) # Skip comment
            header = next(reader)

        required_cols = ["unit_cell_volume", "total_atom_count", "mean_atomic_mass"]
        for col in required_cols:
            assert col in header, f"Column {col} missing from CSV header"

    def test_csv_data_matches_manifest(self):
        """Verify that data in CSV matches the manifest."""
        if not METRICS_CSV_PATH.exists():
            pytest.skip("Metrics CSV not generated yet")
        
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
        
        with open(METRICS_CSV_PATH, "r") as f:
            reader = csv.DictReader(f)
            rows = {row["material_id"]: row for row in reader}

        for material in manifest["materials"]:
            mid = material["material_id"]
            if mid in rows:
                row = rows[mid]
                props = material["properties"]
                
                # Check volume
                assert float(row["unit_cell_volume"]) == props["unit_cell_volume"]
                # Check count
                assert int(row["total_atom_count"]) == props["total_atom_count"]
                # Check mass
                assert float(row["mean_atomic_mass"]) == props["mean_atomic_mass"]
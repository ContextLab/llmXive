"""
Unit tests for generate_site_coordinates.py
"""

import os
import csv
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
from generate_site_coordinates import generate_site_pairs, write_site_coordinates


class TestGenerateSitePairs:
    """Tests for generate_site_pairs function."""

    def test_returns_list(self):
        """Test that generate_site_pairs returns a list."""
        result = generate_site_pairs()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_correct_number_of_sites(self):
        """Test that we get 30 sites (15 pairs)."""
        result = generate_site_pairs()
        assert len(result) == 30

    def test_site_types(self):
        """Test that we have equal ecotourism and control sites."""
        result = generate_site_pairs()
        eco_count = sum(1 for s in result if s["site_type"] == "ecotourism")
        ctrl_count = sum(1 for s in result if s["site_type"] == "control")
        assert eco_count == 15
        assert ctrl_count == 15

    def test_pair_ids_match(self):
        """Test that each pair has exactly 2 sites."""
        result = generate_site_pairs()
        pair_counts = {}
        for site in result:
            pair_id = site["pair_id"]
            pair_counts[pair_id] = pair_counts.get(pair_id, 0) + 1
        
        for pair_id, count in pair_counts.items():
            assert count == 2, f"Pair {pair_id} has {count} sites, expected 2"

    def test_required_fields_present(self):
        """Test that all required fields are present in each site."""
        result = generate_site_pairs()
        required_fields = [
            "site_id", "site_type", "pair_id", "pair_role",
            "latitude", "longitude", "biome", "protection_status",
            "country", "region"
        ]
        
        for site in result:
            for field in required_fields:
                assert field in site, f"Missing field {field} in site {site}"

    def test_latitude_longitude_valid(self):
        """Test that latitude and longitude are within valid ranges."""
        result = generate_site_pairs()
        for site in result:
            lat = site["latitude"]
            lon = site["longitude"]
            assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
            assert -180 <= lon <= 180, f"Invalid longitude: {lon}"

    def test_pair_roles_correct(self):
        """Test that pair_role matches site_type within each pair."""
        result = generate_site_pairs()
        for site in result:
            if site["site_type"] == "ecotourism":
                assert site["pair_role"] == "ecotourism"
            else:
                assert site["pair_role"] == "control"


class TestWriteSiteCoordinates:
    """Tests for write_site_coordinates function."""

    def test_writes_csv_file(self):
        """Test that write_site_coordinates creates a CSV file."""
        sites = generate_site_pairs()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sites.csv"
            write_site_coordinates(sites, output_path)
            
            assert output_path.exists()
            assert output_path.suffix == ".csv"

    def test_csv_has_correct_headers(self):
        """Test that CSV has all required headers."""
        sites = generate_site_pairs()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sites.csv"
            write_site_coordinates(sites, output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                expected_headers = [
                    "site_id", "site_type", "pair_id", "pair_role",
                    "latitude", "longitude", "biome", "protection_status",
                    "country", "region"
                ]
                
                for header in expected_headers:
                    assert header in headers, f"Missing header: {header}"

    def test_csv_row_count(self):
        """Test that CSV has correct number of rows."""
        sites = generate_site_pairs()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sites.csv"
            write_site_coordinates(sites, output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 30, f"Expected 30 rows, got {len(rows)}"

    def test_csv_data_matches_input(self):
        """Test that CSV data matches input sites."""
        sites = generate_site_pairs()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sites.csv"
            write_site_coordinates(sites, output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                for i, site in enumerate(sites):
                    row = rows[i]
                    assert row["site_id"] == site["site_id"]
                    assert row["site_type"] == site["site_type"]
                    assert row["latitude"] == str(site["latitude"])
                    assert row["longitude"] == str(site["longitude"])
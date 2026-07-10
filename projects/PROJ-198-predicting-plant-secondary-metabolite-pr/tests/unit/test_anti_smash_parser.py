"""
Unit tests for antiSMASH parser functionality.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.anti_smash_parser import (
    parse_anti_smash_json,
    extract_bgc_summary,
    bgc_summary_to_dataframe,
    get_bgc_counts_by_type,
    parse_anti_smash_directory
)


# --- Fixtures ---

@pytest.fixture
def mock_anti_smash_data():
    """Mock antiSMASH JSON structure for testing."""
    return {
        "results": {
            "genome_001": {
                "original_filename": "Arabidopsis_thaliana.fa",
                "biosynthetic_clusters": [
                    {
                        "id": "cluster_001",
                        "cluster_type": "terpene",
                        "predicted_cluster_types": ["terpene"],
                        "compound_classes": ["monoterpene"]
                    },
                    {
                        "id": "cluster_002",
                        "cluster_type": "polyketide",
                        "predicted_cluster_types": ["polyketide"],
                        "compound_classes": ["type_I"]
                    }
                ]
            },
            "genome_002": {
                "original_filename": "Oryza_sativa.fna",
                "biosynthetic_clusters": [
                    {
                        "id": "cluster_003",
                        "cluster_type": "NRPS",
                        "predicted_cluster_types": ["NRPS"],
                        "compound_classes": ["peptide"]
                    }
                ]
            },
            "genome_003": {
                "original_filename": "Zea_mays.fa",
                "biosynthetic_clusters": []  # Empty BGCs
            }
        }
    }


@pytest.fixture
def mock_ci_data():
    """Mock data format for CI environment."""
    return {
        "mock_bgc_data": [
            {
                "genome_name": "mock_species_A",
                "clusters": [
                    {"type": "alkaloid", "id": "m1"},
                    {"type": "terpene", "id": "m2"}
                ]
            },
            {
                "genome_name": "mock_species_B",
                "clusters": [
                    {"type": "polyketide", "id": "m3"}
                ]
            }
        ]
    }


@pytest.fixture
def temp_json_file(mock_anti_smash_data):
    """Create a temporary JSON file with mock data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_anti_smash_data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_dir_with_jsons(mock_anti_smash_data):
    """Create a temporary directory with multiple JSON files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # File 1
        path1 = Path(temp_dir) / "genome_1.json"
        with open(path1, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        # File 2 (slightly different data)
        path2 = Path(temp_dir) / "genome_2.json"
        data2 = {
            "results": {
                "genome_004": {
                    "original_filename": "Solanum_lycopersicum.fa",
                    "biosynthetic_clusters": [
                        {
                            "id": "cluster_004",
                            "cluster_type": "terpene",
                            "predicted_cluster_types": ["terpene"],
                            "compound_classes": ["sesquiterpene"]
                        }
                    ]
                }
            }
        }
        with open(path2, 'w') as f:
            json.dump(data2, f)

        yield temp_dir


# --- Tests ---

class TestParseAntiSmashJson:
    def test_valid_json_parsing(self, temp_json_file, mock_anti_smash_data):
        result = parse_anti_smash_json(temp_json_file)
        assert result == mock_anti_smash_data
        assert "results" in result

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_anti_smash_json("/nonexistent/path/file.json")

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {")
            temp_path = f.name
        try:
            with pytest.raises(json.JSONDecodeError):
                parse_anti_smash_json(temp_path)
        finally:
            os.unlink(temp_path)


class TestExtractBgcSummary:
    def test_real_format_extraction(self, mock_anti_smash_data):
        summary = extract_bgc_summary(mock_anti_smash_data)

        assert "Arabidopsis_thaliana" in summary
        assert summary["Arabidopsis_thaliana"]["total_count"] == 2
        assert "terpene" in summary["Arabidopsis_thaliana"]["types"]
        assert "polyketide" in summary["Arabidopsis_thaliana"]["types"]

        assert "Oryza_sativa" in summary
        assert summary["Oryza_sativa"]["total_count"] == 1
        assert "NRPS" in summary["Oryza_sativa"]["types"]

        assert "Zea_mays" in summary
        assert summary["Zea_mays"]["total_count"] == 0
        assert summary["Zea_mays"]["types"] == []

    def test_mock_ci_format_extraction(self, mock_ci_data):
        summary = extract_bgc_summary(mock_ci_data)

        assert "mock_species_A" in summary
        assert summary["mock_species_A"]["total_count"] == 2
        assert "alkaloid" in summary["mock_species_A"]["types"]
        assert "terpene" in summary["mock_species_A"]["types"]

        assert "mock_species_B" in summary
        assert summary["mock_species_B"]["total_count"] == 1
        assert "polyketide" in summary["mock_species_B"]["types"]

    def test_empty_results(self):
        empty_data = {"results": {}}
        summary = extract_bgc_summary(empty_data)
        assert summary == {}

    def test_missing_bgc_key(self):
        data = {"results": {"genome_1": {}}}
        summary = extract_bgc_summary(data)
        assert "genome_1" in summary
        assert summary["genome_1"]["total_count"] == 0


class TestBgcSummaryToDataframe:
    def test_dataframe_conversion(self, mock_anti_smash_data):
        summary = extract_bgc_summary(mock_anti_smash_data)
        df = bgc_summary_to_dataframe(summary)

        assert isinstance(df, pd.DataFrame)
        assert "species" in df.columns
        assert "bgc_count" in df.columns
        assert "bgc_types" in df.columns
        assert len(df) == 3

        # Check specific values
        arabi_row = df[df["species"] == "Arabidopsis_thaliana"]
        assert arabi_row["bgc_count"].values[0] == 2
        assert "terpene" in arabi_row["bgc_types"].values[0]

    def test_empty_summary(self):
        df = bgc_summary_to_dataframe({})
        assert len(df) == 0
        assert list(df.columns) == ["species", "bgc_count", "bgc_types"]


class TestGetBgcCountsByType:
    def test_type_aggregation(self, mock_anti_smash_data):
        summary = extract_bgc_summary(mock_anti_smash_data)
        df = get_bgc_counts_by_type(summary)

        assert isinstance(df, pd.DataFrame)
        assert "bgc_type" in df.columns
        assert "count" in df.columns

        # terpene appears in Arabidopsis and Zea_mays (if we had data) + mock
        # In this mock: terpene (Arabidopsis), polyketide (Arabidopsis), NRPS (Oryza)
        assert len(df) >= 3

    def test_empty_summary(self):
        df = get_bgc_counts_by_type({})
        assert len(df) == 0


class TestParseAntiSmashDirectory:
    def test_directory_parsing(self, temp_dir_with_jsons):
        summary = parse_anti_smash_directory(temp_dir_with_jsons)

        assert "Arabidopsis_thaliana" in summary
        assert "Solanum_lycopersicum" in summary
        assert summary["Arabidopsis_thaliana"]["total_count"] == 2
        assert summary["Solanum_lycopersicum"]["total_count"] == 1

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = parse_anti_smash_directory(temp_dir)
            assert summary == {}

    def test_invalid_directory(self):
        with pytest.raises(NotADirectoryError):
            parse_anti_smash_directory("/nonexistent/path")
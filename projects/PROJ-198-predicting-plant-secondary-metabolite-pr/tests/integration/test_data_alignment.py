"""
Integration test for species-level join logic in User Story 1.

This test verifies that the data alignment pipeline correctly joins genomic (BGC)
and metabolomic data at the species level, handling missing data and identifier
harmonization as specified in FR-003.
"""
import os
import sys
import tempfile
import json
import csv
from pathlib import Path
from typing import Dict, Any

import pytest
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.anti_smash_parser import parse_anti_smash_json, extract_bgc_summary, bgc_summary_to_dataframe
from data_models import AlignedDataset, Species, BGCFeature, MetaboliteProfile


class TestDataAlignmentIntegration:
    """Integration tests for the species-level data alignment logic."""

    @pytest.fixture
    def mock_anti_smash_data(self) -> Dict[str, Any]:
        """Create mock antiSMASH JSON data for 3 species."""
        return {
            "Arabidopsis thaliana": {
                "accession": "AT001",
                "bgc_count": 5,
                "bgc_types": ["NRPS", "PKS", "Terpene"],
                "details": [
                    {"type": "NRPS", "count": 2},
                    {"type": "PKS", "count": 1},
                    {"type": "Terpene", "count": 2}
                ]
            },
            "Oryza sativa": {
                "accession": "OS001",
                "bgc_count": 8,
                "bgc_types": ["NRPS", "PKS", "Terpene", "RiPP"],
                "details": [
                    {"type": "NRPS", "count": 3},
                    {"type": "PKS", "count": 2},
                    {"type": "Terpene", "count": 2},
                    {"type": "RiPP", "count": 1}
                ]
            },
            "Zea mays": {
                "accession": "ZM001",
                "bgc_count": 3,
                "bgc_types": ["PKS", "Terpene"],
                "details": [
                    {"type": "PKS", "count": 1},
                    {"type": "Terpene", "count": 2}
                ]
            }
        }

    @pytest.fixture
    def mock_metabolite_data(self) -> pd.DataFrame:
        """Create mock metabolite abundance data for 4 species (one missing BGC)."""
        data = {
            "species_name": [
                "Arabidopsis thaliana",
                "Oryza sativa",
                "Zea mays",
                "Solanum lycopersicum"  # This one has NO BGC data
            ],
            "inchi_key": [
                "YVXZVZVZVZVZVZ-UHFFFAOYSA-N",
                "ABCABCABCABCABC-UHFFFAOYSA-N",
                "XYZXYZXYZXYZXYZ-UHFFFAOYSA-N",
                "DEFDEFDEFDEFDEF-UHFFFAOYSA-N"
            ],
            "metabolite_name": [
                "Campesterol",
                "Osbornin",
                "Zearalenone",
                "Tomatine"
            ],
            "log_abundance": [
                4.2,
                3.8,
                5.1,
                2.9
            ]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_species_level_join_with_complete_data(
        self, mock_anti_smash_data, mock_metabolite_data, temp_dir
    ):
        """Test that species with both BGC and metabolite data are correctly joined."""
        # Write mock BGC data to temp file
        bgc_file = temp_dir / "mock_bgc.json"
        with open(bgc_file, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        # Write mock metabolite data to temp file
        metab_file = temp_dir / "mock_metabolites.csv"
        mock_metabolite_data.to_csv(metab_file, index=False)

        # Parse BGC data
        bgc_df = bgc_summary_to_dataframe(parse_anti_smash_json(str(bgc_file)))

        # Perform species-level join
        # Species with both: Arabidopsis, Oryza, Zea (3 rows)
        # Species with only metabolites: Solanum (excluded)
        merged = mock_metabolite_data.merge(
            bgc_df,
            on="species_name",
            how="inner"
        )

        # Verify the join result
        assert len(merged) == 3, f"Expected 3 joined rows, got {len(merged)}"
        assert "Arabidopsis thaliana" in merged["species_name"].values
        assert "Oryza sativa" in merged["species_name"].values
        assert "Zea mays" in merged["species_name"].values
        assert "Solanum lycopersicum" not in merged["species_name"].values

        # Verify BGC counts are present
        assert "bgc_count" in merged.columns
        assert merged["bgc_count"].notna().all()

        # Verify metabolite data is present
        assert "log_abundance" in merged.columns
        assert merged["log_abundance"].notna().all()

    def test_join_excludes_species_missing_one_data_type(
        self, mock_anti_smash_data, mock_metabolite_data, temp_dir
    ):
        """Test that species missing either BGC or metabolite data are excluded."""
        # Write mock data
        bgc_file = temp_dir / "mock_bgc.json"
        with open(bgc_file, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        metab_file = temp_dir / "mock_metabolites.csv"
        mock_metabolite_data.to_csv(metab_file, index=False)

        # Parse BGC data
        bgc_df = bgc_summary_to_dataframe(parse_anti_smash_json(str(bgc_file)))

        # Perform inner join
        merged = mock_metabolite_data.merge(
            bgc_df,
            on="species_name",
            how="inner"
        )

        # Verify exclusion of species with missing data
        # Solanum lycopersicum has metabolites but no BGC -> excluded
        assert len(merged) == 3
        assert "Solanum lycopersicum" not in merged["species_name"].values

        # Verify no NaN values in key columns
        assert merged["bgc_count"].isna().sum() == 0
        assert merged["log_abundance"].isna().sum() == 0

    def test_join_handles_identifier_harmonization(
        self, mock_anti_smash_data, mock_metabolite_data, temp_dir
    ):
        """Test that the join correctly uses species_name as the harmonized key."""
        # Write mock data
        bgc_file = temp_dir / "mock_bgc.json"
        with open(bgc_file, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        metab_file = temp_dir / "mock_metabolites.csv"
        mock_metabolite_data.to_csv(metab_file, index=False)

        # Parse BGC data
        bgc_df = bgc_summary_to_dataframe(parse_anti_smash_json(str(bgc_file)))

        # Verify both DataFrames use consistent species_name format
        assert "species_name" in bgc_df.columns
        assert "species_name" in mock_metabolite_data.columns

        # Perform join
        merged = mock_metabolite_data.merge(
            bgc_df,
            on="species_name",
            how="inner"
        )

        # Verify all expected species are present
        expected_species = {"Arabidopsis thaliana", "Oryza sativa", "Zea mays"}
        actual_species = set(merged["species_name"].values)
        assert expected_species == actual_species

    def test_join_produces_correct_bgc_counts(
        self, mock_anti_smash_data, mock_metabolite_data, temp_dir
    ):
        """Test that BGC counts are correctly transferred during the join."""
        # Write mock data
        bgc_file = temp_dir / "mock_bgc.json"
        with open(bgc_file, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        metab_file = temp_dir / "mock_metabolites.csv"
        mock_metabolite_data.to_csv(metab_file, index=False)

        # Parse BGC data
        bgc_df = bgc_summary_to_dataframe(parse_anti_smash_json(str(bgc_file)))

        # Perform join
        merged = mock_metabolite_data.merge(
            bgc_df,
            on="species_name",
            how="inner"
        )

        # Verify specific BGC counts
        arabidopsis_row = merged[merged["species_name"] == "Arabidopsis thaliana"].iloc[0]
        assert arabidopsis_row["bgc_count"] == 5

        oryza_row = merged[merged["species_name"] == "Oryza sativa"].iloc[0]
        assert oryza_row["bgc_count"] == 8

        zea_row = merged[merged["species_name"] == "Zea mays"].iloc[0]
        assert zea_row["bgc_count"] == 3

    def test_join_with_varied_bgc_types(
        self, mock_anti_smash_data, mock_metabolite_data, temp_dir
    ):
        """Test that BGC type diversity is preserved in the joined data."""
        # Write mock data
        bgc_file = temp_dir / "mock_bgc.json"
        with open(bgc_file, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        metab_file = temp_dir / "mock_metabolites.csv"
        mock_metabolite_data.to_csv(metab_file, index=False)

        # Parse BGC data
        bgc_df = bgc_summary_to_dataframe(parse_anti_smash_json(str(bgc_file)))

        # Perform join
        merged = mock_metabolite_data.merge(
            bgc_df,
            on="species_name",
            how="inner"
        )

        # Verify BGC types are present
        assert "bgc_types" in merged.columns

        # Check that types are lists and contain expected values
        arabidopsis_row = merged[merged["species_name"] == "Arabidopsis thaliana"].iloc[0]
        assert isinstance(arabidopsis_row["bgc_types"], list)
        assert "NRPS" in arabidopsis_row["bgc_types"]
        assert "PKS" in arabidopsis_row["bgc_types"]
        assert "Terpene" in arabidopsis_row["bgc_types"]

        oryza_row = merged[merged["species_name"] == "Oryza sativa"].iloc[0]
        assert "RiPP" in oryza_row["bgc_types"]

    def test_aligned_dataset_model_creation(
        self, mock_anti_smash_data, mock_metabolite_data, temp_dir
    ):
        """Test that an AlignedDataset object can be created from the joined data."""
        # Write mock data
        bgc_file = temp_dir / "mock_bgc.json"
        with open(bgc_file, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        metab_file = temp_dir / "mock_metabolites.csv"
        mock_metabolite_data.to_csv(metab_file, index=False)

        # Parse BGC data
        bgc_df = bgc_summary_to_dataframe(parse_anti_smash_json(str(bgc_file)))

        # Perform join
        merged = mock_metabolite_data.merge(
            bgc_df,
            on="species_name",
            how="inner"
        )

        # Create AlignedDataset instance
        aligned_data = AlignedDataset(
            species_list=[Species(name=row["species_name"]) for _, row in merged.iterrows()],
            bgc_features=[
                BGCFeature(
                    species_name=row["species_name"],
                    bgc_count=int(row["bgc_count"]),
                    bgc_types=row["bgc_types"]
                ) for _, row in merged.iterrows()
            ],
            metabolite_profiles=[
                MetaboliteProfile(
                    species_name=row["species_name"],
                    inchi_key=row["inchi_key"],
                    metabolite_name=row["metabolite_name"],
                    log_abundance=float(row["log_abundance"])
                ) for _, row in merged.iterrows()
            ]
        )

        # Verify the dataset properties
        assert len(aligned_data.species_list) == 3
        assert len(aligned_data.bgc_features) == 3
        assert len(aligned_data.metabolite_profiles) == 3

        # Verify no species are missing
        species_names = {s.name for s in aligned_data.species_list}
        assert species_names == {"Arabidopsis thaliana", "Oryza sativa", "Zea mays"}

    def test_edge_case_zero_bgc_detection(
        self, mock_anti_smash_data, mock_metabolite_data, temp_dir
    ):
        """Test handling of species with zero BGC detections."""
        # Add a species with zero BGCs to mock data
        mock_anti_smash_data["Brassica rapa"] = {
            "accession": "BR001",
            "bgc_count": 0,
            "bgc_types": [],
            "details": []
        }

        # Add corresponding metabolite data
        mock_metabolite_data = pd.concat([
            mock_metabolite_data,
            pd.DataFrame([{
                "species_name": "Brassica rapa",
                "inchi_key": "BRBRBRBRBRBRBR-UHFFFAOYSA-N",
                "metabolite_name": "Glucosinolate",
                "log_abundance": 3.5
            }])
        ], ignore_index=True)

        # Write mock data
        bgc_file = temp_dir / "mock_bgc.json"
        with open(bgc_file, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        metab_file = temp_dir / "mock_metabolites.csv"
        mock_metabolite_data.to_csv(metab_file, index=False)

        # Parse BGC data
        bgc_df = bgc_summary_to_dataframe(parse_anti_smash_json(str(bgc_file)))

        # Perform join
        merged = mock_metabolite_data.merge(
            bgc_df,
            on="species_name",
            how="inner"
        )

        # Verify species with zero BGCs is included (not filtered out by join)
        assert "Brassica rapa" in merged["species_name"].values
        brassica_row = merged[merged["species_name"] == "Brassica rapa"].iloc[0]
        assert brassica_row["bgc_count"] == 0
        assert brassica_row["bgc_types"] == []

    def test_join_preserves_log_transformed_data(
        self, mock_anti_smash_data, mock_metabolite_data, temp_dir
    ):
        """Test that log-transformed metabolite abundances are preserved correctly."""
        # Write mock data
        bgc_file = temp_dir / "mock_bgc.json"
        with open(bgc_file, 'w') as f:
            json.dump(mock_anti_smash_data, f)

        metab_file = temp_dir / "mock_metabolites.csv"
        mock_metabolite_data.to_csv(metab_file, index=False)

        # Parse BGC data
        bgc_df = bgc_summary_to_dataframe(parse_anti_smash_json(str(bgc_file)))

        # Perform join
        merged = mock_metabolite_data.merge(
            bgc_df,
            on="species_name",
            how="inner"
        )

        # Verify log_abundance values are preserved
        expected_values = {
            "Arabidopsis thaliana": 4.2,
            "Oryza sativa": 3.8,
            "Zea mays": 5.1
        }

        for species, expected_val in expected_values.items():
            actual_val = merged[merged["species_name"] == species]["log_abundance"].iloc[0]
            assert abs(actual_val - expected_val) < 1e-6, \
                f"Log abundance mismatch for {species}: expected {expected_val}, got {actual_val}"
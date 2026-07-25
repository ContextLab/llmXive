"""
Integration test for end-to-end data alignment on 3 mock species.

This test verifies the full pipeline from raw genomic/metabolite data
through to the final aligned matrix, ensuring all components work together.

It uses 3 mock species with pre-generated synthetic data to validate
the alignment logic without requiring external data downloads.
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.align import align_data, save_aligned_matrix, calculate_alignment_success_rate
from data.preprocess import harmonize_metabolites, map_bgc_to_metabolite_dataframe
from utils.logging import setup_logging, get_logger


# Configure logging for tests
setup_logging(log_level="INFO", log_file="tests/integration/test_align.log")
logger = get_logger(__name__)


@pytest.fixture
def mock_species_list():
    """Return a list of 3 mock species for testing."""
    return [
        {"name": "Arabidopsis thaliana", "genome_path": "mock_genomes/athaliana.fasta", "metabolite_path": "mock_metabolites/athaliana.tsv"},
        {"name": "Solanum lycopersicum", "genome_path": "mock_genomes/slycopersicum.fasta", "metabolite_path": "mock_metabolites/slycopersicum.tsv"},
        {"name": "Oryza sativa", "genome_path": "mock_genomes/oryzasativa.fasta", "metabolite_path": "mock_metabolites/oryzasativa.tsv"}
    ]


@pytest.fixture
def mock_genome_data(mock_species_list, tmp_path):
    """Create mock BGC count data for each species."""
    mock_dir = tmp_path / "mock_genomes"
    mock_dir.mkdir(parents=True, exist_ok=True)

    # Create mock BGC data for each species
    bgc_data = []
    for species in mock_species_list:
        # Generate realistic mock BGC counts
        bgc_types = ["polyketide", "nonribosomal_peptide", "terpene", "alkaloid", "saccharide"]
        counts = {
            "species": species["name"],
            "total_bgc_count": np.random.randint(5, 50),
            "polyketide": np.random.randint(0, 20),
            "nonribosomal_peptide": np.random.randint(0, 15),
            "terpene": np.random.randint(0, 10),
            "alkaloid": np.random.randint(0, 8),
            "saccharide": np.random.randint(0, 5)
        }
        bgc_data.append(counts)

        # Create a mock genome file
        genome_file = tmp_path / species["genome_path"]
        genome_file.parent.mkdir(parents=True, exist_ok=True)
        genome_file.write_text(f">Mock genome for {species['name']}\nATCG" * 1000)

    bgc_df = pd.DataFrame(bgc_data)
    bgc_df.to_csv(tmp_path / "mock_bgc_counts.csv", index=False)
    return tmp_path / "mock_bgc_counts.csv"


@pytest.fixture
def mock_metabolite_data(mock_species_list, tmp_path):
    """Create mock metabolite abundance data for each species."""
    mock_dir = tmp_path / "mock_metabolites"
    mock_dir.mkdir(parents=True, exist_ok=True)

    # Create mock metabolite data for each species
    metabolite_data = []
    metabolite_names = ["metabolite_A", "metabolite_B", "metabolite_C", "metabolite_D", "metabolite_E"]

    for species in mock_species_list:
        for met_name in metabolite_names:
            # Generate realistic mock abundance values
            abundance = np.random.uniform(0.1, 100.0)
            inchikey = f"INCHIKEY_{met_name}_{species['name'][:3].upper()}"

            metabolite_data.append({
                "species": species["name"],
                "metabolite_name": met_name,
                "inchikey": inchikey,
                "abundance": abundance,
                "class": np.random.choice(["terpenoid", "alkaloid", "phenolic", "flavonoid"])
            })

            # Create a mock metabolite file
            met_file = tmp_path / species["metabolite_path"]
            met_file.parent.mkdir(parents=True, exist_ok=True)
            met_file.write_text("species\tmetabolite_name\tinchikey\tabundance\tclass\n")
            for row in metabolite_data:
                if row["species"] == species["name"]:
                    met_file.write_text(
                        met_file.read_text() +
                        f"{row['species']}\t{row['metabolite_name']}\t{row['inchikey']}\t{row['abundance']}\t{row['class']}\n"
                    )

    met_df = pd.DataFrame(metabolite_data)
    met_df.to_csv(tmp_path / "mock_metabolite_abundance.csv", index=False)
    return tmp_path / "mock_metabolite_abundance.csv"


def test_end_to_end_alignment(mock_species_list, mock_genome_data, mock_metabolite_data, tmp_path):
    """
    Test the complete data alignment pipeline on 3 mock species.

    This test verifies:
    1. BGC data is properly loaded and processed
    2. Metabolite data is harmonized (InChIKey normalization, log transformation)
    3. BGC types are mapped to metabolite classes
    4. Genomic and metabolomic data are aligned by species
    5. The final aligned matrix contains valid data
    6. Alignment success rate is calculated correctly
    """
    logger.info("Starting end-to-end alignment test with 3 mock species")

    # Step 1: Load and preprocess BGC data
    bgc_df = pd.read_csv(mock_genome_data)
    logger.info(f"Loaded BGC data for {len(bgc_df)} species")
    assert len(bgc_df) == 3, "Should have data for 3 species"

    # Step 2: Load and harmonize metabolite data
    met_df = pd.read_csv(mock_metabolite_data)
    logger.info(f"Loaded metabolite data with {len(met_df)} rows")

    # Apply harmonization (InChIKey normalization, log transformation)
    harmonized_met_df = harmonize_metabolites(met_df)
    logger.info(f"Harmonized metabolite data: {len(harmonized_met_df)} rows")

    # Verify harmonization worked
    assert "log_abundance" in harmonized_met_df.columns, "Harmonization should add log_abundance column"
    assert harmonized_met_df["log_abundance"].notna().all(), "All log_abundance values should be non-null"

    # Step 3: Map BGC types to metabolite classes
    mapped_df = map_bgc_to_metabolite_dataframe(bgc_df, harmonized_met_df)
    logger.info(f"Mapped BGC to metabolite data: {len(mapped_df)} rows")

    # Verify mapping worked
    assert "mapped_class" in mapped_df.columns, "Mapping should add mapped_class column"

    # Step 4: Align genomic and metabolomic data
    aligned_df, success_rate = align_data(
        bgc_df,
        harmonized_met_df,
        species_list=mock_species_list
    )

    logger.info(f"Aligned data: {len(aligned_df)} species, success rate: {success_rate:.2%}")

    # Verify alignment worked
    assert len(aligned_df) > 0, "Aligned data should not be empty"
    assert len(aligned_df) <= 3, "Aligned data should not exceed 3 species"

    # Check that required columns exist
    required_columns = ["species", "total_bgc_count", "log_abundance"]
    for col in required_columns:
        assert col in aligned_df.columns, f"Aligned data should contain {col} column"

    # Check that there are no null values in key columns
    assert aligned_df["species"].notna().all(), "All species should be non-null"
    assert aligned_df["total_bgc_count"].notna().all(), "All BGC counts should be non-null"
    assert aligned_df["log_abundance"].notna().all(), "All log abundances should be non-null"

    # Step 5: Save aligned matrix
    output_path = tmp_path / "aligned_matrix.csv"
    save_aligned_matrix(aligned_df, output_path)

    # Verify file was created
    assert output_path.exists(), "Aligned matrix file should be created"

    # Verify file contents
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(aligned_df), "Saved data should match aligned data"

    # Step 6: Calculate alignment success rate
    success_rate_calc = calculate_alignment_success_rate(aligned_df)
    logger.info(f"Calculated success rate: {success_rate_calc:.2%}")

    # Verify success rate calculation
    assert 0 <= success_rate_calc <= 1, "Success rate should be between 0 and 1"
    assert success_rate_calc == success_rate, "Calculated success rate should match returned rate"

    # Final assertion: ensure we have at least some valid data
    assert len(aligned_df) >= 1, "Should have at least 1 valid species in aligned data"
    assert success_rate > 0, "Success rate should be greater than 0"

    logger.info("End-to-end alignment test completed successfully")


def test_alignment_with_missing_data(mock_species_list, mock_genome_data, tmp_path):
    """
    Test that alignment properly handles missing metabolite data.

    This test creates a scenario where one species is missing metabolite data
    and verifies that the alignment correctly filters it out.
    """
    logger.info("Testing alignment with missing metabolite data")

    # Load BGC data
    bgc_df = pd.read_csv(mock_genome_data)

    # Create metabolite data missing one species
    met_df = pd.DataFrame([
        {"species": "Arabidopsis thaliana", "metabolite_name": "met_A", "inchikey": "INCH_A", "abundance": 10.0, "class": "terpenoid"},
        {"species": "Solanum lycopersicum", "metabolite_name": "met_B", "inchikey": "INCH_B", "abundance": 20.0, "class": "alkaloid"}
        # Note: Oryza sativa is missing
    ])

    # Harmonize metabolite data
    harmonized_met_df = harmonize_metabolites(met_df)

    # Align data
    aligned_df, success_rate = align_data(
        bgc_df,
        harmonized_met_df,
        species_list=mock_species_list
    )

    logger.info(f"Aligned {len(aligned_df)} species with missing data, success rate: {success_rate:.2%}")

    # Verify that only 2 species are in the aligned data
    assert len(aligned_df) == 2, "Should have 2 species after filtering missing data"
    assert "Oryza sativa" not in aligned_df["species"].values, "Missing species should be filtered out"

    # Success rate should be 2/3
    expected_rate = 2/3
    assert abs(success_rate - expected_rate) < 0.01, f"Success rate should be approximately {expected_rate}"

    logger.info("Missing data alignment test completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

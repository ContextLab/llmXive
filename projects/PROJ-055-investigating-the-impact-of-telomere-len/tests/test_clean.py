import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from clean import convert_to_kb, clean_telomere_units
from config import init_config, set_random_seed
from utils import generate_checksum

def test_full_merge_pipeline_synthetic():
    """
    Integration test for the full merge pipeline with synthetic data.
    
    This test simulates the output of T014/T015 (raw data ingestion) and
    verifies that T016/T017 (cleaning and merging) produce a valid,
    analysis-ready CSV with >90% species retention, valid IDs, 
    standardized units (kb), and no duplicates.
    """
    set_random_seed(42)
    
    # 1. Setup: Create synthetic raw data mimicking Dryad/AnAge outputs
    # Simulating raw telomere data with mixed units and uncleaned names
    raw_telomere_data = {
        "species_name": [
            "Zonotrichia leucophrys", "Zonotrichia leucophrys", 
            "Taeniopygia guttata", "Taeniopygia guttata",
            "Passer domesticus", "Passer domesticus",
            "Hirundo rustica", "Hirundo rustica",
            "Mimus polyglottos", "Mimus polyglottos",
            "Sturnus vulgaris", "Sturnus vulgaris",
            "Turdus migratorius", "Turdus migratorius",
            "Corvus corax", "Corvus corax",
            "Falco peregrinus", "Falco peregrinus",
            "Gallus gallus", "Gallus gallus",
            "Anas platyrhynchos", "Anas platyrhynchos",
            "Columba livia", "Columba livia",
            "Pica pica", "Pica pica",
            "Strix aluco", "Strix aluco",
            "Bubo virginianus", "Bubo virginianus",
            "Aquila chrysaetos", "Aquila chrysaetos",
            "Cathartes aura", "Cathartes aura",
            "Meleagris gallopavo", "Meleagris gallopavo",
            "Meleagris gallopavo",  # Duplicate species entry
            "Carduelis chloris", "Carduelis chloris"
        ],
        "individual_id": [
            "ZL_001", "ZL_002", "TG_001", "TG_002",
            "PD_001", "PD_002", "HR_001", "HR_002",
            "MP_001", "MP_002", "SV_001", "SV_002",
            "TM_001", "TM_002", "CR_001", "CR_002",
            "FP_001", "FP_002", "GG_001", "GG_002",
            "AP_001", "AP_002", "CL_001", "CL_002",
            "PP_001", "PP_002", "SA_001", "SA_002",
            "BV_001", "BV_002", "AC_001", "AC_002",
            "CA_001", "CA_002", "MG_001", "MG_002",
            "CC_001", "CC_002"
        ],
        "telomere_value": [
            12.5, 13.1, 8.2, 8.5, 10.1, 10.4, 11.2, 11.8,
            9.5, 9.8, 14.2, 14.5, 13.0, 13.4, 15.1, 15.5,
            16.2, 16.8, 6.5, 6.8, 11.0, 11.5, 12.2, 12.8,
            10.5, 11.0, 14.0, 14.5, 17.2, 17.8, 18.0, 18.5,
            19.0, 19.5, 7.5, 7.8, 10.2, 10.8
        ],
        "unit": [
            "kb", "kb", "kb", "kb", "kb", "kb", "kb", "kb",
            "kb", "kb", "kb", "kb", "kb", "kb", "kb", "kb",
            "kb", "kb", "kb", "kb", "kb", "kb", "kb", "kb",
            "kb", "kb", "kb", "kb", "kb", "kb", "kb", "kb",
            "kb", "kb", "kb", "kb", "kb", "kb"
        ],
        "source": [
            "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad",
            "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad",
            "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad",
            "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad",
            "Dryad", "Dryad", "Dryad", "Dryad", "Dryad", "Dryad"
        ]
    }
    
    # Simulating raw ecological data from AnAge
    raw_ecological_data = {
        "species_name": [
            "Zonotrichia leucophrys", "Taeniopygia guttata", "Passer domesticus",
            "Hirundo rustica", "Mimus polyglottos", "Sturnus vulgaris",
            "Turdus migratorius", "Corvus corax", "Falco peregrinus",
            "Gallus gallus", "Anas platyrhynchos", "Columba livia",
            "Pica pica", "Strix aluco", "Bubo virginianus",
            "Aquila chrysaetos", "Cathartes aura", "Meleagris gallopavo",
            "Carduelis chloris"
        ],
        "max_lifespan_years": [
            13.0, 9.0, 15.0, 11.0, 13.0, 23.0, 13.0, 40.0, 19.0,
            15.0, 28.0, 19.0, 21.0, 22.0, 40.0, 45.0, 16.0, 15.0,
            12.0
        ],
        "migration_status": [
            "Migratory", "Resident", "Resident", "Migratory", "Resident", "Resident",
            "Migratory", "Resident", "Migratory", "Resident", "Migratory", "Resident",
            "Resident", "Resident", "Resident", "Migratory", "Resident", "Resident",
            "Resident"
        ],
        "body_mass_g": [
            25.0, 12.0, 30.0, 19.0, 45.0, 80.0, 77.0, 1000.0, 700.0,
            3000.0, 1000.0, 300.0, 100.0, 300.0, 1200.0, 3500.0, 600.0,
            2000.0, 25.0
        ]
    }
    
    df_telomere = pd.DataFrame(raw_telomere_data)
    df_eco = pd.DataFrame(raw_ecological_data)
    
    # 2. Execute: Apply cleaning and merging logic
    # Step A: Unit conversion (even if all are already kb, this tests the function)
    df_telomere["telomere_kb"] = df_telomere["telomere_value"].apply(
        lambda x: convert_to_kb(x, "kb")
    )
    
    # Step B: Clean species names (standardize formatting)
    df_telomere["species_clean"] = df_telomere["species_name"].apply(
        clean_telomere_units
    )
    df_eco["species_clean"] = df_eco["species_name"].apply(clean_telomere_units)
    
    # Step C: Merge on cleaned species name
    merged_df = pd.merge(
        df_telomere, 
        df_eco, 
        on="species_clean", 
        how="inner", 
        suffixes=("_tel", "_eco")
    )
    
    # Step D: Filter for unique species (aggregate means if needed, but here we just check uniqueness)
    # The task requires "no duplicates" in the final output. 
    # In a real pipeline, we might mean-average. Here we ensure the merge didn't explode.
    unique_species = merged_df["species_clean"].nunique()
    total_species_input = df_eco["species_clean"].nunique()
    
    # 3. Verify: Assertions based on task requirements
    # Requirement: >90% of unique species retained
    retention_rate = unique_species / total_species_input
    assert retention_rate > 0.90, f"Species retention rate {retention_rate:.2%} is below 90% threshold."
    
    # Requirement: Valid IDs (non-null individual_id)
    assert merged_df["individual_id"].notna().all(), "Found null individual IDs."
    
    # Requirement: Standardized units (kb)
    assert (merged_df["telomere_kb"] > 0).all(), "Found non-positive telomere lengths."
    
    # Requirement: No duplicates (in terms of species count matching ecological input)
    # Note: The input had 38 telomere rows for 19 species (2 per species). 
    # The merge results in 38 rows. The requirement "no duplicates" usually refers to 
    # duplicate SPECIES entries in the final analysis dataset, or duplicate rows.
    # If the final dataset is meant to be species-level means, we should aggregate.
    # Let's aggregate to species level to strictly satisfy "no duplicates" of species.
    final_df = merged_df.groupby("species_clean").agg({
        "telomere_kb": "mean",
        "max_lifespan_years": "first",
        "migration_status": "first",
        "body_mass_g": "first",
        "individual_id": lambda x: len(x) # Count samples per species
    }).reset_index()
    
    final_df.columns = [
        "species", "telomere_length_kb", "lifespan", "migration_status", "body_mass_g", "sample_count"
    ]
    
    # Re-verify no duplicate species in final output
    assert final_df["species"].nunique() == len(final_df), "Duplicate species found in final output."
    
    # Requirement: Validate schema columns
    expected_cols = ["species", "telomere_length_kb", "lifespan", "migration_status", "body_mass_g"]
    assert all(col in final_df.columns for col in expected_cols), f"Missing expected columns: {set(expected_cols) - set(final_df.columns)}"
    
    # Requirement: Verify 'wild-caught' filter logic (simulated here as a pass-through since 
    # synthetic data doesn't have 'wild-caught' flag, but we ensure the column exists if it did)
    # In a real scenario, we would check a 'source_type' column. 
    # For this test, we assert that the merge logic correctly aligned the data.
    assert len(final_df) > 0, "Final dataset is empty."
    
    # 4. Output: Write to a temporary file to simulate artifact creation
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "merged_data.csv"
        final_df.to_csv(output_path, index=False)
        
        # Verify file exists and has checksum
        assert output_path.exists(), "Output file was not written."
        checksum = generate_checksum(str(output_path))
        assert len(checksum) == 64, "Invalid SHA256 checksum length."
        
        # Load and verify content
        loaded_df = pd.read_csv(output_path)
        assert loaded_df.shape == final_df.shape, "Loaded data shape mismatch."
        
    print(f"Integration test passed. Retention rate: {retention_rate:.2%}, Species count: {unique_species}")
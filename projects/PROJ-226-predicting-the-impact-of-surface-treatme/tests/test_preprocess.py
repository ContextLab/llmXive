import json
import os
from pathlib import Path

import pandas as pd

# Import the main function from the preprocessing script
from preprocess import main as preprocess_main

def test_preprocess_creates_outputs(tmp_path):
    """
    Run the preprocessing pipeline and verify that the expected output files are
    created and contain sensible data (no missing values, correct one‑hot columns).
    """
    # Ensure a clean environment – remove any existing cleaned artifacts
    cleaned_dir = Path(__file__).resolve().parents[1] / "data" / "cleaned"
    if cleaned_dir.exists():
        for f in cleaned_dir.iterdir():
            f.unlink()
    # Execute the preprocessing pipeline
    preprocess_main()

    # 1. Check that the cleaned CSV exists
    cleaned_csv = cleaned_dir / "cleaned.csv"
    assert cleaned_csv.is_file(), "cleaned.csv was not created"

    # Load the cleaned data
    df = pd.read_csv(cleaned_csv)

    # 2. Verify that there are no missing values
    assert not df.isna().any().any(), "Missing values remain in cleaned data"

    # 3. Verify that required one‑hot columns exist
    #   - treatment_type variants (Oxygen Plasma, Nitrogen Plasma)
    #   - pair_id variants (PP_Al, PE_Cu, PE_Al)
    expected_treatment_cols = {"treatment_type_Oxygen Plasma", "treatment_type_Nitrogen Plasma"}
    expected_pair_cols = {"pair_id_PP_Al", "pair_id_PE_Cu", "pair_id_PE_Al"}
    actual_cols = set(df.columns)

    assert expected_treatment_cols.issubset(actual_cols), f"Missing one‑hot columns for treatment_type: {expected_treatment_cols - actual_cols}"
    assert expected_pair_cols.issubset(actual_cols), f"Missing one‑hot columns for pair_id: {expected_pair_cols - actual_cols}"

    # 4. Verify that the imputation log records at least one imputed value
    impute_log_path = cleaned_dir / "imputation_log.json"
    assert impute_log_path.is_file(), "imputation_log.json was not created"
    with impute_log_path.open("r", encoding="utf-8") as f:
        impute_log = json.load(f)
    # The bad_source.csv lacks exposure_time_s, so there should be an entry for it
    assert "exposure_time_s" in impute_log, "Imputation log missing entry for exposure_time_s"
    # At least one class should have a median recorded
    exposure_impute = impute_log["exposure_time_s"]
    assert any(v is not None for v in exposure_impute.values()), "No median recorded for exposure_time_s imputation"

    # 5. Verify that field coverage JSON is created and contains expected keys
    coverage_path = cleaned_dir / "field_coverage.json"
    assert coverage_path.is_file(), "field_coverage.json was not created"
    with coverage_path.open("r", encoding="utf-8") as f:
        coverage = json.load(f)
    # All original columns should be present in the coverage report
    original_columns = ["plasma_power_w", "exposure_time_s", "chemical_concentration_pct",
                        "polymer_surface_energy", "substrate_roughness_nm",
                        "adhesion_strength_mj_m2", "treatment_type", "pair_id"]
    for col in original_columns:
        assert col in coverage, f"Coverage report missing column {col}"

    # Clean up (optional, not required for CI)
    # for f in cleaned_dir.iterdir():
    #     f.unlink()
import pathlib
import pandas as pd
from src.data.clean import main as clean_main

def test_clean_outputs_exist(tmp_path, monkeypatch):
    """
    Integration‑style test that runs the cleaning script and checks that
    the expected artefacts are produced and contain the required columns.
    """
    # Run the cleaning script (it uses project‑relative paths)
    clean_main()

    # Paths to expected outputs
    cleaned_parquet = pathlib.Path("data/processed/cleaned.parquet")
    summary_log = pathlib.Path("logs/clean_summary.txt")
    validate_log = pathlib.Path("logs/validate_clean_pass.txt")

    assert cleaned_parquet.is_file(), "cleaned.parquet not created"
    assert summary_log.is_file(), "clean_summary.txt not created"
    assert validate_log.is_file(), "validate_clean_pass.txt not created"

    # Load a few rows to verify column presence
    df = pd.read_parquet(cleaned_parquet, columns=["VAERS_ID", "VAX_GROUP", "SOC_CODE", "SOC_NAME", "REPT_DATE"])
    required = {"VAERS_ID", "VAX_GROUP", "SOC_CODE", "SOC_NAME", "REPT_DATE"}
    assert required.issubset(set(df.columns)), f"Missing required columns: {required - set(df.columns)}"